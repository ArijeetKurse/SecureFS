"""
Integration Tests for SecureFS GUI and Services
===============================================
Tests Qt background workers, vault service orchestration, and GUI navigation.
"""

import os
import sys
import shutil
import tempfile
import pytest

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QCoreApplication

from securefs import SecureFS
from gui.services.vault_service import (
    VaultService, EncryptWorker, DecryptWorker, VerifyWorker, ShredWorker
)
from gui.main_window import MainWindow

# Ensure Qt application exists
@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        os.environ["QT_QPA_PLATFORM"] = "offscreen"
        app = QApplication(sys.argv)
    yield app


@pytest.fixture
def temp_gui_env():
    tmp_dir = tempfile.mkdtemp(prefix="securefs_gui_test_")
    log_file = os.path.join(tmp_dir, "gui_audit.log")
    service = VaultService(storage_dir=tmp_dir, log_file=log_file)
    yield service, tmp_dir, log_file
    shutil.rmtree(tmp_dir, ignore_errors=True)


class TestGUIIntegration:

    def test_encrypt_worker_execution(self, qapp, temp_gui_env):
        service, tmp_dir, _ = temp_gui_env
        src_file = os.path.join(tmp_dir, "sample.txt")
        with open(src_file, "w") as f:
            f.write("Sample plaintext content for worker test.")

        results = {}

        def on_finished(success, path, msg):
            results["success"] = success
            results["path"] = path
            results["msg"] = msg

        worker = EncryptWorker(
            fs=service.fs,
            src_path=src_file,
            target_name="sample.txt",
            password="WorkerPassword123!",
            overwrite=True
        )
        worker.finished.connect(on_finished)
        worker.run()  # Direct synchronous run for test determinism

        assert results.get("success") is True
        assert os.path.exists(results.get("path"))

    def test_decrypt_worker_execution(self, qapp, temp_gui_env):
        service, tmp_dir, _ = temp_gui_env
        password = "DecryptWorkerPass!"
        service.fs.write_file("data.bin", b"EncryptedBinaryData", password)

        dest_dir = os.path.join(tmp_dir, "exports")
        os.makedirs(dest_dir, exist_ok=True)

        results = {}

        def on_finished(success, path, msg):
            results["success"] = success
            results["path"] = path

        worker = DecryptWorker(
            fs=service.fs,
            filename="data.bin",
            password=password,
            dest_path=dest_dir,
            overwrite=True
        )
        worker.finished.connect(on_finished)
        worker.run()

        assert results.get("success") is True
        out_file = results.get("path")
        assert os.path.exists(out_file)
        with open(out_file, "rb") as f:
            assert f.read() == b"EncryptedBinaryData"

    def test_verify_worker_integrity(self, qapp, temp_gui_env):
        service, tmp_dir, _ = temp_gui_env
        password = "VerifyPass123!"
        service.fs.write_file("verify_doc.txt", b"Valid authenticated content", password)

        results = {}

        def on_finished(is_valid, msg):
            results["valid"] = is_valid
            results["msg"] = msg

        # Correct password
        w1 = VerifyWorker(service.fs, "verify_doc.txt", password)
        w1.finished.connect(on_finished)
        w1.run()
        assert results["valid"] is True

        # Incorrect password
        w2 = VerifyWorker(service.fs, "verify_doc.txt", "WrongPassword!")
        w2.finished.connect(on_finished)
        w2.run()
        assert results["valid"] is False

    def test_main_window_navigation_and_pages(self, qapp, temp_gui_env):
        service, tmp_dir, log_file = temp_gui_env
        win = MainWindow(storage_dir=tmp_dir, log_file=log_file)
        assert win.windowTitle() == "SecureFS — Encrypted File Vault"

        # Test switching across all 7 pages
        pages = ["dashboard", "vault", "encrypt", "decrypt", "security", "logs", "settings"]
        for p in pages:
            win._switch_page(p)
            assert win.stack.currentWidget() == win.pages[p]

        win.close()
