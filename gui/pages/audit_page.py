"""
SecureFS — Forensic Audit Logs Page
===================================
Visualizes immutable JSON-lines append-only audit trail with real-time
filtering by action type, security status, and search query.
"""

import os
import json
from typing import Optional, List, Dict
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QFrame,
    QComboBox, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

from gui.styles.theme import (
    BG_CARD, BG_PANEL, BG_INPUT, ACCENT_RED, BORDER_MUTED, BORDER_LIGHT,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    STATUS_SUCCESS, STATUS_ALERT, STATUS_WARNING, STATUS_INFO, IconFactory
)
from gui.services.vault_service import VaultService


class AuditPage(QWidget):
    """Forensic audit log viewer and filtering interface."""

    def __init__(self, vault_service: VaultService, parent=None):
        super().__init__(parent)
        self.service = vault_service
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 28, 28, 28)
        main_layout.setSpacing(20)

        # Header
        top_layout = QHBoxLayout()
        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)
        title = QLabel("Forensic Audit Logs")
        title.setStyleSheet(f"font-size: 24px; font-weight: 700; color: {TEXT_PRIMARY};")
        self.lbl_subtitle = QLabel("Append-only tamper-evident security log")
        self.lbl_subtitle.setStyleSheet(f"font-size: 13px; color: {TEXT_SECONDARY};")
        title_layout.addWidget(title)
        title_layout.addWidget(self.lbl_subtitle)
        top_layout.addLayout(title_layout)

        top_layout.addStretch()

        btn_export = QPushButton("Export Log...")
        btn_export.setIcon(IconFactory.create_icon("export", "#ffffff", 14))
        btn_export.clicked.connect(self._export_log)
        top_layout.addWidget(btn_export)

        btn_clear = QPushButton("Clear Log")
        btn_clear.setProperty("class", "btn-danger")
        btn_clear.setIcon(IconFactory.create_icon("trash", ACCENT_RED, 14))
        btn_clear.clicked.connect(self._clear_log)
        top_layout.addWidget(btn_clear)

        btn_refresh = QPushButton("Refresh")
        btn_refresh.setIcon(IconFactory.create_icon("refresh", TEXT_SECONDARY, 14))
        btn_refresh.clicked.connect(self.refresh_logs)
        top_layout.addWidget(btn_refresh)

        main_layout.addLayout(top_layout)

        # Filter Bar
        filter_frame = QFrame()
        filter_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_CARD};
                border: 1px solid {BORDER_MUTED};
                border-radius: 8px;
                padding: 6px;
            }}
        """)
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(12, 6, 12, 6)
        filter_layout.setSpacing(12)

        lbl_search_ico = QLabel()
        lbl_search_ico.setPixmap(IconFactory.create_icon("search", TEXT_MUTED, 18).pixmap(18, 18))
        filter_layout.addWidget(lbl_search_ico)

        self.input_search = QLineEdit()
        self.input_search.setPlaceholderText("Filter by filename, status, or details...")
        self.input_search.textChanged.connect(self.refresh_logs)
        filter_layout.addWidget(self.input_search)

        lbl_action = QLabel("Action:")
        lbl_action.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px; font-weight: 600;")
        filter_layout.addWidget(lbl_action)

        self.combo_action = QComboBox()
        self.combo_action.addItems(["ALL", "WRITE", "READ", "VERIFY", "EXPORT", "SECURE_DELETE"])
        self.combo_action.currentTextChanged.connect(self.refresh_logs)
        filter_layout.addWidget(self.combo_action)

        lbl_status = QLabel("Status:")
        lbl_status.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px; font-weight: 600;")
        filter_layout.addWidget(lbl_status)

        self.combo_status = QComboBox()
        self.combo_status.addItems(["ALL", "SUCCESS", "ALERT_TAMPER_OR_AUTH_FAIL", "FAILED"])
        self.combo_status.currentTextChanged.connect(self.refresh_logs)
        filter_layout.addWidget(self.combo_status)

        self.lbl_entry_count = QLabel("0 entries")
        self.lbl_entry_count.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px; font-weight: 600;")
        filter_layout.addWidget(self.lbl_entry_count)

        main_layout.addWidget(filter_frame)

        # Audit Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Timestamp (UTC)", "Action", "Status", "Filename / Target", "Audit Details"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        main_layout.addWidget(self.table)

    def refresh_logs(self):
        """Reads logs using backend parser with active filters."""
        self.lbl_subtitle.setText(f"Active log file: {self.service.fs.log_file}")
        action = self.combo_action.currentText()
        status = self.combo_status.currentText()
        search = self.input_search.text().strip()

        entries = self.service.get_audit_logs(
            max_entries=1000,
            action=action if action != "ALL" else None,
            status=status if status != "ALL" else None,
            search=search if search else None
        )

        self.lbl_entry_count.setText(f"{len(entries)} entry/entries")
        self.table.setRowCount(len(entries))

        for row, item in enumerate(entries):
            ts = item.get("timestamp", "-").replace("T", " ")[:19]
            act = item.get("action", "-")
            st = item.get("status", "-")
            fn = item.get("filename", "-")
            det = item.get("details", "")

            it_ts = QTableWidgetItem(ts)
            it_act = QTableWidgetItem(act)
            it_st = QTableWidgetItem(st)
            it_fn = QTableWidgetItem(fn)
            it_det = QTableWidgetItem(det)

            # Highlighting status
            if "SUCCESS" in st:
                it_st.setForeground(QColor(STATUS_SUCCESS))
            elif "ALERT" in st:
                it_st.setForeground(QColor(STATUS_ALERT))
                it_act.setForeground(QColor(STATUS_ALERT))
            else:
                it_st.setForeground(QColor(STATUS_WARNING))

            self.table.setItem(row, 0, it_ts)
            self.table.setItem(row, 1, it_act)
            self.table.setItem(row, 2, it_st)
            self.table.setItem(row, 3, it_fn)
            self.table.setItem(row, 4, it_det)

    def _export_log(self):
        """Exports the active log to a chosen path."""
        dest_path, _ = QFileDialog.getSaveFileName(self, "Export Audit Log", "audit_export.json", "JSON Files (*.json);;All Files (*)")
        if not dest_path:
            return

        entries = self.service.get_audit_logs(max_entries=5000)
        try:
            with open(dest_path, "w", encoding="utf-8") as f:
                json.dump(entries, f, indent=2)
            QMessageBox.information(self, "Log Exported", f"Exported {len(entries)} audit entries to:\n{dest_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export log:\n{str(e)}")

    def _clear_log(self):
        """Authorizes clearing of the audit log."""
        confirm = QMessageBox.warning(
            self, "Confirm Audit Log Reset",
            "Are you sure you want to clear the audit log?\n\n"
            "This will archive a reset event and truncate previous log entries.\n\n"
            "Proceed?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            self.service.fs.clear_audit_log()
            self.refresh_logs()
            QMessageBox.information(self, "Log Cleared", "Audit log has been reset.")
