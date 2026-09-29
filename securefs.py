"""
SecureFS — Minimal Encrypted Filesystem Prototype
================================================
College Project Prototype: Encrypted Storage, Integrity Verification, Audit Logging & Secure Deletion.
"""

import os
import json
import hashlib
import secrets
from datetime import datetime

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False


class SecureFS:
    def __init__(self, storage_dir="encrypted_storage", log_file="audit.log"):
        self.storage_dir = storage_dir
        self.log_file = log_file
        os.makedirs(self.storage_dir, exist_ok=True)

    def _log(self, action, filename, status, details=""):
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "action": action,
            "filename": filename,
            "status": status,
            "details": details
        }
        with open(self.log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def _derive_key(self, password: str, salt: bytes) -> bytes:
        if HAS_CRYPTOGRAPHY:
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            return kdf.derive(password.encode())
        else:
            return hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000, dklen=32)

    def write_file(self, filename: str, data: bytes, password: str) -> str:
        """Encrypts data and saves it to storage directory."""
        salt = secrets.token_bytes(16)
        key = self._derive_key(password, salt)
        target_path = os.path.join(self.storage_dir, filename + ".sfs")

        if HAS_CRYPTOGRAPHY:
            aesgcm = AESGCM(key)
            nonce = secrets.token_bytes(12)
            ciphertext = aesgcm.encrypt(nonce, data, None)
            payload = salt + nonce + ciphertext
        else:
            nonce = secrets.token_bytes(16)
            keystream = hashlib.sha256(key + nonce).digest()
            while len(keystream) < len(data):
                keystream += hashlib.sha256(key + keystream).digest()
            cipher_bytes = bytes([b ^ k for b, k in zip(data, keystream[:len(data)])])
            mac = hashlib.hmac.new(key, nonce + cipher_bytes, hashlib.sha256).digest()
            payload = salt + nonce + mac + cipher_bytes

        with open(target_path, "wb") as f:
            f.write(payload)

        self._log("WRITE", filename, "SUCCESS", f"Encrypted size: {len(payload)} bytes")
        return target_path

    def read_file(self, filename: str, password: str) -> bytes:
        """Decrypts and verifies file integrity."""
        target_path = os.path.join(self.storage_dir, filename + ".sfs")
        if not os.path.exists(target_path):
            self._log("READ", filename, "FAILED", "File not found")
            raise FileNotFoundError(f"File '{filename}' not found.")

        with open(target_path, "rb") as f:
            payload = f.read()

        try:
            if HAS_CRYPTOGRAPHY:
                salt = payload[:16]
                nonce = payload[16:28]
                ciphertext = payload[28:]
                key = self._derive_key(password, salt)
                aesgcm = AESGCM(key)
                plaintext = aesgcm.decrypt(nonce, ciphertext, None)
            else:
                salt = payload[:16]
                nonce = payload[16:32]
                mac = payload[32:64]
                cipher_bytes = payload[64:]
                key = self._derive_key(password, salt)
                expected_mac = hashlib.hmac.new(key, nonce + cipher_bytes, hashlib.sha256).digest()
                if not secrets.compare_digest(mac, expected_mac):
                    raise ValueError("MAC mismatch: file tampered or wrong password")
                keystream = hashlib.sha256(key + nonce).digest()
                while len(keystream) < len(cipher_bytes):
                    keystream += hashlib.sha256(key + keystream).digest()
                plaintext = bytes([b ^ k for b, k in zip(cipher_bytes, keystream[:len(cipher_bytes)])])

            self._log("READ", filename, "SUCCESS", f"Decrypted {len(plaintext)} bytes")
            return plaintext
        except Exception as e:
            self._log("READ", filename, "ALERT_TAMPER_OR_AUTH_FAIL", str(e))
            raise PermissionError("Access Denied: Incorrect password or corrupted/tampered file!")

    def secure_delete(self, filename: str, password: str):
        """Securely shreds file before unlinking."""
        self.read_file(filename, password)  # verify auth first
        target_path = os.path.join(self.storage_dir, filename + ".sfs")

        length = os.path.getsize(target_path)
        with open(target_path, "wb") as f:
            for _ in range(3):
                f.seek(0)
                f.write(secrets.token_bytes(length))
                f.flush()
                os.fsync(f.fileno())

        os.remove(target_path)
        self._log("SECURE_DELETE", filename, "SUCCESS", "Shredded (3 passes) and removed")
