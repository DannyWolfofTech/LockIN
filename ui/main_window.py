"""
Main window for Lock In.

Layout: left navigation rail + stacked screens.

    Focus    - set up and start a session
    History  - past sessions with notes
    Stats    - lifetime totals, streaks, most-blocked apps

During a session the window minimizes and the floating FocusPill
takes over. A theme toggle (light/dark) lives at the bottom of the
rail and persists via the settings table.
"""

import json
from datetime import datetime

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QStackedWidget, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QScrollArea, QMessageBox, QApplication, QButtonGroup, QCheckBox,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCloseEvent, QColor

from ui.theme import apply_theme, palette, mode
from ui.widgets import (
    button, label, Card, StatTile, DurationPicker,
    FocusPill, StatsPopover, NotesPopover, FocusHeatmap,
)
from core.session_manager import SessionManager, SessionState
from core.stats_tracker import StatsTracker
from database.db_manager import DatabaseManager


# ================================================================ screens

class FocusSetupScreen(QWidget):
    """Name it, time it, pick what's allowed, lock in."""

    start_session_requested = pyqtSignal(str, int, list, bool)  # +strict

    def __init__(self, session_manager: SessionManager, parent=None):
        super().__init__(parent)
        self.setObjectName("Screen")
        self.session_manager = session_manager
        self.all_apps = []
        self._build_ui()
        self.refresh_apps()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 32, 36, 28)
        layout.setSpacing(18)

        layout.addWidget(label("Lock in.", "display"))
        layout.addWidget(label(
            "Everything not on your list gets closed and stays closed.", "sub"
        ))

        # --- saved templates (hidden until one exists)
        self.templates_bar = QWidget()
        self.templates_layout = QHBoxLayout(self.templates_bar)
        self.templates_layout.setContentsMargins(0, 0, 0, 0)
        self.templates_layout.setSpacing(8)
        layout.addWidget(self.templates_bar)

        # --- session config
        config = Card(padding=24, spacing=14)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText(
            "What are you working on?  e.g. Thesis draft"
        )
        config.body.addWidget(self.name_input)
        self.duration = DurationPicker()
        config.body.addWidget(self.duration)
        self.strict_check = QCheckBox(
            "Strict mode — ending early requires typing a confirmation"
        )
        self.strict_check.setCursor(Qt.CursorShape.PointingHandCursor)
        config.body.addWidget(self.strict_check)
        layout.addWidget(config)

        # --- app picker
        picker = Card(padding=24, spacing=12)
        picker.body.addWidget(label("Allowed apps", "h2"))

        lists = QHBoxLayout()
        lists.setSpacing(16)

        left = QVBoxLayout()
        left.setSpacing(8)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search apps…")
        self.search.textChanged.connect(self._filter)
        left.addWidget(self.search)
        self.available = QListWidget()
        self.available.itemDoubleClicked.connect(lambda _: self._add())
        left.addWidget(self.available, 1)
        lists.addLayout(left, 3)

        middle = QVBoxLayout()
        middle.addStretch()
        add_btn = button("Add →", "ghost", "Allow the selected app")
        add_btn.clicked.connect(self._add)
        remove_btn = button("← Remove", "ghost", "Disallow the selected app")
        remove_btn.clicked.connect(self._remove)
        middle.addWidget(add_btn)
        middle.addWidget(remove_btn)
        middle.addStretch()
        lists.addLayout(middle, 0)

        right = QVBoxLayout()
        right.setSpacing(8)
        right.addWidget(label("Allowed during the session", "sub"))
        self.allowed = QListWidget()
        self.allowed.itemDoubleClicked.connect(lambda _: self._remove())
        right.addWidget(self.allowed, 1)
        lists.addLayout(right, 2)

        picker.body.addLayout(lists, 1)
        layout.addWidget(picker, 1)

        # --- actions
        actions = QHBoxLayout()
        refresh = button("Refresh apps", "ghost")
        refresh.clicked.connect(self.refresh_apps)
        actions.addWidget(refresh)
        save_tpl = button("Save as template", "ghost",
                          "Save this name + duration + app list for one-click reuse")
        save_tpl.clicked.connect(self._save_template)
        actions.addWidget(save_tpl)
        actions.addStretch()
        start = button("Start focus session", "primary")
        start.clicked.connect(self._start)
        actions.addWidget(start)
        layout.addLayout(actions)

        self._reload_templates()

    # ---- app list

    def refresh_apps(self):
        # Single scan: installed apps already carry the 'running' flag.
        blocker = self.session_manager.app_blocker
        self.all_apps = sorted(
            blocker.get_all_installed_apps(),
            key=lambda a: (not a.get("running"), a["display_name"].lower()),
        )
        self._filter(self.search.text())

    def _filter(self, text: str):
        text = text.lower()
        self.available.clear()
        for app in self.all_apps:
            name = app["display_name"]
            if text and text not in name.lower():
                continue
            running = bool(app.get("running"))
            item = QListWidgetItem(("●  " if running else "") + name)
            item.setData(Qt.ItemDataRole.UserRole, name)
            if app.get("icon"):
                item.setIcon(app["icon"])
            if running:
                item.setForeground(QColor(palette()["accent"]))
            self.available.addItem(item)

    def _add(self):
        item = self.available.currentItem()
        if not item:
            return
        name = item.data(Qt.ItemDataRole.UserRole)
        existing = [self.allowed.item(i).text() for i in range(self.allowed.count())]
        if name not in existing:
            self.allowed.addItem(name)

    def _remove(self):
        row = self.allowed.currentRow()
        if row >= 0:
            self.allowed.takeItem(row)

    def _whitelist(self) -> list:
        return [self.allowed.item(i).text() for i in range(self.allowed.count())]

    # ---- templates

    MAX_TEMPLATES = 6

    def _read_templates(self) -> list:
        raw = self.session_manager.db_manager.get_setting("templates", "[]")
        try:
            templates = json.loads(raw)
            return templates if isinstance(templates, list) else []
        except (ValueError, TypeError):
            return []

    def _write_templates(self, templates: list):
        self.session_manager.db_manager.set_setting(
            "templates", json.dumps(templates[: self.MAX_TEMPLATES])
        )
        self._reload_templates()

    def _reload_templates(self):
        while self.templates_layout.count():
            item = self.templates_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        templates = self._read_templates()
        self.templates_bar.setVisible(bool(templates))
        if not templates:
            return
        self.templates_layout.addWidget(label("Templates", "hint"))
        for tpl in templates:
            chip = button(tpl.get("name", "?"), "chip",
                          "Click to load · right-click to delete")
            chip.clicked.connect(lambda _, t=tpl: self._apply_template(t))
            chip.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            chip.customContextMenuRequested.connect(
                lambda _, t=tpl: self._delete_template(t))
            self.templates_layout.addWidget(chip)
        self.templates_layout.addStretch()

    def _apply_template(self, tpl: dict):
        self.name_input.setText(tpl.get("name", ""))
        self.duration.set_minutes(int(tpl.get("minutes", 50)))
        self.strict_check.setChecked(bool(tpl.get("strict", False)))
        self.allowed.clear()
        for app in tpl.get("apps", []):
            self.allowed.addItem(app)

    def _save_template(self):
        from PyQt6.QtWidgets import QInputDialog
        default = self.name_input.text().strip() or "My setup"
        name, ok = QInputDialog.getText(
            self, "Save template", "Template name:", text=default)
        name = (name or "").strip()
        if not ok or not name:
            return
        tpl = {
            "name": name,
            "minutes": self.duration.get_total_minutes(),
            "apps": self._whitelist(),
            "strict": self.strict_check.isChecked(),
        }
        templates = [t for t in self._read_templates()
                     if t.get("name") != name]
        templates.insert(0, tpl)
        self._write_templates(templates)

    def _delete_template(self, tpl: dict):
        templates = [t for t in self._read_templates()
                     if t.get("name") != tpl.get("name")]
        self._write_templates(templates)

    # ---- start

    def _start(self):
        name = self.name_input.text().strip() or "Focus session"
        minutes = self.duration.get_total_minutes()
        if minutes <= 0:
            QMessageBox.warning(self, "Duration", "Set a duration first.")
            return
        apps = self._whitelist()
        if not apps:
            reply = QMessageBox.question(
                self, "Nothing allowed",
                "No apps are allowed - everything will be blocked.\nLock in anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.No:
                return
        self.start_session_requested.emit(
            name, minutes, apps, self.strict_check.isChecked()
        )

    def reset_form(self):
        self.name_input.clear()
        self.duration.reset()
        self.allowed.clear()
        self.strict_check.setChecked(False)
        self.refresh_apps()


class HistoryScreen(QWidget):
    """Past sessions, newest first, with notes."""

    def __init__(self, stats_tracker: StatsTracker, parent=None):
        super().__init__(parent)
        self.setObjectName("Screen")
        self.stats_tracker = stats_tracker

        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 32, 36, 28)
        layout.setSpacing(18)
        layout.addWidget(label("History", "display"))

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.container = QWidget()
        self.container.setObjectName("Screen")
        self.list_layout = QVBoxLayout(self.container)
        self.list_layout.setContentsMargins(0, 0, 8, 0)
        self.list_layout.setSpacing(12)
        self.scroll.setWidget(self.container)
        layout.addWidget(self.scroll, 1)

    def refresh(self):
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        sessions = self.stats_tracker.get_recent_sessions(limit=30)
        if not sessions:
            empty = label("No sessions yet. Go lock in.", "sub")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.list_layout.addWidget(empty)
        for s in sessions:
            self.list_layout.addWidget(self._session_card(s))
        self.list_layout.addStretch()

    def _session_card(self, s: dict) -> Card:
        card = Card(padding=18, spacing=6)
        top = QHBoxLayout()
        name = label(s["name"])
        font = name.font()
        font.setBold(True)
        name.setFont(font)
        top.addWidget(name)
        top.addStretch()
        top.addWidget(label(self._fmt_date(s.get("created_at", "")), "hint"))
        card.body.addLayout(top)

        summary = (
            f"{s['time_locked_in_formatted']} of {s['duration_formatted']}"
            f"  ·  {s['completion_percentage']:.0f}% complete"
            f"  ·  {s['apps_blocked_count']} blocked"
        )
        if s.get("emergency_exit_used"):
            summary += "  ·  ended early"
        card.body.addWidget(label(summary, "sub"))

        notes = (s.get("notes") or "").strip()
        if notes:
            preview = notes if len(notes) <= 160 else notes[:157] + "…"
            card.body.addWidget(label(f"“{preview}”", "hint"))
        return card

    @staticmethod
    def _fmt_date(raw: str) -> str:
        try:
            return datetime.fromisoformat(raw).strftime("%b %d, %H:%M")
        except (ValueError, TypeError):
            return raw or ""


class StatsScreen(QWidget):
    """Lifetime numbers: totals, streaks, most-blocked offenders."""

    def __init__(self, stats_tracker: StatsTracker, parent=None):
        super().__init__(parent)
        self.setObjectName("Screen")
        self.stats_tracker = stats_tracker

        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 32, 36, 28)
        layout.setSpacing(18)
        layout.addWidget(label("Stats", "display"))

        tiles = QGridLayout()
        tiles.setSpacing(14)
        self.total_tile = StatTile("Total focus time")
        self.sessions_tile = StatTile("Sessions")
        self.streak_tile = StatTile("Current streak")
        self.best_streak_tile = StatTile("Longest streak")
        tiles.addWidget(self.total_tile, 0, 0)
        tiles.addWidget(self.sessions_tile, 0, 1)
        tiles.addWidget(self.streak_tile, 0, 2)
        tiles.addWidget(self.best_streak_tile, 0, 3)
        layout.addLayout(tiles)

        heatmap_card = Card(padding=20, spacing=10)
        heatmap_card.body.addWidget(label("LAST 12 MONTHS", "statLabel"))
        self.heatmap = FocusHeatmap()
        heatmap_card.body.addWidget(self.heatmap)
        layout.addWidget(heatmap_card)

        row = QHBoxLayout()
        row.setSpacing(14)

        self.week_card = Card(padding=20, spacing=8)
        self.week_card.body.addWidget(label("THIS WEEK", "statLabel"))
        self.week_value = label("–", "statValue")
        self.week_card.body.addWidget(self.week_value)
        self.week_caption = label("", "hint")
        self.week_card.body.addWidget(self.week_caption)
        self.week_card.body.addStretch()
        row.addWidget(self.week_card, 1)

        self.blocked_card = Card(padding=20, spacing=8)
        self.blocked_card.body.addWidget(label("MOST BLOCKED", "statLabel"))
        self.blocked_rows = QVBoxLayout()
        self.blocked_rows.setSpacing(6)
        self.blocked_card.body.addLayout(self.blocked_rows)
        self.blocked_card.body.addStretch()
        row.addWidget(self.blocked_card, 1)

        layout.addLayout(row, 1)

    def refresh(self):
        daily = self.stats_tracker.get_daily_breakdown(days=365)
        self.heatmap.set_data(
            {d["date"]: d["total_time_seconds"] for d in daily}
        )

        totals = self.stats_tracker.get_total_stats()
        self.total_tile.set_value(totals.get("total_time_formatted", "0h 0m"))
        self.sessions_tile.set_value(str(totals.get("total_sessions") or 0))

        streaks = self.stats_tracker.get_streak_info()
        self.streak_tile.set_value(f"{streaks['current_streak']} d")
        self.best_streak_tile.set_value(f"{streaks['longest_streak']} d")

        week = self.stats_tracker.get_weekly_stats()
        self.week_value.setText(week["total_time_formatted"])
        self.week_caption.setText(
            f"{week['total_sessions']} sessions · "
            f"{week['total_apps_blocked']} apps blocked"
        )

        while self.blocked_rows.count():
            item = self.blocked_rows.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                while item.layout().count():
                    sub = item.layout().takeAt(0)
                    if sub.widget():
                        sub.widget().deleteLater()
        top = self.stats_tracker.get_top_blocked_apps(limit=5)
        if not top:
            self.blocked_rows.addWidget(
                label("Nothing blocked yet - clean hands.", "sub")
            )
        for app in top:
            row = QHBoxLayout()
            row.addWidget(label(app["app_name"], "sub"))
            row.addStretch()
            row.addWidget(label(f"{app['total_blocks']}×", "accent"))
            self.blocked_rows.addLayout(row)


class SessionEndScreen(QWidget):
    """Post-session debrief: numbers, comparison, notes."""

    new_session_requested = pyqtSignal()

    def __init__(self, stats_tracker: StatsTracker, parent=None):
        super().__init__(parent)
        self.setObjectName("Screen")
        self.stats_tracker = stats_tracker

        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 40, 36, 32)
        layout.setSpacing(18)

        self.title = label("Session complete", "display")
        layout.addWidget(self.title)
        self.subtitle = label("", "sub")
        layout.addWidget(self.subtitle)

        tiles = QGridLayout()
        tiles.setSpacing(14)
        self.locked_tile = StatTile("Locked in")
        self.planned_tile = StatTile("Planned")
        self.blocked_tile = StatTile("Apps blocked")
        self.completion_tile = StatTile("Completion")
        tiles.addWidget(self.locked_tile, 0, 0)
        tiles.addWidget(self.planned_tile, 0, 1)
        tiles.addWidget(self.blocked_tile, 0, 2)
        tiles.addWidget(self.completion_tile, 0, 3)
        layout.addLayout(tiles)

        self.comparison = label("", "sub")
        layout.addWidget(self.comparison)

        self.notes_card = Card(padding=20, spacing=8)
        self.notes_card.body.addWidget(label("YOUR NOTES", "statLabel"))
        self.notes_label = label("", "sub")
        self.notes_label.setWordWrap(True)
        self.notes_card.body.addWidget(self.notes_label)
        self.notes_card.setVisible(False)
        layout.addWidget(self.notes_card)

        layout.addStretch()
        actions = QHBoxLayout()
        actions.addStretch()
        again = button("Start another session", "primary")
        again.clicked.connect(self.new_session_requested.emit)
        actions.addWidget(again)
        layout.addLayout(actions)

    def show_results(self, session_id: int, emergency_exit: bool):
        if emergency_exit:
            self.title.setText("Ended early")
            self.title.setProperty("role", "danger")
        else:
            self.title.setText("Session complete")
            self.title.setProperty("role", "display")
        # repolish after property change
        self.title.style().unpolish(self.title)
        self.title.style().polish(self.title)

        session = self.stats_tracker.get_session_details(session_id)
        if not session:
            return
        self.subtitle.setText(session["name"])
        self.locked_tile.set_value(session["time_locked_in_formatted"])
        self.planned_tile.set_value(session["duration_formatted"])
        self.blocked_tile.set_value(str(session["apps_blocked_count"]))
        self.completion_tile.set_value(f"{session['completion_percentage']:.0f}%")

        comp = self.stats_tracker.compare_to_previous(session_id)
        if comp.get("has_previous"):
            if comp["time_improved"]:
                self.comparison.setText(
                    f"{comp['time_difference_formatted']} longer than last time. "
                    "Keep stacking."
                )
            else:
                self.comparison.setText(
                    f"Last session was {comp['time_difference_formatted']} longer. "
                    "Next one's yours."
                )
        else:
            self.comparison.setText("First session logged. The streak starts now.")

        notes = (session.get("notes") or "").strip()
        self.notes_label.setText(notes)
        self.notes_card.setVisible(bool(notes))


# ================================================================ shell

class MainWindow(QMainWindow):
    """App shell: nav rail + screens + floating focus pill."""

    def __init__(self):
        super().__init__()
        self.db_manager = DatabaseManager()
        self.session_manager = SessionManager(self.db_manager)
        self.stats_tracker = StatsTracker(self.db_manager)
        self.allow_close = True

        saved = self.db_manager.get_setting("theme", "light")
        apply_theme(QApplication.instance(), saved)

        self._build_ui()
        self._connect()

    # ---- ui

    def _build_ui(self):
        self.setWindowTitle("Lock In")
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            w = min(1140, int(geo.width() * 0.9))
            h = min(760, int(geo.height() * 0.9))
            self.setGeometry(
                geo.x() + (geo.width() - w) // 2,
                geo.y() + (geo.height() - h) // 2, w, h,
            )
        self.setMinimumSize(960, 620)

        root = QWidget()
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        self.setCentralWidget(root)

        # nav rail
        rail = QWidget()
        rail.setObjectName("NavRail")
        rail.setFixedWidth(92)
        rail_layout = QVBoxLayout(rail)
        rail_layout.setContentsMargins(10, 20, 10, 16)
        rail_layout.setSpacing(8)

        logo = label("●", "accent")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_font = logo.font()
        logo_font.setPointSize(16)
        logo.setFont(logo_font)
        rail_layout.addWidget(logo)
        rail_layout.addSpacing(12)

        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        self.nav_buttons = {}
        for key, text in [("focus", "Focus"), ("history", "History"),
                          ("stats", "Stats")]:
            btn = button(text, "nav")
            btn.setCheckable(True)
            self.nav_group.addButton(btn)
            self.nav_buttons[key] = btn
            rail_layout.addWidget(btn)
        rail_layout.addStretch()

        self.theme_btn = button("Dark" if mode() == "light" else "Light", "nav",
                                "Switch theme")
        self.theme_btn.clicked.connect(self._toggle_theme)
        rail_layout.addWidget(self.theme_btn)
        root_layout.addWidget(rail)

        # screens
        self.stack = QStackedWidget()
        self.setup_screen = FocusSetupScreen(self.session_manager)
        self.history_screen = HistoryScreen(self.stats_tracker)
        self.stats_screen = StatsScreen(self.stats_tracker)
        self.end_screen = SessionEndScreen(self.stats_tracker)
        for s in (self.setup_screen, self.history_screen,
                  self.stats_screen, self.end_screen):
            self.stack.addWidget(s)
        root_layout.addWidget(self.stack, 1)

        self.nav_buttons["focus"].setChecked(True)
        self.stack.setCurrentWidget(self.setup_screen)

        # floating session UI
        self.pill = FocusPill(self.session_manager)
        self.stats_popover = StatsPopover(self.session_manager, self.stats_tracker)
        self.notes_popover = NotesPopover(self.session_manager)

    def _connect(self):
        self.nav_buttons["focus"].clicked.connect(
            lambda: self.stack.setCurrentWidget(self.setup_screen))
        self.nav_buttons["history"].clicked.connect(self._show_history)
        self.nav_buttons["stats"].clicked.connect(self._show_stats)

        self.setup_screen.start_session_requested.connect(self._start_session)
        self.end_screen.new_session_requested.connect(self._new_session)

        self.pill.exit_requested.connect(self._emergency_exit)
        self.pill.stats_requested.connect(
            lambda: self.stats_popover.refresh_and_open(self.pill))
        self.pill.notes_requested.connect(
            lambda: self.notes_popover.refresh_and_open(self.pill))

        self.session_manager.session_ended.connect(self._on_session_ended)

    # ---- navigation

    def _show_history(self):
        self.history_screen.refresh()
        self.stack.setCurrentWidget(self.history_screen)

    def _show_stats(self):
        self.stats_screen.refresh()
        self.stack.setCurrentWidget(self.stats_screen)

    def _toggle_theme(self):
        new_mode = "dark" if mode() == "light" else "light"
        apply_theme(QApplication.instance(), new_mode)
        self.db_manager.set_setting("theme", new_mode)
        self.theme_btn.setText("Dark" if new_mode == "light" else "Light")
        self.setup_screen.refresh_apps()  # re-tint running indicators

    # ---- session lifecycle

    def _start_session(self, name: str, minutes: int, apps: list,
                       strict: bool = False):
        if self.session_manager.current_state != SessionState.IDLE:
            self.session_manager.reset()
        if not self.session_manager.setup_session(name, minutes, apps):
            QMessageBox.critical(self, "Error", "Could not set up the session.")
            return
        if not self.session_manager.start_session():
            QMessageBox.critical(self, "Error", "Could not start the session.")
            self.session_manager.reset()
            return
        self.allow_close = False
        self.pill.start_display(strict=strict)
        self.showMinimized()

    def _emergency_exit(self):
        self.session_manager.end_session(emergency_exit=True)

    def _on_session_ended(self, session_id: int, emergency_exit: bool):
        self.allow_close = True
        for w in (self.pill, self.stats_popover, self.notes_popover):
            w.hide()
        self.setWindowState(Qt.WindowState.WindowNoState)
        self.showNormal()
        self.raise_()
        self.activateWindow()
        self.end_screen.show_results(session_id, emergency_exit)
        self.stack.setCurrentWidget(self.end_screen)

    def _new_session(self):
        self.session_manager.reset()
        self.setup_screen.reset_form()
        self.nav_buttons["focus"].setChecked(True)
        self.stack.setCurrentWidget(self.setup_screen)

    # ---- close guard

    def closeEvent(self, event: QCloseEvent):
        if not self.allow_close and self.session_manager.is_session_active():
            QMessageBox.warning(
                self, "Session active",
                "A focus session is running. End it from the floating "
                "timer before closing.",
            )
            event.ignore()
            return
        self.session_manager.reset()
        self.db_manager.close()
        event.accept()
