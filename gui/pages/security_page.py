"""
SecureFS — Security Architecture & Integrity Verification Page
==============================================================
Exposes cryptographic specifications, interactive AEAD tag verifier,
and formal security disclaimers regarding user-space and storage limitations.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QComboBox, QFrame, QGridLayout, QMessageBox, QTextEdit
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

from gui.styles.theme import (
    BG_CARD, BG_PANEL, BG_INPUT, ACCENT_RED, BORDER_MUTED, BORDER_LIGHT,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    STATUS_SUCCESS, STATUS_ALERT, STATUS_WARNING, STATUS_INFO, IconFactory
)
from gui.services.vault_service import VaultService, VerifyWorker


class SecuritySpecRow(QFrame):
    """Row displaying a single cryptographic specification item."""

    def __init__(self, label: str, value: str, standard: str, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: transparent;
                border-bottom: 1px solid {BORDER_MUTED};
                padding: 8px 0px;
            }}
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 6, 4, 6)

        lbl = QLabel(label)
        lbl.setStyleSheet(f"color: {TEXT_PRIMARY}; font-weight: 600; font-size: 13px; min-width: 180px;")
        layout.addWidget(lbl)

        val = QLabel(value)
        val.setStyleSheet(f"color: {ACCENT_RED}; font-family: monospace; font-size: 13px; min-width: 200px;")
        layout.addWidget(val)

        std = QLabel(standard)
        std.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        layout.addWidget(std)
        layout.addStretch()


class SecurityPage(QWidget):
    """Cryptographic specifications and live integrity verification tool."""

    def __init__(self, vault_service: VaultService, parent=None):
        super().__init__(parent)
        self.service = vault_service
        self.v_worker = None
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 28, 28, 28)
        main_layout.setSpacing(24)

        # Title
        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)
        title = QLabel("Security Architecture & Integrity")
        title.setStyleSheet(f"font-size: 24px; font-weight: 700; color: {TEXT_PRIMARY};")
        subtitle = QLabel("Cryptographic specifications, in-memory AEAD tamper testing, and threat model analysis")
        subtitle.setStyleSheet(f"font-size: 13px; color: {TEXT_SECONDARY};")
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        main_layout.addLayout(title_layout)

        # Top section: 2 columns
        grid = QGridLayout()
        grid.setSpacing(20)

        # 1. Cryptographic Specifications Card
        spec_card = QFrame()
        spec_card.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_CARD};
                border: 1px solid {BORDER_MUTED};
                border-radius: 8px;
            }}
        """)
        spec_layout = QVBoxLayout(spec_card)
        spec_layout.setContentsMargins(20, 20, 20, 20)
        spec_layout.setSpacing(12)

        lbl_spec_title = QLabel("ACTIVE CRYPTOGRAPHIC PROFILE")
        lbl_spec_title.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px; font-weight: 700; letter-spacing: 0.5px;")
        spec_layout.addWidget(lbl_spec_title)

        spec_layout.addWidget(SecuritySpecRow("Symmetric Cipher", "AES-256-GCM", "NIST SP 800-38D (AEAD)"))
        spec_layout.addWidget(SecuritySpecRow("Key Derivation", "PBKDF2-HMAC-SHA256", "RFC 8018 (600,000 rounds)"))
        spec_layout.addWidget(SecuritySpecRow("Legacy Compatibility", "PBKDF2-HMAC-SHA256", "100,000 rounds backward-compatible"))
        spec_layout.addWidget(SecuritySpecRow("Nonce / IV Size", "96-bit (12 bytes)", "CSPRNG secrets.token_bytes"))
        spec_layout.addWidget(SecuritySpecRow("Salt Size", "128-bit (16 bytes)", "CSPRNG unique per container"))
        spec_layout.addWidget(SecuritySpecRow("Tamper Tag", "128-bit GHASH", "Constant-time comparison"))
        spec_layout.addWidget(SecuritySpecRow("Secure Shredding", "3-Pass DoD 5220.22-M", "Random overwrite + os.fsync"))

        spec_layout.addStretch()
        grid.addWidget(spec_card, 0, 0)

        # 2. Interactive Tamper & Integrity Verifier Card
        verifier_card = QFrame()
        verifier_card.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_CARD};
                border: 1px solid {BORDER_MUTED};
                border-radius: 8px;
            }}
        """)
        verifier_layout = QVBoxLayout(verifier_card)
        verifier_layout.setContentsMargins(20, 20, 20, 20)
        verifier_layout.setSpacing(14)

        lbl_ver_title = QLabel("IN-MEMORY INTEGRITY VERIFIER")
        lbl_ver_title.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px; font-weight: 700; letter-spacing: 0.5px;")
        verifier_layout.addWidget(lbl_ver_title)

        lbl_ver_desc = QLabel("Test file authentication without writing plaintext to disk. Detects byte tampering, bit-flips, and unauthorized passphrases.")
        lbl_ver_desc.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px; line-height: 1.4;")
        lbl_ver_desc.setWordWrap(True)
        verifier_layout.addWidget(lbl_ver_desc)

        lbl_select_file = QLabel("Select Vault Container:")
        lbl_select_file.setStyleSheet(f"color: {TEXT_PRIMARY}; font-weight: 600; font-size: 12px;")
        verifier_layout.addWidget(lbl_select_file)

        self.combo_files = QComboBox()
        verifier_layout.addWidget(self.combo_files)

        lbl_ver_pwd = QLabel("Passphrase:")
        lbl_ver_pwd.setStyleSheet(f"color: {TEXT_PRIMARY}; font-weight: 600; font-size: 12px;")
        verifier_layout.addWidget(lbl_ver_pwd)

        pwd_row = QHBoxLayout()
        self.input_pwd = QLineEdit()
        self.input_pwd.setEchoMode(QLineEdit.Password)
        self.input_pwd.setPlaceholderText("Enter vault passphrase...")
        pwd_row.addWidget(self.input_pwd)

        self.btn_toggle_pwd = QPushButton("Show")
        self.btn_toggle_pwd.setFixedWidth(64)
        self.btn_toggle_pwd.clicked.connect(self._toggle_pwd)
        pwd_row.addWidget(self.btn_toggle_pwd)
        verifier_layout.addLayout(pwd_row)

        self.btn_verify = QPushButton("Execute Cryptographic Verification")
        self.btn_verify.setProperty("class", "btn-primary")
        self.btn_verify.setIcon(IconFactory.create_icon("security", "#ffffff", 16))
        self.btn_verify.setFixedHeight(38)
        self.btn_verify.clicked.connect(self._execute_verification)
        verifier_layout.addWidget(self.btn_verify)

        # Result badge
        self.lbl_ver_result = QLabel("Status: Ready to verify")
        self.lbl_ver_result.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        self.lbl_ver_result.setWordWrap(True)
        verifier_layout.addWidget(self.lbl_ver_result)

        verifier_layout.addStretch()
        grid.addWidget(verifier_card, 0, 1)

        main_layout.addLayout(grid)

        # 3. Engineering & Threat Model Disclaimers Card
        disclaimer_card = QFrame()
        disclaimer_card.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_CARD};
                border: 1px solid {BORDER_MUTED};
                border-radius: 8px;
                padding: 16px;
            }}
        """)
        disc_layout = QVBoxLayout(disclaimer_card)
        disc_layout.setContentsMargins(18, 16, 18, 16)
        disc_layout.setSpacing(10)

        lbl_disc_title = QLabel("ENGINEERING SPECIFICATIONS & STORAGE BOUNDARIES")
        lbl_disc_title.setStyleSheet(f"color: {STATUS_WARNING}; font-size: 11px; font-weight: 700; letter-spacing: 0.5px;")
        disc_layout.addWidget(lbl_disc_title)

        disc_text = (
            "• Architecture: SecureFS operates strictly as an encrypted file vault in Linux user-space (Python 3). "
            "It does not run as a Linux kernel-space module, block device driver, or privileged daemon.\n"
            "• Flash Wear-Leveling Disclaimer: The 3-pass DoD 5220.22-M overwrite routine calls os.fsync() to flush file buffers. "
            "However, on modern solid-state drives (SSDs, NVMe), flash translation layers (FTL) remap physical NAND blocks during wear-leveling, "
            "meaning raw physical wear cells cannot be guaranteed erased from user space.\n"
            "• Copy-on-Write Filesystems: On CoW filesystems (e.g., Btrfs, ZFS) or storage with volume snapshots, overwriting an existing file "
            "allocates new disk blocks rather than overwriting original blocks in place.\n"
            "• Zero Secret Plaintext: Passwords and encryption keys are never logged to disk, stored in memory caches, or exposed in audit trails."
        )
        lbl_disc_content = QLabel(disc_text)
        lbl_disc_content.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px; line-height: 1.5;")
        lbl_disc_content.setWordWrap(True)
        disc_layout.addWidget(lbl_disc_content)

        main_layout.addWidget(disclaimer_card)
        main_layout.addStretch()

    def refresh_vault_files(self):
        """Populates the verifier dropdown."""
        files = self.service.get_files()
        self.combo_files.clear()
        if not files:
            self.combo_files.addItem("No files in vault", None)
            self.combo_files.setEnabled(False)
            self.btn_verify.setEnabled(False)
        else:
            self.combo_files.setEnabled(True)
            self.btn_verify.setEnabled(True)
            for f in files:
                self.combo_files.addItem(f"{f['filename']}.sfs", f['filename'])

    def _toggle_pwd(self):
        if self.input_pwd.echoMode() == QLineEdit.Password:
            self.input_pwd.setEchoMode(QLineEdit.Normal)
            self.btn_toggle_pwd.setText("Hide")
        else:
            self.input_pwd.setEchoMode(QLineEdit.Password)
            self.btn_toggle_pwd.setText("Show")

    def _execute_verification(self):
        filename = self.combo_files.currentData()
        pwd = self.input_pwd.text()

        if not filename:
            QMessageBox.warning(self, "No File", "Please select a vault container to verify.")
            return

        if not pwd:
            QMessageBox.warning(self, "Password Required", "Please enter the passphrase.")
            return

        self.btn_verify.setEnabled(False)
        self.lbl_ver_result.setText("Computing PBKDF2 key and checking AEAD GHASH tag...")
        self.lbl_ver_result.setStyleSheet(f"color: {TEXT_SECONDARY};")

        self.v_worker = VerifyWorker(self.service.fs, filename, pwd)
        self.v_worker.finished.connect(self._on_verification_done)
        self.v_worker.start()

    def _on_verification_done(self, is_valid: bool, msg: str):
        self.btn_verify.setEnabled(True)
        if is_valid:
            self.lbl_ver_result.setText(f"✓ INTEGRITY VERIFIED: {msg}")
            self.lbl_ver_result.setStyleSheet(f"color: {STATUS_SUCCESS}; font-weight: 600;")
            QMessageBox.information(
                self, "Integrity Verified",
                f"Container: {self.combo_files.currentText()}\n\n"
                f"Status: PASS\n"
                "The authentication tag matches perfectly. Zero bytes have been tampered or corrupted."
            )
        else:
            self.lbl_ver_result.setText(f"✗ AUTHENTICATION FAILED: {msg}")
            self.lbl_ver_result.setStyleSheet(f"color: {STATUS_ALERT}; font-weight: 600;")
            QMessageBox.critical(
                self, "Integrity Alarm",
                f"Container: {self.combo_files.currentText()}\n\n"
                f"Status: FAIL\n\n"
                f"{msg}\n\n"
                "A security incident has been recorded in the audit log."
            )
