"""
Design system for Lock In.

Single source of truth for colors, typography, and control styling.
Every widget is styled through the one application-level stylesheet
built here; widgets opt in via objectName ("Card", "Popover", ...)
or dynamic properties (variant="primary", role="h2", ...).

Usage:
    from ui.theme import apply_theme, palette
    apply_theme(app, "light")          # or "dark"
    palette()["accent"]                # programmatic color access
"""

from PyQt6.QtWidgets import QApplication

FONT_STACK = '"Segoe UI", "SF Pro Text", "Inter", system-ui, sans-serif'
MONO_STACK = '"Cascadia Code", "Consolas", "SF Mono", monospace'

LIGHT = {
    "bg":           "#f5f6f8",
    "surface":      "#ffffff",
    "surface2":     "#eef0f3",
    "text":         "#16181d",
    "text2":        "#5f6672",
    "text3":        "#9aa1ad",
    "border":       "#e4e7ec",
    "accent":       "#10b981",
    "accent_hover": "#0ea271",
    "accent_press": "#0c8a60",
    "accent_soft":  "#e6f7f0",
    "on_accent":    "#ffffff",
    "danger":       "#e5484d",
    "danger_hover": "#d93a40",
    "danger_soft":  "#fdebec",
}

DARK = {
    "bg":           "#101216",
    "surface":      "#181b21",
    "surface2":     "#20242c",
    "text":         "#e8eaee",
    "text2":        "#a2a8b4",
    "text3":        "#6d7480",
    "border":       "#2a2f38",
    "accent":       "#10b981",
    "accent_hover": "#2fd3a0",
    "accent_press": "#0c8a60",
    "accent_soft":  "#16352b",
    "on_accent":    "#ffffff",
    "danger":       "#e5484d",
    "danger_hover": "#f06568",
    "danger_soft":  "#3a1d1f",
}

_current_mode = "light"


def palette() -> dict:
    """Palette for the active theme."""
    return DARK if _current_mode == "dark" else LIGHT


def mode() -> str:
    return _current_mode


def apply_theme(app: QApplication, theme_mode: str = "light") -> None:
    """Build and install the global stylesheet for the given mode."""
    global _current_mode
    _current_mode = "dark" if theme_mode == "dark" else "light"
    app.setStyleSheet(_build_qss(palette()))


def _build_qss(c: dict) -> str:
    return f"""
/* ---------- base ---------- */
QWidget {{
    color: {c['text']};
    font-family: {FONT_STACK};
    font-size: 14px;
}}
QMainWindow, QWidget#Screen {{
    background-color: {c['bg']};
}}
QToolTip {{
    background-color: {c['text']};
    color: {c['bg']};
    border: none;
    padding: 6px 10px;
    font-size: 12px;
}}

/* ---------- surfaces ---------- */
QFrame#Card {{
    background-color: {c['surface']};
    border: 1px solid {c['border']};
    border-radius: 14px;
}}
QWidget#NavRail {{
    background-color: {c['surface']};
    border-right: 1px solid {c['border']};
}}
QFrame#PillCard {{
    background-color: {c['surface']};
    border: 1px solid {c['border']};
    border-radius: 18px;
}}
QFrame#Popover {{
    background-color: {c['surface']};
    border: 1px solid {c['border']};
    border-radius: 14px;
}}

/* ---------- typography roles ---------- */
QLabel {{ background: transparent; }}
QLabel[role="display"] {{ font-size: 28px; font-weight: 700; letter-spacing: -0.5px; }}
QLabel[role="h2"]      {{ font-size: 18px; font-weight: 700; }}
QLabel[role="sub"]     {{ font-size: 13px; color: {c['text2']}; }}
QLabel[role="hint"]    {{ font-size: 12px; color: {c['text3']}; }}
QLabel[role="statValue"] {{ font-size: 26px; font-weight: 700; }}
QLabel[role="statLabel"] {{
    font-size: 11px; font-weight: 700; color: {c['text3']};
    letter-spacing: 1px;
}}
QLabel[role="accent"]  {{ color: {c['accent']}; }}
QLabel[role="danger"]  {{ color: {c['danger']}; }}
QLabel[role="timer"] {{
    font-family: {MONO_STACK};
    font-size: 24px; font-weight: 700; color: {c['accent']};
}}

/* ---------- buttons ---------- */
QPushButton {{
    border: none;
    border-radius: 10px;
    padding: 10px 18px;
    font-size: 14px;
    font-weight: 600;
    background-color: transparent;
}}
QPushButton[variant="primary"] {{
    background-color: {c['accent']};
    color: {c['on_accent']};
    padding: 12px 24px;
}}
QPushButton[variant="primary"]:hover   {{ background-color: {c['accent_hover']}; }}
QPushButton[variant="primary"]:pressed {{ background-color: {c['accent_press']}; }}
QPushButton[variant="primary"]:disabled {{
    background-color: {c['surface2']}; color: {c['text3']};
}}
QPushButton[variant="ghost"] {{
    background-color: {c['surface']};
    border: 1px solid {c['border']};
    color: {c['text']};
}}
QPushButton[variant="ghost"]:hover {{
    border-color: {c['accent']};
    color: {c['accent']};
}}
QPushButton[variant="danger"] {{
    background-color: {c['danger']};
    color: {c['on_accent']};
}}
QPushButton[variant="danger"]:hover {{ background-color: {c['danger_hover']}; }}
QPushButton[variant="dangerGhost"] {{
    background-color: transparent;
    border: 1px solid {c['border']};
    color: {c['danger']};
}}
QPushButton[variant="dangerGhost"]:hover {{
    background-color: {c['danger_soft']};
    border-color: {c['danger']};
}}
QPushButton[variant="nav"] {{
    background-color: transparent;
    color: {c['text2']};
    border-radius: 10px;
    padding: 10px 0px;
    font-size: 11px;
    font-weight: 600;
}}
QPushButton[variant="nav"]:hover {{ background-color: {c['surface2']}; }}
QPushButton[variant="nav"]:checked {{
    background-color: {c['accent_soft']};
    color: {c['accent']};
}}
QPushButton[variant="chip"] {{
    background-color: {c['surface']};
    border: 1px solid {c['border']};
    border-radius: 18px;
    padding: 8px 18px;
    font-size: 13px;
    color: {c['text2']};
}}
QPushButton[variant="chip"]:hover {{ border-color: {c['accent']}; }}
QPushButton[variant="chip"]:checked {{
    background-color: {c['accent_soft']};
    border-color: {c['accent']};
    color: {c['accent']};
    font-weight: 700;
}}
QPushButton[variant="pillBtn"] {{
    background-color: transparent;
    color: {c['text2']};
    border-radius: 8px;
    padding: 6px 10px;
    font-size: 12px;
    font-weight: 600;
}}
QPushButton[variant="pillBtn"]:hover {{
    background-color: {c['surface2']};
    color: {c['text']};
}}
QPushButton[variant="pillDanger"] {{
    background-color: transparent;
    color: {c['danger']};
    border-radius: 8px;
    padding: 6px 10px;
    font-size: 13px;
    font-weight: 700;
}}
QPushButton[variant="pillDanger"]:hover {{ background-color: {c['danger_soft']}; }}

/* ---------- inputs ---------- */
QLineEdit, QTextEdit {{
    background-color: {c['surface']};
    border: 1px solid {c['border']};
    border-radius: 10px;
    padding: 10px 14px;
    font-size: 14px;
    selection-background-color: {c['accent']};
    selection-color: {c['on_accent']};
}}
QLineEdit:focus, QTextEdit:focus {{ border: 1px solid {c['accent']}; }}
QLineEdit::placeholder {{ color: {c['text3']}; }}

QSpinBox {{
    background-color: {c['surface']};
    border: 1px solid {c['border']};
    border-radius: 10px;
    padding: 6px 34px;
    font-size: 16px;
    font-weight: 600;
}}
QSpinBox:focus {{ border-color: {c['accent']}; }}
QSpinBox::up-button {{
    subcontrol-origin: border; subcontrol-position: center right;
    width: 30px; height: 30px; margin-right: 2px;
    border-radius: 8px; background: {c['surface2']};
}}
QSpinBox::down-button {{
    subcontrol-origin: border; subcontrol-position: center left;
    width: 30px; height: 30px; margin-left: 2px;
    border-radius: 8px; background: {c['surface2']};
}}
QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
    background: {c['accent']};
}}

/* ---------- lists ---------- */
QListWidget {{
    background-color: {c['surface']};
    border: 1px solid {c['border']};
    border-radius: 12px;
    padding: 6px;
    outline: none;
}}
QListWidget::item {{
    padding: 10px 12px;
    border-radius: 8px;
    margin: 1px 2px;
    color: {c['text']};
}}
QListWidget::item:hover    {{ background-color: {c['surface2']}; }}
QListWidget::item:selected {{
    background-color: {c['accent_soft']};
    color: {c['accent']};
}}

/* ---------- progress ---------- */
QProgressBar {{
    background-color: {c['surface2']};
    border: none;
    border-radius: 3px;
}}
QProgressBar::chunk {{
    background-color: {c['accent']};
    border-radius: 3px;
}}

/* ---------- scrollbars ---------- */
QScrollArea {{ border: none; background: transparent; }}
QScrollBar:vertical {{
    background: transparent; width: 8px; margin: 2px;
}}
QScrollBar::handle:vertical {{
    background: {c['border']}; border-radius: 4px; min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{ background: {c['text3']}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{ height: 0; }}

/* ---------- dialogs ---------- */
QMessageBox {{ background-color: {c['surface']}; }}
QMessageBox QPushButton {{
    background-color: {c['surface2']};
    border: 1px solid {c['border']};
    min-width: 80px;
    padding: 8px 16px;
}}
QMessageBox QPushButton:hover {{ border-color: {c['accent']}; }}
"""
