"""
Main Window - Lock In Application
Contains all UI screens and manages navigation
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QLabel, QLineEdit, QMessageBox,
    QListWidget, QListWidgetItem, QScrollArea, QGridLayout,
    QDialog, QDialogButtonBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QCloseEvent

from ui.widgets import (
    ModernButton, TimerDisplay, AppListWidget,
    SessionInfoCard, ProgressCard, TimePickerWidget,
    MotivationalQuote
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
        self._setup_ui()

    def _setup_ui(self):
        """Setup UI components"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)

        # Title
        title = QLabel("Lock In - Start a Focus Session")
        title.setFont(QFont("Segoe UI", 32, QFont.Weight.Bold))
        title.setStyleSheet("color: #e2e8f0;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Session name
        name_label = QLabel("Session Name:")
        name_label.setStyleSheet("color: #94a3b8; font-size: 14px;")
        layout.addWidget(name_label)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., Deep Work Session, Study Time, etc.")
        self.name_input.setStyleSheet("""
            QLineEdit {
                background-color: #1e293b;
                color: #e2e8f0;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #3b82f6;
            }
        """)
        layout.addWidget(self.name_input)

        # Duration picker
        duration_label = QLabel("Session Duration:")
        duration_label.setStyleSheet("color: #94a3b8; font-size: 14px;")
        layout.addWidget(duration_label)

        self.time_picker = TimePickerWidget()
        layout.addWidget(self.time_picker)

        # App selection
        apps_label = QLabel("Select Apps to Whitelist:")
        apps_label.setStyleSheet("color: #94a3b8; font-size: 14px;")
        layout.addWidget(apps_label)

        # Running apps list and whitelist side by side
        apps_layout = QHBoxLayout()

        # Running apps column
        running_layout = QVBoxLayout()
        running_title = QLabel("Running Apps")
        running_title.setStyleSheet("color: #e2e8f0; font-size: 13px; font-weight: bold;")
        running_layout.addWidget(running_title)

        self.running_apps_list = QListWidget()
        self.running_apps_list.setStyleSheet("""
            QListWidget {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
                color: #e2e8f0;
                padding: 8px;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 4px;
            }
            QListWidget::item:hover {
                background-color: #334155;
            }
        """)
        running_layout.addWidget(self.running_apps_list)

        add_btn = ModernButton("Add to Whitelist →")
        add_btn.clicked.connect(self._add_to_whitelist)
        running_layout.addWidget(add_btn)

        apps_layout.addLayout(running_layout)

        # Whitelisted apps column
        self.whitelist_widget = AppListWidget()
        self.whitelist_widget.app_removed.connect(self._on_app_removed)
        apps_layout.addWidget(self.whitelist_widget)

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

    def _refresh_running_apps(self):
        """Refresh list of running applications"""
        self.running_apps_list.clear()

        running_apps = self.session_manager.app_blocker.get_running_apps()
        for app in running_apps:
            item = QListWidgetItem(app['name'])
            item.setData(Qt.ItemDataRole.UserRole, app)
            self.running_apps_list.addItem(item)

    def _add_to_whitelist(self):
        """Add selected app to whitelist"""
        current_item = self.running_apps_list.currentItem()
        if current_item:
            app_data = current_item.data(Qt.ItemDataRole.UserRole)
            self.whitelist_widget.add_app(app_data['name'], app_data['path'])

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
            QMessageBox.warning(self, "Invalid Duration", "Please set a duration greater than 0.")
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
        self.time_picker.set_time(1, 0)
        self.whitelist_widget.clear_apps()
        self._refresh_running_apps()


class LockInScreen(QWidget):
    """Screen shown during active focus session"""

    emergency_exit_requested = pyqtSignal()

    def __init__(self, session_manager: SessionManager, parent=None):
        super().__init__(parent)
        self.session_manager = session_manager
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Setup UI components"""
        layout = QVBoxLayout(self)
        layout.setSpacing(30)
        layout.setContentsMargins(40, 40, 40, 40)

        # Session name
        self.session_name_label = QLabel()
        self.session_name_label.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        self.session_name_label.setStyleSheet("color: #e2e8f0;")
        self.session_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.session_name_label)

        # Timer display
        self.timer_display = TimerDisplay()
        layout.addWidget(self.timer_display)

        # Progress bar
        self.progress_card = ProgressCard("Session Progress")
        layout.addWidget(self.progress_card)

        # Stats cards
        stats_layout = QHBoxLayout()

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
        exit_btn.setMaximumWidth(200)
        exit_btn.setFont(QFont("Segoe UI", 10))

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

        # Initial update
        self._update_display(0, session_info['duration'])

    def _request_emergency_exit(self):
        """Request emergency exit"""
        reply = QMessageBox.warning(
            self, "Emergency Exit",
            "Are you sure you want to exit early? This will end your focus session.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
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
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)

        # Title
        self.title_label = QLabel("Session Complete!")
        self.title_label.setFont(QFont("Segoe UI", 32, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: #10b981;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)

        # Session name
        self.session_name_label = QLabel()
        self.session_name_label.setFont(QFont("Segoe UI", 18))
        self.session_name_label.setStyleSheet("color: #94a3b8;")
        self.session_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.session_name_label)

        # Stats grid
        stats_layout = QGridLayout()
        stats_layout.setSpacing(15)

        self.time_card = SessionInfoCard("Time Locked In", "0m")
        stats_layout.addWidget(self.time_card, 0, 0)

        self.duration_card = SessionInfoCard("Planned Duration", "0m")
        stats_layout.addWidget(self.duration_card, 0, 1)

        self.blocked_card = SessionInfoCard("Apps Blocked", "0")
        stats_layout.addWidget(self.blocked_card, 1, 0)

        self.completion_card = SessionInfoCard("Completion", "0%")
        stats_layout.addWidget(self.completion_card, 1, 1)

        layout.addLayout(stats_layout)

        # Comparison section
        self.comparison_label = QLabel()
        self.comparison_label.setWordWrap(True)
        self.comparison_label.setStyleSheet("""
            QLabel {
                color: #94a3b8;
                font-size: 14px;
                padding: 20px;
                background-color: #1e293b;
                border-radius: 8px;
            }
        """)
        layout.addWidget(self.comparison_label)

        layout.addStretch()

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        view_stats_btn = ModernButton("View Statistics")
        view_stats_btn.clicked.connect(self.view_stats_requested.emit)
        button_layout.addWidget(view_stats_btn)

        new_session_btn = ModernButton("Start New Session", primary=True)
        new_session_btn.clicked.connect(self.new_session_requested.emit)
        button_layout.addWidget(new_session_btn)

        layout.addLayout(button_layout)

    def show_results(self, session_id: int, emergency_exit: bool):
        """Display session results"""
        if emergency_exit:
            self.title_label.setText("Session Ended Early")
            self.title_label.setStyleSheet("color: #ef4444;")
        else:
            self.title_label.setText("Session Complete!")
            self.title_label.setStyleSheet("color: #10b981;")

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
                comp_text = f"🎉 You locked in {comparison['time_difference_formatted']} longer than last time!"
            else:
                comp_text = f"Last session was {comparison['time_difference_formatted']} longer. Keep pushing!"
        else:
            comp_text = "This is your first session. Great start! Keep building the habit."

        self.comparison_label.setText(comp_text)


class MainWindow(QMainWindow):
    """Main application window"""

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
        self.setMinimumSize(1000, 700)

        # Apply dark theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0f172a;
            }
            QWidget {
                background-color: #0f172a;
                color: #e2e8f0;
            }
        """)

        # Stack widget for different screens
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Create screens
        self.setup_screen = SessionSetupScreen(self.session_manager)
        self.lockin_screen = LockInScreen(self.session_manager)
        self.end_screen = SessionEndScreen(self.session_manager, self.stats_tracker)

        # Add screens to stack
        self.stack.addWidget(self.setup_screen)
        self.stack.addWidget(self.lockin_screen)
        self.stack.addWidget(self.end_screen)

        # Start with setup screen
        self.stack.setCurrentWidget(self.setup_screen)

    def _connect_signals(self):
        """Connect signals between components"""
        # Setup screen signals
        self.setup_screen.start_session_requested.connect(self._start_session)

        # Lock-in screen signals
        self.lockin_screen.emergency_exit_requested.connect(self._emergency_exit)

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

        # Switch to lock-in screen
        self.lockin_screen.start_display()
        self.stack.setCurrentWidget(self.lockin_screen)

        # Prevent closing
        self.allow_close = False

    def _emergency_exit(self):
        """Handle emergency exit"""
        self.allow_close = True
        self.session_manager.end_session(emergency_exit=True)

    def _new_session(self):
        """Start a new session"""
        self.setup_screen.reset_form()
        self.stack.setCurrentWidget(self.setup_screen)

    def _on_session_started(self, session_id: int):
        """Handle session started"""
        print(f"Session {session_id} started")

    def _on_session_ended(self, session_id: int, emergency_exit: bool):
        """Handle session ended"""
        self.allow_close = True

        # Show end screen
        self.end_screen.show_results(session_id, emergency_exit)
        self.stack.setCurrentWidget(self.end_screen)

    def closeEvent(self, event: QCloseEvent):
        """Handle window close event"""
        if not self.allow_close and self.session_manager.is_session_active():
            reply = QMessageBox.warning(
                self, "Session Active",
                "A focus session is currently active. Use Emergency Exit to end it first.",
                QMessageBox.StandardButton.Ok
            )
            event.ignore()
        else:
            # Cleanup
            self.session_manager.reset()
            self.db_manager.close()
            event.accept()
