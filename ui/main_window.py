"""
Main Window - Lock In Application
Contains all UI screens and manages navigation
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QLabel, QLineEdit, QMessageBox,
    QListWidget, QListWidgetItem, QScrollArea, QGridLayout,
    QDialog, QDialogButtonBox, QSizeGrip, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import QFont, QCloseEvent, QColor, QScreen

from ui.widgets import (
    ModernButton, TimerDisplay, AppListWidget,
    SessionInfoCard, ProgressCard, TimePickerWidget,
    MotivationalQuote, ModernCard, VerticalSidebarLockIn,
    QuickStatsPopup, SessionNotesPopup, COLORS
)
from core.session_manager import SessionManager, SessionState
from core.stats_tracker import StatsTracker
from database.db_manager import DatabaseManager


class SessionSetupScreen(QWidget):
    """Screen for setting up a new focus session"""

    start_session_requested = pyqtSignal(str, int, list)  # name, duration_mins, apps

    def __init__(self, session_manager: SessionManager, parent=None):
        super().__init__(parent)
        self.session_manager = session_manager
        self.selected_apps = []
        self.all_apps = []  # Store all apps for filtering
        self._setup_ui()

    def _setup_ui(self):
        """Setup UI components"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)

        # Title
        title = QLabel("Lock In - Start a Focus Session")
        title.setFont(QFont("Segoe UI", 32, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Session name
        name_label = QLabel("Session Name:")
        name_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 14px; font-weight: 600;")
        layout.addWidget(name_label)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., Deep Work Session, Study Time, etc.")
        self.name_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLORS['bg_tertiary']};
                color: {COLORS['text_primary']};
                border: 2px solid {COLORS['border']};
                border-radius: 6px;
                padding: 12px;
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border-color: {COLORS['border_focus']};
            }}
        """)
        layout.addWidget(self.name_input)

        # Duration picker
        duration_label = QLabel("Session Duration:")
        duration_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 14px; font-weight: 600;")
        layout.addWidget(duration_label)

        self.time_picker = TimePickerWidget()
        layout.addWidget(self.time_picker)

        # App selection with PREMIUM CARD DESIGN
        apps_label = QLabel("Select Apps to Whitelist:")
        apps_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 16px; font-weight: 700; margin-top: 12px;")
        layout.addWidget(apps_label)

        # Running apps list and whitelist side by side - BIGGER LAYOUT
        apps_layout = QHBoxLayout()
        apps_layout.setSpacing(20)

        # Running apps column - Takes 60% of space
        running_layout = QVBoxLayout()
        running_layout.setSpacing(12)

        running_title = QLabel("Available Apps")
        running_title.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 15px; font-weight: 700; background: transparent;")
        running_layout.addWidget(running_title)

        # Search box with MODERN DESIGN
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍 Search apps...")
        self.search_box.setMinimumHeight(40)
        self.search_box.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLORS['bg_secondary']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border: 2px solid {COLORS['accent_primary']};
            }}
        """)
        self.search_box.textChanged.connect(self._filter_apps)
        running_layout.addWidget(self.search_box)

        # Available apps list - PREMIUM CARD DESIGN - INCREASED HEIGHT
        self.running_apps_list = QListWidget()
        self.running_apps_list.setMinimumHeight(550)  # EVEN BIGGER to prevent overlap
        self.running_apps_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
                color: {COLORS['text_primary']};
                padding: 12px;
                font-size: 14px;
            }}
            QListWidget::item {{
                padding: 14px;
                border-radius: 8px;
                margin: 4px 0;
                min-height: 40px;
            }}
            QListWidget::item:hover {{
                background-color: {COLORS['bg_tertiary']};
                border-left: 4px solid {COLORS['accent_primary']};
            }}
            QListWidget::item:selected {{
                background-color: {COLORS['accent_primary']};
                color: {COLORS['text_primary']};
            }}
        """)
        self.running_apps_list.setIconSize(QSize(28, 28))
        running_layout.addWidget(self.running_apps_list, 1)  # Give it stretch factor

        # Add spacing before button to prevent overlap
        running_layout.addSpacing(15)

        add_btn = ModernButton("Add to Whitelist →", primary=False)
        add_btn.clicked.connect(self._add_to_whitelist)
        running_layout.addWidget(add_btn, 0)  # Don't stretch the button

        apps_layout.addLayout(running_layout, 60)  # 60% of space

        # Whitelisted apps column - Takes 40% of space
        self.whitelist_widget = AppListWidget()
        self.whitelist_widget.app_removed.connect(self._on_app_removed)
        self.whitelist_widget.list_widget.setIconSize(QSize(28, 28))
        self.whitelist_widget.list_widget.setMinimumHeight(550)  # Match available apps height
        apps_layout.addWidget(self.whitelist_widget, 40)  # 40% of space

        layout.addLayout(apps_layout)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        refresh_btn = ModernButton("Refresh Apps")
        refresh_btn.clicked.connect(self._refresh_running_apps)
        button_layout.addWidget(refresh_btn)

        self.start_btn = ModernButton("Start Session", primary=True)
        self.start_btn.clicked.connect(self._start_session)
        button_layout.addWidget(self.start_btn)

        layout.addLayout(button_layout)

        # Initial load of running apps
        self._refresh_running_apps()

    def _filter_apps(self, search_text: str):
        """Filter apps based on search text"""
        search_lower = search_text.lower()
        self.running_apps_list.clear()

        for app in self.all_apps:
            if search_lower in app['display_name'].lower():
                item = QListWidgetItem(app['display_name'])
                item.setData(Qt.ItemDataRole.UserRole, app)
                if app.get('icon'):
                    item.setIcon(app['icon'])
                self.running_apps_list.addItem(item)

    def _refresh_running_apps(self):
        """Refresh list of ALL available applications (running + installed) - RUNNING APPS FIRST"""
        self.running_apps_list.clear()
        self.all_apps.clear()

        # Get ALL installed applications + currently running apps
        all_installed = self.session_manager.app_blocker.get_all_installed_apps()
        running_apps = self.session_manager.app_blocker.get_running_apps()

        # Create a set of running app names for quick lookup
        running_names = {app['display_name'] for app in running_apps}

        # Sort: running apps first (priority 0), then installed apps (priority 1)
        # Within each group, sort alphabetically by display name
        all_apps = sorted(all_installed, key=lambda x: (
            0 if x['display_name'] in running_names else 1,
            x['display_name'].lower()
        ))

        self.all_apps = all_apps

        for app in all_apps:
            is_running = app['display_name'] in running_names

            # Add visual indicator for running apps
            display_text = f"● {app['display_name']}" if is_running else app['display_name']

            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, app)

            # Add icon if available
            if app.get('icon'):
                item.setIcon(app['icon'])

            # Style running apps differently
            if is_running:
                item.setForeground(QColor(COLORS['accent_primary']))

            self.running_apps_list.addItem(item)

    def _add_to_whitelist(self):
        """Add selected app to whitelist"""
        current_item = self.running_apps_list.currentItem()
        if current_item:
            app_data = current_item.data(Qt.ItemDataRole.UserRole)
            self.whitelist_widget.add_app(
                app_data['display_name'],
                app_data['path'],
                app_data.get('icon')
            )

    def _on_app_removed(self, app_name: str):
        """Handle app removed from whitelist"""
        pass  # Could refresh UI if needed

    def _start_session(self):
        """Start the session"""
        session_name = self.name_input.text().strip()
        if not session_name:
            QMessageBox.warning(self, "Invalid Input", "Please enter a session name.")
            return

        duration_mins = self.time_picker.get_total_minutes()
        if duration_mins <= 0:
            QMessageBox.warning(self, "Invalid Duration", "Please set a duration greater than 0 minutes.")
            return

        whitelisted_apps = self.whitelist_widget.get_apps()
        if not whitelisted_apps:
            reply = QMessageBox.question(
                self, "No Whitelisted Apps",
                "You haven't whitelisted any apps. This will block ALL applications. Continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return

        self.start_session_requested.emit(session_name, duration_mins, whitelisted_apps)

    def reset_form(self):
        """Reset form to default state"""
        self.name_input.clear()
        self.time_picker.set_time(1, 30)
        self.whitelist_widget.clear_apps()
        self._refresh_running_apps()


class LockInScreen(QWidget):
    """Screen shown during active focus session - transparent and always on top"""

    emergency_exit_requested = pyqtSignal()

    def __init__(self, session_manager: SessionManager, parent=None):
        super().__init__(parent)
        self.session_manager = session_manager
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Setup UI components"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # Session name
        self.session_name_label = QLabel()
        self.session_name_label.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        self.session_name_label.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        self.session_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.session_name_label)

        # Timer display
        self.timer_display = TimerDisplay()
        layout.addWidget(self.timer_display)

        # Progress bar card
        self.progress_card = ProgressCard("Session Progress")
        layout.addWidget(self.progress_card)

        # Stats cards in a grid
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(15)

        self.elapsed_card = SessionInfoCard("Time Elapsed", "00:00")
        stats_layout.addWidget(self.elapsed_card)

        self.remaining_card = SessionInfoCard("Time Remaining", "00:00")
        stats_layout.addWidget(self.remaining_card)

        self.blocked_card = SessionInfoCard("Apps Blocked", "0")
        stats_layout.addWidget(self.blocked_card)

        layout.addLayout(stats_layout)

        # Motivational quote
        self.quote_widget = MotivationalQuote()
        layout.addWidget(self.quote_widget)

        layout.addStretch()

        # Emergency exit button
        exit_btn = ModernButton("Emergency Exit", danger=True)
        exit_btn.clicked.connect(self._request_emergency_exit)
        exit_btn.setMaximumWidth(180)
        exit_btn.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))

        exit_layout = QHBoxLayout()
        exit_layout.addStretch()
        exit_layout.addWidget(exit_btn)
        exit_layout.addStretch()

        layout.addLayout(exit_layout)

    def _connect_signals(self):
        """Connect session manager signals"""
        self.session_manager.session_updated.connect(self._update_display)
        self.session_manager.app_blocked.connect(self._on_app_blocked)

    def _update_display(self, elapsed_seconds: int, remaining_seconds: int):
        """Update display with current session info"""
        # Update timer
        hours = remaining_seconds // 3600
        minutes = (remaining_seconds % 3600) // 60
        seconds = remaining_seconds % 60
        self.timer_display.set_time(hours, minutes, seconds)

        # Update cards
        elapsed_formatted = SessionManager.format_time(elapsed_seconds)
        remaining_formatted = SessionManager.format_time(remaining_seconds)

        self.elapsed_card.set_value(elapsed_formatted)
        self.remaining_card.set_value(remaining_formatted)

        # Update progress
        progress = int(self.session_manager.get_progress_percentage())
        self.progress_card.set_progress(progress)

    def _on_app_blocked(self, app_name: str, total_blocked: int):
        """Handle app blocked event"""
        self.blocked_card.set_value(str(total_blocked))

    def start_display(self):
        """Initialize display for session start"""
        session_info = self.session_manager.get_session_info()
        self.session_name_label.setText(session_info['name'])
        self.blocked_card.set_value("0")

        # Initial update with starting values
        self._update_display(0, session_info['duration'])

    def _request_emergency_exit(self):
        """Request emergency exit"""
        reply = QMessageBox.warning(
            self, "Emergency Exit",
            "Are you sure you want to exit early?\n\nThis will end your focus session and restore all applications.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.emergency_exit_requested.emit()


class SessionEndScreen(QWidget):
    """Screen shown after session ends"""

    new_session_requested = pyqtSignal()
    view_stats_requested = pyqtSignal()

    def __init__(self, session_manager: SessionManager,
                 stats_tracker: StatsTracker, parent=None):
        super().__init__(parent)
        self.session_manager = session_manager
        self.stats_tracker = stats_tracker
        self._setup_ui()

    def _setup_ui(self):
        """Setup UI components"""
        layout = QVBoxLayout(self)
        layout.setSpacing(25)
        layout.setContentsMargins(40, 40, 40, 40)

        # Title
        self.title_label = QLabel("Session Complete!")
        self.title_label.setFont(QFont("Segoe UI", 36, QFont.Weight.Bold))
        self.title_label.setStyleSheet(f"color: {COLORS['accent_primary']}; background: transparent;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)

        # Session name
        self.session_name_label = QLabel()
        self.session_name_label.setFont(QFont("Segoe UI", 18))
        self.session_name_label.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")
        self.session_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.session_name_label)

        # Stats grid
        stats_layout = QGridLayout()
        stats_layout.setSpacing(20)

        self.time_card = SessionInfoCard("Time Locked In", "0m")
        stats_layout.addWidget(self.time_card, 0, 0)

        self.duration_card = SessionInfoCard("Planned Duration", "0m")
        stats_layout.addWidget(self.duration_card, 0, 1)

        self.blocked_card = SessionInfoCard("Apps Blocked", "0")
        stats_layout.addWidget(self.blocked_card, 1, 0)

        self.completion_card = SessionInfoCard("Completion", "0%")
        stats_layout.addWidget(self.completion_card, 1, 1)

        layout.addLayout(stats_layout)

        # Comparison section - PREMIUM CARD DESIGN with shadow
        comparison_card = ModernCard()
        comparison_layout = QVBoxLayout(comparison_card)
        comparison_layout.setContentsMargins(30, 30, 30, 30)

        self.comparison_label = QLabel()
        self.comparison_label.setWordWrap(True)
        self.comparison_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.comparison_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_secondary']};
                font-size: 15px;
                background: transparent;
                line-height: 1.6;
            }}
        """)
        comparison_layout.addWidget(self.comparison_label)

        layout.addWidget(comparison_card)

        # Session notes section - PREMIUM CARD DESIGN
        self.notes_card = ModernCard()
        notes_layout = QVBoxLayout(self.notes_card)
        notes_layout.setContentsMargins(30, 30, 30, 30)

        notes_title = QLabel("📝 Session Notes")
        notes_title.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_primary']};
                font-size: 18px;
                font-weight: 700;
                background: transparent;
                margin-bottom: 10px;
            }}
        """)
        notes_layout.addWidget(notes_title)

        self.notes_label = QLabel("No notes for this session.")
        self.notes_label.setWordWrap(True)
        self.notes_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.notes_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_secondary']};
                font-size: 14px;
                background: transparent;
                line-height: 1.5;
                padding: 10px;
            }}
        """)
        notes_layout.addWidget(self.notes_label)

        layout.addWidget(self.notes_card)
        self.notes_card.hide()  # Initially hidden, show only if notes exist

        layout.addStretch()

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        new_session_btn = ModernButton("Start New Session", primary=True)
        new_session_btn.clicked.connect(self.new_session_requested.emit)
        button_layout.addWidget(new_session_btn)

        layout.addLayout(button_layout)

    def show_results(self, session_id: int, emergency_exit: bool):
        """Display session results"""
        if emergency_exit:
            self.title_label.setText("Session Ended Early")
            self.title_label.setStyleSheet(f"color: {COLORS['danger']}; background: transparent;")
        else:
            self.title_label.setText("Session Complete!")
            self.title_label.setStyleSheet(f"color: {COLORS['accent_primary']}; background: transparent;")

        # Get session details
        session = self.stats_tracker.get_session_details(session_id)
        if not session:
            return

        self.session_name_label.setText(session['name'])

        # Update cards
        self.time_card.set_value(session['time_locked_in_formatted'])
        self.duration_card.set_value(session['duration_formatted'])
        self.blocked_card.set_value(str(session['apps_blocked_count']))
        self.completion_card.set_value(f"{session['completion_percentage']:.0f}%")

        # Show comparison
        comparison = self.stats_tracker.compare_to_previous(session_id)
        if comparison.get('has_previous'):
            if comparison['time_improved']:
                comp_text = f"🎉 You locked in {comparison['time_difference_formatted']} longer than last time!\n\nKeep up the great work!"
            else:
                comp_text = f"Last session was {comparison['time_difference_formatted']} longer.\n\nYou'll get it next time!"
        else:
            comp_text = "This is your first session!\n\nGreat start. Keep building the habit."

        self.comparison_label.setText(comp_text)

        # Show session notes if they exist
        notes = session.get('notes', '')
        if notes and notes.strip():
            self.notes_label.setText(notes)
            self.notes_card.show()
        else:
            self.notes_card.hide()


class MainWindow(QMainWindow):
    """Main application window with resizable, transparent lock-in screen"""

    def __init__(self):
        super().__init__()
        self.db_manager = DatabaseManager()
        self.session_manager = SessionManager(self.db_manager)
        self.stats_tracker = StatsTracker(self.db_manager)

        self._setup_ui()
        self._connect_signals()

        # Prevent closing during active session
        self.allow_close = True

    def _setup_ui(self):
        """Setup main window UI"""
        self.setWindowTitle("Lock In - Focus & Productivity")

       # Fixed window size to fit properly on screen
        screen = QApplication.primaryScreen()
        if screen:
            screen_geometry = screen.availableGeometry()
            
            # Maximum dimensions
            max_width = 1200
            max_height = 750
            
            # Use max size but don't exceed screen
            width = min(max_width, screen_geometry.width() - 100)
            height = min(max_height, screen_geometry.height() - 100)

            # Center the window
            x = (screen_geometry.width() - width) // 2
            y = (screen_geometry.height() - height) // 2

            self.setGeometry(x, y, width, height)
        else:
            # Fallback if screen detection fails
            self.setMinimumSize(1100, 750)
            self.resize(1400, 900)

        # Apply dark theme
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {COLORS['bg_primary']};
            }}
            QWidget {{
                background-color: {COLORS['bg_primary']};
                color: {COLORS['text_primary']};
            }}
        """)

        # Stack widget for different screens
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Create screens
        self.setup_screen = SessionSetupScreen(self.session_manager)
        self.end_screen = SessionEndScreen(self.session_manager, self.stats_tracker)

        # Create vertical sidebar (separate window, not in stack)
        self.sidebar = VerticalSidebarLockIn(self.session_manager)

        # Create popup widgets
        self.stats_popup = QuickStatsPopup(self.session_manager, self.stats_tracker)
        self.notes_popup = SessionNotesPopup(self.session_manager)

        # Add screens to stack (sidebar is NOT in stack - it's its own window)
        self.stack.addWidget(self.setup_screen)
        self.stack.addWidget(self.end_screen)

        # Start with setup screen
        self.stack.setCurrentWidget(self.setup_screen)

    def _connect_signals(self):
        """Connect signals between components"""
        # Setup screen signals
        self.setup_screen.start_session_requested.connect(self._start_session)

        # Vertical sidebar signals
        self.sidebar.emergency_exit_requested.connect(self._emergency_exit)
        self.sidebar.stats_button.clicked.connect(self._show_stats_popup)
        self.sidebar.notes_button.clicked.connect(self._show_notes_popup)

        # Popup signals
        self.notes_popup.notes_saved.connect(self._on_notes_saved)

        # End screen signals
        self.end_screen.new_session_requested.connect(self._new_session)

        # Session manager signals
        self.session_manager.session_started.connect(self._on_session_started)
        self.session_manager.session_ended.connect(self._on_session_ended)

    def _start_session(self, name: str, duration_mins: int, apps: list):
        """Start a new focus session"""
        # Setup session
        success = self.session_manager.setup_session(
            name=name,
            duration_minutes=duration_mins,
            whitelisted_apps=apps
        )

        if not success:
            QMessageBox.critical(self, "Error", "Failed to setup session.")
            return

        # Start session
        success = self.session_manager.start_session()
        if not success:
            QMessageBox.critical(self, "Error", "Failed to start session.")
            return

        # Show the vertical sidebar (NEW: taskbar-style lock-in screen)
        self.sidebar.start_display()

        # Keep main window visible but user can minimize it
        # The sidebar will stay on top regardless
        self.setWindowState(Qt.WindowState.WindowMinimized)  # Minimize main window

        # Prevent closing
        self.allow_close = False

    def _emergency_exit(self):
        """Handle emergency exit"""
        self.allow_close = True

        # Hide the sidebar
        self.sidebar.hide()

        # Restore main window
        self.setWindowState(Qt.WindowState.WindowNoState)  # Restore from minimized
        self.showNormal()
        self.activateWindow()

        self.session_manager.end_session(emergency_exit=True)

    def _new_session(self):
        """Start a new session"""
        self.setup_screen.reset_form()
        self.stack.setCurrentWidget(self.setup_screen)

        # Hide sidebar if visible
        self.sidebar.hide()

        # Restore main window
        self.setWindowState(Qt.WindowState.WindowNoState)
        self.showNormal()
        self.activateWindow()

    def _on_session_started(self, session_id: int):
        """Handle session started"""
        print(f"Session {session_id} started")

    def _on_session_ended(self, session_id: int, emergency_exit: bool):
        """Handle session ended"""
        self.allow_close = True

        # Hide the sidebar
        self.sidebar.hide()

        # Restore main window
        self.setWindowState(Qt.WindowState.WindowNoState)
        self.showNormal()
        self.activateWindow()

        # Show end screen
        self.end_screen.show_results(session_id, emergency_exit)
        self.stack.setCurrentWidget(self.end_screen)

    def _show_stats_popup(self):
        """Show the quick stats popup"""
        self.stats_popup.show_stats()

    def _show_notes_popup(self):
        """Show the session notes popup"""
        self.notes_popup.show_notes()

    def _on_notes_saved(self, notes: str):
        """Handle notes saved"""
        print(f"Session notes saved: {notes[:50]}...")  # Log first 50 chars

    def closeEvent(self, event: QCloseEvent):
        """Handle window close event"""
        if not self.allow_close and self.session_manager.is_session_active():
            reply = QMessageBox.warning(
                self, "Session Active",
                "A focus session is currently active.\n\nUse Emergency Exit to end it first, or the session will continue in the background.",
                QMessageBox.StandardButton.Ok
            )
            event.ignore()
        else:
            # Cleanup
            self.session_manager.reset()
            self.db_manager.close()
            event.accept()
