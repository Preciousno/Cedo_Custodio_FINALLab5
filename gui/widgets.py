
# gui/widgets.py


import os

from PyQt6.QtWidgets import (
    QLabel, QPushButton, QFrame, QWidget,
    QHBoxLayout, QVBoxLayout, QSizePolicy,
    QGraphicsDropShadowEffect,
)
from PyQt6.QtGui import (
    QFont, QPixmap, QIcon, QCursor, QColor,
    QPainter, QPainterPath, QLinearGradient, QBrush,
)
from PyQt6.QtCore import Qt, QSize, QRectF

from gui.styles import C

# ── Asset resolution ───────────────────────────────────────────────────────────
_ASSETS = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "assets", "images",
)

def img_path(name: str) -> str:
    return os.path.join(_ASSETS, name)

def load_pixmap(name: str, w: int, h: int) -> QPixmap:
    px = QPixmap(img_path(name))
    if not px.isNull():
        px = px.scaled(w, h,
                       Qt.AspectRatioMode.KeepAspectRatio,
                       Qt.TransformationMode.SmoothTransformation)
    return px

def load_icon(name: str, size: int = 28) -> QIcon:
    return QIcon(load_pixmap(name, size, size))

# ── Font constants ─────────────────────────────────────────────────────────────
FWB = QFont.Weight.Bold
FWN = QFont.Weight.Normal

# ── Drop-shadow factory ────────────────────────────────────────────────────────
def drop_shadow(blur: int = 24, x: int = 0,
                y: int = 6, alpha: int = 40,
                color: tuple[int,int,int] = (180, 0, 100)) -> QGraphicsDropShadowEffect:
    e = QGraphicsDropShadowEffect()
    e.setBlurRadius(blur)
    e.setOffset(x, y)
    e.setColor(QColor(color[0], color[1], color[2], alpha))
    return e

# ── Transparent PNG label ──────────────────────────────────────────────────────
def pix_label(name: str, w: int, h: int) -> QLabel:
    lw = QLabel()
    lw.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
    lw.setStyleSheet("background: transparent; border: none;")
    lw.setAlignment(Qt.AlignmentFlag.AlignCenter)
    px = load_pixmap(name, w, h)
    if not px.isNull():
        lw.setPixmap(px)
    return lw

# ── Text label helper ──────────────────────────────────────────────────────────
def lbl(text: str, size: int = 13, bold: bool = False,
        color: str | None = None, family: str | None = None) -> QLabel:
    w = QLabel(text)
    w.setFont(QFont(family or "MS Reference Sans Serif",
                    size, FWB if bold else FWN))
    style = "background: transparent;"
    if color:
        style += " color: " + color + ";"
    w.setStyleSheet(style)
    return w

# ── Button helper ──────────────────────────────────────────────────────────────
def btn(text: str, obj_name: str, parent=None) -> QPushButton:
    b = QPushButton(text, parent)
    b.setObjectName(obj_name)
    b.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
    return b

# ── Horizontal rule ────────────────────────────────────────────────────────────
def hline() -> QFrame:
    f = QFrame()
    f.setFrameShape(QFrame.Shape.HLine)
    f.setFixedHeight(1)
    f.setStyleSheet(
        "background: rgba(204,0,126,0.15); border: none; max-height: 1px;"
    )
    return f

# ── Stock status helpers ───────────────────────────────────────────────────────
def stock_status(stock: int) -> str:
    if stock == 0:  return "Out of Stock"
    if stock <= 5:  return "Low Stock"
    return "In Stock"

def status_badge(status: str) -> QLabel:
    s = status.lower()
    if "out" in s:   bg, fg = C['danger_bg'],  C['danger']
    elif "low" in s: bg, fg = C['warning_bg'], C['warning']
    else:            bg, fg = C['success_bg'], C['success']
    w = QLabel(status)
    w.setAlignment(Qt.AlignmentFlag.AlignCenter)
    w.setStyleSheet(
        "background: " + bg + "; color: " + fg + ";"
        " border-radius: 10px; padding: 3px 10px;"
        " font-size: 10px; font-weight: bold; border: none;"
    )
    w.setFixedHeight(24)
    return w

def stock_bar(stock: int, max_stock: int = 20) -> QFrame:
    ratio = min(stock / max(max_stock, 1), 1.0)
    color = (C['danger']  if stock == 0 else
             C['warning'] if stock <= 5 else C['success'])
    outer = QFrame()
    outer.setFixedSize(110, 10)
    outer.setStyleSheet(
        "background: rgba(0,0,0,0.08); border-radius:5px; border:none;"
    )
    inner = QFrame(outer)
    inner.setFixedHeight(10)
    inner.setFixedWidth(max(int(110 * ratio), 4 if stock > 0 else 0))
    inner.setStyleSheet(
        "background: " + color + "; border-radius:5px; border:none;"
    )
    return outer

# ── Cell widget wrapper ────────────────────────────────────────────────────────
def cell_widget(*widgets, margins=(6, 2, 6, 2), spacing=6) -> QWidget:
    w = QWidget()
    w.setStyleSheet("background: transparent;")
    lay = QHBoxLayout(w)
    lay.setContentsMargins(*margins)
    lay.setSpacing(spacing)
    for widget in widgets:
        lay.addWidget(widget)
    lay.addStretch()
    return w


# ══════════════════════════════════════════════════════════════════════════════
#  GLASS CARD  — painted frosted glass panel with layered shadows
# ══════════════════════════════════════════════════════════════════════════════
class GlassCard(QFrame):
    """
    Painted glass card with:
      - Multi-layer coloured shadows for depth
      - Frosted gradient body
      - Subtle top-edge highlight
    Use as a drop-in for QFrame#content_card or QFrame#stat_card.
    """

    def __init__(self, radius: int = 18, parent=None):
        super().__init__(parent)
        self._r = radius
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setObjectName("glass_card")

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h, r = self.width(), self.height(), float(self._r)
        pad = 10

        # ── Shadow layers (magenta-tinted) ──────────────────────────────
        for i in range(6, 0, -1):
            sp = i * 2.5
            alpha = max(0, 18 - i * 2)
            sh = QColor(180, 0, 100, alpha)
            p.setBrush(QBrush(sh))
            p.setPen(Qt.PenStyle.NoPen)
            path = QPainterPath()
            path.addRoundedRect(
                QRectF(pad - sp, pad + sp * 0.4,
                       w - pad * 2 + sp * 2, h - pad * 2 + sp),
                r + sp * 0.4, r + sp * 0.4
            )
            p.drawPath(path)

        # ── Glass body ──────────────────────────────────────────────────
        body = QPainterPath()
        body.addRoundedRect(QRectF(pad, pad, w - pad * 2, h - pad * 2), r, r)

        grad = QLinearGradient(0, pad, 0, h - pad)
        grad.setColorAt(0.0, QColor(255, 255, 255, 205))
        grad.setColorAt(0.5, QColor(255, 248, 252, 190))
        grad.setColorAt(1.0, QColor(255, 240, 248, 175))
        p.setBrush(QBrush(grad))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawPath(body)

        # ── Top highlight ───────────────────────────────────────────────
        from PyQt6.QtGui import QPen
        p.setPen(QPen(QColor(255, 255, 255, 200), 1.5))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(
            QRectF(pad + 0.75, pad + 0.75, w - pad * 2 - 1.5, h - pad * 2 - 1.5),
            r - 0.5, r - 0.5
        )

        p.end()


# ══════════════════════════════════════════════════════════════════════════════
#  STAT CARD  — glassmorphism dashboard summary card
# ══════════════════════════════════════════════════════════════════════════════
class StatCard(GlassCard):
    """
    Dashboard summary card with glassmorphism surface.
    ┌─────────────────────────────┐  ← gradient accent bar (5 px)
    │  [icon box]  VALUE          │
    │              LABEL          │
    └─────────────────────────────┘
    """

    def __init__(self, img_file: str, value: str, label: str, color: str):
        super().__init__(radius=18)
        self._color = color
        self.setMinimumHeight(118)
        self.setMaximumHeight(132)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # Accent bar (painted on top in resizeEvent)
        self._bar = QFrame(self)
        self._bar.setFixedHeight(5)
        self._bar.setStyleSheet(
            "background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            " stop:0 " + color + ", stop:1 rgba(255,255,255,0.5));"
            " border: none; border-radius: 3px;"
        )

        lay = QVBoxLayout(self)
        lay.setContentsMargins(22, 20, 22, 18)
        lay.setSpacing(0)

        row = QHBoxLayout()
        row.setSpacing(14)

        # Icon container
        box = QWidget()
        box.setFixedSize(48, 48)
        box.setStyleSheet(
            "background: rgba(255,255,255,0.60);"
            " border-radius: 13px; border: 1px solid rgba(255,255,255,0.85);"
        )
        bl = QHBoxLayout(box)
        bl.setContentsMargins(6, 6, 6, 6)
        icon_lbl = QLabel()
        icon_lbl.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        icon_lbl.setStyleSheet("background: transparent; border: none;")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        px = load_pixmap(img_file, 30, 30)
        if not px.isNull():
            icon_lbl.setPixmap(px)
        bl.addWidget(icon_lbl)
        row.addWidget(box)

        col = QVBoxLayout()
        col.setSpacing(2)

        self._val = QLabel(str(value))
        self._val.setFont(QFont("Segoe UI", 22, FWB))
        self._val.setStyleSheet(
            "color: " + color + "; background: transparent; border: none;"
        )

        self._lbl = QLabel(label)
        self._lbl.setStyleSheet(
            "color: " + C['text_light'] + "; font-size: 9px;"
            " font-weight: bold; letter-spacing: 1.2px;"
            " background: transparent; border: none;"
        )

        col.addWidget(self._val)
        col.addWidget(self._lbl)
        row.addLayout(col)
        row.addStretch()
        lay.addLayout(row)

    def set_value(self, v: str) -> None:
        self._val.setText(str(v))

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._bar.setGeometry(10, 10, self.width() - 20, 5)


# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR NAV BUTTONS
# ══════════════════════════════════════════════════════════════════════════════
class NavBtn(QPushButton):
    """Full sidebar: icon + text, 52 px tall."""

    def __init__(self, img_file: str, label: str, icon_size: int = 26):
        super().__init__("   " + label)
        self.setObjectName("nav_btn")
        self.setFixedHeight(52)
        self.setProperty("active", False)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setIcon(load_icon(img_file, icon_size))
        self.setIconSize(QSize(icon_size, icon_size))

    def set_active(self, active: bool) -> None:
        self.setProperty("active", active)
        self.style().unpolish(self)
        self.style().polish(self)


class NavBtnMini(QPushButton):
    """Mini sidebar: icon-only, 52×52 px with tooltip."""

    def __init__(self, img_file: str, tooltip: str, icon_size: int = 34):
        super().__init__()
        self.setObjectName("nav_btn_mini")
        self.setFixedSize(52, 52)
        self.setProperty("active", False)
        self.setToolTip(tooltip)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setIcon(load_icon(img_file, icon_size))
        self.setIconSize(QSize(icon_size, icon_size))

    def set_active(self, active: bool) -> None:
        self.setProperty("active", active)
        self.style().unpolish(self)
        self.style().polish(self)
