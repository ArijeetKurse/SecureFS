"""
SecureFS — Main Application Window & Navigation
===============================================
Linux desktop dashboard featuring dark and vivid red cybersecurity theme,
smooth sidebar navigation, and modular page orchestration.
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QLabel, QStackedWidget, QFrame, QButtonGroup, QScrollArea
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon

from gui.styles.theme import (
    GLOBAL_STYLESHEET, BG_WINDOW, BG_SIDEBAR, BG_PANEL, BG_CARD,
    ACCENT_RED, ACCENT_RED_HOVER, ACCENT_RED_SUBTLE, BORDER_MUTED,
    BORDER_LIGHT, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    STATUS_SUCCESS, IconFactory
)
from gui.services.vault_service import VaultService
from gui.pages import (
    DashboardPage, VaultPage, EncryptPage, DecryptPage,
    SecurityPage, AuditPage, SettingsPage
)


class NavButton(QPushButton):
    """Custom sidebar navigation button with active highlight state."""

    def __init__(self, text: str, icon_name: str, parent=None):
        super().__init__(text, parent)
        self.icon_name = icon_name
        self.setCheckable(True)
        self.setAutoExclusive(True)
        self.setFixedHeight(42)
        self.setCursor(Qt.PointingHandCursor)
        self.setIcon(IconFactory.create_icon(icon_name, TEXT_SECONDARY, 18))
        self.setIconSize(QSize(18, 18))

        self.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {TEXT_SECONDARY};
                text-align: left;
                padding-left: 16px;
                font-size: 13px;
                font-weight: 500;
                border: none;
                border-left: 3px solid transparent;
                border-radius: 0px;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.04);
                color: #ffffff;
            }}
            QPushButton:checked {{
                background-color: {ACCENT_RED_SUBTLE};
                color: #ffffff;
                font-weight: 600;
                border-left: 3px solid {ACCENT_RED};
            }}
        """)


class MainWindow(QMainWindow):
    """Main Application Window."""

    def __init__(self, storage_dir: str = "encrypted_storage", log_file: str = "audit.log"):
        super().__init__()
        self.setWindowTitle("SecureFS — Encrypted File Vault")
        self.setMinimumSize(1040, 680)
        self.resize(1180, 760)

        # Apply global dark cyber stylesheet
        self.setStyleSheet(GLOBAL_STYLESHEET)

        # Initialize backend service
        self.service = VaultService(storage_dir=storage_dir, log_file=log_file, parent=self)

        self._init_ui()
        self._connect_signals()

        # Initial load
        self.nav_dashboard.setChecked(True)
        self._switch_page("dashboard")

    def _init_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # =====================================================================
        # 1. Left Sidebar
        # =====================================================================
        sidebar = QFrame()
        sidebar.setFixedWidth(240)
        sidebar.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_SIDEBAR};
                border-right: 1px solid {BORDER_MUTED};
            }}
        """)
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(0, 0, 0, 16)
        sb_layout.setSpacing(4)

        # Brand Header
        brand_frame = QFrame()
        brand_frame.setStyleSheet(f"background-color: transparent; border-bottom: 1px solid {BORDER_MUTED};")
        b_layout = QHBoxLayout(brand_frame)
        b_layout.setContentsMargins(18, 20, 18, 20)
        b_layout.setSpacing(12)

        lbl_logo = QLabel()
        lbl_logo.setPixmap(IconFactory.create_icon("shield", ACCENT_RED, 26).pixmap(26, 26))
        b_layout.addWidget(lbl_logo)

        brand_text_layout = QVBoxLayout()
        brand_text_layout.setSpacing(2)
        lbl_title = QLabel("SECUREFS")
        lbl_title.setStyleSheet(f"font-size: 15px; font-weight: 800; color: #ffffff; letter-spacing: 1px;")
        lbl_sub = QLabel("Encrypted Vault")
        lbl_sub.setStyleSheet(f"font-size: 11px; color: {TEXT_MUTED}; font-weight: 600; text-transform: uppercase;")
        brand_text_layout.addWidget(lbl_title)
        brand_text_layout.addWidget(lbl_sub)
        b_layout.addLayout(brand_text_layout)
        b_layout.addStretch()

        sb_layout.addWidget(brand_frame)
        sb_layout.addSpacing(10)

        # Nav Buttons
        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)

        self.nav_dashboard = NavButton("Dashboard", "dashboard")
        self.nav_vault = NavButton("My Vault", "vault")
        self.nav_encrypt = NavButton("Encrypt Files", "lock")
        self.nav_decrypt = NavButton("Decrypt / Export", "unlock")
        self.nav_security = NavButton("Security && Integrity", "security")
        self.nav_logs = NavButton("Audit Logs", "logs")
        self.nav_settings = NavButton("Settings", "settings")

        self.nav_buttons = [
            ("dashboard", self.nav_dashboard),
            ("vault", self.nav_vault),
            ("encrypt", self.nav_encrypt),
            ("decrypt", self.nav_decrypt),
            ("security", self.nav_security),
            ("logs", self.nav_logs),
            ("settings", self.nav_settings),
        ]

        for name, btn in self.nav_buttons:
            self.nav_group.addButton(btn)
            sb_layout.addWidget(btn)
            btn.clicked.connect(lambda checked, n=name: self._switch_page(n))

        sb_layout.addStretch()

        # Sidebar Footer: Engine Status Badge
        footer_frame = QFrame()
        footer_frame.setStyleSheet(f"background-color: transparent; padding: 0px 16px;")
        ft_layout = QVBoxLayout(footer_frame)
        ft_layout.setSpacing(6)

        self.lbl_vault_status = QLabel("● AES-256-GCM Active")
        self.lbl_vault_status.setStyleSheet(f"color: {STATUS_SUCCESS}; font-size: 11px; font-weight: 600;")
        ft_layout.addWidget(self.lbl_vault_status)

        self.lbl_version = QLabel("v2.0 • Linux Native")
        self.lbl_version.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        ft_layout.addWidget(self.lbl_version)

        sb_layout.addWidget(footer_frame)
        root_layout.addWidget(sidebar)

        # =====================================================================
        # 2. Main Content Stacked Area
        # =====================================================================
        self.stack = QStackedWidget()
        self.stack.setStyleSheet(f"background-color: {BG_WINDOW};")

        # Instantiate Pages
        self.page_dashboard = DashboardPage(self.service)
        self.page_vault = VaultPage(self.service)
        self.page_encrypt = EncryptPage(self.service)
        self.page_decrypt = DecryptPage(self.service)
        self.page_security = SecurityPage(self.service)
        self.page_logs = AuditPage(self.service)
        self.page_settings = SettingsPage(self.service)

        # Wrap pages in QScrollArea for responsiveness
        self.pages = {
            "dashboard": self._wrap_scroll(self.page_dashboard),
            "vault": self._wrap_scroll(self.page_vault),
            "encrypt": self._wrap_scroll(self.page_encrypt),
            "decrypt": self._wrap_scroll(self.page_decrypt),
            "security": self._wrap_scroll(self.page_security),
            "logs": self._wrap_scroll(self.page_logs),
            "settings": self._wrap_scroll(self.page_settings),
        }

        for p in self.pages.values():
            self.stack.addWidget(p)

        root_layout.addWidget(self.stack)

    def _wrap_scroll(self, widget: QWidget) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background-color: transparent;")
        scroll.setWidget(widget)
        return scroll

    def _connect_signals(self):
        # Cross-page navigation events
        self.page_dashboard.navigateRequested.connect(self._switch_page)
        self.page_vault.navigateRequested.connect(self._switch_page)

        # Auto-refresh on modifications
        self.page_encrypt.encryptionCompleted.connect(self._on_data_modified)
        self.page_decrypt.decryptionCompleted.connect(self._on_data_modified)
        self.page_settings.settingsChanged.connect(self._on_settings_modified)
        self.service.vaultChanged.connect(self._on_data_modified)

    def _switch_page(self, name: str):
        page_widget = self.pages.get(name)
        if not page_widget:
            return

        self.stack.setCurrentWidget(page_widget)

        # Sync sidebar button check state
        for btn_name, btn in self.nav_buttons:
            if btn_name == name:
                btn.setChecked(True)
                btn.setIcon(IconFactory.create_icon(btn.icon_name, "#ffffff", 18))
            else:
                btn.setIcon(IconFactory.create_icon(btn.icon_name, TEXT_SECONDARY, 18))

        # Dynamic refresh of the active page
        if name == "dashboard":
            self.page_dashboard.refresh_data()
        elif name == "vault":
            self.page_vault.refresh_files()
        elif name == "decrypt":
            self.page_decrypt.refresh_vault_files()
        elif name == "security":
            self.page_security.refresh_vault_files()
        elif name == "logs":
            self.page_logs.refresh_logs()

    def _on_data_modified(self):
        self.page_dashboard.refresh_data()
        self.page_vault.refresh_files()
        self.page_decrypt.refresh_vault_files()
        self.page_security.refresh_vault_files()
        self.page_logs.refresh_logs()

    def _on_settings_modified(self):
        self._on_data_modified()
