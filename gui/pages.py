
# gui/pages.py  — CC Crafts v8

from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QTableWidget, QTableWidgetItem,
    QScrollArea, QGridLayout, QMessageBox, QLineEdit, QPushButton,
    QAbstractItemView, QHeaderView, QSizePolicy,
    QGraphicsDropShadowEffect, QSpacerItem,
)
from PyQt6.QtGui  import QFont, QColor, QPixmap, QCursor

from PyQt6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve,
    QTimer,
)
try:
    from PyQt6.QtCore import pyqtProperty
except ImportError:
    from PyQt6.sip import pyqtProperty

import database as db
from gui.styles  import C
from gui.widgets import (
    lbl, btn, hline, drop_shadow,
    stock_status, status_badge, stock_bar, cell_widget,
    StatCard, GlassCard, FWB,
)
from gui.dialogs import (
    ProductDialog, SaleDialog,
    ProductPreviewDialog, bytes_to_pixmap,
)

_AF   = Qt.AlignmentFlag
_ETG  = QAbstractItemView.EditTrigger.NoEditTriggers
_SBR  = QAbstractItemView.SelectionBehavior.SelectRows
_RST  = QHeaderView.ResizeMode.Stretch
_RTC  = QHeaderView.ResizeMode.ResizeToContents
_RFXD = QHeaderView.ResizeMode.Fixed
_DC   = 1

_TABLE_CSS = (
    "QTableWidget {"
    " background: transparent; color: " + C['text'] + ";"
    " border: none; gridline-color: transparent;"
    " font: 10pt 'MS Reference Sans Serif';"
    " alternate-background-color: rgba(204,0,126,0.04);"
    " selection-background-color: rgba(204,0,126,0.12);"
    "}"
    "QTableWidget::item {"
    " padding: 8px 12px;"
    " border-bottom: 1px solid rgba(229,231,235,0.55);"
    " background: transparent;"
    "}"
    "QHeaderView::section {"
    " background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
    " stop:0 " + C['header_bg'] + ", stop:1 " + C['magenta_d'] + ");"
    " color: white; padding: 10px 12px; border: none;"
    " font-weight: bold; font-size: 10pt; letter-spacing: 0.4px;"
    "}"
    "QTableCornerButton::section { background: " + C['header_bg'] + "; border: none; }"
)


# ── shared helpers ────────────────────────────────────────────────────────────
def _table(cols: list[str], row_h: int = 52) -> QTableWidget:
    t = QTableWidget()
    t.setColumnCount(len(cols))
    t.setHorizontalHeaderLabels(cols)
    t.setEditTriggers(_ETG)
    t.setSelectionBehavior(_SBR)
    t.verticalHeader().setVisible(False)
    t.setAlternatingRowColors(True)
    t.setShowGrid(False)
    t.verticalHeader().setDefaultSectionSize(row_h)
    t.setStyleSheet(_TABLE_CSS)
    t.setFrameShape(QFrame.Shape.NoFrame)
    t.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    return t


def _glass_card_frame() -> QFrame:
    f = QFrame()
    f.setObjectName("content_card")
    f.setGraphicsEffect(drop_shadow(blur=32, y=8, alpha=36, color=(180, 0, 100)))
    f.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    return f


def _search_bar(placeholder: str, on_change, action_label: str,
                on_action) -> tuple[QHBoxLayout, QLineEdit]:
    search = QLineEdit()
    search.setPlaceholderText(placeholder)
    search.setMinimumWidth(260); search.setMaximumWidth(380)
    search.setFixedHeight(40)
    search.textChanged.connect(on_change)
    action_b = btn(action_label, "primary_btn")
    action_b.setFixedHeight(40); action_b.setMinimumWidth(130)
    action_b.clicked.connect(on_action)
    row = QHBoxLayout()
    row.addStretch(); row.addWidget(search); row.addWidget(action_b)
    return row, search


def _scrolled_body() -> tuple[QScrollArea, QWidget, QVBoxLayout]:
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.Shape.NoFrame)
    scroll.setStyleSheet(
        "QScrollArea { background: transparent; border: none; }"
        "QScrollArea > QWidget { background: transparent; }"
        "QScrollArea > QWidget > QWidget { background: transparent; }"
    )
    body = QWidget()
    body.setStyleSheet("background: transparent;")
    body.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    scroll.setWidget(body)
    lay = QVBoxLayout(body)
    lay.setContentsMargins(32, 40, 32, 32)
    lay.setSpacing(22)
    return scroll, body, lay


def _safe_pixmap(data: bytes | None, w: int, h: int) -> QPixmap | None:
    if not data:
        return None
    px = QPixmap()
    if not px.loadFromData(bytes(data)):
        return None
    if px.isNull() or px.width() == 0 or px.height() == 0:
        return None
    result = px.scaled(
        max(1, w), max(1, h),
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )
    return result if (not result.isNull() and result.width() > 0) else None


# ══════════════════════════════════════════════════════════════════════════════
#  ANIMATED STAT CARD SLOT  (v5 — unchanged, still crash-safe)
# ══════════════════════════════════════════════════════════════════════════════
class _AnimatedCardSlot(QWidget):

    def _get_top_gap(self) -> int:
        return self._gap_val

    def _set_top_gap(self, v: int):
        self._gap_val = max(0, v)
        self._spacer.changeSize(
            0, self._gap_val,
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        lay = self.layout()
        if lay:
            lay.invalidate(); lay.activate()

    topGap = pyqtProperty(int, fget=_get_top_gap, fset=_set_top_gap)

    def __init__(self, card: StatCard, delay_ms: int = 0, parent=None):
        super().__init__(parent)
        self._card    = card
        self._delay   = delay_ms
        self._gap_val = 0
        self._played  = False

        self.setStyleSheet("background: transparent;")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 14, 12, 14); outer.setSpacing(0)

        self._spacer = QSpacerItem(
            0, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        outer.addSpacerItem(self._spacer)
        outer.addWidget(card)

        self._slide_anim = QPropertyAnimation(self, b"topGap")
        self._slide_anim.setDuration(420)
        self._slide_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._shadow_fx = QGraphicsDropShadowEffect(card)
        self._shadow_fx.setBlurRadius(26)
        self._shadow_fx.setOffset(0, 6)
        self._shadow_fx.setColor(QColor(180, 0, 100, 42))
        card.setGraphicsEffect(self._shadow_fx)

        self._hover_anim = QPropertyAnimation(self._shadow_fx, b"blurRadius")
        self._hover_anim.setDuration(180)
        self._hover_anim.setEasingCurve(QEasingCurve.Type.OutQuad)

    def play_entrance(self):
        if self._played: return
        self._played = True
        self._gap_val = 26
        self._spacer.changeSize(
            0, 26, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        lay = self.layout()
        if lay: lay.invalidate(); lay.activate()
        self._slide_anim.setStartValue(26)
        self._slide_anim.setEndValue(0)
        self._slide_anim.start()

    def enterEvent(self, event):
        super().enterEvent(event)
        self._hover_anim.stop()
        self._hover_anim.setStartValue(int(self._shadow_fx.blurRadius()))
        self._hover_anim.setEndValue(52)
        self._hover_anim.start()

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self._hover_anim.stop()
        self._hover_anim.setStartValue(int(self._shadow_fx.blurRadius()))
        self._hover_anim.setEndValue(26)
        self._hover_anim.start()


# ══════════════════════════════════════════════════════════════════════════════
#  DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
class DashboardPage(QWidget):

    def __init__(self, nav_cb):
        super().__init__()
        self._nav   = nav_cb
        self._slots: list[_AnimatedCardSlot] = []
        self._build_ui()

    def _build_ui(self):
        scroll, _body, lay = _scrolled_body()
        outer = QVBoxLayout(self); outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        self._cards: dict[str, StatCard] = {}
        row = QHBoxLayout(); row.setSpacing(0); row.setContentsMargins(0, 0, 0, 0)
        for i, (key, img, label, color) in enumerate([
            ("products",     "products.png",     "TOTAL PRODUCTS",     C['magenta']),
            ("transactions", "transactions.png", "TOTAL TRANSACTIONS", C['magenta_d']),
            ("revenue",      "revenues.png",     "TOTAL REVENUE",      C['success']),
            ("low",          "items.png",        "LOW STOCK ITEMS",    C['warning']),
        ]):
            card = StatCard(img, "0", label, color)
            self._cards[key] = card
            slot = _AnimatedCardSlot(card, delay_ms=i * 90)
            self._slots.append(slot)
            row.addWidget(slot)
        lay.addLayout(row)

        rc = _glass_card_frame()
        rl = QVBoxLayout(rc); rl.setContentsMargins(24, 18, 24, 18); rl.setSpacing(12)
        rh = QHBoxLayout()
        rh.addWidget(lbl("Recent Transactions", 12, bold=True, color=C['text']))
        rh.addStretch()
        va = btn("View all →", "ghost_btn")
        va.clicked.connect(lambda: self._nav("transactions"))
        rh.addWidget(va)
        rl.addLayout(rh); rl.addWidget(hline())
        self.recent_tbl = _table(["DATE", "PRODUCT", "CUSTOMER", "QTY", "TOTAL"], 46)
        h = self.recent_tbl.horizontalHeader()
        h.setSectionResizeMode(_RST); h.setSectionResizeMode(0, _RTC)
        self.recent_tbl.setMinimumHeight(200); self.recent_tbl.setMaximumHeight(280)
        rl.addWidget(self.recent_tbl)
        lay.addWidget(rc)

        pc = _glass_card_frame()
        pl = QVBoxLayout(pc); pl.setContentsMargins(24, 18, 24, 18); pl.setSpacing(12)
        ph = QHBoxLayout()
        ph.addWidget(lbl("Product Summary", 12, bold=True, color=C['text']))
        ph.addStretch()
        vp = btn("View Products →", "ghost_btn")
        vp.clicked.connect(lambda: self._nav("products"))
        ph.addWidget(vp)
        pl.addLayout(ph); pl.addWidget(hline())
        self.prod_tbl = _table(["PRODUCT", "CATEGORY", "PRICE", "STOCK STATUS"], 46)
        self.prod_tbl.horizontalHeader().setSectionResizeMode(_RST)
        self.prod_tbl.setMinimumHeight(180); self.prod_tbl.setMaximumHeight(260)
        pl.addWidget(self.prod_tbl)
        lay.addWidget(pc)
        lay.addStretch()

    def refresh(self):
        s = db.stats()
        self._cards["products"].set_value(str(s.get("products", 0)))
        self._cards["transactions"].set_value(str(s.get("transactions", 0)))
        self._cards["revenue"].set_value(f"₱{s.get('revenue', 0):,.0f}")
        self._cards["low"].set_value(str(s.get("low", 0)))

        for i, slot in enumerate(self._slots):
            QTimer.singleShot(i * 90, slot.play_entrance)

        txns = db.get_transactions()[:8]
        self.recent_tbl.setRowCount(len(txns))
        for r, t in enumerate(txns):
            ds = t[7][:10] if t[7] else ""
            for c, v in enumerate([ds, t[2], t[6] or "—", str(t[3]), f"₱{t[5]:,.2f}"]):
                item = QTableWidgetItem(str(v))
                item.setTextAlignment(
                    _AF.AlignVCenter |
                    (_AF.AlignRight if c == 4 else _AF.AlignLeft))
                self.recent_tbl.setItem(r, c, item)

        prods = db.get_products()
        self.prod_tbl.setRowCount(len(prods))
        for r, p in enumerate(prods):
            status = stock_status(p[5])
            for c, v in enumerate([f"{p[1]} {p[2]}", p[3], f"₱{p[4]:,.2f}", status]):
                item = QTableWidgetItem(str(v))
                item.setTextAlignment(_AF.AlignVCenter | _AF.AlignLeft)
                if c == 3:
                    fg = (C['danger'] if "Out" in v else
                          C['warning'] if "Low" in v else C['success'])
                    item.setForeground(QColor(fg))
                self.prod_tbl.setItem(r, c, item)


# ══════════════════════════════════════════════════════════════════════════════
#  PRODUCTS  — Shopee/Amazon storefront with image preview lightbox
# ══════════════════════════════════════════════════════════════════════════════
class ProductsPage(QWidget):

    def __init__(self):
        super().__init__()
        self._all: list[tuple] = []
        self._active_filter = "all"
        self._build_ui()

    def _build_ui(self):
        scroll, _body, lay = _scrolled_body()
        outer = QVBoxLayout(self); outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        top = QHBoxLayout(); top.setSpacing(10)

        self._search = QLineEdit()
        self._search.setPlaceholderText("🔍  Search by name or category…")
        self._search.setMinimumWidth(300); self._search.setMaximumWidth(460)
        self._search.setFixedHeight(42)
        self._search.textChanged.connect(lambda _: self._apply_filters())

        self._pills: dict[str, QPushButton] = {}
        for key, label in [("all", "All"), ("in stock", "In Stock"),
                            ("low", "Low Stock"), ("out", "Out of Stock")]:
            b = QPushButton(label)
            b.setCheckable(True); b.setChecked(key == "all")
            b.setFixedHeight(36)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setStyleSheet(self._pill_css(key == "all"))
            b.clicked.connect(lambda _, k=key, w=b: self._set_filter(k, w))
            self._pills[key] = b

        top.addWidget(self._search); top.addSpacing(8)
        for b in self._pills.values():
            top.addWidget(b)
        top.addStretch()

        self._count_lbl = QLabel("")
        self._count_lbl.setStyleSheet(
            "color: " + C['text_light'] + "; font-size: 12px; background: transparent;")
        top.addWidget(self._count_lbl)
        lay.addLayout(top)

        # Hint label about clicking images
        hint = QLabel("💡  Click a product image to preview it in full size")
        hint.setStyleSheet(
            "color: " + C['text_light'] + "; font-size: 11px;"
            " background: rgba(204,0,126,0.06);"
            " border-radius: 8px; padding: 6px 16px; border: none;")
        lay.addWidget(hint)

        self._grid_w = QWidget()
        self._grid_w.setStyleSheet("background: transparent;")
        self._grid_w.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._grid = QGridLayout(self._grid_w)
        self._grid.setSpacing(22); self._grid.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self._grid_w)

        self._empty_lbl = QLabel("No products match your search.")
        self._empty_lbl.setAlignment(_AF.AlignCenter)
        self._empty_lbl.setStyleSheet(
            "color: " + C['text_light'] + "; font-size: 15px; background: transparent;")
        self._empty_lbl.setVisible(False)
        lay.addWidget(self._empty_lbl)
        lay.addStretch()

    @staticmethod
    def _pill_css(active: bool) -> str:
        if active:
            return (
                "QPushButton { background: " + C['magenta'] + "; color: white;"
                " border: none; border-radius: 18px; padding: 4px 16px;"
                " font-size: 11px; font-weight: bold; }"
            )
        return (
            "QPushButton { background: rgba(204,0,126,0.08); color: " + C['magenta'] + ";"
            " border: 1.5px solid rgba(204,0,126,0.30); border-radius: 18px;"
            " padding: 4px 16px; font-size: 11px; }"
            "QPushButton:hover { background: " + C['magenta_bg'] + "; }"
        )

    def _set_filter(self, key: str, _btn_ref):
        self._active_filter = key
        for k, b in self._pills.items():
            is_active = (k == key)
            b.setChecked(is_active)
            b.setStyleSheet(self._pill_css(is_active))
        self._apply_filters()

    def refresh(self):
        self._all = db.get_products()
        self._apply_filters()

    def _apply_filters(self):
        text = self._search.text().lower().strip()
        af   = self._active_filter
        results = []
        for p in self._all:
            if text and text not in str(p[2]).lower() and text not in str(p[3]).lower():
                continue
            sv = int(p[5])
            if af == "in stock" and sv <= 5:            continue
            if af == "low"      and not (1 <= sv <= 5): continue
            if af == "out"      and sv != 0:            continue
            results.append(p)
        self._render(results)

    def _render(self, products: list[tuple]):
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

        self._empty_lbl.setVisible(len(products) == 0)
        self._count_lbl.setText(f"{len(products)} of {len(self._all)} products")

        COLS = 4
        for i, p in enumerate(products):
            self._grid.addWidget(self._make_card(p), i // COLS, i % COLS)

    # ── Product card ─────────────────────────────────────────────────────────
    def _make_card(self, p: tuple) -> QFrame:
        sv     = int(p[5])
        status = stock_status(sv)

        # ── Card frame + single shadow ────────────────────────────────────
        card = QFrame()
        card.setObjectName("prod_card")
        card.setMinimumWidth(230); card.setMaximumWidth(340)
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        card.setStyleSheet(
            "QFrame#prod_card {"
            " background: rgba(255,255,255,0.90);"
            " border: 1.5px solid rgba(255,255,255,0.95);"
            " border-radius: 20px; }"
            "QFrame#prod_card:hover {"
            " background: white;"
            " border-color: " + C['magenta'] + "; }"
        )

        # Shadow — animated on hover
        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(24); shadow.setOffset(0, 5)
        shadow.setColor(QColor(180, 0, 100, 30))
        card.setGraphicsEffect(shadow)

        # Hover animations on shadow blurRadius
        hover_in  = QPropertyAnimation(shadow, b"blurRadius")
        hover_in.setDuration(200); hover_in.setStartValue(24); hover_in.setEndValue(48)
        hover_in.setEasingCurve(QEasingCurve.Type.OutQuad)

        hover_out = QPropertyAnimation(shadow, b"blurRadius")
        hover_out.setDuration(200); hover_out.setStartValue(48); hover_out.setEndValue(24)
        hover_out.setEasingCurve(QEasingCurve.Type.OutQuad)

        # Store on card so they don't get GC'd
        card._shadow      = shadow
        card._hover_in    = hover_in
        card._hover_out   = hover_out

        def _on_enter(ev, c=card):
            c._hover_out.stop()
            c._hover_in.setStartValue(int(c._shadow.blurRadius()))
            c._hover_in.start()

        def _on_leave(ev, c=card):
            c._hover_in.stop()
            c._hover_out.setStartValue(int(c._shadow.blurRadius()))
            c._hover_out.start()

        card.enterEvent = _on_enter
        card.leaveEvent = _on_leave

        lay = QVBoxLayout(card); lay.setContentsMargins(0, 0, 0, 16); lay.setSpacing(0)

        # ── Image area — clickable, opens preview lightbox ────────────────
        img_lbl = QLabel()
        img_lbl.setFixedHeight(185)
        img_lbl.setAlignment(_AF.AlignCenter)
        img_lbl.setScaledContents(False)
        img_lbl.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        img_lbl.setToolTip("Click to preview")

        has_photo  = False
        img_data   = p[7] if len(p) > 7 else None
        if img_data:
            px = _safe_pixmap(img_data, 340, 185)
            if px and not px.isNull():
                img_lbl.setPixmap(px)
                img_lbl.setStyleSheet(
                    "background: #f5f0f5;"
                    " border-radius: 20px 20px 0 0; border: none;")
                has_photo = True

        if not has_photo:
            em_bg = ("#fee2e2" if sv == 0 else "#fef3c7" if sv <= 5 else "#f0fdf4")
            img_lbl.setText(str(p[1]))
            img_lbl.setFont(QFont("Segoe UI", 52))
            img_lbl.setStyleSheet(
                "background: " + em_bg + ";"
                " border-radius: 20px 20px 0 0; border: none;")

        # Click on image → open preview dialog
        pid = p[0]
        img_lbl.mousePressEvent = lambda ev, _pid=pid: self._open_preview(_pid)
        lay.addWidget(img_lbl)

        # ── Stock badge ───────────────────────────────────────────────────
        badge_row = QHBoxLayout()
        badge_row.setContentsMargins(14, 8, 14, 0)
        badge_row.addStretch()
        badge_row.addWidget(status_badge(status))
        lay.addLayout(badge_row)

        # ── Text info ─────────────────────────────────────────────────────
        info = QWidget(); info.setStyleSheet("background: transparent;")
        ii = QVBoxLayout(info); ii.setContentsMargins(16, 4, 16, 0); ii.setSpacing(3)

        name_lbl = QLabel(str(p[2]))
        name_lbl.setFont(QFont("MS Reference Sans Serif", 11, FWB))
        name_lbl.setWordWrap(True); name_lbl.setMaximumHeight(44)
        name_lbl.setStyleSheet("color: " + C['text'] + "; background: transparent;")

        cat_lbl = QLabel(str(p[3]))
        cat_lbl.setStyleSheet(
            "color: " + C['magenta'] + "; font-size: 10px;"
            " font-weight: bold; background: transparent;")

        desc_text = str(p[8]).strip() if len(p) > 8 and p[8] else ""
        ii.addWidget(name_lbl); ii.addWidget(cat_lbl)
        if desc_text:
            desc_lbl = QLabel(desc_text)
            desc_lbl.setWordWrap(True); desc_lbl.setMaximumHeight(36)
            desc_lbl.setStyleSheet(
                "color: " + C['text_light'] + "; font-size: 10px; background: transparent;")
            ii.addWidget(desc_lbl)

        ii.addSpacing(6)

        pr = QHBoxLayout(); pr.setContentsMargins(0, 0, 0, 0)
        price_lbl = QLabel(f"₱{float(p[4]):,.2f}")
        price_lbl.setFont(QFont("Segoe UI", 16, FWB))
        price_lbl.setStyleSheet("color: " + C['magenta'] + "; background: transparent;")
        stk_color = (C['danger'] if sv == 0 else
                     C['warning'] if sv <= 5 else C['text_light'])
        stk_lbl = QLabel(f"Stock: {sv}")
        stk_lbl.setStyleSheet(f"color: {stk_color}; font-size: 10px; background: transparent;")
        pr.addWidget(price_lbl); pr.addStretch(); pr.addWidget(stk_lbl)
        ii.addLayout(pr)
        lay.addWidget(info)

        # ── Buy Now / Out of Stock ────────────────────────────────────────
        btn_wrap = QWidget(); btn_wrap.setStyleSheet("background: transparent;")
        bl = QHBoxLayout(btn_wrap); bl.setContentsMargins(16, 8, 16, 0)

        if sv > 0:
            buy = btn("🛒  Buy Now", "primary_btn")
            buy.setFixedHeight(40)
            buy.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            buy.clicked.connect(lambda _, _pid=pid: self._buy(_pid))
            bl.addWidget(buy)
        else:
            oos = QLabel("Out of Stock")
            oos.setAlignment(_AF.AlignCenter)
            oos.setStyleSheet(
                "background: rgba(185,28,28,0.10); color: " + C['danger'] + ";"
                " border-radius: 10px; padding: 8px; font-size: 12px;"
                " font-weight: bold; border: none;")
            bl.addWidget(oos)

        lay.addWidget(btn_wrap)
        return card

    def _open_preview(self, pid: int):
        """Open the fullscreen image preview lightbox for a product."""
        p = db.get_product(pid)
        if not p:
            return
        # on_buy callback: close preview then open SaleDialog
        dlg = ProductPreviewDialog(
            self, product=p,
            on_buy=(self._buy if int(p[5]) > 0 else None),
        )
        dlg.exec()

    def _buy(self, pid: int):
        products = db.get_available()
        if not products:
            QMessageBox.warning(self, "No Stock",
                                "No products are currently in stock."); return
        dlg = SaleDialog(self, products, preselect_id=pid)
        if dlg.exec() == _DC:
            d = dlg.result_data
            try:
                db.record_sale(d["product_id"], d["qty"], d["customer"])
            except ValueError as ex:
                QMessageBox.critical(self, "Sale Failed", str(ex)); return
            self.refresh()
            win = self.window()
            if hasattr(win, "set_status"):
                win.set_status(
                    f"✅  Sold {d['product_name']} ×{d['qty']} = ₱{d['total']:,.2f}")
            if hasattr(win, "sync_all"):
                win.sync_all("products")


# ══════════════════════════════════════════════════════════════════════════════
#  INVENTORY  — full CRUD
# ══════════════════════════════════════════════════════════════════════════════
class InventoryPage(QWidget):

    def __init__(self):
        super().__init__()
        self._all: list[tuple] = []
        self._build_ui()

    def _build_ui(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(32, 28, 32, 28); lay.setSpacing(18)
        bar, self._search = _search_bar(
            "🔍  Search inventory…", self._filter, "+ Add Item", self._add)
        lay.addLayout(bar)

        card = _glass_card_frame()
        cl = QVBoxLayout(card); cl.setContentsMargins(0, 0, 0, 0)
        self.tbl = _table(
            ["IMG", "PRODUCT", "CATEGORY", "PRICE", "STOCK", "STATUS", "LEVEL", "ACTION"],
            64)
        h = self.tbl.horizontalHeader(); h.setSectionResizeMode(_RST)
        h.setSectionResizeMode(0, _RFXD); self.tbl.setColumnWidth(0, 76)
        h.setSectionResizeMode(4, _RFXD); self.tbl.setColumnWidth(4, 72)
        h.setSectionResizeMode(6, _RFXD); self.tbl.setColumnWidth(6, 140)
        h.setSectionResizeMode(7, _RFXD); self.tbl.setColumnWidth(7, 200)
        cl.addWidget(self.tbl)
        lay.addWidget(card)

    def refresh(self):
        self._all = db.get_products(); self._populate(self._all)

    def _filter(self, text: str):
        t = text.lower().strip()
        self._populate(self._all if not t else
                       [p for p in self._all
                        if t in str(p[2]).lower() or t in str(p[3]).lower()])

    def _populate(self, products: list[tuple]):
        self.tbl.setRowCount(0); self.tbl.setRowCount(len(products))
        for r, p in enumerate(products):
            status   = stock_status(p[5])
            img_data = p[7] if len(p) > 7 else None

            thumb_lbl = QLabel()
            thumb_lbl.setAlignment(_AF.AlignCenter)
            thumb_lbl.setFixedSize(56, 56)
            if img_data:
                px = _safe_pixmap(img_data, 56, 56)
                if px and not px.isNull():
                    thumb_lbl.setPixmap(px)
                    thumb_lbl.setStyleSheet(
                        "border-radius: 8px; border: none; background: transparent;")
                else:
                    thumb_lbl.setText(p[1]); thumb_lbl.setStyleSheet("font-size:24px;")
            else:
                thumb_lbl.setText(p[1]); thumb_lbl.setStyleSheet("font-size:24px;")
            self.tbl.setCellWidget(r, 0,
                                   cell_widget(thumb_lbl, margins=(4, 4, 4, 4), spacing=0))

            i1 = QTableWidgetItem(str(p[2]))
            i1.setFont(QFont("MS Reference Sans Serif", 10, FWB))
            self.tbl.setItem(r, 1, i1)
            self.tbl.setItem(r, 2, QTableWidgetItem(str(p[3])))

            pi = QTableWidgetItem(f"₱{float(p[4]):,.2f}")
            pi.setTextAlignment(_AF.AlignVCenter | _AF.AlignRight)
            self.tbl.setItem(r, 3, pi)

            si = QTableWidgetItem(str(p[5]))
            si.setTextAlignment(_AF.AlignCenter)
            si.setFont(QFont("Segoe UI", 12, FWB))
            self.tbl.setItem(r, 4, si)

            self.tbl.setCellWidget(r, 5, cell_widget(status_badge(status), margins=(8,0,0,0)))
            self.tbl.setCellWidget(r, 6, cell_widget(stock_bar(p[5]),      margins=(8,0,0,0)))

            upd  = btn("✏ Edit",   "success_btn"); upd.setFixedHeight(30)
            del_ = btn("🗑 Delete", "danger_btn");  del_.setFixedHeight(30)
            upd.clicked.connect(lambda _, pid=p[0]: self._edit(pid))
            del_.clicked.connect(lambda _, pid=p[0]: self._delete(pid))
            self.tbl.setCellWidget(r, 7, cell_widget(upd, del_))

    def _add(self):
        dlg = ProductDialog(self)
        if dlg.exec() == _DC:
            d = dlg.result_data
            db.add_product(d["emoji"], d["name"], d["category"], d["price"],
                           d["stock"], d["image_data"], d["description"])
            self.refresh()
            win = self.window()
            if hasattr(win, "set_status"):  win.set_status(f"✅  '{d['name']}' added.")
            if hasattr(win, "sync_all"):    win.sync_all("inventory")

    def _edit(self, pid: int):
        p = db.get_product(pid)
        if not p: QMessageBox.warning(self, "Error", "Product not found."); return
        dlg = ProductDialog(self, p)
        if dlg.exec() == _DC:
            d = dlg.result_data
            db.update_product(pid, d["emoji"], d["name"], d["category"],
                              d["price"], d["stock"],
                              d["image_data"], d["description"],
                              update_image=d["update_image"])
            self.refresh()
            win = self.window()
            if hasattr(win, "set_status"):  win.set_status("✅  Item updated.")
            if hasattr(win, "sync_all"):    win.sync_all("inventory")

    def _delete(self, pid: int):
        p = db.get_product(pid)
        if not p: QMessageBox.warning(self, "Error", "Product not found."); return
        msg = QMessageBox(self)
        msg.setWindowTitle("Confirm Delete")
        msg.setText(f"Delete <b>{p[2]}</b>?")
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setStyleSheet("""
            QMessageBox { background: white; }
            QLabel { color: #1a1a2e; font-size: 13px; }
            QPushButton {
                background: #cc007e;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 6px 18px;
                font-size: 12px;
            }
            QPushButton:hover { background: #e6008c; }
        """)
        try:
            if msg.exec() == QMessageBox.StandardButton.Yes:
                db.delete_product(pid)
                self.refresh()
                win = self.window()
                if hasattr(win, "set_status"):  win.set_status("🗑️  Item deleted.")
                if hasattr(win, "sync_all"):    win.sync_all("inventory")
        except Exception as ex:
            QMessageBox.warning(self, "Delete Error", f"Could not delete item:\n{str(ex)}")


# ══════════════════════════════════════════════════════════════════════════════
#  TRANSACTIONS
# ══════════════════════════════════════════════════════════════════════════════
class TransactionsPage(QWidget):

    def __init__(self):
        super().__init__()
        self._all: list[tuple] = []
        self._build_ui()

    def _build_ui(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(32, 28, 32, 28); lay.setSpacing(18)
        bar, self._search = _search_bar(
            "🔍  Search transactions…", self._filter, "+ New Sale", self._new_sale)
        lay.addLayout(bar)
        card = _glass_card_frame()
        cl = QVBoxLayout(card); cl.setContentsMargins(0, 0, 0, 0)
        self.tbl = _table(
            ["TXN #", "PRODUCT", "CUSTOMER", "QTY", "UNIT PRICE", "TOTAL", "DATE"], 52)
        h = self.tbl.horizontalHeader(); h.setSectionResizeMode(_RST)
        h.setSectionResizeMode(0, _RTC)
        h.setSectionResizeMode(3, _RFXD); self.tbl.setColumnWidth(3, 64)
        h.setSectionResizeMode(6, _RTC)
        cl.addWidget(self.tbl)
        lay.addWidget(card)

    def refresh(self):
        self._all = db.get_transactions(); self._populate(self._all)

    def _filter(self, text: str):
        t = text.lower().strip()
        self._populate(self._all if not t else
                       [x for x in self._all
                        if t in str(x[2]).lower() or t in str(x[6] or "").lower()])

    def _populate(self, txns: list[tuple]):
        self.tbl.setRowCount(0); self.tbl.setRowCount(len(txns))
        for r, t in enumerate(txns):
            ds = t[7][:10] if t[7] else ""
            for c, v in enumerate([
                f"#{t[0]:04d}", t[2], t[6] or "—",
                str(t[3]), f"₱{float(t[4]):,.2f}", f"₱{float(t[5]):,.2f}", ds,
            ]):
                item = QTableWidgetItem(str(v))
                align = (_AF.AlignRight  if c in (4, 5) else
                         _AF.AlignCenter if c in (0, 3) else _AF.AlignLeft)
                item.setTextAlignment(_AF.AlignVCenter | align)
                if c == 0: item.setFont(QFont("Segoe UI", 11, FWB))
                if c == 5:
                    item.setForeground(QColor(C['success']))
                    item.setFont(QFont("Segoe UI", 11, FWB))
                self.tbl.setItem(r, c, item)

    def _new_sale(self):
        products = db.get_available()
        if not products:
            QMessageBox.warning(self, "No Stock",
                                "No products in stock. Restock in Inventory first.")
            return
        dlg = SaleDialog(self, products)
        if dlg.exec() == _DC:
            d = dlg.result_data
            try:
                db.record_sale(d["product_id"], d["qty"], d["customer"])
            except ValueError as ex:
                QMessageBox.critical(self, "Sale Failed", str(ex)); return
            self.refresh()
            win = self.window()
            if hasattr(win, "set_status"):
                win.set_status(
                    f"✅  Sale — {d['product_name']} ×{d['qty']} = ₱{d['total']:,.2f}")
            if hasattr(win, "sync_all"):
                win.sync_all("transactions")
