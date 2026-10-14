"""
SecureFS — Dashboard Page
=========================
Displays vault health, storage metrics, quick action launcher, and recent audit activity.
"""

from typing import Dict, Any, List
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGridLayout, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor

from gui.styles.theme import (
    BG_CARD, BG_CARD_HOVER, BG_PANEL, ACCENT_RED, BORDER_MUTED, BORDER_LIGHT,
    BORDER_WHITE_10, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    STATUS_SUCCESS, STATUS_ALERT, STATUS_WARNING, STATUS_INFO, IconFactory
)
from gui.services.vault_service import VaultService


class StatCard(QFrame):
    """Modern dark card displaying a single key metric."""

    def __init__(self, title: str, value: str, subtext: str, accent_color: str = ACCENT_RED, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_CARD};
                border: 1px solid {BORDER_MUTED};
                border-radius: 8px;
                padding: 14px;
            }}
            QFrame:hover {{
                border: 1px solid {BORDER_LIGHT};
                background-color: {BG_CARD_HOVER};
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(6)

        self.lbl_title = QLabel(title.upper())
        self.lbl_title.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px; font-weight: 600; letter-spacing: 0.5px;")

        self.lbl_val = QLabel(value)
        self.lbl_val.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 24px; font-weight: 700;")

        self.lbl_sub = QLabel(subtext)
        self.lbl_sub.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")

        layout.addWidget(self.lbl_title)
        layout.addWidget(self.lbl_val)
        layout.addWidget(self.lbl_sub)

    def update_values(self, value: str, subtext: str):
        self.lbl_val.setText(value)
        self.lbl_sub.setText(subtext)


class DashboardPage(QWidget):
    """Main overview dashboard with stats, quick actions, and recent audit activity."""

    navigateRequested = Signal(str)  # 'vault', 'encrypt', 'decrypt', 'security', 'logs', 'settings'

    def __init__(self, vault_service: VaultService, parent=None):
        super().__init__(parent)
        self.service = vault_service
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 28, 28, 28)
        main_layout.setSpacing(24)

        # 1. Header Banner
        header_layout = QHBoxLayout()
        header_text_layout = QVBoxLayout()
        header_text_layout.setSpacing(4)

        title = QLabel("Security Operations Center")
        title.setStyleSheet(f"font-size: 24px; font-weight: 700; color: {TEXT_PRIMARY};")
        subtitle = QLabel("Hardware-backed AES-256-GCM authenticated file vault")
        subtitle.setStyleSheet(f"font-size: 13px; color: {TEXT_SECONDARY};")

        header_text_layout.addWidget(title)
        header_text_layout.addWidget(subtitle)
        header_layout.addLayout(header_text_layout)
        header_layout.addStretch()

        # Vault Status Badge
        self.status_badge = QLabel("● VAULT ONLINE & PROTECTED")
        self.status_badge.setStyleSheet(f"""
            background-color: rgba(34, 197, 94, 0.12);
            color: {STATUS_SUCCESS};
            border: 1px solid rgba(34, 197, 94, 0.35);
            border-radius: 6px;
            padding: 6px 14px;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.5px;
        """)
        header_layout.addWidget(self.status_badge)
        main_layout.addLayout(header_layout)

        # 2. Metric Cards Grid
        grid_layout = QGridLayout()
        grid_layout.setSpacing(16)

        self.card_files = StatCard("Encrypted Files", "0", "0 v2 modern • 0 v1 legacy")
        self.card_storage = StatCard("Vault Storage", "0 B", "Encrypted on-disk size")
        self.card_security = StatCard("Integrity Status", "100%", "Zero tamper anomalies")
        self.card_engine = StatCard("Cipher Engine", "AES-256-GCM", "PBKDF2 600K rounds")

        grid_layout.addWidget(self.card_files, 0, 0)
        grid_layout.addWidget(self.card_storage, 0, 1)
        grid_layout.addWidget(self.card_security, 0, 2)
        grid_layout.addWidget(self.card_engine, 0, 3)
        main_layout.addLayout(grid_layout)

        # 3. Quick Actions Bar
        actions_frame = QFrame()
        actions_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_CARD};
                border: 1px solid {BORDER_MUTED};
                border-radius: 8px;
                padding: 12px;
            }}
        """)
        actions_layout = QHBoxLayout(actions_frame)
        actions_layout.setContentsMargins(16, 12, 16, 12)
        actions_layout.setSpacing(12)

        lbl_qa = QLabel("Quick Actions:")
        lbl_qa.setStyleSheet(f"font-weight: 600; color: {TEXT_PRIMARY}; font-size: 13px;")
        actions_layout.addWidget(lbl_qa)

        btn_enc = QPushButton("Encrypt New File")
        btn_enc.setProperty("class", "btn-primary")
        btn_enc.setIcon(IconFactory.create_icon("lock", "#ffffff", 16))
        btn_enc.clicked.connect(lambda: self.navigateRequested.emit("encrypt"))
        actions_layout.addWidget(btn_enc)

        btn_dec = QPushButton("Decrypt / Export")
        btn_dec.setIcon(IconFactory.create_icon("unlock", "#ffffff", 16))
        btn_dec.clicked.connect(lambda: self.navigateRequested.emit("decrypt"))
        actions_layout.addWidget(btn_dec)

        btn_vault = QPushButton("Browse Vault")
        btn_vault.setIcon(IconFactory.create_icon("vault", "#ffffff", 16))
        btn_vault.clicked.connect(lambda: self.navigateRequested.emit("vault"))
        actions_layout.addWidget(btn_vault)

        btn_verify = QPushButton("Verify Integrity")
        btn_verify.setIcon(IconFactory.create_icon("security", "#ffffff", 16))
        btn_verify.clicked.connect(lambda: self.navigateRequested.emit("security"))
        actions_layout.addWidget(btn_verify)

        actions_layout.addStretch()

        btn_refresh = QPushButton("Refresh")
        btn_refresh.setIcon(IconFactory.create_icon("refresh", TEXT_SECONDARY, 14))
        btn_refresh.clicked.connect(self.refresh_data)
        actions_layout.addWidget(btn_refresh)

        main_layout.addWidget(actions_frame)

        # 4. Recent Operations Table
        recent_label_layout = QHBoxLayout()
        lbl_recent = QLabel("Recent Security Audit Activity")
        lbl_recent.setStyleSheet(f"font-size: 15px; font-weight: 600; color: {TEXT_PRIMARY};")
        recent_label_layout.addWidget(lbl_recent)
        recent_label_layout.addStretch()

        btn_all_logs = QPushButton("View All Logs →")
        btn_all_logs.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {ACCENT_RED};
                font-weight: 600;
                font-size: 12px;
            }}
            QPushButton:hover {{
                color: #ffffff;
                text-decoration: underline;
            }}
        """)
        btn_all_logs.clicked.connect(lambda: self.navigateRequested.emit("logs"))
        recent_label_layout.addWidget(btn_all_logs)
        main_layout.addLayout(recent_label_layout)

        self.table_recent = QTableWidget()
        self.table_recent.setColumnCount(5)
        self.table_recent.setHorizontalHeaderLabels(["Timestamp (UTC)", "Operation", "Status", "Target File", "Details"])
        self.table_recent.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table_recent.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table_recent.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table_recent.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table_recent.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.table_recent.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_recent.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_recent.verticalHeader().setVisible(False)
        self.table_recent.setFixedHeight(240)
        main_layout.addWidget(self.table_recent)

        main_layout.addStretch()

    def _format_size(self, size_bytes: int) -> str:
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.2f} MB"

    def refresh_data(self):
        """Reloads stats and recent audit log events."""
        files = self.service.get_files()
        stats = self.service.get_stats()
        logs = self.service.get_audit_logs(max_entries=8)

        # Counts
        total_files = len(files)
        v2_count = sum(1 for f in files if "v2" in f.get("version", ""))
        v1_count = total_files - v2_count
        self.card_files.update_values(str(total_files), f"{v2_count} v2 modern • {v1_count} v1 legacy")

        # Storage
        total_size = sum(f["size_bytes"] for f in files)
        self.card_storage.update_values(self._format_size(total_size), f"{len(files)} encrypted archives")

        # Security anomalies
        tamper_events = sum(1 for l in logs if "ALERT" in l.get("status", ""))
        if tamper_events == 0:
            self.card_security.update_values("100% OK", "Zero tamper alarms detected")
        else:
            self.card_security.update_values(f"{tamper_events} ALARMS", "Tamper/Auth failures in logs")

        # Populate recent operations table
        self.table_recent.setRowCount(len(logs))
        for row, entry in enumerate(logs):
            ts = entry.get("timestamp", "-").replace("T", " ")[:19]
            action = entry.get("action", "-")
            status = entry.get("status", "-")
            filename = entry.get("filename", "-")
            details = entry.get("details", "")

            it_ts = QTableWidgetItem(ts)
            it_action = QTableWidgetItem(action)
            it_status = QTableWidgetItem(status)
            it_filename = QTableWidgetItem(filename)
            it_details = QTableWidgetItem(details)

            # Color status
            if "SUCCESS" in status:
                it_status.setForeground(QColor(STATUS_SUCCESS))
            elif "ALERT" in status:
                it_status.setForeground(QColor(STATUS_ALERT))
            else:
                it_status.setForeground(QColor(STATUS_WARNING))

            self.table_recent.setItem(row, 0, it_ts)
            self.table_recent.setItem(row, 1, it_action)
            self.table_recent.setItem(row, 2, it_status)
            self.table_recent.setItem(row, 3, it_filename)
            self.table_recent.setItem(row, 4, it_details)
