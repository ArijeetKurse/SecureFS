"""
SecureFS — File Encryption Interface Page
=========================================
Securely imports, encrypts, and packages files into AES-256-GCM containers
with PBKDF2-HMAC-SHA256 key stretching and integrity authentication tags.
"""

import os
import re
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QFileDialog, QCheckBox, QComboBox, QProgressBar, QFrame, QMessageBox,
    QGroupBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

from gui.styles.theme import (
    BG_CARD, BG_PANEL, BG_INPUT, ACCENT_RED, BORDER_MUTED, BORDER_LIGHT,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    STATUS_SUCCESS, STATUS_ALERT, STATUS_WARNING, STATUS_INFO, IconFactory
)
from gui.services.vault_service import VaultService, EncryptWorker
from securefs import MODERN_ITERATIONS, LEGACY_ITERATIONS


class EncryptPage(QWidget):
    """File encryption interface."""

    encryptionCompleted = Signal()

    def __init__(self, vault_service: VaultService, parent=None):
        super().__init__(parent)
        self.service = vault_service
        self.worker: Optional[EncryptWorker] = None
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 28, 28, 28)
        main_layout.setSpacing(20)

        # Title
        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)
        title = QLabel("Encrypt & Secure File")
        title.setStyleSheet(f"font-size: 24px; font-weight: 700; color: {TEXT_PRIMARY};")
        subtitle = QLabel("Generate a military-grade AES-256-GCM sealed container with PBKDF2 key stretching")
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

        # 1. Source File Selector
        lbl_src = QLabel("1. SELECT SOURCE FILE")
        lbl_src.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px; font-weight: 700; letter-spacing: 0.5px;")
        card_layout.addWidget(lbl_src)

        src_layout = QHBoxLayout()
        self.input_src = QLineEdit()
        self.input_src.setPlaceholderText("Select any file to encrypt (PDF, image, document, binary)...")
        self.input_src.textChanged.connect(self._on_src_changed)
        src_layout.addWidget(self.input_src)

        btn_browse = QPushButton("Browse...")
        btn_browse.setIcon(IconFactory.create_icon("search", "#ffffff", 14))
        btn_browse.clicked.connect(self._browse_source)
        src_layout.addWidget(btn_browse)
        card_layout.addLayout(src_layout)

        self.lbl_src_info = QLabel("No file selected.")
        self.lbl_src_info.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
        card_layout.addWidget(self.lbl_src_info)

        card_layout.addSpacing(6)

        # 2. Vault Target Name
        lbl_target = QLabel("2. VAULT DESTINATION FILENAME")
        lbl_target.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px; font-weight: 700; letter-spacing: 0.5px;")
        card_layout.addWidget(lbl_target)

        target_layout = QHBoxLayout()
        self.input_target = QLineEdit()
        self.input_target.setPlaceholderText("Vault entry name (e.g., secret_report.txt)")
        target_layout.addWidget(self.input_target)

        lbl_ext = QLabel(".sfs")
        lbl_ext.setStyleSheet(f"color: {ACCENT_RED}; font-weight: 700; font-size: 14px; padding-right: 8px;")
        target_layout.addWidget(lbl_ext)
        card_layout.addLayout(target_layout)

        card_layout.addSpacing(6)

        # 3. Passphrase & Confirmation
        lbl_pwd = QLabel("3. ENCRYPTION PASSPHRASE")
        lbl_pwd.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px; font-weight: 700; letter-spacing: 0.5px;")
        card_layout.addWidget(lbl_pwd)

        pwd_row = QHBoxLayout()
        self.input_pwd = QLineEdit()
        self.input_pwd.setEchoMode(QLineEdit.Password)
        self.input_pwd.setPlaceholderText("Enter a strong secret passphrase...")
        self.input_pwd.textChanged.connect(self._check_password_strength)
        pwd_row.addWidget(self.input_pwd)

        self.btn_toggle_pwd = QPushButton("Show")
        self.btn_toggle_pwd.setFixedWidth(64)
        self.btn_toggle_pwd.clicked.connect(self._toggle_password_visibility)
        pwd_row.addWidget(self.btn_toggle_pwd)
        card_layout.addLayout(pwd_row)

        # Confirm password row
        conf_row = QHBoxLayout()
        self.input_conf = QLineEdit()
        self.input_conf.setEchoMode(QLineEdit.Password)
        self.input_conf.setPlaceholderText("Confirm secret passphrase...")
        self.input_conf.textChanged.connect(self._check_password_match)
        conf_row.addWidget(self.input_conf)
        card_layout.addLayout(conf_row)

        # Strength & Match Status
        status_row = QHBoxLayout()
        self.lbl_strength = QLabel("Password Strength: —")
        self.lbl_strength.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        status_row.addWidget(self.lbl_strength)

        status_row.addStretch()

        self.lbl_match = QLabel("")
        self.lbl_match.setStyleSheet(f"font-size: 12px; font-weight: 600;")
        status_row.addWidget(self.lbl_match)
        card_layout.addLayout(status_row)

        card_layout.addSpacing(6)

        # 4. Security Configuration
        lbl_sec = QLabel("4. CRYPTOGRAPHIC PROFILE & POLICIES")
        lbl_sec.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px; font-weight: 700; letter-spacing: 0.5px;")
        card_layout.addWidget(lbl_sec)

        sec_layout = QHBoxLayout()
        lbl_format = QLabel("Format Architecture:")
        lbl_format.setStyleSheet(f"color: {TEXT_SECONDARY};")
        sec_layout.addWidget(lbl_format)

        self.combo_format = QComboBox()
        self.combo_format.addItem("v2 (Modern - 600,000 PBKDF2 Rounds + AAD Header)", 2)
        self.combo_format.addItem("v1 (Legacy - 100,000 PBKDF2 Rounds)", 1)
        sec_layout.addWidget(self.combo_format)
        sec_layout.addStretch()
        card_layout.addLayout(sec_layout)

        self.chk_overwrite = QCheckBox("Allow overwriting if destination .sfs already exists in vault")
        card_layout.addWidget(self.chk_overwrite)

        self.chk_wipe_source = QCheckBox("Securely shred plaintext source file after successful encryption (3-pass overwrite)")
        self.chk_wipe_source.setStyleSheet(f"color: {STATUS_WARNING};")
        card_layout.addWidget(self.chk_wipe_source)

        card_layout.addSpacing(10)

        # 5. Progress Bar & Action Button
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        card_layout.addWidget(self.progress_bar)

        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet("font-size: 12px;")
        self.lbl_status.setVisible(False)
        card_layout.addWidget(self.lbl_status)

        action_layout = QHBoxLayout()
        action_layout.addStretch()

        self.btn_encrypt = QPushButton("Encrypt && Seal File")
        self.btn_encrypt.setProperty("class", "btn-primary")
        self.btn_encrypt.setIcon(IconFactory.create_icon("lock", "#ffffff", 16))
        self.btn_encrypt.setFixedHeight(40)
        self.btn_encrypt.clicked.connect(self._start_encryption)
        action_layout.addWidget(self.btn_encrypt)

        card_layout.addLayout(action_layout)
        main_layout.addWidget(card)
        main_layout.addStretch()

    def _browse_source(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Plaintext File to Encrypt", os.path.expanduser("~"))
        if file_path:
            self.input_src.setText(file_path)

    def _on_src_changed(self, text: str):
        path = text.strip()
        if os.path.isfile(path):
            size = os.path.getsize(path)
            size_str = f"{size} bytes" if size < 1024 else f"{size / 1024:.1f} KB" if size < 1024 * 1024 else f"{size / (1024 * 1024):.2f} MB"
            self.lbl_src_info.setText(f"File Size: {size_str} • Path: {path}")
            if not self.input_target.text().strip():
                self.input_target.setText(os.path.basename(path))
        else:
            self.lbl_src_info.setText("Selected path is not a valid file.")

    def _toggle_password_visibility(self):
        if self.input_pwd.echoMode() == QLineEdit.Password:
            self.input_pwd.setEchoMode(QLineEdit.Normal)
            self.input_conf.setEchoMode(QLineEdit.Normal)
            self.btn_toggle_pwd.setText("Hide")
        else:
            self.input_pwd.setEchoMode(QLineEdit.Password)
            self.input_conf.setEchoMode(QLineEdit.Password)
            self.btn_toggle_pwd.setText("Show")

    def _check_password_strength(self, pwd: str):
        self._check_password_match()
        if not pwd:
            self.lbl_strength.setText("Password Strength: —")
            self.lbl_strength.setStyleSheet(f"color: {TEXT_MUTED};")
            return

        score = 0
        if len(pwd) >= 8:
            score += 1
        if len(pwd) >= 14:
            score += 1
        if re.search(r"[a-z]", pwd) and re.search(r"[A-Z]", pwd):
            score += 1
        if re.search(r"[0-9]", pwd):
            score += 1
        if re.search(r"[!@#$%^&*(),.?\":{}|<>]", pwd):
            score += 1

        if score <= 2:
            self.lbl_strength.setText("Password Strength: Weak")
            self.lbl_strength.setStyleSheet(f"color: {STATUS_ALERT}; font-weight: 600;")
        elif score <= 4:
            self.lbl_strength.setText("Password Strength: Moderate")
            self.lbl_strength.setStyleSheet(f"color: {STATUS_WARNING}; font-weight: 600;")
        else:
            self.lbl_strength.setText("Password Strength: Strong (High Entropy)")
            self.lbl_strength.setStyleSheet(f"color: {STATUS_SUCCESS}; font-weight: 600;")

    def _check_password_match(self):
        pwd = self.input_pwd.text()
        conf = self.input_conf.text()
        if not conf:
            self.lbl_match.setText("")
            return

        if pwd == conf:
            self.lbl_match.setText("Passwords Match ✓")
            self.lbl_match.setStyleSheet(f"color: {STATUS_SUCCESS};")
        else:
            self.lbl_match.setText("Passwords Do Not Match ✗")
            self.lbl_match.setStyleSheet(f"color: {STATUS_ALERT};")

    def _start_encryption(self):
        src_path = self.input_src.text().strip()
        target_name = self.input_target.text().strip()
        pwd = self.input_pwd.text()
        conf = self.input_conf.text()

        if not src_path or not os.path.isfile(src_path):
            QMessageBox.warning(self, "Invalid Source", "Please select a valid plaintext source file.")
            return

        if not target_name:
            QMessageBox.warning(self, "Missing Name", "Please specify a target vault entry name.")
            return

        if not pwd:
            QMessageBox.warning(self, "Missing Password", "Please enter an encryption passphrase.")
            return

        if pwd != conf:
            QMessageBox.warning(self, "Password Mismatch", "The entered passphrases do not match. Please verify.")
            return

        format_ver = self.combo_format.currentData()
        iterations = MODERN_ITERATIONS if format_ver == 2 else LEGACY_ITERATIONS
        overwrite = self.chk_overwrite.isChecked()
        wipe_source = self.chk_wipe_source.isChecked()

        if wipe_source:
            warn = QMessageBox.warning(
                self, "Confirm Plaintext Shredding",
                f"You have requested to securely shred the original file '{src_path}' after encryption.\n\n"
                "The original file will be permanently overwritten with 3 random passes.\n\n"
                "Continue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if warn != QMessageBox.Yes:
                return

        # Disable button and show progress
        self.btn_encrypt.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.lbl_status.setText("Initializing encryption engine...")
        self.lbl_status.setStyleSheet(f"color: {TEXT_SECONDARY};")
        self.lbl_status.setVisible(True)

        self.worker = EncryptWorker(
            fs=self.service.fs,
            src_path=src_path,
            target_name=target_name,
            password=pwd,
            overwrite=overwrite,
            format_version=format_ver,
            iterations=iterations,
            wipe_source=wipe_source
        )
        self.worker.progress.connect(self._on_worker_progress)
        self.worker.finished.connect(self._on_worker_finished)
        self.worker.start()

    def _on_worker_progress(self, percent: int, msg: str):
        self.progress_bar.setValue(percent)
        self.lbl_status.setText(msg)

    def _on_worker_finished(self, success: bool, out_path: str, detail: str):
        self.btn_encrypt.setEnabled(True)
        self.progress_bar.setVisible(False)

        if success:
            self.lbl_status.setText(f"✓ {detail}")
            self.lbl_status.setStyleSheet(f"color: {STATUS_SUCCESS}; font-weight: 600;")
            QMessageBox.information(
                self, "Encryption Complete",
                f"File encrypted and sealed successfully!\n\n"
                f"Vault Container:\n{out_path}\n\n"
                f"{detail}"
            )
            # Reset inputs
            self.input_src.clear()
            self.input_target.clear()
            self.input_pwd.clear()
            self.input_conf.clear()
            self.encryptionCompleted.emit()
        else:
            self.lbl_status.setText(f"✗ {detail}")
            self.lbl_status.setStyleSheet(f"color: {STATUS_ALERT}; font-weight: 600;")
            QMessageBox.critical(self, "Encryption Failed", f"Operation failed:\n\n{detail}")
