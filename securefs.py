"""
SecureFS — Secure Encrypted Filesystem & Vault Engine
=====================================================
User-space encrypted file vault with AES-256-GCM, PBKDF2-HMAC-SHA256,
cryptographic tamper detection, JSON-lines audit logging, and secure shredding.

Security Architecture:
- Primary Cipher: AES-256-GCM (Authenticated Encryption with Associated Data - AEAD).
- Key Derivation: PBKDF2-HMAC-SHA256 with 16-byte cryptographically secure random salt.
  * Modern Format (v2): 600,000 iterations (OWASP recommendation), versioned header with AAD.
  * Legacy Format (v1): 100,000 iterations for 100% backward compatibility with existing .sfs files.
- Nonce/IV: 12-byte cryptographically secure random nonce generated per encryption.
- Tamper Detection: 16-byte GHASH authentication tag checked prior to decryption.
- Secure Deletion: 3-pass overwrite with random bytes + fsync before unlinking.
  * Disclaimer: Best-effort user-space shredding. Flash wear-leveling (SSDs/NVMe),
    copy-on-write filesystems (Btrfs, ZFS), and journaling may retain underlying blocks.
"""

import os
import hmac
import json
import struct
import hashlib
import secrets
from datetime import datetime, timezone
from typing import List, Dict, Optional, Tuple, Any

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False

# Constants
MAGIC_V2 = b"SFS\x02"
LEGACY_ITERATIONS = 100000
MODERN_ITERATIONS = 600000
SALT_SIZE = 16
NONCE_SIZE = 12
TAG_SIZE = 16
LEGACY_MIN_SIZE = SALT_SIZE + NONCE_SIZE + TAG_SIZE  # 44 bytes


class SecureFS:
    """User-space encrypted filesystem and vault management engine."""

    def __init__(self, storage_dir: str = "encrypted_storage", log_file: str = "audit.log"):
        self.storage_dir = os.path.abspath(storage_dir)
        self.log_file = os.path.abspath(log_file)
        os.makedirs(self.storage_dir, exist_ok=True)
        # Ensure log directory exists if nested
        log_dir = os.path.dirname(self.log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

    # -------------------------------------------------------------------------
    # Internal Helpers & Security Primitives
    # -------------------------------------------------------------------------

    def _get_utc_timestamp(self) -> str:
        """Returns standard ISO-8601 UTC timestamp string."""
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    def _log(self, action: str, filename: str, status: str, details: str = ""):
        """Appends an event to the JSON-lines audit log securely. Never logs passwords/keys."""
        entry = {
            "timestamp": self._get_utc_timestamp(),
            "action": action,
            "filename": filename,
            "status": status,
            "details": details
        }
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception:
            # Audit logging failure should not crash execution but should be handled safely
            pass

    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitizes a filename to prevent path traversal attacks.
        Strips directory components and rejects empty or unsafe names.
        """
        if not filename or not isinstance(filename, str):
            raise ValueError("Invalid filename: must be a non-empty string.")

        # Strip directory path
        clean = os.path.basename(filename.strip())

        # Strip .sfs extension if already provided to prevent double extension
        if clean.endswith(".sfs"):
            clean = clean[:-4]

        # Prevent empty or dangerous names
        if not clean or clean in (".", "..") or "\x00" in clean:
            raise ValueError("Invalid filename: path traversal or invalid characters detected.")

        return clean

    def _derive_key(self, password: str, salt: bytes, iterations: int = MODERN_ITERATIONS) -> bytes:
        """Derives a 256-bit encryption key using PBKDF2-HMAC-SHA256."""
        if not isinstance(password, str) or not password:
            raise ValueError("Password must be a non-empty string.")

        if HAS_CRYPTOGRAPHY:
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=iterations,
            )
            return kdf.derive(password.encode("utf-8"))
        else:
            return hashlib.pbkdf2_hmac(
                "sha256",
                password.encode("utf-8"),
                salt,
                iterations,
                dklen=32
            )

    # -------------------------------------------------------------------------
    # Encryption (Write)
    # -------------------------------------------------------------------------

    def write_file(
        self,
        filename: str,
        data: bytes,
        password: str,
        overwrite: bool = False,
        format_version: int = 2,
        iterations: int = MODERN_ITERATIONS
    ) -> str:
        """
        Encrypts plaintext data and atomically saves it to the vault storage directory.

        Args:
            filename: Target base filename (e.g. 'report.pdf').
            data: Raw binary plaintext payload.
            password: Secret encryption passphrase.
            overwrite: If False, raises FileExistsError if target .sfs file exists.
            format_version: 2 (modern versioned format) or 1 (legacy unversioned).
            iterations: PBKDF2 iteration rounds (default 600,000 for v2, 100,000 for v1).

        Returns:
            Absolute path to the created .sfs encrypted container.
        """
        if not isinstance(data, (bytes, bytearray)):
            raise TypeError("Data must be bytes or bytearray.")
        data = bytes(data)

        clean_name = self._sanitize_filename(filename)
        target_path = os.path.join(self.storage_dir, clean_name + ".sfs")

        if os.path.exists(target_path) and not overwrite:
            self._log("WRITE", clean_name, "FAILED", "Destination file already exists (overwrite=False)")
            raise FileExistsError(f"Vault file '{clean_name}.sfs' already exists. Set overwrite=True to replace.")

        salt = secrets.token_bytes(SALT_SIZE)
        nonce = secrets.token_bytes(NONCE_SIZE)

        if format_version == 1:
            # Legacy format compatibility
            actual_iterations = LEGACY_ITERATIONS
            key = self._derive_key(password, salt, actual_iterations)
            if HAS_CRYPTOGRAPHY:
                aesgcm = AESGCM(key)
                ciphertext = aesgcm.encrypt(nonce, data, None)
                payload = salt + nonce + ciphertext
            else:
                # Cryptography library required for AES-GCM
                raise RuntimeError("The 'cryptography' library is required for AES-256-GCM operations.")
        else:
            # Modern v2 versioned format with authenticated header (AAD)
            actual_iterations = iterations
            key = self._derive_key(password, salt, actual_iterations)

            header_meta = {
                "v": 2,
                "kdf": "pbkdf2-sha256",
                "iter": actual_iterations,
                "orig_name": clean_name,
                "created_at": self._get_utc_timestamp(),
                "size": len(data)
            }
            header_bytes = json.dumps(header_meta, separators=(",", ":")).encode("utf-8")
            if len(header_bytes) > 65535:
                raise ValueError("Metadata header exceeds maximum allowed size.")

            # Structure: [MAGIC_V2 (4B)] + [HEADER_LEN (2B uint16)] + [HEADER_BYTES]
            aad_prefix = MAGIC_V2 + struct.pack(">H", len(header_bytes)) + header_bytes

            if HAS_CRYPTOGRAPHY:
                aesgcm = AESGCM(key)
                # Authenticate aad_prefix along with salt and nonce
                # Encrypted payload: salt (16B) + nonce (12B) + ciphertext+tag
                ciphertext = aesgcm.encrypt(nonce, data, aad_prefix)
                payload = aad_prefix + salt + nonce + ciphertext
            else:
                raise RuntimeError("The 'cryptography' library is required for AES-256-GCM operations.")

        # Atomic write pattern: write to temporary file then replace
        temp_filename = f".{clean_name}.{secrets.token_hex(6)}.tmp"
        temp_path = os.path.join(self.storage_dir, temp_filename)

        try:
            with open(temp_path, "wb") as f:
                f.write(payload)
                f.flush()
                os.fsync(f.fileno())

            os.replace(temp_path, target_path)
        except Exception as e:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass
            self._log("WRITE", clean_name, "FAILED", f"I/O Error: {str(e)}")
            raise

        self._log(
            "WRITE",
            clean_name,
            "SUCCESS",
            f"Encrypted size: {len(payload)} bytes (v{format_version}, {actual_iterations} rounds)"
        )
        return target_path

    # -------------------------------------------------------------------------
    # Decryption (Read)
    # -------------------------------------------------------------------------

    def read_file(self, filename: str, password: str) -> bytes:
        """
        Decrypts an encrypted .sfs container and verifies cryptographic integrity.

        Args:
            filename: Target base filename or full filename.
            password: Secret encryption passphrase.

        Returns:
            Decrypted plaintext bytes.

        Raises:
            FileNotFoundError: If the .sfs file does not exist.
            ValueError: If file container is truncated or structurally invalid.
            PermissionError: If authentication fails (wrong password or tampered data).
        """
        clean_name = self._sanitize_filename(filename)
        target_path = os.path.join(self.storage_dir, clean_name + ".sfs")

        if not os.path.exists(target_path):
            self._log("READ", clean_name, "FAILED", "File not found")
            raise FileNotFoundError(f"Vault file '{clean_name}.sfs' not found.")

        try:
            with open(target_path, "rb") as f:
                payload = f.read()
        except Exception as e:
            self._log("READ", clean_name, "FAILED", f"Read error: {str(e)}")
            raise

        plaintext = self._decrypt_payload(payload, password, clean_name)
        self._log("READ", clean_name, "SUCCESS", f"Decrypted {len(plaintext)} bytes")
        return plaintext

    def _decrypt_payload(self, payload: bytes, password: str, clean_name: str) -> bytes:
        """Internal worker to parse container format and decrypt payload."""
        if not HAS_CRYPTOGRAPHY:
            raise RuntimeError("The 'cryptography' library is required for AES-256-GCM operations.")

        # Check if v2 container
        if payload.startswith(MAGIC_V2):
            if len(payload) < len(MAGIC_V2) + 2:
                self._log("READ", clean_name, "ALERT_TAMPER_OR_AUTH_FAIL", "Container truncated (v2 header missing)")
                raise PermissionError("Access Denied: Incorrect password or corrupted/tampered file!")

            header_len = struct.unpack(">H", payload[4:6])[0]
            header_end = 6 + header_len
            if len(payload) < header_end + SALT_SIZE + NONCE_SIZE + TAG_SIZE:
                self._log("READ", clean_name, "ALERT_TAMPER_OR_AUTH_FAIL", "Container truncated (v2 body incomplete)")
                raise PermissionError("Access Denied: Incorrect password or corrupted/tampered file!")

            aad_prefix = payload[:header_end]
            try:
                header_data = json.loads(payload[6:header_end].decode("utf-8"))
            except Exception:
                self._log("READ", clean_name, "ALERT_TAMPER_OR_AUTH_FAIL", "Corrupted metadata header")
                raise PermissionError("Access Denied: Incorrect password or corrupted/tampered file!")

            iterations = header_data.get("iter", MODERN_ITERATIONS)
            offset = header_end
            salt = payload[offset:offset + SALT_SIZE]
            offset += SALT_SIZE
            nonce = payload[offset:offset + NONCE_SIZE]
            offset += NONCE_SIZE
            ciphertext = payload[offset:]

            try:
                key = self._derive_key(password, salt, iterations)
                aesgcm = AESGCM(key)
                plaintext = aesgcm.decrypt(nonce, ciphertext, aad_prefix)
                return plaintext
            except Exception as e:
                self._log("READ", clean_name, "ALERT_TAMPER_OR_AUTH_FAIL", f"Auth failure: {type(e).__name__}")
                raise PermissionError("Access Denied: Incorrect password or corrupted/tampered file!")

        else:
            # Legacy v1 container
            if len(payload) < LEGACY_MIN_SIZE:
                self._log("READ", clean_name, "ALERT_TAMPER_OR_AUTH_FAIL", f"Container size too small ({len(payload)}B)")
                raise PermissionError("Access Denied: Incorrect password or corrupted/tampered file!")

            salt = payload[:SALT_SIZE]
            nonce = payload[SALT_SIZE:SALT_SIZE + NONCE_SIZE]
            ciphertext = payload[SALT_SIZE + NONCE_SIZE:]

            try:
                key = self._derive_key(password, salt, LEGACY_ITERATIONS)
                aesgcm = AESGCM(key)
                plaintext = aesgcm.decrypt(nonce, ciphertext, None)
                return plaintext
            except Exception as e:
                self._log("READ", clean_name, "ALERT_TAMPER_OR_AUTH_FAIL", f"Auth failure: {type(e).__name__}")
                raise PermissionError("Access Denied: Incorrect password or corrupted/tampered file!")

    # -------------------------------------------------------------------------
    # Integrity Verification (Without plain export)
    # -------------------------------------------------------------------------

    def verify_integrity(self, filename: str, password: str) -> Tuple[bool, str]:
        """
        Verifies the cryptographic authentication tag of an encrypted file
        without persisting or returning plaintext data.

        Returns:
            Tuple of (is_valid: bool, status_message: str)
        """
        clean_name = self._sanitize_filename(filename)
        target_path = os.path.join(self.storage_dir, clean_name + ".sfs")

        if not os.path.exists(target_path):
            return False, f"File '{clean_name}.sfs' not found in vault."

        try:
            self.read_file(clean_name, password)
            self._log("VERIFY", clean_name, "SUCCESS", "Integrity verified (Authentication Tag OK)")
            return True, "Integrity verified successfully: Authenticated and untampered."
        except PermissionError:
            self._log("VERIFY", clean_name, "ALERT_TAMPER_OR_AUTH_FAIL", "Verification failed: bad password or tampered tag")
            return False, "Authentication failed: Incorrect password or corrupted/tampered ciphertext."
        except Exception as e:
            self._log("VERIFY", clean_name, "FAILED", str(e))
            return False, f"Verification error: {str(e)}"

    # -------------------------------------------------------------------------
    # Secure Shredding & Deletion
    # -------------------------------------------------------------------------

    def secure_delete(self, filename: str, password: str) -> bool:
        """
        Authenticates caller password, overwrites file 3 times with cryptographically
        random bytes, forces filesystem sync, and removes the file.

        Storage Disclaimer:
        On modern flash storage (SSDs, NVMe wear-leveling controllers) and
        copy-on-write filesystems (Btrfs, ZFS, snapshots), user-space overwriting
        is best-effort and does not guarantee physical NAND gate erasure.
        """
        clean_name = self._sanitize_filename(filename)
        target_path = os.path.join(self.storage_dir, clean_name + ".sfs")

        if not os.path.exists(target_path):
            self._log("SECURE_DELETE", clean_name, "FAILED", "File not found")
            raise FileNotFoundError(f"File '{clean_name}' not found.")

        # Authenticate first to prevent unauthorized deletion
        self.read_file(clean_name, password)

        length = os.path.getsize(target_path)
        try:
            with open(target_path, "wb") as f:
                for _ in range(3):
                    f.seek(0)
                    f.write(secrets.token_bytes(length))
                    f.flush()
                    os.fsync(f.fileno())

            os.remove(target_path)
            self._log("SECURE_DELETE", clean_name, "SUCCESS", "Shredded (3 passes + fsync) and removed")
            return True
        except Exception as e:
            self._log("SECURE_DELETE", clean_name, "FAILED", f"Error during shredding: {str(e)}")
            raise

    # -------------------------------------------------------------------------
    # File Import & Export Utilities
    # -------------------------------------------------------------------------

    def import_file(
        self,
        src_path: str,
        password: str,
        target_filename: Optional[str] = None,
        overwrite: bool = False,
        format_version: int = 2,
        iterations: int = MODERN_ITERATIONS
    ) -> str:
        """
        Reads a file from the host filesystem, encrypts it, and writes it to the vault.
        """
        src_path = os.path.abspath(src_path)
        if not os.path.isfile(src_path):
            raise FileNotFoundError(f"Source file '{src_path}' not found.")

        base_name = target_filename or os.path.basename(src_path)
        with open(src_path, "rb") as f:
            data = f.read()

        return self.write_file(
            filename=base_name,
            data=data,
            password=password,
            overwrite=overwrite,
            format_version=format_version,
            iterations=iterations
        )

    def export_file(
        self,
        filename: str,
        password: str,
        dest_path: str,
        overwrite: bool = False
    ) -> str:
        """
        Decrypts a vault entry and safely writes the plaintext to the given destination path.
        """
        dest_path = os.path.abspath(dest_path)

        # If dest_path is a directory, append the original or decrypted filename
        if os.path.isdir(dest_path):
            clean_name = self._sanitize_filename(filename)
            dest_path = os.path.join(dest_path, clean_name)

        if os.path.exists(dest_path) and not overwrite:
            raise FileExistsError(f"Destination file '{dest_path}' already exists.")

        plaintext = self.read_file(filename, password)

        dest_dir = os.path.dirname(dest_path)
        if dest_dir:
            os.makedirs(dest_dir, exist_ok=True)

        temp_dest = os.path.join(dest_dir or ".", f".tmp_export_{secrets.token_hex(6)}")
        try:
            with open(temp_dest, "wb") as f:
                f.write(plaintext)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temp_dest, dest_path)
        finally:
            if os.path.exists(temp_dest):
                try:
                    os.remove(temp_dest)
                except OSError:
                    pass

        self._log("EXPORT", self._sanitize_filename(filename), "SUCCESS", f"Exported to {dest_path}")
        return dest_path

    # -------------------------------------------------------------------------
    # Vault Inventory & Statistics
    # -------------------------------------------------------------------------

    def list_vault_files(self) -> List[Dict[str, Any]]:
        """
        Inspects the storage directory and returns metadata for all .sfs files.
        """
        files = []
        if not os.path.exists(self.storage_dir):
            return files

        for entry in os.scandir(self.storage_dir):
            if entry.is_file() and entry.name.endswith(".sfs") and not entry.name.startswith("."):
                file_path = entry.path
                size = entry.stat().st_size
                mtime = datetime.fromtimestamp(entry.stat().st_mtime, tz=timezone.utc).isoformat().replace("+00:00", "Z")
                base_name = entry.name[:-4]

                # Inspect header without decrypting
                version = "v1 (Legacy)"
                is_valid = True
                orig_name = base_name

                try:
                    with open(file_path, "rb") as f:
                        header_sample = f.read(64)

                    if header_sample.startswith(MAGIC_V2):
                        version = "v2 (Modern)"
                        if len(header_sample) >= 6:
                            h_len = struct.unpack(">H", header_sample[4:6])[0]
                            with open(file_path, "rb") as f:
                                full_header = f.read(6 + h_len)
                            if len(full_header) >= 6 + h_len:
                                meta = json.loads(full_header[6:6 + h_len].decode("utf-8"))
                                orig_name = meta.get("orig_name", base_name)
                    elif len(header_sample) < LEGACY_MIN_SIZE:
                        is_valid = False
                except Exception:
                    is_valid = False

                files.append({
                    "filename": base_name,
                    "sfs_name": entry.name,
                    "path": file_path,
                    "size_bytes": size,
                    "modified": mtime,
                    "version": version,
                    "is_valid": is_valid,
                    "orig_name": orig_name
                })

        files.sort(key=lambda x: x["filename"].lower())
        return files

    def get_vault_stats(self) -> Dict[str, Any]:
        """Returns high-level statistics for the active vault."""
        files = self.list_vault_files()
        total_size = sum(f["size_bytes"] for f in files)
        log_count = 0
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, "r", encoding="utf-8", errors="ignore") as f:
                    log_count = sum(1 for line in f if line.strip())
            except Exception:
                log_count = 0

        return {
            "file_count": len(files),
            "total_bytes": total_size,
            "storage_dir": self.storage_dir,
            "log_file": self.log_file,
            "log_entries_count": log_count,
            "cipher": "AES-256-GCM",
            "kdf": "PBKDF2-HMAC-SHA256",
            "modern_iterations": MODERN_ITERATIONS,
            "legacy_iterations": LEGACY_ITERATIONS,
        }

    # -------------------------------------------------------------------------
    # Audit Log Inspection
    # -------------------------------------------------------------------------

    def parse_audit_log(
        self,
        max_entries: int = 1000,
        action_filter: Optional[str] = None,
        status_filter: Optional[str] = None,
        search_query: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """
        Safely reads and filters audit log entries from the JSON-lines log file.
        Gracefully handles corrupted, malformed, or incomplete lines.
        """
        entries = []
        if not os.path.exists(self.log_file):
            return entries

        try:
            with open(self.log_file, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()

            # Process most recent first
            for line in reversed(lines):
                line = line.strip()
                if not line:
                    continue
                try:
                    item = json.loads(line)
                    if not isinstance(item, dict):
                        continue

                    # Filter by action
                    if action_filter and action_filter.upper() != "ALL":
                        if item.get("action", "").upper() != action_filter.upper():
                            continue

                    # Filter by status
                    if status_filter and status_filter.upper() != "ALL":
                        if item.get("status", "").upper() != status_filter.upper():
                            continue

                    # Search query across filename, action, or details
                    if search_query:
                        sq = search_query.lower()
                        match = (
                            sq in item.get("filename", "").lower() or
                            sq in item.get("action", "").lower() or
                            sq in item.get("status", "").lower() or
                            sq in item.get("details", "").lower()
                        )
                        if not match:
                            continue

                    entries.append(item)
                    if len(entries) >= max_entries:
                        break
                except json.JSONDecodeError:
                    # Record corrupted line as an anomaly entry
                    entries.append({
                        "timestamp": "UNKNOWN",
                        "action": "CORRUPTED_ENTRY",
                        "filename": "-",
                        "status": "MALFORMED_JSON",
                        "details": line[:100]
                    })
        except Exception as e:
            entries.append({
                "timestamp": self._get_utc_timestamp(),
                "action": "LOG_READ_ERROR",
                "filename": "-",
                "status": "FAILED",
                "details": str(e)
            })

        return entries

    def clear_audit_log(self):
        """Clears the audit log file after logging a CLEAR action."""
        entry = {
            "timestamp": self._get_utc_timestamp(),
            "action": "AUDIT_LOG_CLEARED",
            "filename": "-",
            "status": "SUCCESS",
            "details": "Audit log reset by authorized user"
        }
        with open(self.log_file, "w", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
