"""
SecureFS — My Vault Explorer Page
=================================
Manages encrypted .sfs files in the vault: listing, searching, importing,
exporting/decrypting, verifying integrity, and secure 3-pass shredding.
"""

import os
from typing import Optional, List, Dict, Any
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QFrame,
    QFileDialog, QMessageBox, QInputDialog, QDialog, QSplitter
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

from gui.styles.theme import (
    BG_CARD, BG_PANEL, BG_INPUT, ACCENT_RED, BORDER_MUTED, BORDER_LIGHT,
    BORDER_WHITE_10, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    STATUS_SUCCESS, STATUS_ALERT, STATUS_WARNING, STATUS_INFO, IconFactory
)
from gui.services.vault_service import (
    VaultService, VerifyWorker, ShredWorker, DecryptWorker
)


class PasswordDialog(QDialog):
    """Secure dialog for passphrase input."""

    def __init__(self, title: str, prompt: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedWidth(420)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {BG_PANEL};
                border: 1px solid {BORDER_LIGHT};
                border-radius: 8px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        lbl = QLabel(prompt)
        lbl.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 14px; font-weight: 600;")
        layout.addWidget(lbl)

        self.input_pwd = QLineEdit()
        self.input_pwd.setEchoMode(QLineEdit.Password)
        self.input_pwd.setPlaceholderText("Enter vault passphrase...")
        layout.addWidget(self.input_pwd)

        btn_box = QHBoxLayout()
        btn_box.setSpacing(12)

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(self.btn_cancel)

        self.btn_ok = QPushButton("Authorize")
        self.btn_ok.setProperty("class", "btn-primary")
        self.btn_ok.clicked.connect(self.accept)
        btn_box.addWidget(self.btn_ok)

        layout.addLayout(btn_box)

    def get_password(self) -> str:
        return self.input_pwd.text().strip()


class VaultPage(QWidget):
    """Vault management explorer page."""

    navigateRequested = Signal(str)  # navigate to 'encrypt', etc.
    fileSelectedForExport = Signal(str)

    def __init__(self, vault_service: VaultService, parent=None):
        super().__init__(parent)
        self.service = vault_service
        self.current_files: List[Dict[str, Any]] = []
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 28, 28, 28)
        main_layout.setSpacing(20)

        # 1. Top Header & Action Bar
        top_layout = QHBoxLayout()

        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)
        title = QLabel("My Vault")
        title.setStyleSheet(f"font-size: 24px; font-weight: 700; color: {TEXT_PRIMARY};")
        self.lbl_subtitle = QLabel("Encrypted containers in active storage")
        self.lbl_subtitle.setStyleSheet(f"font-size: 13px; color: {TEXT_SECONDARY};")
        title_layout.addWidget(title)
        title_layout.addWidget(self.lbl_subtitle)
        top_layout.addLayout(title_layout)

        top_layout.addStretch()

        btn_import = QPushButton("Import && Encrypt File")
        btn_import.setProperty("class", "btn-primary")
        btn_import.setIcon(IconFactory.create_icon("lock", "#ffffff", 16))
        btn_import.clicked.connect(lambda: self.navigateRequested.emit("encrypt"))
        top_layout.addWidget(btn_import)

        btn_refresh = QPushButton("Refresh")
        btn_refresh.setIcon(IconFactory.create_icon("refresh", TEXT_SECONDARY, 14))
        btn_refresh.clicked.connect(self.refresh_files)
        top_layout.addWidget(btn_refresh)

        main_layout.addLayout(top_layout)

        # 2. Filter & Search Bar
        search_frame = QFrame()
        search_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_CARD};
                border: 1px solid {BORDER_MUTED};
                border-radius: 8px;
                padding: 6px;
            }}
        """)
        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(12, 6, 12, 6)
        search_layout.setSpacing(12)

        lbl_search_icon = QLabel()
        lbl_search_icon.setPixmap(IconFactory.create_icon("search", TEXT_MUTED, 18).pixmap(18, 18))
        search_layout.addWidget(lbl_search_icon)

        self.input_search = QLineEdit()
        self.input_search.setPlaceholderText("Search encrypted files by name or format...")
        self.input_search.textChanged.connect(self._apply_filter)
        search_layout.addWidget(self.input_search)

        self.lbl_count = QLabel("0 files")
        self.lbl_count.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px; font-weight: 600;")
        search_layout.addWidget(self.lbl_count)

        main_layout.addWidget(search_frame)

        # 3. Splitter with Table and Details Panel
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet("QSplitter::handle { background-color: transparent; width: 12px; }")

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Encrypted File", "Container Size", "Modified (UTC)", "Format", "Integrity State"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.itemSelectionChanged.connect(self._on_row_selected)
        splitter.addWidget(self.table)

        # Details Panel
        self.details_panel = QFrame()
        self.details_panel.setFixedWidth(320)
        self.details_panel.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_CARD};
                border: 1px solid {BORDER_MUTED};
                border-radius: 8px;
            }}
        """)
        details_layout = QVBoxLayout(self.details_panel)
        details_layout.setContentsMargins(18, 18, 18, 18)
        details_layout.setSpacing(14)

        lbl_panel_title = QLabel("ENTRY DETAILS")
        lbl_panel_title.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px; font-weight: 700; letter-spacing: 0.5px;")
        details_layout.addWidget(lbl_panel_title)

        self.det_filename = QLabel("No file selected")
        self.det_filename.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 16px; font-weight: 700;")
        self.det_filename.setWordWrap(True)
        details_layout.addWidget(self.det_filename)

        self.det_meta = QLabel("Select an entry to view cryptographic details or perform export and shred operations.")
        self.det_meta.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px; line-height: 1.4;")
        self.det_meta.setWordWrap(True)
        details_layout.addWidget(self.det_meta)

        details_layout.addStretch()

        # Action Buttons
        self.btn_export = QPushButton("Decrypt && Export...")
        self.btn_export.setIcon(IconFactory.create_icon("export", "#ffffff", 16))
        self.btn_export.setEnabled(False)
        self.btn_export.clicked.connect(self._action_export)
        details_layout.addWidget(self.btn_export)

        self.btn_verify = QPushButton("Verify Integrity Tag")
        self.btn_verify.setIcon(IconFactory.create_icon("security", "#ffffff", 16))
        self.btn_verify.setEnabled(False)
        self.btn_verify.clicked.connect(self._action_verify)
        details_layout.addWidget(self.btn_verify)

        self.btn_shred = QPushButton("Secure Shred (3 Passes)")
        self.btn_shred.setProperty("class", "btn-danger")
        self.btn_shred.setIcon(IconFactory.create_icon("trash", ACCENT_RED, 16))
        self.btn_shred.setEnabled(False)
        self.btn_shred.clicked.connect(self._action_shred)
        details_layout.addWidget(self.btn_shred)

        splitter.addWidget(self.details_panel)
        splitter.setSizes([680, 320])

        main_layout.addWidget(splitter, 1)

    def _format_size(self, size_bytes: int) -> str:
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.2f} MB"

    def refresh_files(self):
        """Scans the vault directory and reloads the table."""
        self.current_files = self.service.get_files()
        self.lbl_subtitle.setText(f"Active vault: {self.service.fs.storage_dir}")
        self._apply_filter()

    def _apply_filter(self):
        query = self.input_search.text().strip().lower()
        filtered = [
            f for f in self.current_files
            if query in f["filename"].lower() or query in f["version"].lower()
        ]

        self.lbl_count.setText(f"{len(filtered)} file(s)")
        self.table.setRowCount(len(filtered))

        for row, f in enumerate(filtered):
            name_item = QTableWidgetItem(f["filename"] + ".sfs")
            name_item.setData(Qt.UserRole, f["filename"])

            size_item = QTableWidgetItem(self._format_size(f["size_bytes"]))
            mod_item = QTableWidgetItem(f["modified"].replace("T", " ")[:19])
            ver_item = QTableWidgetItem(f["version"])

            valid_str = "Authenticated Sealed" if f["is_valid"] else "Corrupted Header"
            status_item = QTableWidgetItem(valid_str)
            if f["is_valid"]:
                status_item.setForeground(QColor(STATUS_SUCCESS))
            else:
                status_item.setForeground(QColor(STATUS_ALERT))

            self.table.setItem(row, 0, name_item)
            self.table.setItem(row, 1, size_item)
            self.table.setItem(row, 2, mod_item)
            self.table.setItem(row, 3, ver_item)
            self.table.setItem(row, 4, status_item)

        self._on_row_selected()

    def _get_selected_filename(self) -> Optional[str]:
        rows = self.table.selectedItems()
        if not rows:
            return None
        row = self.table.currentRow()
        item = self.table.item(row, 0)
        return item.data(Qt.UserRole) if item else None

    def _on_row_selected(self):
        filename = self._get_selected_filename()
        if not filename:
            self.det_filename.setText("No file selected")
            self.det_meta.setText("Select an encrypted container to view security details or perform actions.")
            self.btn_export.setEnabled(False)
            self.btn_verify.setEnabled(False)
            self.btn_shred.setEnabled(False)
            return

        # Find file dict
        file_info = next((f for f in self.current_files if f["filename"] == filename), None)
        if not file_info:
            return

        self.det_filename.setText(file_info["filename"] + ".sfs")
        meta_text = (
            f"Original Name: {file_info.get('orig_name', '-')}\n"
            f"Encrypted Size: {self._format_size(file_info['size_bytes'])}\n"
            f"Format Architecture: {file_info['version']}\n"
            f"Modified: {file_info['modified'].replace('T', ' ')[:19]} UTC\n"
            f"On-Disk Path:\n{file_info['path']}"
        )
        self.det_meta.setText(meta_text)
        self.btn_export.setEnabled(True)
        self.btn_verify.setEnabled(True)
        self.btn_shred.setEnabled(True)

    def _action_export(self):
        """Launches export flow for the selected file."""
        filename = self._get_selected_filename()
        if not filename:
            return

        dlg = PasswordDialog("Decrypt Vault Entry", f"Enter passphrase to decrypt '{filename}.sfs':", self)
        if dlg.exec() != QDialog.Accepted:
            return

        pwd = dlg.get_password()
        if not pwd:
            QMessageBox.warning(self, "Password Required", "Passphrase cannot be empty.")
            return

        dest_dir = QFileDialog.getExistingDirectory(self, "Select Export Destination Directory", os.path.expanduser("~"))
        if not dest_dir:
            return

        # Export worker
        self.worker = DecryptWorker(
            fs=self.service.fs,
            filename=filename,
            password=pwd,
            dest_path=dest_dir,
            overwrite=True
        )
        self.worker.finished.connect(self._on_export_finished)
        self.btn_export.setEnabled(False)
        self.worker.start()

    def _on_export_finished(self, success: bool, out_path: str, msg: str):
        self.btn_export.setEnabled(True)
        if success:
            QMessageBox.information(
                self, "Export Successful",
                f"File decrypted and verified successfully!\n\nExported to:\n{out_path}"
            )
        else:
            QMessageBox.critical(self, "Decryption Error", f"Failed to decrypt file:\n\n{msg}")

    def _action_verify(self):
        """Verifies AEAD integrity tag with passphrase."""
        filename = self._get_selected_filename()
        if not filename:
            return

        dlg = PasswordDialog("Verify Integrity Tag", f"Enter passphrase to verify '{filename}.sfs':", self)
        if dlg.exec() != QDialog.Accepted:
            return

        pwd = dlg.get_password()
        if not pwd:
            return

        self.v_worker = VerifyWorker(self.service.fs, filename, pwd)
        self.v_worker.finished.connect(self._on_verify_finished)
        self.btn_verify.setEnabled(False)
        self.v_worker.start()

    def _on_verify_finished(self, is_valid: bool, msg: str):
        self.btn_verify.setEnabled(True)
        if is_valid:
            QMessageBox.information(
                self, "Integrity Verified",
                f"Cryptographic check PASSED!\n\n{msg}"
            )
        else:
            QMessageBox.critical(
                self, "Security Alert: Tamper or Bad Key",
                f"Authentication check FAILED!\n\n{msg}\n\nThis incident has been logged to audit.log."
            )

    def _action_shred(self):
        """Securely shreds vault file with 3 overwrite passes."""
        filename = self._get_selected_filename()
        if not filename:
            return

        confirm = QMessageBox.warning(
            self,
            "Confirm Secure Shredding",
            f"Are you sure you want to securely shred '{filename}.sfs'?\n\n"
            "This performs a 3-pass overwrite with random bytes followed by hardware fsync. "
            "The data will be PERMANENTLY DESTROYED.\n\n"
            "Proceed?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if confirm != QMessageBox.Yes:
            return

        dlg = PasswordDialog("Authorization Required", f"Enter passphrase to authorize shredding of '{filename}.sfs':", self)
        if dlg.exec() != QDialog.Accepted:
            return

        pwd = dlg.get_password()
        if not pwd:
            return

        self.s_worker = ShredWorker(self.service.fs, filename, pwd)
        self.s_worker.finished.connect(self._on_shred_finished)
        self.btn_shred.setEnabled(False)
        self.s_worker.start()

    def _on_shred_finished(self, success: bool, msg: str):
        self.btn_shred.setEnabled(True)
        if success:
            QMessageBox.information(self, "File Shredded", msg)
            self.refresh_files()
        else:
            QMessageBox.critical(self, "Shredding Aborted", msg)
