"""
Unit and Integration Tests for SecureFS Backend Engine
======================================================
Tests encryption, decryption, authentication tags, tampering,
backward compatibility, audit logging, and edge cases.
"""

import os
import shutil
import tempfile
import pytest
from securefs import SecureFS, MODERN_ITERATIONS, LEGACY_ITERATIONS


@pytest.fixture
def temp_vault():
    """Provides an isolated temporary vault environment."""
    tmp_dir = tempfile.mkdtemp(prefix="securefs_test_vault_")
    log_path = os.path.join(tmp_dir, "test_audit.log")
    fs = SecureFS(storage_dir=tmp_dir, log_file=log_path)
    yield fs, tmp_dir, log_path
    shutil.rmtree(tmp_dir, ignore_errors=True)


class TestSecureFSBackend:

    def test_text_file_encryption_decryption(self, temp_vault):
        fs, tmp_dir, _ = temp_vault
        payload = b"Top secret operational intelligence report.\nLine 2.\n"
        password = "MasterPassword2026!"

        # Write
        path = fs.write_file("intel_report.txt", payload, password)
        assert os.path.exists(path)
        assert path.endswith("intel_report.txt.sfs")

        # Read back
        decrypted = fs.read_file("intel_report.txt", password)
        assert decrypted == payload

    def test_binary_image_and_pdf_roundtrip(self, temp_vault):
        fs, tmp_dir, _ = temp_vault
        password = "BinaryEncryptionKey99#"

        # Synthetic PDF bytes
        synthetic_pdf = b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n1 0 obj\n<< /Length 12 >>\nstream\nBinaryTest\nendstream\nendobj\n%%EOF"
        fs.write_file("doc.pdf", synthetic_pdf, password)
        dec_pdf = fs.read_file("doc.pdf", password)
        assert dec_pdf == synthetic_pdf

        # Synthetic PNG image bytes (magic + random bytes)
        synthetic_png = b"\x89PNG\r\n\x1a\n" + os.urandom(1024)
        fs.write_file("chart.png", synthetic_png, password)
        dec_png = fs.read_file("chart.png", password)
        assert dec_png == synthetic_png

    def test_empty_zero_byte_file(self, temp_vault):
        fs, tmp_dir, _ = temp_vault
        password = "EmptyFilePassword1!"

        fs.write_file("empty.dat", b"", password)
        dec = fs.read_file("empty.dat", password)
        assert dec == b""

    def test_large_file_payload(self, temp_vault):
        fs, tmp_dir, _ = temp_vault
        password = "LargeFilePassphrase!"
        # 2 MB synthetic payload
        large_data = os.urandom(2 * 1024 * 1024)

        fs.write_file("large.bin", large_data, password)
        dec = fs.read_file("large.bin", password)
        assert dec == large_data

    def test_incorrect_password_access_denied(self, temp_vault):
        fs, tmp_dir, _ = temp_vault
        password = "CorrectPassword123"
        wrong_pwd = "WrongPassword456"

        fs.write_file("secret.txt", b"Confidential Data", password)

        with pytest.raises(PermissionError) as exc_info:
            fs.read_file("secret.txt", wrong_pwd)
        assert "Access Denied" in str(exc_info.value)

    def test_tampered_ciphertext_fails_integrity(self, temp_vault):
        fs, tmp_dir, _ = temp_vault
        password = "IntegrityCheckPass!"
        target_path = fs.write_file("tamper_test.txt", b"Original untampered content", password)

        # Flip a bit near the end (ciphertext / GHASH tag)
        with open(target_path, "r+b") as f:
            f.seek(-5, os.SEEK_END)
            b = f.read(1)
            f.seek(-5, os.SEEK_END)
            f.write(bytes([b[0] ^ 0x01]))

        with pytest.raises(PermissionError):
            fs.read_file("tamper_test.txt", password)

    def test_tampered_header_fails_integrity(self, temp_vault):
        fs, tmp_dir, _ = temp_vault
        password = "HeaderTamperPass!"
        target_path = fs.write_file("header_tamper.txt", b"Header authentication test", password)

        # Alter byte in AAD prefix (metadata header)
        with open(target_path, "r+b") as f:
            f.seek(15)
            b = f.read(1)
            f.seek(15)
            f.write(bytes([b[0] ^ 0x01]))

        with pytest.raises(PermissionError):
            fs.read_file("header_tamper.txt", password)

    def test_truncated_file_fails_safely(self, temp_vault):
        fs, tmp_dir, _ = temp_vault
        password = "TruncatePass!"
        target_path = fs.write_file("trunc.txt", b"Truncation test data payload", password)

        # Truncate file to 10 bytes (smaller than minimum header)
        with open(target_path, "wb") as f:
            f.write(b"SFS\x02\x00\x05short")

        with pytest.raises(PermissionError):
            fs.read_file("trunc.txt", password)

    def test_legacy_v1_format_backward_compatibility(self, temp_vault):
        fs, tmp_dir, _ = temp_vault
        password = "LegacyV1Password!"
        content = b"Legacy v1 container content without SFS2 magic header."

        # Write in format_version 1
        v1_path = fs.write_file("legacy.txt", content, password, format_version=1)

        # Verify raw bytes do NOT start with MAGIC_V2
        with open(v1_path, "rb") as f:
            raw = f.read()
        assert not raw.startswith(b"SFS\x02")

        # Decrypt legacy file
        dec = fs.read_file("legacy.txt", password)
        assert dec == content

    def test_filename_collision_protection(self, temp_vault):
        fs, tmp_dir, _ = temp_vault
        password = "CollisionPass!"

        fs.write_file("collision.txt", b"Initial file", password)

        # Writing again without overwrite=True must raise FileExistsError
        with pytest.raises(FileExistsError):
            fs.write_file("collision.txt", b"Replacement file", password, overwrite=False)

        # Writing with overwrite=True succeeds
        fs.write_file("collision.txt", b"Replaced content", password, overwrite=True)
        assert fs.read_file("collision.txt", password) == b"Replaced content"

    def test_path_traversal_sanitization(self, temp_vault):
        fs, tmp_dir, _ = temp_vault
        password = "PathTraversalPass!"

        # Slashes and traversal dots must be sanitized to basename
        path = fs.write_file("../../etc/malicious.txt", b"Data", password)
        assert os.path.dirname(path) == tmp_dir
        assert os.path.basename(path) == "malicious.txt.sfs"

    def test_secure_shredding_three_passes(self, temp_vault):
        fs, tmp_dir, _ = temp_vault
        password = "ShredPass!"

        path = fs.write_file("shred_me.txt", b"Top secret data to be shredded", password)
        assert os.path.exists(path)

        # Wrong password shred attempt fails
        with pytest.raises(PermissionError):
            fs.secure_delete("shred_me.txt", "WrongPassword")
        assert os.path.exists(path)

        # Correct password shred succeeds
        res = fs.secure_delete("shred_me.txt", password)
        assert res is True
        assert not os.path.exists(path)

    def test_audit_log_generation_and_filtering(self, temp_vault):
        fs, tmp_dir, log_path = temp_vault
        password = "AuditPass!"

        fs.write_file("audit_test.txt", b"Audit content", password)
        fs.read_file("audit_test.txt", password)
        try:
            fs.read_file("audit_test.txt", "WrongPass")
        except PermissionError:
            pass

        logs = fs.parse_audit_log()
        assert len(logs) >= 3

        # Check tamper alarm logged
        tamper_logs = fs.parse_audit_log(status_filter="ALERT_TAMPER_OR_AUTH_FAIL")
        assert len(tamper_logs) >= 1

        # Check action filter
        write_logs = fs.parse_audit_log(action_filter="WRITE")
        assert len(write_logs) >= 1
