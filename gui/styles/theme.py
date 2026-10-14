"""
SecureFS — Dark & Vivid Red Cybersecurity Theme
================================================
Strictly controlled color palette:
- Deep black and charcoal backgrounds
- Vivid red primary accent
- Crisp thin muted-white and subtle outlines
- Clean white and light gray typography
"""

from PySide6.QtGui import QColor, QIcon, QPixmap, QPainter, QPen, QBrush, QFont, QPolygon
from PySide6.QtCore import Qt, QPoint, QRectF

# Color Palette Constants
BG_WINDOW = "#080a0c"
BG_SIDEBAR = "#0d1013"
BG_PANEL = "#12161a"
BG_CARD = "#171c21"
BG_CARD_HOVER = "#1e242b"
BG_INPUT = "#0c0f12"

ACCENT_RED = "#ff2b3d"
ACCENT_RED_HOVER = "#ff4d5e"
ACCENT_RED_PRESSED = "#d91d2d"
ACCENT_RED_SUBTLE = "rgba(255, 43, 61, 0.12)"
ACCENT_RED_BORDER = "rgba(255, 43, 61, 0.45)"

BORDER_MUTED = "#242c33"
BORDER_SUBTLE = "#1d2329"
BORDER_LIGHT = "#35404b"
BORDER_WHITE_10 = "rgba(255, 255, 255, 0.10)"
BORDER_WHITE_20 = "rgba(255, 255, 255, 0.20)"

TEXT_PRIMARY = "#ffffff"
TEXT_SECONDARY = "#a4b2be"
TEXT_MUTED = "#62707c"

STATUS_SUCCESS = "#22c55e"
STATUS_SUCCESS_BG = "rgba(34, 197, 94, 0.12)"
STATUS_ALERT = "#ff2b3d"
STATUS_ALERT_BG = "rgba(255, 43, 61, 0.15)"
STATUS_WARNING = "#f59e0b"
STATUS_WARNING_BG = "rgba(245, 158, 11, 0.12)"
STATUS_INFO = "#38bdf8"
STATUS_INFO_BG = "rgba(56, 189, 248, 0.12)"

# Global QSS Stylesheet
GLOBAL_STYLESHEET = f"""
/* Global Reset */
* {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Inter", "Ubuntu", sans-serif;
    outline: none;
}}

QWidget {{
    background-color: transparent;
    color: {TEXT_PRIMARY};
    font-size: 13px;
}}

QMainWindow {{
    background-color: {BG_WINDOW};
}}

QToolTip {{
    background-color: {BG_PANEL};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_LIGHT};
    border-radius: 4px;
    padding: 6px 10px;
    font-size: 12px;
}}

/* Scrollbars */
QScrollBar:vertical {{
    background: transparent;
    width: 8px;
    margin: 0px;
}}

QScrollBar::handle:vertical {{
    background: {BORDER_LIGHT};
    min-height: 24px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical:hover {{
    background: {TEXT_MUTED};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar:horizontal {{
    background: transparent;
    height: 8px;
    margin: 0px;
}}

QScrollBar::handle:horizontal {{
    background: {BORDER_LIGHT};
    min-width: 24px;
    border-radius: 4px;
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}

/* Inputs & Forms */
QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: {BG_INPUT};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_MUTED};
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 13px;
    selection-background-color: {ACCENT_RED};
    selection-color: #ffffff;
}}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border: 1px solid {ACCENT_RED};
    background-color: #0e1216;
}}

QLineEdit:disabled, QTextEdit:disabled {{
    background-color: #080a0c;
    color: {TEXT_MUTED};
    border: 1px solid {BORDER_SUBTLE};
}}

/* Push Buttons */
QPushButton {{
    background-color: {BG_CARD};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_MUTED};
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 500;
    font-size: 13px;
}}

QPushButton:hover {{
    background-color: {BG_CARD_HOVER};
    border: 1px solid {BORDER_LIGHT};
}}

QPushButton:pressed {{
    background-color: #12161b;
}}

QPushButton:disabled {{
    background-color: #0b0e11;
    color: {TEXT_MUTED};
    border: 1px solid {BORDER_SUBTLE};
}}

/* Primary Red Button */
QPushButton.btn-primary {{
    background-color: {ACCENT_RED};
    color: #ffffff;
    border: 1px solid {ACCENT_RED};
    font-weight: 600;
}}

QPushButton.btn-primary:hover {{
    background-color: {ACCENT_RED_HOVER};
    border: 1px solid {ACCENT_RED_HOVER};
}}

QPushButton.btn-primary:pressed {{
    background-color: {ACCENT_RED_PRESSED};
    border: 1px solid {ACCENT_RED_PRESSED};
}}

QPushButton.btn-primary:disabled {{
    background-color: rgba(255, 43, 61, 0.3);
    border: 1px solid transparent;
    color: rgba(255, 255, 255, 0.4);
}}

/* Danger Button */
QPushButton.btn-danger {{
    background-color: rgba(255, 43, 61, 0.15);
    color: {ACCENT_RED};
    border: 1px solid rgba(255, 43, 61, 0.4);
    font-weight: 600;
}}

QPushButton.btn-danger:hover {{
    background-color: {ACCENT_RED};
    color: #ffffff;
    border: 1px solid {ACCENT_RED};
}}

/* Subtle Outline Button */
QPushButton.btn-outline {{
    background-color: transparent;
    border: 1px solid {BORDER_LIGHT};
    color: {TEXT_PRIMARY};
}}

QPushButton.btn-outline:hover {{
    background-color: {BG_CARD};
    border: 1px solid rgba(255, 255, 255, 0.4);
}}

/* ComboBox */
QComboBox {{
    background-color: {BG_INPUT};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_MUTED};
    border-radius: 6px;
    padding: 8px 12px;
    min-width: 120px;
}}

QComboBox:hover {{
    border: 1px solid {BORDER_LIGHT};
}}

QComboBox:focus {{
    border: 1px solid {ACCENT_RED};
}}

QComboBox::drop-down {{
    border: none;
    width: 24px;
}}

QComboBox QAbstractItemView {{
    background-color: {BG_PANEL};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_LIGHT};
    selection-background-color: {ACCENT_RED};
    selection-color: #ffffff;
    padding: 4px;
}}

/* CheckBoxes */
QCheckBox {{
    color: {TEXT_SECONDARY};
    spacing: 8px;
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 1px solid {BORDER_MUTED};
    border-radius: 4px;
    background-color: {BG_INPUT};
}}

QCheckBox::indicator:hover {{
    border: 1px solid {TEXT_SECONDARY};
}}

QCheckBox::indicator:checked {{
    background-color: {ACCENT_RED};
    border: 1px solid {ACCENT_RED};
    image: none;
}}

/* Tables */
QTableWidget {{
    background-color: {BG_PANEL};
    border: 1px solid {BORDER_MUTED};
    border-radius: 8px;
    gridline-color: {BORDER_SUBTLE};
    color: {TEXT_PRIMARY};
    selection-background-color: {ACCENT_RED_SUBTLE};
    selection-color: #ffffff;
}}

QTableWidget::item {{
    padding: 10px 12px;
    border-bottom: 1px solid {BORDER_SUBTLE};
}}

QTableWidget::item:selected {{
    background-color: {ACCENT_RED_SUBTLE};
    border-left: 2px solid {ACCENT_RED};
}}

QHeaderView::section {{
    background-color: {BG_CARD};
    color: {TEXT_SECONDARY};
    padding: 10px 12px;
    border: none;
    border-bottom: 1px solid {BORDER_MUTED};
    font-weight: 600;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}

/* Progress Bar */
QProgressBar {{
    background-color: {BG_INPUT};
    border: 1px solid {BORDER_MUTED};
    border-radius: 4px;
    height: 10px;
    text-align: center;
    color: transparent;
}}

QProgressBar::chunk {{
    background-color: {ACCENT_RED};
    border-radius: 3px;
}}

/* Group Boxes / Cards */
QGroupBox {{
    background-color: {BG_CARD};
    border: 1px solid {BORDER_MUTED};
    border-radius: 8px;
    margin-top: 24px;
    padding: 16px;
    font-weight: 600;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 4px 10px;
    color: {TEXT_PRIMARY};
    background-color: {BG_PANEL};
    border: 1px solid {BORDER_MUTED};
    border-radius: 4px;
    left: 12px;
}}
"""


class IconFactory:
    """Generates crisp minimal vector icons using QPainter."""

    @staticmethod
    def create_icon(name: str, color_hex: str = "#ffffff", size: int = 24) -> QIcon:
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        color = QColor(color_hex)
        pen = QPen(color, 2)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)

        s = float(size)
        pad = s * 0.15

        if name == "shield" or name == "security":
            # Shield outline with checkmark
            points = [
                QPoint(int(s * 0.5), int(s * 0.15)),
                QPoint(int(s * 0.85), int(s * 0.28)),
                QPoint(int(s * 0.85), int(s * 0.6)),
                QPoint(int(s * 0.5), int(s * 0.88)),
                QPoint(int(s * 0.15), int(s * 0.6)),
                QPoint(int(s * 0.15), int(s * 0.28)),
            ]
            painter.drawPolygon(QPolygon(points))
            # inner check
            painter.drawLine(int(s * 0.35), int(s * 0.5), int(s * 0.48), int(s * 0.65))
            painter.drawLine(int(s * 0.48), int(s * 0.65), int(s * 0.68), int(s * 0.38))

        elif name == "dashboard":
            # Grid / Dashboard gauge
            w = int(s * 0.3)
            h = int(s * 0.3)
            painter.drawRoundedRect(int(s * 0.15), int(s * 0.15), w, h, 2, 2)
            painter.drawRoundedRect(int(s * 0.55), int(s * 0.15), w, h, 2, 2)
            painter.drawRoundedRect(int(s * 0.15), int(s * 0.55), w, h, 2, 2)
            painter.drawRoundedRect(int(s * 0.55), int(s * 0.55), w, h, 2, 2)

        elif name == "vault":
            # Safe / Vault box with dial
            painter.drawRoundedRect(int(s * 0.15), int(s * 0.15), int(s * 0.7), int(s * 0.7), 3, 3)
            painter.drawEllipse(QPoint(int(s * 0.5), int(s * 0.5)), int(s * 0.16), int(s * 0.16))
            painter.drawLine(int(s * 0.5), int(s * 0.5), int(s * 0.62), int(s * 0.42))

        elif name == "lock" or name == "encrypt":
            # Padlock closed
            painter.drawRoundedRect(int(s * 0.22), int(s * 0.42), int(s * 0.56), int(s * 0.44), 3, 3)
            painter.drawArc(int(s * 0.32), int(s * 0.14), int(s * 0.36), int(s * 0.4), 0, 180 * 16)
            painter.drawPoint(int(s * 0.5), int(s * 0.62))
            painter.drawLine(int(s * 0.5), int(s * 0.62), int(s * 0.5), int(s * 0.72))

        elif name == "unlock" or name == "decrypt":
            # Padlock open
            painter.drawRoundedRect(int(s * 0.22), int(s * 0.42), int(s * 0.56), int(s * 0.44), 3, 3)
            painter.drawArc(int(s * 0.4), int(s * 0.12), int(s * 0.36), int(s * 0.4), 0, 180 * 16)
            painter.drawPoint(int(s * 0.5), int(s * 0.62))
            painter.drawLine(int(s * 0.5), int(s * 0.62), int(s * 0.5), int(s * 0.72))

        elif name == "logs" or name == "audit":
            # Activity document / list
            painter.drawRoundedRect(int(s * 0.2), int(s * 0.14), int(s * 0.6), int(s * 0.72), 3, 3)
            painter.drawLine(int(s * 0.32), int(s * 0.34), int(s * 0.68), int(s * 0.34))
            painter.drawLine(int(s * 0.32), int(s * 0.50), int(s * 0.68), int(s * 0.50))
            painter.drawLine(int(s * 0.32), int(s * 0.66), int(s * 0.54), int(s * 0.66))

        elif name == "settings":
            # Sliders / Cog minimal
            painter.drawLine(int(s * 0.2), int(s * 0.3), int(s * 0.8), int(s * 0.3))
            painter.drawEllipse(QPoint(int(s * 0.4), int(s * 0.3)), 3, 3)
            painter.drawLine(int(s * 0.2), int(s * 0.7), int(s * 0.8), int(s * 0.7))
            painter.drawEllipse(QPoint(int(s * 0.65), int(s * 0.7)), 3, 3)

        elif name == "refresh":
            # Circular arrow
            painter.drawArc(int(s * 0.2), int(s * 0.2), int(s * 0.6), int(s * 0.6), 45 * 16, 270 * 16)
            painter.drawLine(int(s * 0.62), int(s * 0.2), int(s * 0.8), int(s * 0.2))
            painter.drawLine(int(s * 0.8), int(s * 0.2), int(s * 0.8), int(s * 0.38))

        elif name == "trash" or name == "shred":
            # Trash can with shred hash
            painter.drawLine(int(s * 0.2), int(s * 0.3), int(s * 0.8), int(s * 0.3))
            painter.drawLine(int(s * 0.4), int(s * 0.2), int(s * 0.6), int(s * 0.2))
            painter.drawRoundedRect(int(s * 0.28), int(s * 0.3), int(s * 0.44), int(s * 0.55), 2, 2)
            painter.drawLine(int(s * 0.42), int(s * 0.42), int(s * 0.42), int(s * 0.72))
            painter.drawLine(int(s * 0.58), int(s * 0.42), int(s * 0.58), int(s * 0.72))

        elif name == "search":
            painter.drawEllipse(QPoint(int(s * 0.42), int(s * 0.42)), int(s * 0.24), int(s * 0.24))
            painter.drawLine(int(s * 0.6), int(s * 0.6), int(s * 0.82), int(s * 0.82))

        elif name == "export":
            # Arrow up-right or arrow down
            painter.drawLine(int(s * 0.5), int(s * 0.2), int(s * 0.5), int(s * 0.65))
            painter.drawLine(int(s * 0.32), int(s * 0.48), int(s * 0.5), int(s * 0.65))
            painter.drawLine(int(s * 0.68), int(s * 0.48), int(s * 0.5), int(s * 0.65))
            painter.drawLine(int(s * 0.2), int(s * 0.8), int(s * 0.8), int(s * 0.8))

        else:
            # Default dot
            painter.drawEllipse(QPoint(int(s * 0.5), int(s * 0.5)), int(s * 0.3), int(s * 0.3))

        painter.end()
        return QIcon(pixmap)
