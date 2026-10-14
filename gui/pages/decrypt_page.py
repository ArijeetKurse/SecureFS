"""
SecureFS — Decrypt & Export Interface Page
==========================================
Decrypts authenticated .sfs containers, verifies cryptographic tags,
and exports plaintext to a selected local filesystem destination.
"""

import os
from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QFileDialog, QCheckBox, QComboBox, QProgressBar, QFrame, QMessageBox,
    QRadioButton, QButtonGroup
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

from gui.styles.theme import (
    BG_CARD, BG_PANEL, BG_INPUT, ACCENT_RED, BORDER_MUTED, BORDER_LIGHT,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    STATUS_SUCCESS, STATUS_ALERT, STATUS_WARNING, STATUS_INFO, IconFactory
)
from gui.services.vault_service import VaultService, DecryptWorker


class DecryptPage(QWidget):
    """File decryption and export interface."""

    decryptionCompleted = Signal()

    def __init__(self, vault_service: VaultService, parent=None):
        super().__init__(parent)
        self.service = vault_service
        self.worker: Optional[DecryptWorker] = None
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 28, 28, 28)
        main_layout.setSpacing(20)

        # Title
        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)
        title = QLabel("Decrypt & Export")
        title.setStyleSheet(f"font-size: 24px; font-weight: 700; color: {TEXT_PRIMARY};")
        subtitle = QLabel("Verify cryptographic MAC authentication tag and restore original plaintext")
        subtitle.setStyleSheet(f"font-size: 13px; color: {TEXT_SECONDARY};")
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        main_layout.addLayout(title_layout)

        # Main Card
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_CARD};
                border: 1px solid {BORDER_MUTED};
                border-radius: 8px;
            }}
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 24, 24, 24)
        card_layout.setSpacing(16)

        # 1. Source Selection Mode
        lbl_src = QLabel("1. SELECT ENCRYPTED .SFS CONTAINER")
        lbl_src.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px; font-weight: 700; letter-spacing: 0.5px;")
        card_layout.addWidget(lbl_src)

        mode_layout = QHBoxLayout()
        self.radio_vault = QRadioButton("Select from My Vault")
        self.radio_vault.setChecked(True)
        self.radio_external = QRadioButton("Browse External .sfs Container")
        mode_layout.addWidget(self.radio_vault)
        mode_layout.addWidget(self.radio_external)
        mode_layout.addStretch()
        card_layout.addLayout(mode_layout)

        # Vault Dropdown
        self.combo_vault_files = QComboBox()
        card_layout.addWidget(self.combo_vault_files)

        # External File Input
        self.ext_frame = QFrame()
        ext_layout = QHBoxLayout(self.ext_frame)
        ext_layout.setContentsMargins(0, 0, 0, 0)
        ext_layout.setSpacing(8)

        self.input_ext_path = QLineEdit()
        self.input_ext_path.setPlaceholderText("Select external .sfs file...")
        ext_layout.addWidget(self.input_ext_path)

        btn_browse_ext = QPushButton("Browse...")
        btn_browse_ext.setIcon(IconFactory.create_icon("search", "#ffffff", 14))
        btn_browse_ext.clicked.connect(self._browse_external)
        ext_layout.addWidget(btn_browse_ext)

        self.ext_frame.setVisible(False)
        card_layout.addWidget(self.ext_frame)

        self.radio_vault.toggled.connect(self._on_mode_toggled)

        card_layout.addSpacing(6)

        # 2. Secret Passphrase
        lbl_pwd = QLabel("2. SECRET DECRYPTION PASSPHRASE")
        lbl_pwd.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px; font-weight: 700; letter-spacing: 0.5px;")
        card_layout.addWidget(lbl_pwd)

        pwd_row = QHBoxLayout()
        self.input_pwd = QLineEdit()
        self.input_pwd.setEchoMode(QLineEdit.Password)
        self.input_pwd.setPlaceholderText("Enter the secret passphrase used to encrypt this file...")
        pwd_row.addWidget(self.input_pwd)

        self.btn_toggle_pwd = QPushButton("Show")
        self.btn_toggle_pwd.setFixedWidth(64)
        self.btn_toggle_pwd.clicked.connect(self._toggle_password_visibility)
        pwd_row.addWidget(self.btn_toggle_pwd)
        card_layout.addLayout(pwd_row)

        card_layout.addSpacing(6)

        # 3. Export Destination
        lbl_dest = QLabel("3. EXPORT DESTINATION DIRECTORY")
        lbl_dest.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px; font-weight: 700; letter-spacing: 0.5px;")
        card_layout.addWidget(lbl_dest)

        dest_row = QHBoxLayout()
        self.input_dest = QLineEdit()
        self.input_dest.setText(os.path.expanduser("~/Downloads") if os.path.isdir(os.path.expanduser("~/Downloads")) else os.path.expanduser("~"))
        dest_row.addWidget(self.input_dest)

        btn_browse_dest = QPushButton("Choose...")
        btn_browse_dest.setIcon(IconFactory.create_icon("search", "#ffffff", 14))
        btn_browse_dest.clicked.connect(self._browse_destination)
        dest_row.addWidget(btn_browse_dest)
        card_layout.addLayout(dest_row)

        self.chk_overwrite = QCheckBox("Overwrite destination file if it already exists")
        card_layout.addWidget(self.chk_overwrite)

        card_layout.addSpacing(10)

        # 4. Progress and Status
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        card_layout.addWidget(self.progress_bar)

        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet("font-size: 12px;")
        self.lbl_status.setVisible(False)
        card_layout.addWidget(self.lbl_status)

        # Action Button
        action_layout = QHBoxLayout()
        action_layout.addStretch()

        self.btn_decrypt = QPushButton("Verify Integrity && Export")
        self.btn_decrypt.setProperty("class", "btn-primary")
        self.btn_decrypt.setIcon(IconFactory.create_icon("unlock", "#ffffff", 16))
        self.btn_decrypt.setFixedHeight(40)
        self.btn_decrypt.clicked.connect(self._start_decryption)
        action_layout.addWidget(self.btn_decrypt)

        card_layout.addLayout(action_layout)
        main_layout.addWidget(card)
        main_layout.addStretch()

    def refresh_vault_files(self):
        """Populates the vault files dropdown."""
        files = self.service.get_files()
        self.combo_vault_files.clear()
        if not files:
            self.combo_vault_files.addItem("No encrypted files in vault", None)
            self.combo_vault_files.setEnabled(False)
        else:
            self.combo_vault_files.setEnabled(True)
            for f in files:
                self.combo_vault_files.addItem(
                    f"{f['filename']}.sfs ({f['version']}, {f['size_bytes']} bytes)",
                    f['filename']
                )

    def select_file(self, filename: str):
        """Pre-selects a specific file in the dropdown."""
        self.radio_vault.setChecked(True)
        idx = self.combo_vault_files.findData(filename)
        if idx >= 0:
            self.combo_vault_files.setCurrentIndex(idx)

    def _on_mode_toggled(self, checked: bool):
        self.combo_vault_files.setVisible(self.radio_vault.isChecked())
        self.ext_frame.setVisible(self.radio_external.isChecked())

    def _browse_external(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Encrypted .sfs File", os.path.expanduser("~"), "SecureFS Containers (*.sfs);;All Files (*)")
        if file_path:
            self.input_ext_path.setText(file_path)

    def _browse_destination(self):
        dest_dir = QFileDialog.getExistingDirectory(self, "Select Export Directory", self.input_dest.text() or os.path.expanduser("~"))
        if dest_dir:
            self.input_dest.setText(dest_dir)

    def _toggle_password_visibility(self):
        if self.input_pwd.echoMode() == QLineEdit.Password:
            self.input_pwd.setEchoMode(QLineEdit.Normal)
            self.btn_toggle_pwd.setText("Hide")
        else:
            self.input_pwd.setEchoMode(QLineEdit.Password)
            self.btn_toggle_pwd.setText("Show")

    def _start_decryption(self):
        pwd = self.input_pwd.text()
        if not pwd:
            QMessageBox.warning(self, "Password Required", "Please enter the secret decryption passphrase.")
            return

        dest_dir = self.input_dest.text().strip()
        if not dest_dir or not os.path.isdir(dest_dir):
            QMessageBox.warning(self, "Invalid Destination", "Please choose a valid destination directory.")
            return

        # Determine target file
        if self.radio_vault.isChecked():
            filename = self.combo_vault_files.currentData()
            if not filename:
                QMessageBox.warning(self, "No File", "No vault file selected.")
                return
            src_fs = self.service.fs
        else:
            ext_path = self.input_ext_path.text().strip()
            if not ext_path or not os.path.isfile(ext_path):
                QMessageBox.warning(self, "Invalid File", "Please select a valid external .sfs file.")
                return
            # Create temporary SecureFS pointing to external file's directory
            ext_dir = os.path.dirname(ext_path)
            base = os.path.basename(ext_path)
            if base.endswith(".sfs"):
                filename = base[:-4]
            else:
                filename = base
            from securefs import SecureFS
            src_fs = SecureFS(storage_dir=ext_dir, log_file=self.service.fs.log_file)

        overwrite = self.chk_overwrite.isChecked()

        self.btn_decrypt.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.lbl_status.setText("Verifying AEAD authentication tag and decrypting...")
        self.lbl_status.setStyleSheet(f"color: {TEXT_SECONDARY};")
        self.lbl_status.setVisible(True)

        self.worker = DecryptWorker(
            fs=src_fs,
            filename=filename,
            password=pwd,
            dest_path=dest_dir,
            overwrite=overwrite
        )
        self.worker.progress.connect(self._on_worker_progress)
        self.worker.finished.connect(self._on_worker_finished)
        self.worker.start()

    def _on_worker_progress(self, percent: int, msg: str):
        self.progress_bar.setValue(percent)
        self.lbl_status.setText(msg)

    def _on_worker_finished(self, success: bool, out_file: str, detail: str):
        self.btn_decrypt.setEnabled(True)
        self.progress_bar.setVisible(False)

        if success:
            self.lbl_status.setText(f"✓ {detail}")
            self.lbl_status.setStyleSheet(f"color: {STATUS_SUCCESS}; font-weight: 600;")
            QMessageBox.information(
                self, "Decryption Successful",
                f"Integrity check passed!\n\nPlaintext exported to:\n{out_file}"
            )
            self.input_pwd.clear()
            self.decryptionCompleted.emit()
        else:
            self.lbl_status.setText(f"✗ {detail}")
            self.lbl_status.setStyleSheet(f"color: {STATUS_ALERT}; font-weight: 600;")
            QMessageBox.critical(
                self, "Security Alert: Decryption Failed",
                f"Failed to authenticate or decrypt:\n\n{detail}\n\n"
                "An audit record has been appended to the audit log."
            )
