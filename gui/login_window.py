
#gui/login_window.py


from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QSpacerItem, QSizePolicy,
    QFrame,
)
from PyQt6.QtGui  import (
    QFont, QCursor, QPainter, QPainterPath, QBrush, QColor,
    QLinearGradient,
)
from PyQt6.QtCore import Qt, QRectF

import database as db
from gui.styles  import C
from gui.widgets import pix_label, FWB


# ── Magenta gradient left panel ────────────────────────────────────────────────
class _LeftPanel(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r    = QRectF(0, 0, self.width(), self.height())
        rad  = 100.0

        # Gradient fill
        grad = QLinearGradient(0, 0, 0, self.height())
        grad.setColorAt(0.0, QColor("#e6006e"))
        grad.setColorAt(0.5, QColor("#cc007e"))
        grad.setColorAt(1.0, QColor("#7a0050"))

        path = QPainterPath()
        path.moveTo(r.left(), r.top())
        path.lineTo(r.right() - rad, r.top())
        path.quadTo(r.right(), r.top(),    r.right(), r.top() + rad)
        path.lineTo(r.right(), r.bottom() - rad)
        path.quadTo(r.right(), r.bottom(), r.right() - rad, r.bottom())
        path.lineTo(r.left(), r.bottom())
        path.closeSubpath()

        p.fillPath(path, QBrush(grad))

        # Decorative circles
        p.setBrush(QBrush(QColor(255, 255, 255, 18)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QRectF(-40, -40, 200, 200))
        p.drawEllipse(QRectF(r.width() - 120, r.height() - 120, 180, 180))
        p.end()


# ── Frosted glass right panel ──────────────────────────────────────────────────
class _RightPanel(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # White base
        p.setBrush(QBrush(QColor(255, 255, 255, 230)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRect(0, 0, w, h)

        # Subtle rose tint gradient
        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(0.0, QColor(255, 240, 250, 60))
        grad.setColorAt(1.0, QColor(248, 224, 244, 40))
        p.fillRect(0, 0, w, h, QBrush(grad))
        p.end()


# ── Login dialog ───────────────────────────────────────────────────────────────
class LoginWindow(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("CC Crafts — Sales Inventory System")
        self.setFixedSize(820, 520)
        self.setStyleSheet("QDialog { background: " + C['white'] + "; }")
        self._user: dict | None = None
        self._build_ui()

    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._make_left(), 1)
        root.addWidget(self._make_right())

    # ── Left panel ─────────────────────────────────────────────────────────────
    def _make_left(self) -> QWidget:
        panel = _LeftPanel()
        lay   = QVBoxLayout(panel)
        lay.setContentsMargins(32, 52, 32, 44)
        lay.setSpacing(0)

        # Cream logo box
        logo_box = QWidget()
        logo_box.setFixedSize(178, 158)
        logo_box.setStyleSheet(
            "background: " + C['logo_bg'] + ";"
            " border-radius: 32px; border: none;"
        )
        ll = QVBoxLayout(logo_box)
        ll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ll.setContentsMargins(12, 12, 12, 12)
        ll.addWidget(pix_label("cclogo.png", 148, 128))

        logo_row = QHBoxLayout()
        logo_row.addStretch()
        logo_row.addWidget(logo_box)
        logo_row.addStretch()
        lay.addLayout(logo_row)
        lay.addSpacing(28)

        for text, color in [
            ("SALES",     C['text_inv']),
            ("INVENTORY", "#ffd6f0"),
            ("SYSTEM",    C['text_inv']),
        ]:
            lw = QLabel(text)
            lw.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lw.setFont(QFont("Segoe UI", 23, FWB))
            lw.setStyleSheet(
                "color: " + color + "; background: transparent; border: none;"
            )
            lay.addWidget(lw)

        lay.addStretch()
        return panel

    # ── Right panel ────────────────────────────────────────────────────────────
    def _make_right(self) -> QWidget:
        panel = _RightPanel()
        panel.setFixedSize(400, 520)

        lay = QVBoxLayout(panel)
        lay.setContentsMargins(48, 0, 48, 24)
        lay.setSpacing(0)

        lay.addItem(QSpacerItem(0, 60, QSizePolicy.Policy.Minimum,
                                QSizePolicy.Policy.Expanding))

        # Heading
        heading = QLabel("Login")
        heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        heading.setFont(QFont("MS Outlook", 32, FWB))
        heading.setStyleSheet(
            "color: " + C['text'] + "; background: transparent; border: none;"
        )
        lay.addWidget(heading)
        lay.addSpacing(8)

        # Subtitle
        sub = QLabel("Welcome back to CC Crafts")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet(
            "color: " + C['text_light'] + "; font-size: 12px;"
            " background: transparent; border: none;"
        )
        lay.addWidget(sub)
        lay.addSpacing(32)

        # Username input
        self.username = QLineEdit()
        self.username.setObjectName("username")
        self.username.setFixedSize(306, 46)
        self.username.setFont(QFont("Segoe UI", 12))
        self.username.setPlaceholderText("Username")
        self.username.setStyleSheet(_input_css("username"))
        self.username.textChanged.connect(self._clear_err)
        lay.addLayout(_centred(self.username))
        lay.addSpacing(14)

        # Password input
        self.password = QLineEdit()
        self.password.setObjectName("password")
        self.password.setFixedSize(306, 46)
        self.password.setFont(QFont("Segoe UI", 12))
        self.password.setPlaceholderText("Password")
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.setStyleSheet(_input_css("password"))
        self.password.textChanged.connect(self._clear_err)
        self.password.returnPressed.connect(self._do_login)
        lay.addLayout(_centred(self.password))
        lay.addSpacing(28)

        # Login button
        self.logbot = QPushButton("Login")
        self.logbot.setObjectName("logbot")
        self.logbot.setFixedSize(306, 46)
        self.logbot.setFont(QFont("Segoe UI", 13, FWB))
        self.logbot.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.logbot.setStyleSheet(_login_btn_css())
        self.logbot.clicked.connect(self._do_login)
        lay.addLayout(_centred(self.logbot))
        lay.addSpacing(10)

        # Error label
        self._err = QLabel("")
        self._err.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._err.setStyleSheet(
            "color: " + C['danger'] + ";"
            " font-size: 11px; background: transparent; border: none;"
        )
        lay.addWidget(self._err)

        lay.addItem(QSpacerItem(0, 30, QSizePolicy.Policy.Minimum,
                                QSizePolicy.Policy.Expanding))

        hint = QLabel("Default:  admin / admin123   |   staff / staff123")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet(
            "color: " + C['text_light'] + ";"
            " font-size: 10px; background: transparent; border: none;"
        )
        lay.addWidget(hint)
        return panel

    # ── Auth ────────────────────────────────────────────────────────────────────
    def _do_login(self):
        user = db.login(self.username.text().strip(), self.password.text())
        if user:
            self._user = user
            self.accept()
        else:
            self._err.setText("❌  Invalid username or password.")
            self.password.clear()
            self.password.setFocus()

    def _clear_err(self):
        self._err.setText("")

    def current_user(self) -> dict | None:
        return self._user


# ── CSS helpers ────────────────────────────────────────────────────────────────
def _input_css(name: str) -> str:
    m, mh = C['magenta'], C['magenta_h']
    return (
        f"#{name} {{"
        f" background: {m}; border-radius: 23px;"
        f" color: white; padding-left: 22px; border: none;"
        f" font-size: 13px;"
        f"}}"
        f"#{name}::placeholder {{ color: rgba(255,255,255,0.72); }}"
        f"#{name}:hover  {{ background: {mh}; }}"
        f"#{name}:focus  {{ border: 2.5px solid rgba(255,255,255,0.85); }}"
    )


def _login_btn_css() -> str:
    m, mh = C['magenta'], C['magenta_h']
    return (
        f"QPushButton {{"
        f" border-radius: 23px; border: 2px solid {m};"
        f" color: {m}; background: rgba(255,255,255,0.90);"
        f" font-size: 13px; font-weight: bold;"
        f"}}"
        f"QPushButton:hover   {{ background: {m};  color: white; }}"
        f"QPushButton:pressed {{ background: {mh}; color: white; border-color: {mh}; }}"
    )


def _centred(widget: QWidget) -> QHBoxLayout:
    row = QHBoxLayout()
    row.addStretch()
    row.addWidget(widget)
    row.addStretch()
    return row
