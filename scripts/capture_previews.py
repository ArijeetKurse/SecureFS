"""
SecureFS — Safe GUI Preview & Screenshot Capturer
=================================================
Runs in an isolated temporary environment with synthetic test data.
Captures screenshots to project-local `artifacts/gui-previews/` directory.
Safely cleans up all temporary files upon completion.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from securefs import SecureFS
from gui.main_window import MainWindow

OUTPUT_DIR = PROJECT_ROOT / "artifacts" / "gui-previews"


def create_synthetic_test_vault(temp_dir: str):
    """Populates an isolated temporary vault with synthetic test data."""
    vault_dir = os.path.join(temp_dir, "test_vault")
    log_file = os.path.join(temp_dir, "test_audit.log")
    os.makedirs(vault_dir, exist_ok=True)

    fs = SecureFS(storage_dir=vault_dir, log_file=log_file)

    # 1. Synthetic modern v2 file
    fs.write_file(
        "financial_summary.pdf",
        b"%PDF-1.7 Synthetic confidential financial quarterly statement data.",
        "TestPass123!",
        format_version=2
    )

    # 2. Synthetic legacy v1 file
    fs.write_file(
        "backup_archive.tar",
        b"Synthetic legacy archive data container contents.",
        "LegacyPass123!",
        format_version=1
    )

    # 3. Simulate verification and access event in audit log
    fs.verify_integrity("financial_summary.pdf", "TestPass123!")

    return vault_dir, log_file


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Create isolated temp environment
    temp_dir = tempfile.mkdtemp(prefix="securefs_preview_")
    print(f"[+] Created isolated temporary environment: {temp_dir}")

    try:
        vault_dir, log_file = create_synthetic_test_vault(temp_dir)
        print(f"[+] Populated synthetic vault in: {vault_dir}")

        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        win = MainWindow(storage_dir=vault_dir, log_file=log_file)
        win.show()

        results = {}
        pages_to_capture = [
            ("dashboard", "01_dashboard.png"),
            ("vault", "02_my_vault.png"),
            ("encrypt", "03_encrypt_files.png"),
            ("decrypt", "04_decrypt_export.png"),
            ("security", "05_security_integrity.png"),
            ("logs", "06_audit_logs.png"),
            ("settings", "07_settings.png"),
        ]

        def process_captures():
            app.processEvents()
            for page_name, filename in pages_to_capture:
                try:
                    win._switch_page(page_name)
                    app.processEvents()
                    # Grab window pixmap
                    pixmap = win.grab()
                    target_file = OUTPUT_DIR / filename
                    saved = pixmap.save(str(target_file), "PNG")
                    if saved and target_file.exists() and target_file.stat().st_size > 0:
                        results[page_name] = (True, str(target_file), target_file.stat().st_size)
                        print(f"  [✓] Captured {page_name} -> {target_file.name} ({target_file.stat().st_size} bytes)")
                    else:
                        results[page_name] = (False, f"Save failed for {filename}", 0)
                        print(f"  [✗] Failed to save {page_name}")
                except Exception as e:
                    results[page_name] = (False, str(e), 0)
                    print(f"  [✗] Exception capturing {page_name}: {e}")

            win.close()
            app.quit()

        # Execute captures after window paints
        QTimer.singleShot(400, process_captures)
        app.exec()

        print("\n=== Screenshot Capture Summary ===")
        all_passed = True
        for name, (ok, path_or_err, sz) in results.items():
            status = "PASS" if ok else "FAIL"
            print(f" - {name:<12}: {status:<5} | {path_or_err}")
            if not ok:
                all_passed = False

        if not all_passed:
            sys.exit(1)

    finally:
        # Clean up temporary test data
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
            print(f"[+] Safely removed temporary test environment: {temp_dir}")


if __name__ == "__main__":
    main()
