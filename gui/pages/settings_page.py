"""
SecureFS — Settings & Configuration Page
========================================
Manages storage vault directories, audit log paths, security preferences,
and application version information.
"""

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QFrame, QFileDialog, QMessageBox, QCheckBox, QComboBox
)
from PySide6.QtCore import Qt, Signal

from gui.styles.theme import (
    BG_CARD, BG_PANEL, BG_INPUT, ACCENT_RED, BORDER_MUTED, BORDER_LIGHT,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    STATUS_SUCCESS, STATUS_ALERT, STATUS_WARNING, STATUS_INFO, IconFactory
)
from gui.services.vault_service import VaultService


class SettingsPage(QWidget):
    """Configuration and application preferences page."""

    settingsChanged = Signal()

    def __init__(self, vault_service: VaultService, parent=None):
        super().__init__(parent)
        self.service = vault_service
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 28, 28, 28)
        main_layout.setSpacing(24)

        # Title
        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)
        title = QLabel("Vault Settings & Preferences")
        title.setStyleSheet(f"font-size: 24px; font-weight: 700; color: {TEXT_PRIMARY};")
        subtitle = QLabel("Configure vault storage directories, audit logs, and security policies")
        subtitle.setStyleSheet(f"font-size: 13px; color: {TEXT_SECONDARY};")
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        main_layout.addLayout(title_layout)

        # 1. Vault Storage Location Card
        card_storage = QFrame()
        card_storage.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_CARD};
                border: 1px solid {BORDER_MUTED};
                border-radius: 8px;
            }}
        """)
        cs_layout = QVBoxLayout(card_storage)
        cs_layout.setContentsMargins(20, 20, 20, 20)
        cs_layout.setSpacing(14)

        lbl_cs_title = QLabel("VAULT STORAGE REPOSITORY")
        lbl_cs_title.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px; font-weight: 700; letter-spacing: 0.5px;")
        cs_layout.addWidget(lbl_cs_title)

        lbl_cs_desc = QLabel("Directory where encrypted .sfs containers are persisted.")
        lbl_cs_desc.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
        cs_layout.addWidget(lbl_cs_desc)

        row_storage = QHBoxLayout()
        self.input_storage_dir = QLineEdit()
        self.input_storage_dir.setText(self.service.fs.storage_dir)
        row_storage.addWidget(self.input_storage_dir)

        btn_browse_storage = QPushButton("Browse...")
        btn_browse_storage.setIcon(IconFactory.create_icon("search", "#ffffff", 14))
        btn_browse_storage.clicked.connect(self._browse_storage)
        row_storage.addWidget(btn_browse_storage)

        btn_save_storage = QPushButton("Apply")
        btn_save_storage.setProperty("class", "btn-primary")
        btn_save_storage.clicked.connect(self._apply_storage_dir)
        row_storage.addWidget(btn_save_storage)
        cs_layout.addLayout(row_storage)

        main_layout.addWidget(card_storage)

        # 2. Audit Log File Card
        card_log = QFrame()
        card_log.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_CARD};
                border: 1px solid {BORDER_MUTED};
                border-radius: 8px;
            }}
        """)
        cl_layout = QVBoxLayout(card_log)
        cl_layout.setContentsMargins(20, 20, 20, 20)
        cl_layout.setSpacing(14)

        lbl_cl_title = QLabel("FORENSIC AUDIT LOG PATH")
        lbl_cl_title.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px; font-weight: 700; letter-spacing: 0.5px;")
        cl_layout.addWidget(lbl_cl_title)

        lbl_cl_desc = QLabel("File path where immutable security events are appended.")
        lbl_cl_desc.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
        cl_layout.addWidget(lbl_cl_desc)

        row_log = QHBoxLayout()
        self.input_log_file = QLineEdit()
        self.input_log_file.setText(self.service.fs.log_file)
        row_log.addWidget(self.input_log_file)

        btn_browse_log = QPushButton("Browse...")
        btn_browse_log.setIcon(IconFactory.create_icon("search", "#ffffff", 14))
        btn_browse_log.clicked.connect(self._browse_log)
        row_log.addWidget(btn_browse_log)

        btn_save_log = QPushButton("Apply")
        btn_save_log.setProperty("class", "btn-primary")
        btn_save_log.clicked.connect(self._apply_log_file)
        row_log.addWidget(btn_save_log)
        cl_layout.addLayout(row_log)

        main_layout.addWidget(card_log)

        # 3. Security Preferences Card
        card_pref = QFrame()
        card_pref.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_CARD};
                border: 1px solid {BORDER_MUTED};
                border-radius: 8px;
            }}
        """)
        cp_layout = QVBoxLayout(card_pref)
        cp_layout.setContentsMargins(20, 20, 20, 20)
        cp_layout.setSpacing(14)

        lbl_cp_title = QLabel("SECURITY POLICIES & CONFIRMATIONS")
        lbl_cp_title.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px; font-weight: 700; letter-spacing: 0.5px;")
        cp_layout.addWidget(lbl_cp_title)

        self.chk_confirm_shred = QCheckBox("Always require explicit confirmation before 3-pass secure shredding")
        self.chk_confirm_shred.setChecked(True)
        cp_layout.addWidget(self.chk_confirm_shred)

        self.chk_confirm_overwrite = QCheckBox("Prevent accidental file overwrites across vault imports and exports")
        self.chk_confirm_overwrite.setChecked(True)
        cp_layout.addWidget(self.chk_confirm_overwrite)

        self.chk_audit_all = QCheckBox("Record detailed cryptographic status in audit.log")
        self.chk_audit_all.setChecked(True)
        cp_layout.addWidget(self.chk_audit_all)

        main_layout.addWidget(card_pref)

        # 4. Application Info Card
        card_info = QFrame()
        card_info.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_CARD};
                border: 1px solid {BORDER_MUTED};
                border-radius: 8px;
            }}
        """)
        ci_layout = QVBoxLayout(card_info)
        ci_layout.setContentsMargins(20, 20, 20, 20)
        ci_layout.setSpacing(10)

        lbl_ci_title = QLabel("SYSTEM & PRODUCT IDENTITY")
        lbl_ci_title.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px; font-weight: 700; letter-spacing: 0.5px;")
        ci_layout.addWidget(lbl_ci_title)

        lbl_app_name = QLabel("SecureFS — Encrypted File Vault (v2.0)")
        lbl_app_name.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 15px; font-weight: 700;")
        ci_layout.addWidget(lbl_app_name)

        app_details = (
            "Operating Systems & Cybersecurity Innovation (SIH 2026)\n"
            "Engine: Pure Python 3.14 + PySide6 6.12 + Cryptography 50.0\n"
            "Authenticated Encryption: AES-256-GCM with PBKDF2-HMAC-SHA256 (600k rounds)\n"
            "License: MIT • Pure User-Space Encrypted Filesystem Vault"
        )
        lbl_desc = QLabel(app_details)
        lbl_desc.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px; line-height: 1.5;")
        ci_layout.addWidget(lbl_desc)

        main_layout.addWidget(card_info)
        main_layout.addStretch()

    def _browse_storage(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Vault Storage Directory", self.input_storage_dir.text())
        if dir_path:
            self.input_storage_dir.setText(dir_path)

    def _apply_storage_dir(self):
        new_dir = self.input_storage_dir.text().strip()
        if not new_dir:
            return
        os.makedirs(new_dir, exist_ok=True)
        self.service.set_storage_dir(new_dir)
        self.settingsChanged.emit()
        QMessageBox.information(self, "Settings Updated", f"Vault directory updated to:\n{new_dir}")

    def _browse_log(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Select Audit Log File", self.input_log_file.text(), "Log Files (*.log);;All Files (*)")
        if file_path:
            self.input_log_file.setText(file_path)

    def _apply_log_file(self):
        new_log = self.input_log_file.text().strip()
        if not new_log:
            return
        log_dir = os.path.dirname(new_log)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        self.service.set_log_file(new_log)
        self.settingsChanged.emit()
        QMessageBox.information(self, "Settings Updated", f"Audit log path updated to:\n{new_log}")
