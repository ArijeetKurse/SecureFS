"""
SecureFS — Modern Linux GUI Entry Point
=======================================
Cybersecurity Desktop Vault application built with PySide6 (Qt).
"""

import sys
import os
import argparse

# Ensure workspace root is in python search path
workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if workspace_dir not in sys.path:
    sys.path.insert(0, workspace_dir)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from gui.main_window import MainWindow


def main():
    parser = argparse.ArgumentParser(description="SecureFS — Encrypted File Vault (PySide6 GUI)")
    parser.add_argument(
        "--storage-dir",
        default="encrypted_storage",
        help="Path to encrypted storage directory (default: encrypted_storage)"
    )
    parser.add_argument(
        "--log-file",
        default="audit.log",
        help="Path to JSON-lines audit log (default: audit.log)"
    )
    args = parser.parse_args()

    # Detect if demo storage exists and default storage doesn't
    storage_dir = args.storage_dir
    if not os.path.exists(storage_dir) and os.path.exists("encrypted_storage_demo"):
        storage_dir = "encrypted_storage_demo"

    # Configure Qt application
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("SecureFS")
    app.setApplicationDisplayName("SecureFS — Encrypted File Vault")

    window = MainWindow(storage_dir=storage_dir, log_file=args.log_file)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
