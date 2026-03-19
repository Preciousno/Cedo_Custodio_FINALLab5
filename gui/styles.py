
#gui/styles.py


# ── Palette ────────────────────────────────────────────────────────────────────
C: dict[str, str] = {
    # brand
    "magenta":       "#cc007e",
    "magenta_h":     "#e6008c",
    "magenta_d":     "#99005e",
    "magenta_bg":    "#fce4f3",
    "magenta_light": "#ff4db8",

    # backgrounds
    "white":         "#ffffff",
    "bg":            "#f0eef8",       # soft lavender-rose tint
    "bg2":           "#f8f0f6",
    "card":          "#ffffff",
    "logo_bg":       "#fbf9f1",

    # glass
    "glass_bg":      "rgba(255,255,255,0.72)",
    "glass_border":  "rgba(255,255,255,0.85)",
    "glass_shadow":  "rgba(180,0,120,0.10)",

    # text
    "text":          "#1a1a2e",
    "text_light":    "#6b7280",
    "text_inv":      "#ffffff",

    # status
    "success":       "#15803d",
    "success_bg":    "#dcfce7",
    "warning":       "#b45309",
    "warning_bg":    "#fef3c7",
    "danger":        "#b91c1c",
    "danger_bg":     "#fee2e2",

    # table / borders
    "header_bg":     "#cc007e",
    "row_alt":       "#fdf5fa",
    "border":        "#e5e7eb",
    "border_light":  "#f3f4f6",
    "selection":     "#fce4f3",
}

# ── Stylesheet ─────────────────────────────────────────────────────────────────
QSS = f"""
/* ─── Global defaults ──────────────────────────────────────────── */
* {{
    font-family: 'MS Reference Sans Serif', 'Segoe UI', sans-serif;
    font-size: 13px;
}}
QWidget    {{ background: transparent; color: {C['text']}; }}
QLabel     {{ background: transparent; color: {C['text']}; }}
QMainWindow{{ background: {C['bg']}; }}
QDialog    {{ background: {C['bg']}; }}

/* ─── Named containers ──────────────────────────────────────────── */
QWidget#centralwidget   {{ background: {C['bg']}; }}
QWidget#mainscreen      {{ background: {C['bg']}; }}
QWidget#sidebar         {{ background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                            stop:0 #e6006e, stop:1 #7a0050); }}
QWidget#sidebarmini     {{ background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                            stop:0 #e6006e, stop:1 #7a0050); }}
QWidget#logoholder      {{
    background: {C['logo_bg']};
    border-bottom: 1px solid rgba(255,255,255,0.18);
}}
QWidget#logoholder_mini {{
    background: {C['logo_bg']};
    border-bottom: 1px solid rgba(255,255,255,0.18);
}}
QWidget#topbar          {{
    background: rgba(255,255,255,0.82);
    border-bottom: 1px solid rgba(204,0,126,0.12);
}}

/* ─── Scroll areas ──────────────────────────────────────────────── */
QScrollArea                     {{ background: transparent; border: none; }}
QScrollArea > QWidget > QWidget {{ background: transparent; }}

/* ─── Glass Cards ─────────────────────────────────────────────── */
QFrame#stat_card    {{
    background: rgba(255,255,255,0.76);
    border: 1.5px solid rgba(255,255,255,0.90);
    border-radius: 18px;
}}
QFrame#content_card {{
    background: rgba(255,255,255,0.80);
    border: 1.5px solid rgba(255,255,255,0.90);
    border-radius: 18px;
}}
QFrame#glass_card {{
    background: rgba(255,255,255,0.76);
    border: 1.5px solid rgba(255,255,255,0.90);
    border-radius: 18px;
}}

/* ─── Tables ────────────────────────────────────────────────────── */
QTableWidget {{
    background: transparent;
    color: {C['text']};
    border: none;
    gridline-color: transparent;
    font-size: 10pt;
    alternate-background-color: rgba(204,0,126,0.03);
    selection-background-color: rgba(204,0,126,0.12);
    selection-color: {C['text']};
}}
QTableWidget::item {{
    padding: 7px 10px;
    border-bottom: 1px solid rgba(229,231,235,0.6);
    background: transparent;
}}
QHeaderView::section {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 {C['magenta']}, stop:1 {C['magenta_d']});
    color: white;
    padding: 8px 10px;
    border: none;
    font-weight: bold;
    font-size: 10pt;
    letter-spacing: 0.4px;
}}
QTableCornerButton::section {{
    background: {C['header_bg']}; border: none;
}}

/* ─── Sidebar nav (full) ────────────────────────────────────────── */
QPushButton#nav_btn {{
    background: transparent;
    color: rgba(255,255,255,0.72);
    border: none;
    text-align: left;
    padding: 11px 18px;
    font: 12pt 'MS Reference Sans Serif';
}}
QPushButton#nav_btn:hover {{
    color: white;
    background: rgba(255,255,255,0.15);
    border-radius: 10px;
    margin: 0 8px;
}}
QPushButton#nav_btn[active=true] {{
    color: white;
    background: rgba(255,255,255,0.20);
    border-left: 4px solid white;
    border-radius: 0 10px 10px 0;
    font-weight: bold;
}}

/* ─── Sidebar nav (mini) ────────────────────────────────────────── */
QPushButton#nav_btn_mini {{
    background: transparent;
    border: none;
    border-radius: 12px;
    padding: 6px;
}}
QPushButton#nav_btn_mini:hover {{
    background: rgba(255,255,255,0.18);
}}
QPushButton#nav_btn_mini[active=true] {{
    background: rgba(255,255,255,0.22);
    border: 2px solid rgba(255,255,255,0.60);
}}

/* ─── Toggle button ─────────────────────────────────────────────── */
QPushButton#sidebar_toggle {{
    background: transparent;
    border: none;
    border-radius: 8px;
    padding: 4px;
}}
QPushButton#sidebar_toggle:hover {{
    background: rgba(204,0,126,0.08);
}}

/* ─── Page title pill ───────────────────────────────────────────── */
QLabel#page_title {{
    color: white;
    font-size: 14px;
    font-weight: bold;
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 {C['magenta']}, stop:1 {C['magenta_light']});
    border-radius: 10px;
    padding: 5px 18px;
}}

/* ─── Action buttons ────────────────────────────────────────────── */
QPushButton#primary_btn {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 {C['magenta']}, stop:1 {C['magenta_light']});
    color: #cc007e;
    border: none;
    border-radius: 10px;
    padding: 8px 20px;
    font-size: 12px;
    font-weight: bold;
}}
QPushButton#primary_btn:hover   {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 {C['magenta_h']}, stop:1 #ff66cc);
}}
QPushButton#primary_btn:pressed {{ background: {C['magenta_d']}; }}

QPushButton#success_btn {{
    background:pink;
    color: #cc007e;
    border: none;
    border-radius: 8px;
    padding: 5px 13px;
    font-size: 11px;
    font-weight: bold;
}}
QPushButton#success_btn:hover {{ background:#fbf9f1 ; }}

QPushButton#danger_btn {{
    background: {C['danger']};
    color: red;
    border: none;
    border-radius: 8px;
    padding: 5px 13px;
    font-size: 11px;
    font-weight: bold;
}}
QPushButton#danger_btn:hover {{ background: #991b1b; }}

QPushButton#ghost_btn {{
    background: rgba(204,0,126,0.06);
    color: {C['magenta']};
    border: 1.5px solid rgba(204,0,126,0.40);
    border-radius: 8px;
    padding: 5px 13px;
    font-size: 11px;
}}
QPushButton#ghost_btn:hover {{
    background: {C['magenta_bg']};
    border-color: {C['magenta']};
}}

/* ─── Form inputs ───────────────────────────────────────────────── */
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
    background: rgba(255,255,255,0.85);
    color: {C['text']};
    border: 1.5px solid rgba(204,0,126,0.20);
    border-radius: 10px;
    padding: 8px 13px;
    font-size: 13px;
}}
QLineEdit:focus, QComboBox:focus,
QSpinBox:focus,  QDoubleSpinBox:focus {{
    border-color: {C['magenta']};
    background: rgba(255,255,255,0.95);
}}
QComboBox::drop-down  {{ border: none; width: 24px; background: transparent; }}
QComboBox::down-arrow {{
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {C['magenta']};
    width: 0; height: 0;
}}
QComboBox QAbstractItemView {{
    background: {C['white']};
    color: {C['text']};
    border: 1.5px solid {C['border']};
    selection-background-color: {C['selection']};
    border-radius: 8px;
    outline: none;
}}
QComboBox QAbstractItemView::item {{
    padding: 6px 12px;
    min-height: 28px;
    border: none;
}}
QComboBox QAbstractItemView::item:hover {{
    background: {C['magenta_bg']};
    color: {C['magenta']};
}}

/* ─── Spinbox arrow buttons ─────────────────────────────────────── */
QSpinBox::up-button, QDoubleSpinBox::up-button,
QSpinBox::down-button, QDoubleSpinBox::down-button {{
    background: transparent;
    border: none;
    width: 18px;
}}

/* ─── Dialog title ──────────────────────────────────────────────── */
QLabel#dlg_title {{
    font-size: 17px;
    font-weight: bold;
    color: {C['text']};
    background: transparent;
}}

/* ─── Status bar ────────────────────────────────────────────────── */
QStatusBar {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 {C['magenta']}, stop:1 {C['magenta_d']});
    color: rgba(255,255,255,0.90);
    border-top: 1px solid {C['magenta_d']};
    font-size: 11px;
    font-weight: 500;
}}

/* ─── Scrollbars ────────────────────────────────────────────────── */
QScrollBar:vertical   {{ background: transparent; width: 6px;  border: none; }}
QScrollBar:horizontal {{ background: transparent; height: 6px; border: none; }}
QScrollBar::handle:vertical, QScrollBar::handle:horizontal {{
    background: rgba(204,0,126,0.25); border-radius: 3px;
    min-height: 20px; min-width: 20px;
}}
QScrollBar::handle:vertical:hover,
QScrollBar::handle:horizontal:hover {{ background: {C['magenta']}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height:0; width:0; border:none; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}

/* ─── ToolTip ────────────────────────────────────────────────────── */
QToolTip {{
    background: {C['text']};
    color: white;
    border: none;
    border-radius: 6px;
    padding: 5px 10px;
    font-size: 11px;
}}
"""
