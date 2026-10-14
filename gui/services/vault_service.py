"""
SecureFS — GUI Service Layer & Asynchronous Background Workers
==============================================================
Ensures cryptographic operations (PBKDF2 key derivation, file I/O,
large file encryption/decryption) never freeze the Qt GUI thread.
"""

import os
import secrets
from typing import Optional, List, Dict, Any
from PySide6.QtCore import QObject, QThread, Signal

from securefs import SecureFS, MODERN_ITERATIONS, LEGACY_ITERATIONS


class EncryptWorker(QThread):
    """Background worker for encrypting a file into the vault."""
    progress = Signal(int, str)
    finished = Signal(bool, str, str)  # (success, path_or_error, detail)

    def __init__(
        self,
        fs: SecureFS,
        src_path: str,
        target_name: str,
        password: str,
        overwrite: bool = False,
        format_version: int = 2,
        iterations: int = MODERN_ITERATIONS,
        wipe_source: bool = False,
        parent: Optional[QObject] = None
    ):
        super().__init__(parent)
        self.fs = fs
        self.src_path = src_path
        self.target_name = target_name
        self.password = password
        self.overwrite = overwrite
        self.format_version = format_version
        self.iterations = iterations
        self.wipe_source = wipe_source

    def run(self):
        try:
            self.progress.emit(15, "Reading plaintext source file...")
            if not os.path.isfile(self.src_path):
                self.finished.emit(False, "", f"Source file '{self.src_path}' not found.")
                return

            file_size = os.path.getsize(self.src_path)
            with open(self.src_path, "rb") as f:
                data = f.read()

            self.progress.emit(40, f"Deriving key (PBKDF2 {self.iterations:,} rounds)...")
            self.progress.emit(70, "Encrypting payload (AES-256-GCM)...")

            out_path = self.fs.write_file(
                filename=self.target_name,
                data=data,
                password=self.password,
                overwrite=self.overwrite,
                format_version=self.format_version,
                iterations=self.iterations
            )

            # Optional secure wipe of plaintext source file if requested
            if self.wipe_source:
                self.progress.emit(90, "Securely shredding plaintext source file...")
                try:
                    with open(self.src_path, "wb") as f:
                        for _ in range(3):
                            f.seek(0)
                            f.write(secrets.token_bytes(file_size))
                            f.flush()
                            os.fsync(f.fileno())
                    os.remove(self.src_path)
                except Exception as wipe_err:
                    self.finished.emit(
                        True,
                        out_path,
                        f"File encrypted, but source wipe had notice: {str(wipe_err)}"
                    )
                    return

            self.progress.emit(100, "Encryption completed successfully.")
            self.finished.emit(True, out_path, "File encrypted and saved to vault successfully.")
        except FileExistsError as fe:
            self.finished.emit(False, "", str(fe))
        except Exception as e:
            self.finished.emit(False, "", f"Encryption failed: {str(e)}")


class DecryptWorker(QThread):
    """Background worker for decrypting and exporting a vault entry."""
    progress = Signal(int, str)
    finished = Signal(bool, str, str)  # (success, path_or_error, detail)

    def __init__(
        self,
        fs: SecureFS,
        filename: str,
        password: str,
        dest_path: str,
        overwrite: bool = False,
        parent: Optional[QObject] = None
    ):
        super().__init__(parent)
        self.fs = fs
        self.filename = filename
        self.password = password
        self.dest_path = dest_path
        self.overwrite = overwrite

    def run(self):
        try:
            self.progress.emit(20, "Loading encrypted container...")
            self.progress.emit(50, "Deriving key & verifying AEAD tag...")
            out_file = self.fs.export_file(
                filename=self.filename,
                password=self.password,
                dest_path=self.dest_path,
                overwrite=self.overwrite
            )
            self.progress.emit(100, "Decryption and export completed.")
            self.finished.emit(True, out_file, "Decrypted and exported successfully.")
        except PermissionError:
            self.finished.emit(
                False,
                "",
                "Access Denied: Incorrect passphrase or tampered container! Authentication tag mismatch."
            )
        except FileExistsError as fe:
            self.finished.emit(False, "", str(fe))
        except Exception as e:
            self.finished.emit(False, "", f"Decryption failed: {str(e)}")


class VerifyWorker(QThread):
    """Background worker for verifying cryptographic container integrity."""
    finished = Signal(bool, str)  # (is_valid, message)

    def __init__(
        self,
        fs: SecureFS,
        filename: str,
        password: str,
        parent: Optional[QObject] = None
    ):
        super().__init__(parent)
        self.fs = fs
        self.filename = filename
        self.password = password

    def run(self):
        try:
            ok, msg = self.fs.verify_integrity(self.filename, self.password)
            self.finished.emit(ok, msg)
        except Exception as e:
            self.finished.emit(False, f"Verification error: {str(e)}")


class ShredWorker(QThread):
    """Background worker for shredding and unlinking a vault file."""
    finished = Signal(bool, str)

    def __init__(
        self,
        fs: SecureFS,
        filename: str,
        password: str,
        parent: Optional[QObject] = None
    ):
        super().__init__(parent)
        self.fs = fs
        self.filename = filename
        self.password = password

    def run(self):
        try:
            self.fs.secure_delete(self.filename, self.password)
            self.finished.emit(True, f"File '{self.filename}.sfs' authenticated and shredded (3 passes).")
        except PermissionError:
            self.finished.emit(False, "Access Denied: Incorrect password. Shredding aborted to prevent unauthorized deletion.")
        except Exception as e:
            self.finished.emit(False, f"Shredding failed: {str(e)}")


class ScanVaultWorker(QThread):
    """Background worker to scan vault inventory and compute stats."""
    finished = Signal(list, dict)  # (files_list, stats_dict)

    def __init__(self, fs: SecureFS, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.fs = fs

    def run(self):
        files = self.fs.list_vault_files()
        stats = self.fs.get_vault_stats()
        self.finished.emit(files, stats)


class VaultService(QObject):
    """Central service coordinator for the GUI application."""
    vaultChanged = Signal()

    def __init__(
        self,
        storage_dir: str = "encrypted_storage",
        log_file: str = "audit.log",
        parent: Optional[QObject] = None
    ):
        super().__init__(parent)
        self.fs = SecureFS(storage_dir=storage_dir, log_file=log_file)

    def set_storage_dir(self, new_dir: str):
        """Switches the active vault directory."""
        self.fs = SecureFS(storage_dir=new_dir, log_file=self.fs.log_file)
        self.vaultChanged.emit()

    def set_log_file(self, new_log_file: str):
        """Switches the audit log file path."""
        self.fs = SecureFS(storage_dir=self.fs.storage_dir, log_file=new_log_file)
        self.vaultChanged.emit()

    def get_stats(self) -> Dict[str, Any]:
        return self.fs.get_vault_stats()

    def get_files(self) -> List[Dict[str, Any]]:
        return self.fs.list_vault_files()

    def get_audit_logs(
        self,
        max_entries: int = 1000,
        action: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[Dict[str, str]]:
        return self.fs.parse_audit_log(
            max_entries=max_entries,
            action_filter=action,
            status_filter=status,
            search_query=search
        )
