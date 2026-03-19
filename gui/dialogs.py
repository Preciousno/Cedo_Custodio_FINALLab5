
#gui/dialogs.py  — CC Crafts

from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox,
    QMessageBox, QFrame, QPushButton, QFileDialog, QTextEdit,
    QSizePolicy, QScrollArea,
)
from PyQt6.QtGui  import QFont, QPixmap, QKeyEvent
from PyQt6.QtCore import Qt, QByteArray, QBuffer, QIODevice, QSize

import database as db
from gui.styles  import C, QSS
from gui.widgets import btn, hline, FWB

_AF = Qt.AlignmentFlag
_DC = QDialog.DialogCode.Accepted

EMOJIS = [
    "🌸","🌹","🌺","🌻","🌼","💐","🎀","🎁",
    "🧶","🪡","🎨","✨","🌿","🍀","🦋","🕊️","💎","🧁",
]
CATEGORIES = [
    "Crochet Flowers", "Fresh Flower Arrangement", "Mixed Bouquet",
    "Gift Set", "Dried Flowers", "Accessories", "Home Decor", "Other",
]

_MAX_IMG_BYTES = 600_000

_DIALOG_CSS = """
QDialog {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #f8f0f8, stop:1 #f0e8f4);
}
QFrame#dlg_body {
    background: rgba(255,255,255,0.84);
    border: 1.5px solid rgba(255,255,255,0.92);
    border-radius: 18px;
}
QTextEdit {
    background: rgba(255,255,255,0.85);
    border: 1.5px solid rgba(204,0,126,0.20);
    border-radius: 10px;
    padding: 8px 12px;
    font-size: 13px;
    color: #1a1a2e;
}
QTextEdit:focus {
    border-color: #cc007e;
    background: rgba(255,255,255,0.95);
}
"""

_PREVIEW_CSS = """
QDialog#preview_dlg {
    background: rgba(20, 8, 18, 0.92);
}
QFrame#preview_card {
    background: rgba(255,255,255,0.96);
    border: none;
    border-radius: 24px;
}
"""


def _dlg_title(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName("dlg_title")
    lbl.setFont(QFont("MS Reference Sans Serif", 16, FWB))
    lbl.setStyleSheet("color: " + C['text'] + "; background: transparent;")
    return lbl


def bytes_to_pixmap(data: bytes | None, w: int, h: int) -> QPixmap | None:
    if not data:
        return None
    px = QPixmap()
    if not px.loadFromData(bytes(data)):
        return None
    if px.isNull() or px.width() == 0 or px.height() == 0:
        return None
    scaled = px.scaled(
        w, h,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )
    return scaled if not scaled.isNull() else None


def compress_image_to_bytes(path: str,
                             max_side: int = 480,
                             max_bytes: int = _MAX_IMG_BYTES) -> bytes | None:
    from PyQt6.QtGui import QImage, QImageWriter
    img = QImage(path)
    if img.isNull():
        return None
    if img.width() > max_side or img.height() > max_side:
        img = img.scaled(
            max_side, max_side,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
    if img.isNull():
        return None
    img = img.convertToFormat(QImage.Format.Format_RGB32)
    buf  = QByteArray()
    io   = QBuffer(buf)
    io.open(QIODevice.OpenModeFlag.WriteOnly)
    quality = 85
    while quality >= 30:
        buf.clear(); io.seek(0)
        img.save(io, "JPEG", quality)
        if buf.size() <= max_bytes:
            break
        quality -= 10
    io.close()
    result = bytes(buf)
    return result if result else None


# ══════════════════════════════════════════════════════════════════════════════
#  PRODUCT PREVIEW DIALOG  — image lightbox / product detail modal
# ══════════════════════════════════════════════════════════════════════════════
class ProductPreviewDialog(QDialog):
    """
    Lightbox modal that opens when the user clicks a product card image.

    Layout:
      ┌─────────────────────────────────────────────────────┐
      │  [✕]                                                │  ← dark overlay
      │  ┌─────────────────────────┬─────────────────────┐  │
      │  │   Large product photo   │  Name               │  │
      │  │   (up to 480 × 400)     │  Category • badge   │  │
      │  │                         │  Description        │  │
      │  │                         │  ────────           │  │
      │  │   [emoji fallback if    │  ₱ Price            │  │
      │  │    no image]            │  Stock: N           │  │
      │  │                         │  [🛒 Buy Now]       │  │
      │  └─────────────────────────┴─────────────────────┘  │
      └─────────────────────────────────────────────────────┘
    """

    def __init__(self, parent=None, product: tuple | None = None,
                 on_buy=None):
        super().__init__(parent)
        self._product = product
        self._on_buy  = on_buy   # callable(pid) or None

        self.setObjectName("preview_dlg")
        self.setWindowTitle("")
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.FramelessWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setModal(True)
        self.setMinimumSize(900, 520)
        self.setStyleSheet(QSS + _PREVIEW_CSS)
        self._build_ui()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        super().keyPressEvent(event)

    def _build_ui(self):
        p = self._product

        # Semi-transparent overlay that fills the dialog
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setAlignment(_AF.AlignCenter)

        # Clickable dark backdrop — clicking outside the card closes
        self.setAutoFillBackground(False)

        # White card
        card = QFrame()
        card.setObjectName("preview_card")
        card.setFixedWidth(960)
        card.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        outer.addWidget(card, 0, _AF.AlignCenter)

        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(0, 0, 0, 0)
        card_lay.setSpacing(0)

        # Close button (top-right corner of card)
        close_row = QHBoxLayout()
        close_row.setContentsMargins(0, 14, 16, 0)
        close_row.addStretch()
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(36, 36)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(
            "QPushButton { background: rgba(204,0,126,0.10); color: " + C['magenta'] + ";"
            " border: none; border-radius: 18px; font-size: 15px; font-weight: bold; }"
            "QPushButton:hover { background: " + C['magenta'] + "; color: white; }"
        )
        close_btn.clicked.connect(self.close)
        close_row.addWidget(close_btn)
        card_lay.addLayout(close_row)

        # Two-column content
        content = QHBoxLayout()
        content.setContentsMargins(32, 8, 40, 36)
        content.setSpacing(40)
        card_lay.addLayout(content)

        # ── Left: product image ───────────────────────────────────────────
        img_lbl = QLabel()
        img_lbl.setFixedSize(440, 380)
        img_lbl.setAlignment(_AF.AlignCenter)
        img_lbl.setScaledContents(False)

        sv       = int(p[5]) if p else 0
        img_data = p[7] if p and len(p) > 7 else None

        if img_data:
            px = bytes_to_pixmap(img_data, 440, 380)
            if px and not px.isNull():
                img_lbl.setPixmap(px)
                img_lbl.setStyleSheet(
                    "background: #f8f4f8; border-radius: 18px; border: none;")
            else:
                self._set_emoji_bg(img_lbl, p[1] if p else "🌸", sv)
        else:
            self._set_emoji_bg(img_lbl, p[1] if p else "🌸", sv)

        content.addWidget(img_lbl)

        # ── Right: product details ────────────────────────────────────────
        right = QVBoxLayout()
        right.setSpacing(10)
        right.setAlignment(_AF.AlignTop)
        content.addLayout(right, 1)

        if p:
            # Category tag
            cat_lbl = QLabel(str(p[3]))
            cat_lbl.setStyleSheet(
                "background: " + C['magenta_bg'] + "; color: " + C['magenta'] + ";"
                " border-radius: 10px; padding: 3px 12px;"
                " font-size: 11px; font-weight: bold; border: none;")
            cat_row = QHBoxLayout()
            cat_row.addWidget(cat_lbl); cat_row.addStretch()

            # Stock badge
            from gui.widgets import stock_status, status_badge
            badge = status_badge(stock_status(sv))
            cat_row.addWidget(badge)
            right.addLayout(cat_row)
            right.addSpacing(4)

            # Name
            name_lbl = QLabel(str(p[2]))
            name_lbl.setFont(QFont("MS Reference Sans Serif", 22, FWB))
            name_lbl.setWordWrap(True)
            name_lbl.setStyleSheet("color: " + C['text'] + "; background: transparent;")
            right.addWidget(name_lbl)

            # Description
            desc = str(p[8]).strip() if len(p) > 8 and p[8] else ""
            if desc:
                desc_lbl = QLabel(desc)
                desc_lbl.setWordWrap(True)
                desc_lbl.setStyleSheet(
                    "color: " + C['text_light'] + "; font-size: 13px;"
                    " background: transparent; line-height: 1.5;")
                right.addWidget(desc_lbl)

            right.addWidget(hline())

            # Price
            price_lbl = QLabel(f"₱{float(p[4]):,.2f}")
            price_lbl.setFont(QFont("Segoe UI", 30, FWB))
            price_lbl.setStyleSheet(
                "color: " + C['magenta'] + "; background: transparent;")
            right.addWidget(price_lbl)

            # Stock count
            stock_color = (C['danger'] if sv == 0 else
                           C['warning'] if sv <= 5 else C['text_light'])
            stock_txt = ("Out of stock" if sv == 0 else
                         f"⚠ Only {sv} left!" if sv <= 5 else
                         f"✓  {sv} units available")
            stk_lbl = QLabel(stock_txt)
            stk_lbl.setStyleSheet(
                f"color: {stock_color}; font-size: 13px; background: transparent;")
            right.addWidget(stk_lbl)

            right.addStretch()

            # Buy Now / Out of Stock
            if sv > 0 and self._on_buy is not None:
                buy_btn = btn("🛒   Buy Now", "primary_btn")
                buy_btn.setFixedHeight(48)
                buy_btn.setFont(QFont("MS Reference Sans Serif", 13, FWB))
                buy_btn.setSizePolicy(
                    QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
                buy_btn.clicked.connect(self._handle_buy)
                right.addWidget(buy_btn)
            elif sv == 0:
                oos = QLabel("Currently Out of Stock")
                oos.setAlignment(_AF.AlignCenter)
                oos.setStyleSheet(
                    "background: rgba(185,28,28,0.10); color: " + C['danger'] + ";"
                    " border-radius: 12px; padding: 12px; font-size: 13px;"
                    " font-weight: bold; border: 1px solid rgba(185,28,28,0.20);")
                right.addWidget(oos)

    @staticmethod
    def _set_emoji_bg(label: QLabel, emoji: str, sv: int):
        em_bg = ("#fee2e2" if sv == 0 else "#fef3c7" if sv <= 5 else "#f0fdf4")
        label.setFont(QFont("Segoe UI", 80))
        label.setText(emoji)
        label.setStyleSheet(
            "background: " + em_bg + "; border-radius: 18px; border: none;")

    def _handle_buy(self):
        self.close()
        if self._on_buy and self._product:
            self._on_buy(self._product[0])

    def mousePressEvent(self, event):
        """Close when clicking outside the card (on the dark backdrop)."""
        # The card is centered; if click hit the outer dialog area, close
        child = self.childAt(event.position().toPoint())
        if child is None:
            self.close()
        super().mousePressEvent(event)


# ══════════════════════════════════════════════════════════════════════════════
#  PRODUCT DIALOG  (add / edit)
# ══════════════════════════════════════════════════════════════════════════════
class ProductDialog(QDialog):

    def __init__(self, parent=None, product: tuple | None = None):
        super().__init__(parent)
        self.product         = product
        self.result_data: dict = {}
        self._pending_bytes: bytes | None = None
        self._image_changed  = False

        self.setWindowTitle("Edit Product" if product else "Add Product")
        self.setMinimumWidth(620)
        self.setMinimumHeight(560)
        self.setStyleSheet(QSS + _DIALOG_CSS)
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(18, 18, 18, 18); outer.setSpacing(0)

        body = QFrame(); body.setObjectName("dlg_body")
        lay  = QVBoxLayout(body)
        lay.setContentsMargins(28, 24, 28, 24); lay.setSpacing(14)
        outer.addWidget(body)

        lay.addWidget(_dlg_title(
            "✏️  Edit Product" if self.product else "🌸  Add New Product"))
        lay.addWidget(hline())

        cols = QHBoxLayout(); cols.setSpacing(28)

        # Image column
        img_col = QVBoxLayout(); img_col.setSpacing(10)

        self._img_lbl = QLabel("No image\nuploaded")
        self._img_lbl.setFixedSize(190, 190)
        self._img_lbl.setAlignment(_AF.AlignCenter)
        self._img_lbl.setWordWrap(True)
        self._img_lbl.setStyleSheet(
            "background: rgba(252,228,243,0.70);"
            " border: 2px dashed rgba(204,0,126,0.35);"
            " border-radius: 14px;"
            " color: " + C['text_light'] + ";"
            " font-size: 11px;")

        if self.product and len(self.product) > 7 and self.product[7]:
            self._show_preview(self.product[7])

        upload_btn = QPushButton("📷  Upload Photo")
        upload_btn.setObjectName("ghost_btn"); upload_btn.setFixedHeight(38)
        upload_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        upload_btn.clicked.connect(self._pick_image)

        clear_btn = QPushButton("✕  Remove Photo")
        clear_btn.setObjectName("danger_btn"); clear_btn.setFixedHeight(36)
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.clicked.connect(self._clear_image)

        img_col.addWidget(self._img_lbl)
        img_col.addWidget(upload_btn)
        img_col.addWidget(clear_btn)
        img_col.addStretch()
        cols.addLayout(img_col)

        # Form column
        form = QFormLayout()
        form.setSpacing(11); form.setLabelAlignment(_AF.AlignRight)
        form.setHorizontalSpacing(14)

        self.emoji_cb = QComboBox(); self.emoji_cb.setMinimumHeight(38)
        for e in EMOJIS: self.emoji_cb.addItem(e)

        self.name_e = QLineEdit()
        self.name_e.setPlaceholderText("e.g. Rose Crochet Bouquet")
        self.name_e.setMinimumHeight(38)

        self.cat_e = QComboBox(); self.cat_e.setEditable(True)
        self.cat_e.setMinimumHeight(38)
        for c in CATEGORIES: self.cat_e.addItem(c)

        self.price_e = QDoubleSpinBox()
        self.price_e.setRange(0.01, 99_999.99)
        self.price_e.setDecimals(2); self.price_e.setPrefix("₱ ")
        self.price_e.setMinimumHeight(38)

        self.stock_e = QSpinBox()
        self.stock_e.setRange(0, 9_999); self.stock_e.setMinimumHeight(38)

        self.desc_e = QTextEdit()
        self.desc_e.setPlaceholderText("Short product description (optional)…")
        self.desc_e.setFixedHeight(82)

        if self.product:
            idx = EMOJIS.index(self.product[1]) if self.product[1] in EMOJIS else 0
            self.emoji_cb.setCurrentIndex(idx)
            self.name_e.setText(self.product[2])
            ci = self.cat_e.findText(self.product[3])
            self.cat_e.setCurrentIndex(ci) if ci >= 0 \
                else self.cat_e.setCurrentText(self.product[3])
            self.price_e.setValue(float(self.product[4]))
            self.stock_e.setValue(int(self.product[5]))
            if len(self.product) > 8 and self.product[8]:
                self.desc_e.setPlainText(self.product[8])

        form.addRow("Icon",        self.emoji_cb)
        form.addRow("Name *",      self.name_e)
        form.addRow("Category *",  self.cat_e)
        form.addRow("Price *",     self.price_e)
        form.addRow("Stock *",     self.stock_e)
        form.addRow("Description", self.desc_e)
        cols.addLayout(form, 1)
        lay.addLayout(cols)
        lay.addWidget(hline())

        row = QHBoxLayout()
        cancel = btn("Cancel",       "ghost_btn");   cancel.clicked.connect(self.reject)
        save   = btn("Save Product", "primary_btn"); save.clicked.connect(self._save)
        cancel.setMinimumHeight(38); save.setMinimumHeight(38)
        row.addStretch(); row.addWidget(cancel); row.addWidget(save)
        lay.addLayout(row)

    def _pick_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Product Image", "",
            "Images (*.png *.jpg *.jpeg *.webp *.bmp *.gif *.tiff)")
        if not path: return
        data = compress_image_to_bytes(path)
        if not data:
            QMessageBox.warning(self, "Image Error",
                                "Could not load that image file.\n"
                                "Try JPG or PNG format."); return
        self._pending_bytes = data
        self._image_changed = True
        self._show_preview(data)

    def _clear_image(self):
        self._pending_bytes = None
        self._image_changed = True
        self._img_lbl.setPixmap(QPixmap())
        self._img_lbl.setText("No image\nuploaded")

    def _show_preview(self, data: bytes):
        px = bytes_to_pixmap(data, 186, 186)
        if px and not px.isNull():
            self._img_lbl.setPixmap(px); self._img_lbl.setText("")
        else:
            self._img_lbl.setText("⚠ Preview\nnot available")

    def _save(self):
        name     = self.name_e.text().strip()
        category = self.cat_e.currentText().strip()
        if not name:
            QMessageBox.warning(self, "Required", "Product name cannot be empty.")
            self.name_e.setFocus(); return
        if not category:
            QMessageBox.warning(self, "Required", "Category cannot be empty.")
            self.cat_e.setFocus(); return

        if self._image_changed:
            final_img = self._pending_bytes
        elif self.product and len(self.product) > 7:
            final_img = self.product[7]
        else:
            final_img = None

        self.result_data = {
            "emoji":        self.emoji_cb.currentText(),
            "name":         name,
            "category":     category,
            "price":        self.price_e.value(),
            "stock":        self.stock_e.value(),
            "image_data":   final_img,
            "description":  self.desc_e.toPlainText().strip(),
            "update_image": self._image_changed,
        }
        self.accept()


# ══════════════════════════════════════════════════════════════════════════════
#  SALE DIALOG
# ══════════════════════════════════════════════════════════════════════════════
class SaleDialog(QDialog):

    def __init__(self, parent=None, products: list[tuple] | None = None,
                 preselect_id: int | None = None):
        super().__init__(parent)
        self.products       = products or []
        self._preselect_id  = preselect_id
        self.result_data: dict = {}
        self.setWindowTitle("Record Sale")
        self.setMinimumWidth(500)
        self.setStyleSheet(QSS + _DIALOG_CSS)
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(18, 18, 18, 18); outer.setSpacing(0)

        body = QFrame(); body.setObjectName("dlg_body")
        lay  = QVBoxLayout(body)
        lay.setContentsMargins(28, 24, 28, 24); lay.setSpacing(14)
        outer.addWidget(body)

        lay.addWidget(_dlg_title("🛒  Record Sale"))
        lay.addWidget(hline())

        top_row = QHBoxLayout(); top_row.setSpacing(18)

        self._thumb = QLabel()
        self._thumb.setFixedSize(88, 88)
        self._thumb.setAlignment(_AF.AlignCenter)
        self._thumb.setStyleSheet(
            "background: rgba(252,228,243,0.60);"
            " border-radius: 12px; font-size: 28px; border: none;")
        top_row.addWidget(self._thumb)

        self.prod_cb = QComboBox()
        self.prod_cb.setMinimumHeight(42)
        self.prod_cb.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        for p in self.products:
            self.prod_cb.addItem(f"{p[1]} {p[2]}  (Stock: {p[5]})", p[0])
        self.prod_cb.currentIndexChanged.connect(self._on_product_changed)
        top_row.addWidget(self.prod_cb, 1)
        lay.addLayout(top_row)

        form = QFormLayout()
        form.setSpacing(12); form.setLabelAlignment(_AF.AlignRight)
        form.setHorizontalSpacing(16)

        self.qty_sp = QSpinBox()
        self.qty_sp.setRange(1, 9_999); self.qty_sp.setMinimumHeight(40)
        self.qty_sp.valueChanged.connect(self._refresh_totals)

        self.unit_lbl = QLabel("—")
        self.unit_lbl.setStyleSheet("background: transparent; font-size: 13px;")

        self.total_lbl = QLabel("—")
        self.total_lbl.setFont(QFont("Segoe UI", 17, FWB))
        self.total_lbl.setStyleSheet(
            "color: " + C['success'] + "; background: transparent;")

        self.cust_e = QLineEdit()
        self.cust_e.setPlaceholderText("Customer name (optional)")
        self.cust_e.setMinimumHeight(40)

        form.addRow("Quantity *",  self.qty_sp)
        form.addRow("Unit Price",  self.unit_lbl)
        form.addRow("Total",       self.total_lbl)
        form.addRow("Customer",    self.cust_e)
        lay.addLayout(form)
        lay.addWidget(hline())

        row = QHBoxLayout()
        cancel  = btn("Cancel",         "ghost_btn");  cancel.clicked.connect(self.reject)
        confirm = btn("Confirm Sale ✓", "success_btn"); confirm.clicked.connect(self._save)
        cancel.setMinimumHeight(40); confirm.setMinimumHeight(40)
        row.addStretch(); row.addWidget(cancel); row.addWidget(confirm)
        lay.addLayout(row)

        if self._preselect_id is not None:
            for i, p in enumerate(self.products):
                if p[0] == self._preselect_id:
                    self.prod_cb.setCurrentIndex(i); break
        self._on_product_changed()

    def _current_product(self) -> tuple | None:
        i = self.prod_cb.currentIndex()
        return self.products[i] if 0 <= i < len(self.products) else None

    def _on_product_changed(self):
        p = self._current_product()
        if p:
            img_data = p[7] if len(p) > 7 else None
            if img_data:
                px = bytes_to_pixmap(img_data, 84, 84)
                if px and not px.isNull():
                    self._thumb.setPixmap(px); self._thumb.setText("")
                else:
                    self._thumb.setPixmap(QPixmap()); self._thumb.setText(p[1])
            else:
                self._thumb.setPixmap(QPixmap()); self._thumb.setText(p[1])
        self._refresh_totals()

    def _refresh_totals(self):
        p = self._current_product()
        if p:
            max_qty = max(1, int(p[5]))
            self.qty_sp.setMaximum(max_qty)
            if self.qty_sp.value() > max_qty:
                self.qty_sp.setValue(max_qty)
            self.unit_lbl.setText(f"₱{float(p[4]):,.2f}")
            self.total_lbl.setText(f"₱{float(p[4]) * self.qty_sp.value():,.2f}")
        else:
            self.unit_lbl.setText("—"); self.total_lbl.setText("—")

    def _save(self):
        p = self._current_product()
        if not p:
            QMessageBox.warning(self, "No Product", "Please select a product."); return
        qty = self.qty_sp.value()
        if qty < 1:
            QMessageBox.warning(self, "Invalid", "Quantity must be at least 1."); return
        if qty > int(p[5]):
            QMessageBox.warning(self, "Stock Error",
                                f"Only {p[5]} units available."); return
        self.result_data = {
            "product_id":   p[0],
            "product_name": f"{p[1]} {p[2]}",
            "qty":          qty,
            "unit_price":   float(p[4]),
            "total":        float(p[4]) * qty,
            "customer":     self.cust_e.text().strip(),
        }
        self.accept()
