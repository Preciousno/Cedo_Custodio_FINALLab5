
#gui/main_window.py  — CC Crafts v8


from datetime import datetime

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QStackedWidget, QStatusBar,
    QFrame, QMessageBox, QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect,
)
from PyQt6.QtGui  import QFont, QCursor, QColor
from PyQt6.QtCore import Qt, QTimer, QSize, QPropertyAnimation, QEasingCurve

import database as db
from gui.styles  import C, QSS
from gui.widgets import (
    hline, load_icon, drop_shadow, pix_label,
    NavBtn, NavBtnMini, FWB,
)
from gui.pages import (
    DashboardPage, ProductsPage,
    InventoryPage, TransactionsPage,
)

_AF = Qt.AlignmentFlag

_PAGE_ORDER = ["dashboard", "products", "inventory", "transactions"]
_PAGE_TITLES = {
    "dashboard":    "Dashboard",
    "products":     "Product Showcase",
    "inventory":    "Inventory Management",
    "transactions": "Transactions & Sales",
}

_ACTIVE_FULL = (
    "QPushButton#nav_btn {"
    " color: white;"
    " background: rgba(255,255,255,0.22);"
    " border-left: 4px solid white;"
    " border-radius: 0 10px 10px 0;"
    " font-weight: bold;"
    "}"
)
_ACTIVE_MINI = (
    "QPushButton#nav_btn_mini {"
    " background: rgba(255,255,255,0.24);"
    " border: 2px solid rgba(255,255,255,0.65);"
    " border-radius: 12px;"
    "}"
)


class MainWindow(QMainWindow):

    def __init__(self, user: dict):
        super().__init__()
        self._user             = user
        self._sidebar_expanded = True
        self._fade_anim: QPropertyAnimation | None = None

        self.setWindowTitle("CC Crafts — Sales Inventory System")
        self.setMinimumSize(1280, 1000)
        self.setStyleSheet(QSS)

        self._build_ui()
        self._nav_to("dashboard", animate=False)

    # ══════════════════════════════════════════════════════════════════════════
    #  BUILD
    # ══════════════════════════════════════════════════════════════════════════
    def _build_ui(self):
        central = QWidget()
        central.setObjectName("centralwidget")
        self.setCentralWidget(central)

        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._mini_sb = self._build_mini_sidebar()
        self._mini_sb.setVisible(False)
        root.addWidget(self._mini_sb)

        self._full_sb = self._build_full_sidebar()
        self._full_sb.setVisible(True)
        root.addWidget(self._full_sb)

        root.addWidget(self._build_main_area(), 1)

        sb = QStatusBar()
        self.setStatusBar(sb)
        sb.showMessage("Ready  —  CC Crafts Sales Inventory System")

    # ── Mini sidebar ──────────────────────────────────────────────────────────
    def _build_mini_sidebar(self) -> QWidget:
        w = QWidget(); w.setObjectName("sidebarmini"); w.setFixedWidth(74)
        lay = QVBoxLayout(w); lay.setContentsMargins(0, 0, 0, 16); lay.setSpacing(0)

        lh = QWidget(); lh.setObjectName("logoholder_mini"); lh.setFixedHeight(80)
        lhl = QHBoxLayout(lh); lhl.setAlignment(_AF.AlignCenter)
        lhl.addWidget(pix_label("cclogo.png", 40, 40))
        lay.addWidget(lh)
        lay.addSpacing(10)

        self._mini_btns: dict[str, NavBtnMini] = {}
        for key, img, tip in [
            ("dashboard",    "dashboard.png",   "Dashboard"),
            ("products",     "product.png",     "Products"),
            ("inventory",    "inventory.png",   "Inventory"),
            ("transactions", "transaction.png", "Transactions"),
        ]:
            b = NavBtnMini(img, tip, icon_size=34)
            b.clicked.connect(lambda _, k=key: self._nav_to(k))
            self._mini_btns[key] = b
            lay.addWidget(b, 0, _AF.AlignHCenter)
            lay.addSpacing(6)

        lay.addStretch()
        return w

    # ── Full sidebar ──────────────────────────────────────────────────────────
    def _build_full_sidebar(self) -> QWidget:
        w = QWidget(); w.setObjectName("sidebar"); w.setFixedWidth(240)
        lay = QVBoxLayout(w); lay.setContentsMargins(0, 0, 0, 14); lay.setSpacing(0)

        lh = QWidget(); lh.setObjectName("logoholder"); lh.setFixedHeight(112)
        lhl = QHBoxLayout(lh); lhl.setAlignment(_AF.AlignCenter)
        lhl.addWidget(pix_label("cclogo.png", 88, 88))
        lay.addWidget(lh)
        lay.addSpacing(12)

        self._nav_btns: dict[str, NavBtn] = {}
        for key, img, label in [
            ("dashboard",    "dashboard.png",   "Dashboard"),
            ("products",     "product.png",     "Products"),
            ("inventory",    "inventory.png",   "Inventory"),
            ("transactions", "transaction.png", "Transactions"),
        ]:
            b = NavBtn(img, label, icon_size=26)
            b.setFixedWidth(240)
            b.clicked.connect(lambda _, k=key: self._nav_to(k))
            self._nav_btns[key] = b
            lay.addWidget(b)
            lay.addSpacing(3)

        lay.addStretch()

        div = QFrame(); div.setFrameShape(QFrame.Shape.HLine); div.setFixedHeight(1)
        div.setStyleSheet("background: rgba(255,255,255,0.25); border: none;")
        lay.addWidget(div)
        lay.addSpacing(8)

        user_lbl = QLabel(
            f"  👤  {self._user.get('username', 'User')}  ({self._user.get('role', '')})")
        user_lbl.setStyleSheet(
            "color: rgba(255,255,255,0.80); font-size: 11px; background: transparent;")
        lay.addWidget(user_lbl)

        self._clock_lbl = QLabel()
        self._clock_lbl.setStyleSheet(
            "color: rgba(255,255,255,0.50); font-size: 10px;"
            " background: transparent; padding-left: 5px;")
        lay.addWidget(self._clock_lbl)
        self._clock = QTimer(self)
        self._clock.timeout.connect(self._tick)
        self._clock.start(1000)
        self._tick()

        logout = QPushButton("  🔒  Log Out")
        logout.setObjectName("nav_btn")
        logout.setFixedHeight(44)
        logout.setFont(QFont("MS Reference Sans Serif", 11))
        logout.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        logout.clicked.connect(self._logout)
        lay.addWidget(logout)
        return w

    # ── Main area ─────────────────────────────────────────────────────────────
    def _build_main_area(self) -> QWidget:
        ms = QWidget(); ms.setObjectName("mainscreen")
        ms_lay = QVBoxLayout(ms)
        ms_lay.setContentsMargins(0, 0, 0, 0)
        ms_lay.setSpacing(0)

        # Glass topbar
        topbar = QWidget(); topbar.setObjectName("topbar"); topbar.setFixedHeight(68)
        tb_eff = QGraphicsDropShadowEffect()
        tb_eff.setBlurRadius(20); tb_eff.setOffset(0, 4)
        tb_eff.setColor(QColor(180, 0, 100, 30))
        topbar.setGraphicsEffect(tb_eff)

        tb = QHBoxLayout(topbar)
        tb.setContentsMargins(18, 0, 26, 0); tb.setSpacing(14)

        self._toggle_btn = QPushButton()
        self._toggle_btn.setObjectName("sidebar_toggle")
        self._toggle_btn.setFixedSize(40, 40)
        self._toggle_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._toggle_btn.clicked.connect(self._toggle_sidebar)
        self._refresh_toggle_icon()
        tb.addWidget(self._toggle_btn)

        self._page_title = QLabel("Dashboard")
        self._page_title.setObjectName("page_title")
        self._page_title.setFont(QFont("MS Reference Sans Serif", 13, FWB))
        tb.addWidget(self._page_title)
        tb.addStretch()

        self._topbar_clock = QLabel()
        self._topbar_clock.setStyleSheet(
            "color: " + C['text_light'] + "; font-size: 11px; background: transparent;")
        self._topbar_clock.setText(datetime.now().strftime("%A, %B %d, %Y"))
        tb.addWidget(self._topbar_clock)
        ms_lay.addWidget(topbar)

        # Stacked pages
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background: transparent;")
        self._pages: dict[str, QWidget] = {}
        for key in _PAGE_ORDER:
            if key == "dashboard":
                page = DashboardPage(self._nav_to)
            elif key == "products":
                page = ProductsPage()
            elif key == "inventory":
                page = InventoryPage()
            else:
                page = TransactionsPage()
            self._pages[key] = page
            self.stack.addWidget(page)

        ms_lay.addWidget(self.stack, 1)
        return ms

    # ══════════════════════════════════════════════════════════════════════════
    #  SIDEBAR TOGGLE
    # ══════════════════════════════════════════════════════════════════════════
    def _toggle_sidebar(self):
        self._sidebar_expanded = not self._sidebar_expanded
        self._full_sb.setVisible(self._sidebar_expanded)
        self._mini_sb.setVisible(not self._sidebar_expanded)
        self._refresh_toggle_icon()

    def _refresh_toggle_icon(self):
        img = "sidebar_close.png" if self._sidebar_expanded else "sidebar_open.png"
        self._toggle_btn.setIcon(load_icon(img, 28))
        self._toggle_btn.setIconSize(QSize(28, 28))

    # ══════════════════════════════════════════════════════════════════════════
    #  NAVIGATION with page-fade
    # ══════════════════════════════════════════════════════════════════════════
    def _nav_to(self, key: str, animate: bool = True):
        if key not in self._pages:
            return

        for k, b in self._nav_btns.items():
            b.setStyleSheet(_ACTIVE_FULL if k == key else "")
            b.set_active(k == key)
        for k, b in self._mini_btns.items():
            b.setStyleSheet(_ACTIVE_MINI if k == key else "")
            b.set_active(k == key)

        page = self._pages[key]

        # Refresh data before showing
        try:
            page.refresh()
        except Exception as ex:
            self.statusBar().showMessage(f"⚠️  Error loading {key}: {ex}", 5000)

        if animate and self.stack.currentWidget() is not page:
            # Fade the incoming page in (opacity 0 → 1)
            if self._fade_anim and self._fade_anim.state() == QPropertyAnimation.State.Running:
                self._fade_anim.stop()

            # Give the page a fresh opacity effect
            fx = QGraphicsOpacityEffect(page)
            fx.setOpacity(0.0)
            page.setGraphicsEffect(fx)
            self.stack.setCurrentWidget(page)

            self._fade_anim = QPropertyAnimation(fx, b"opacity")
            self._fade_anim.setDuration(220)
            self._fade_anim.setStartValue(0.0)
            self._fade_anim.setEndValue(1.0)
            self._fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

            def _on_done():
                # Remove the effect after animation so it doesn't affect painting
                page.setGraphicsEffect(None)

            self._fade_anim.finished.connect(_on_done)
            self._fade_anim.start()
        else:
            self.stack.setCurrentWidget(page)

        self._page_title.setText(_PAGE_TITLES.get(key, key.title()))

    # ══════════════════════════════════════════════════════════════════════════
    #  PUBLIC API
    # ══════════════════════════════════════════════════════════════════════════
    def sync_all(self, skip: str | None = None):
        for k, p in self._pages.items():
            if k != skip:
                try:
                    p.refresh()
                except Exception:
                    pass

    def set_status(self, msg: str, ms: int = 4000):
        self.statusBar().showMessage(msg, ms)

    # ══════════════════════════════════════════════════════════════════════════
    #  CLOCK & LOGOUT
    # ══════════════════════════════════════════════════════════════════════════
    def _tick(self):
        now = datetime.now()
        self._clock_lbl.setText(f"  {now.strftime('%Y-%m-%d  %H:%M:%S')}")
        if hasattr(self, "_topbar_clock"):
            self._topbar_clock.setText(now.strftime("%A, %B %d, %Y"))

    def _logout(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Log Out")
        msg.setText("Are you sure you want to log out?")
        msg.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setStyleSheet("""
            QMessageBox {
                background: white;
            }
            QLabel {
                color: #1a1a2e;
                font-size: 13px;
            }
            QPushButton {
                background: #cc007e;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 6px 18px;
                font-size: 12px;
            }
            QPushButton:hover {
                background: #e6008c;
            }
        """)
        if msg.exec() == QMessageBox.StandardButton.Yes:
            self._clock.stop()
            self.close()
            from app_manager import launch_login
            launch_login()
