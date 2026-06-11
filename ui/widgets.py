"""
Component library for Lock In.

All visual styling lives in ui/theme.py (global stylesheet).
Widgets here only declare structure + the objectName / property
hooks the theme targets.
"""

from PyQt6.QtWidgets import (
    QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QFrame,
    QSpinBox, QProgressBar, QTextEdit, QGraphicsDropShadowEffect,
    QApplication, QMessageBox,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QColor


# ---------------------------------------------------------------- factories

def button(text: str, variant: str = "ghost", tooltip: str = "") -> QPushButton:
    """Create a themed button. Variants: primary, ghost, danger,
    dangerGhost, nav, chip, pillBtn, pillDanger."""
    btn = QPushButton(text)
    btn.setProperty("variant", variant)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    if tooltip:
        btn.setToolTip(tooltip)
    return btn


def label(text: str, role: str = "") -> QLabel:
    """Create a themed label. Roles: display, h2, sub, hint,
    statValue, statLabel, accent, timer."""
    lbl = QLabel(text)
    if role:
        lbl.setProperty("role", role)
    return lbl


def card_shadow(widget: QWidget) -> None:
    """Soft elevation shadow, tuned per theme."""
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(24)
    shadow.setColor(QColor(0, 0, 0, 26))
    shadow.setOffset(0, 4)
    widget.setGraphicsEffect(shadow)


# ---------------------------------------------------------------- surfaces

class Card(QFrame):
    """Elevated surface. Styled via #Card in the theme."""

    def __init__(self, parent=None, padding: int = 24, spacing: int = 16):
        super().__init__(parent)
        self.setObjectName("Card")
        card_shadow(self)
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(padding, padding, padding, padding)
        self.body.setSpacing(spacing)


class StatTile(Card):
    """Small KPI tile: LABEL over a big value, optional caption."""

    def __init__(self, title: str, value: str = "–", caption: str = "", parent=None):
        super().__init__(parent, padding=20, spacing=6)
        self.body.addWidget(label(title.upper(), "statLabel"))
        self.value_label = label(value, "statValue")
        self.body.addWidget(self.value_label)
        self.caption_label = label(caption, "hint")
        self.caption_label.setVisible(bool(caption))
        self.body.addWidget(self.caption_label)
        self.body.addStretch()
        self.setMinimumHeight(110)

    def set_value(self, value: str, caption: str = None):
        self.value_label.setText(value)
        if caption is not None:
            self.caption_label.setText(caption)
            self.caption_label.setVisible(bool(caption))


# ---------------------------------------------------------------- duration

class DurationPicker(QWidget):
    """Preset chips (Pomodoro / Deep work / Flow) + custom h:m spinners."""

    PRESETS = [("25 min", 25), ("50 min", 50), ("90 min", 90)]

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        chip_row = QHBoxLayout()
        chip_row.setSpacing(8)
        self.chips = []
        for text, minutes in self.PRESETS:
            chip = button(text, "chip")
            chip.setCheckable(True)
            chip.clicked.connect(lambda _, m=minutes, c=chip: self._pick_preset(m, c))
            self.chips.append(chip)
            chip_row.addWidget(chip)

        self.custom_chip = button("Custom", "chip")
        self.custom_chip.setCheckable(True)
        self.custom_chip.clicked.connect(self._pick_custom)
        chip_row.addWidget(self.custom_chip)
        chip_row.addStretch()
        layout.addLayout(chip_row)

        # Custom spinners (hidden until "Custom" chosen)
        self.custom_row = QWidget()
        row = QHBoxLayout(self.custom_row)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(10)
        self.hours = QSpinBox()
        self.hours.setRange(0, 12)
        self.hours.setSuffix(" h")
        self.hours.setButtonSymbols(QSpinBox.ButtonSymbols.PlusMinus)
        self.minutes = QSpinBox()
        self.minutes.setRange(0, 59)
        self.minutes.setSuffix(" min")
        self.minutes.setButtonSymbols(QSpinBox.ButtonSymbols.PlusMinus)
        for spin in (self.hours, self.minutes):
            spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
            spin.setMinimumWidth(130)
            spin.setMinimumHeight(46)
        row.addWidget(self.hours)
        row.addWidget(self.minutes)
        row.addStretch()
        self.custom_row.setVisible(False)
        layout.addWidget(self.custom_row)

        self._minutes = 50
        self._select_chip(self.chips[1])  # default: 50 min deep work

    def _select_chip(self, active):
        for chip in self.chips + [self.custom_chip]:
            chip.setChecked(chip is active)

    def _pick_preset(self, minutes: int, chip):
        self._minutes = minutes
        self._select_chip(chip)
        self.custom_row.setVisible(False)

    def _pick_custom(self):
        self._select_chip(self.custom_chip)
        self.hours.setValue(self._minutes // 60)
        self.minutes.setValue(self._minutes % 60)
        self.custom_row.setVisible(True)

    def get_total_minutes(self) -> int:
        if self.custom_chip.isChecked():
            return self.hours.value() * 60 + self.minutes.value()
        return self._minutes

    def reset(self):
        self._pick_preset(50, self.chips[1])


# ---------------------------------------------------------------- focus pill

class FocusPill(QWidget):
    """
    In-session control: a small always-on-top draggable pill.

    Replaces the old full-height sidebar - tiny footprint, can be
    dragged anywhere, collapses to timer-only.
    """

    stats_requested = pyqtSignal()
    notes_requested = pyqtSignal()
    exit_requested = pyqtSignal()

    EXPANDED_W, COLLAPSED_W, HEIGHT = 380, 190, 76

    def __init__(self, session_manager, parent=None):
        super().__init__(parent)
        self.session_manager = session_manager
        self.countdown = True
        self.collapsed = False
        self.elapsed = 0
        self.remaining = 0
        self._drag_offset = None

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._build_ui()
        self.session_manager.session_updated.connect(self._on_tick)

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 8, 8, 8)

        pill = QFrame()
        pill.setObjectName("PillCard")
        card_shadow(pill)
        outer.addWidget(pill)

        row = QHBoxLayout(pill)
        row.setContentsMargins(18, 10, 10, 10)
        row.setSpacing(6)

        # Timer block (click to flip countdown <-> elapsed)
        timer_block = QWidget()
        timer_block.setCursor(Qt.CursorShape.PointingHandCursor)
        timer_block.setToolTip("Click to switch between time left and elapsed")
        timer_block.mousePressEvent = lambda e: self._toggle_mode()
        tb = QVBoxLayout(timer_block)
        tb.setContentsMargins(0, 0, 0, 0)
        tb.setSpacing(2)
        self.mode_caption = label("TIME LEFT", "statLabel")
        self.timer_label = label("00:00:00", "timer")
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(4)
        self.progress.setRange(0, 100)
        tb.addWidget(self.mode_caption)
        tb.addWidget(self.timer_label)
        tb.addWidget(self.progress)
        row.addWidget(timer_block)
        row.addStretch()

        self.stats_btn = button("Stats", "pillBtn", "Session stats")
        self.stats_btn.clicked.connect(self.stats_requested.emit)
        self.notes_btn = button("Notes", "pillBtn", "Jot down what you're working on")
        self.notes_btn.clicked.connect(self.notes_requested.emit)
        self.collapse_btn = button("›", "pillBtn", "Collapse to timer only")
        self.collapse_btn.clicked.connect(self._toggle_collapse)
        self.end_btn = button("✕", "pillDanger", "End session early")
        self.end_btn.clicked.connect(self._confirm_exit)
        for btn in (self.stats_btn, self.notes_btn, self.collapse_btn, self.end_btn):
            row.addWidget(btn)

    # ---- behaviour

    def start_display(self):
        info = self.session_manager.get_session_info()
        self.elapsed = 0
        self.remaining = info["duration"] if info else 0
        self.countdown = True
        self.collapsed = False
        self._apply_collapse()
        self._refresh()
        self.progress.setValue(0)

        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            self.move(geo.right() - self.width() - 16, geo.top() + 16)
        self.show()
        self.raise_()

    def _on_tick(self, elapsed: int, remaining: int):
        self.elapsed, self.remaining = elapsed, remaining
        self._refresh()
        info = self.session_manager.get_session_info()
        if info and info["duration"] > 0:
            self.progress.setValue(min(100, int(elapsed / info["duration"] * 100)))

    def _refresh(self):
        secs = self.remaining if self.countdown else self.elapsed
        self.timer_label.setText(
            f"{secs // 3600:02d}:{secs % 3600 // 60:02d}:{secs % 60:02d}"
        )
        self.mode_caption.setText("TIME LEFT" if self.countdown else "ELAPSED")

    def _toggle_mode(self):
        self.countdown = not self.countdown
        self._refresh()

    def _toggle_collapse(self):
        self.collapsed = not self.collapsed
        right_edge = self.x() + self.width()
        self._apply_collapse()
        self.move(right_edge - self.width(), self.y())

    def _apply_collapse(self):
        for btn in (self.stats_btn, self.notes_btn, self.end_btn):
            btn.setVisible(not self.collapsed)
        self.collapse_btn.setText("‹" if self.collapsed else "›")
        self.collapse_btn.setToolTip(
            "Expand" if self.collapsed else "Collapse to timer only"
        )
        self.setFixedSize(
            self.COLLAPSED_W if self.collapsed else self.EXPANDED_W, self.HEIGHT
        )

    def _confirm_exit(self):
        reply = QMessageBox.warning(
            self, "End session",
            "End this focus session early?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.exit_requested.emit()

    # ---- dragging

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )

    def mouseMoveEvent(self, event):
        if self._drag_offset is not None:
            self.move(event.globalPosition().toPoint() - self._drag_offset)

    def mouseReleaseEvent(self, event):
        self._drag_offset = None


# ---------------------------------------------------------------- popovers

class _Popover(QWidget):
    """Frameless floating panel anchored near the focus pill."""

    WIDTH = 320

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 8, 8, 8)
        frame = QFrame()
        frame.setObjectName("Popover")
        card_shadow(frame)
        outer.addWidget(frame)
        self.body = QVBoxLayout(frame)
        self.body.setContentsMargins(20, 20, 20, 20)
        self.body.setSpacing(12)
        self.setFixedWidth(self.WIDTH)

    def open_near(self, anchor: QWidget):
        """Show below the anchor, right-aligned, clamped to screen."""
        x = anchor.x() + anchor.width() - self.width()
        y = anchor.y() + anchor.height() + 4
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = max(geo.left() + 8, min(x, geo.right() - self.width() - 8))
            if y + 300 > geo.bottom():
                y = anchor.y() - 300
        self.move(x, y)
        self.show()
        self.raise_()


class StatsPopover(_Popover):
    """Live session stats next to the pill."""

    def __init__(self, session_manager, stats_tracker, parent=None):
        super().__init__(parent)
        self.session_manager = session_manager
        self.stats_tracker = stats_tracker

        self.body.addWidget(label("Session stats", "h2"))
        self.rows = {}
        for key, title in [
            ("elapsed", "Elapsed"), ("remaining", "Remaining"),
            ("blocked", "Apps blocked"), ("completion", "Completion"),
        ]:
            row = QHBoxLayout()
            row.addWidget(label(title, "sub"))
            row.addStretch()
            value = label("–")
            self.rows[key] = value
            row.addWidget(value)
            self.body.addLayout(row)

        self.previous_label = label("", "hint")
        self.body.addWidget(self.previous_label)
        close_btn = button("Close", "ghost")
        close_btn.clicked.connect(self.hide)
        self.body.addWidget(close_btn)

    def refresh_and_open(self, anchor: QWidget):
        info = self.session_manager.get_session_info()
        if info:
            fmt = lambda s: f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}"
            self.rows["elapsed"].setText(fmt(info["elapsed"]))
            self.rows["remaining"].setText(fmt(info["remaining"]))
            self.rows["blocked"].setText(str(info["apps_blocked"]))
            self.rows["completion"].setText(f"{info['progress']:.0f}%")

        prev = self.stats_tracker.get_previous_session()
        if prev and prev.get("time_locked_in_seconds"):
            mins = prev["time_locked_in_seconds"] // 60
            self.previous_label.setText(f"Last session: {mins} min locked in")
        else:
            self.previous_label.setText("This is your first session - set the bar.")
        self.open_near(anchor)


class NotesPopover(_Popover):
    """Quick capture of what you're working on; saved with the session."""

    def __init__(self, session_manager, parent=None):
        super().__init__(parent)
        self.session_manager = session_manager

        self.body.addWidget(label("Session notes", "h2"))
        self.editor = QTextEdit()
        self.editor.setPlaceholderText("What are you working on?")
        self.editor.setFixedHeight(120)
        self.body.addWidget(self.editor)

        row = QHBoxLayout()
        self.saved_hint = label("", "hint")
        row.addWidget(self.saved_hint)
        row.addStretch()
        close_btn = button("Close", "ghost")
        close_btn.clicked.connect(self.hide)
        save_btn = button("Save", "primary")
        save_btn.clicked.connect(self._save)
        row.addWidget(close_btn)
        row.addWidget(save_btn)
        self.body.addLayout(row)

    def refresh_and_open(self, anchor: QWidget):
        info = self.session_manager.get_session_info()
        self.editor.setPlainText(info.get("notes", "") if info else "")
        self.saved_hint.setText("")
        self.open_near(anchor)
        self.editor.setFocus()

    def _save(self):
        if self.session_manager.update_session_notes(self.editor.toPlainText()):
            self.saved_hint.setText("Saved ✓")
            QTimer.singleShot(1500, lambda: self.saved_hint.setText(""))
