"""
Custom UI Widgets for Lock In Application
Premium, modern UI design with card-based system
"""

from PyQt6.QtWidgets import (
    QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QSpinBox, QLineEdit,
    QProgressBar, QFrame, QScrollArea, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import QFont, QPalette, QColor, QIcon, QPixmap
from typing import List, Dict
import sys

# Modern Premium Color Scheme - LIGHT MODE
COLORS = {
    'bg_primary': '#ffffff',      # Clean white background
    'bg_secondary': '#f8f9fa',    # Light gray card/elevated background
    'bg_tertiary': '#f3f4f6',     # Slightly darker for input fields
    'accent_primary': '#10b981',  # Emerald green accent (keep this!)
    'accent_hover': '#059669',    # Darker green on hover
    'accent_pressed': '#047857',  # Even darker green when pressed
    'danger': '#ef4444',          # Red for danger/exit
    'danger_hover': '#dc2626',
    'danger_pressed': '#b91c1c',
    'text_primary': '#1a1a1a',    # Dark text (was white)
    'text_secondary': '#4b5563',  # Dark gray text (was light gray)
    'text_muted': '#6b7280',      # Muted dark gray (was light)
    'border': '#10b981',          # Emerald green borders (keep)
    'border_focus': '#10b981',    # Emerald green for focused borders (keep)
    'border_subtle': '#e5e7eb',   # Light subtle borders (was dark)
}


class ModernCard(QFrame):
    """Base card widget with clean, minimal design - no green borders"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_style()

    def _setup_style(self):
        """Setup modern card styling - SIMPLIFIED, no green borders"""
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['border_subtle']};
                border-radius: 12px;
            }}
        """)

        # Add subtle shadow effect for depth
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)


class ModernButton(QPushButton):
    """Modern styled button with premium design"""

    def __init__(self, text: str, primary: bool = False, danger: bool = False):
        super().__init__(text)
        self.primary = primary
        self.danger = danger
        self._setup_style()

    def _setup_style(self):
        """Setup button styling"""
        if self.primary:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['accent_primary']};
                    color: {COLORS['text_primary']};
                    border: none;
                    border-radius: 8px;
                    padding: 14px 28px;
                    font-size: 15px;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['accent_hover']};
                }}
                QPushButton:pressed {{
                    background-color: {COLORS['accent_pressed']};
                }}
                QPushButton:disabled {{
                    background-color: {COLORS['bg_tertiary']};
                    color: {COLORS['text_muted']};
                }}
            """)
        elif self.danger:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['danger']};
                    color: {COLORS['text_primary']};
                    border: none;
                    border-radius: 8px;
                    padding: 14px 28px;
                    font-size: 15px;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['danger_hover']};
                }}
                QPushButton:pressed {{
                    background-color: {COLORS['danger_pressed']};
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['bg_tertiary']};
                    color: {COLORS['text_primary']};
                    border: 1px solid {COLORS['border_subtle']};
                    border-radius: 8px;
                    padding: 12px 24px;
                    font-size: 14px;
                    font-weight: 500;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['bg_secondary']};
                    border-color: {COLORS['border']};
                }}
                QPushButton:pressed {{
                    background-color: {COLORS['bg_primary']};
                }}
            """)


class TimerDisplay(QLabel):
    """Large premium timer display"""

    def __init__(self, parent=None):
        super().__init__("00:00:00", parent)
        self._setup_style()

    def _setup_style(self):
        """Setup timer styling"""
        font = QFont("Segoe UI", 80, QFont.Weight.Bold)
        self.setFont(font)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['accent_primary']};
                padding: 30px;
                background: transparent;
            }}
        """)

    def set_time(self, hours: int, minutes: int, seconds: int):
        """Update timer display"""
        self.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")


class AppListWidget(QWidget):
    """Widget for displaying and managing whitelisted apps"""

    app_removed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.apps = []
        self._setup_ui()

    def _setup_ui(self):
        """Setup UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Title
        title = QLabel("Whitelisted Apps")
        title.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_primary']};
                font-size: 16px;
                font-weight: 700;
                padding: 12px;
                background: transparent;
            }}
        """)
        layout.addWidget(title)

        # List widget with premium styling
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet(f"""
            QListWidget {{
                background-color: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 12px;
                color: {COLORS['text_primary']};
                font-size: 14px;
            }}
            QListWidget::item {{
                padding: 12px;
                border-radius: 6px;
                margin: 3px 0;
                min-height: 40px;
            }}
            QListWidget::item:hover {{
                background-color: {COLORS['bg_tertiary']};
                border-left: 3px solid {COLORS['accent_primary']};
            }}
            QListWidget::item:selected {{
                background-color: {COLORS['accent_primary']};
                color: {COLORS['text_primary']};
            }}
        """)
        layout.addWidget(self.list_widget)

        # Remove button
        self.remove_btn = ModernButton("➖ Remove Selected")
        self.remove_btn.clicked.connect(self._remove_selected)
        layout.addWidget(self.remove_btn)

    def add_app(self, app_name: str, app_path: str = "", icon: QIcon = None):
        """Add an app to the list"""
        if app_name not in self.apps:
            self.apps.append(app_name)
            item = QListWidgetItem(app_name)
            item.setData(Qt.ItemDataRole.UserRole, app_name)
            if icon:
                item.setIcon(icon)
            self.list_widget.addItem(item)

    def _remove_selected(self):
        """Remove selected app from list"""
        current_item = self.list_widget.currentItem()
        if current_item:
            app_name = current_item.data(Qt.ItemDataRole.UserRole)
            row = self.list_widget.row(current_item)
            self.list_widget.takeItem(row)
            self.apps.remove(app_name)
            self.app_removed.emit(app_name)

    def get_apps(self) -> List[str]:
        """Get list of all apps"""
        return self.apps.copy()

    def clear_apps(self):
        """Clear all apps from list"""
        self.list_widget.clear()
        self.apps.clear()


class SessionInfoCard(ModernCard):
    """Premium card widget for displaying session information"""

    def __init__(self, title: str, value: str = "", parent=None):
        super().__init__(parent)
        self.title_label = None
        self.value_label = None
        self._setup_ui(title, value)

    def _setup_ui(self, title: str, value: str):
        """Setup UI"""
        self.setMinimumHeight(140)
        self.setMinimumWidth(180)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # Title
        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.title_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_secondary']};
                font-size: 12px;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 1px;
                background: transparent;
            }}
        """)
        layout.addWidget(self.title_label)

        # Value
        self.value_label = QLabel(value)
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.value_label.setWordWrap(True)
        self.value_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_primary']};
                font-size: 36px;
                font-weight: 700;
                background: transparent;
            }}
        """)
        layout.addWidget(self.value_label)
        layout.addStretch()

    def set_value(self, value: str):
        """Update card value"""
        self.value_label.setText(value)


class ProgressCard(ModernCard):
    """Premium card widget with large progress bar"""

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.progress_bar = None
        self.label = None
        self._setup_ui(title)

    def _setup_ui(self, title: str):
        """Setup UI"""
        self.setMinimumHeight(180)

        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # Title
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_secondary']};
                font-size: 12px;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 1px;
                background: transparent;
            }}
        """)
        layout.addWidget(title_label)

        # Progress bar - LARGER and more visible
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setMinimumHeight(28)
        self.progress_bar.setMaximumHeight(28)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                border-radius: 14px;
                background-color: {COLORS['bg_tertiary']};
            }}
            QProgressBar::chunk {{
                border-radius: 14px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['accent_primary']},
                    stop:1 {COLORS['accent_hover']});
            }}
        """)
        layout.addWidget(self.progress_bar)

        # Percentage label - LARGE and BOLD
        self.label = QLabel("0%")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_primary']};
                font-size: 42px;
                font-weight: 700;
                background: transparent;
                margin-top: 8px;
            }}
        """)
        layout.addWidget(self.label)

    def set_progress(self, value: int):
        """Set progress value (0-100)"""
        self.progress_bar.setValue(value)
        self.label.setText(f"{value}%")


class TimePickerWidget(QWidget):
    """Premium time picker with visible +/- buttons"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.hours_spin = None
        self.minutes_spin = None
        self._setup_ui()

    def _setup_ui(self):
        """Setup UI"""
        layout = QHBoxLayout(self)
        layout.setSpacing(20)

        # Hours
        hours_layout = QVBoxLayout()
        hours_label = QLabel("Hours")
        hours_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_secondary']};
                font-size: 13px;
                font-weight: 600;
                background: transparent;
            }}
        """)
        hours_layout.addWidget(hours_label)

        self.hours_spin = QSpinBox()
        self.hours_spin.setRange(0, 23)
        self.hours_spin.setValue(1)
        self.hours_spin.setMinimumWidth(100)
        self.hours_spin.setMinimumHeight(50)
        self.hours_spin.setMaximumHeight(50)
        self.hours_spin.setButtonSymbols(QSpinBox.ButtonSymbols.PlusMinus)  # Use +/- symbols
        self.hours_spin.setStyleSheet(f"""
            QSpinBox {{
                background-color: {COLORS['bg_secondary']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 20px;
                font-weight: 600;
            }}
            QSpinBox:focus {{
                border: 2px solid {COLORS['accent_primary']};
            }}
            QSpinBox::up-button {{
                subcontrol-origin: border;
                subcontrol-position: right;
                width: 30px;
                height: 23px;
                border-left: 1px solid {COLORS['border_subtle']};
                border-top-right-radius: 8px;
                background-color: {COLORS['bg_tertiary']};
                font-size: 18px;
                font-weight: bold;
            }}
            QSpinBox::up-button:hover {{
                background-color: {COLORS['accent_primary']};
                color: {COLORS['text_primary']};
            }}
            QSpinBox::up-button:pressed {{
                background-color: {COLORS['accent_pressed']};
            }}
            QSpinBox::down-button {{
                subcontrol-origin: border;
                subcontrol-position: left;
                width: 30px;
                height: 23px;
                border-right: 1px solid {COLORS['border_subtle']};
                border-top-left-radius: 8px;
                border-bottom-left-radius: 8px;
                background-color: {COLORS['bg_tertiary']};
                font-size: 18px;
                font-weight: bold;
            }}
            QSpinBox::down-button:hover {{
                background-color: {COLORS['accent_primary']};
                color: {COLORS['text_primary']};
            }}
            QSpinBox::down-button:pressed {{
                background-color: {COLORS['accent_pressed']};
            }}
        """)
        hours_layout.addWidget(self.hours_spin)
        layout.addLayout(hours_layout)

        # Separator
        separator = QLabel(":")
        separator.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['accent_primary']};
                font-size: 32px;
                font-weight: bold;
                padding: 22px 10px 0 10px;
                background: transparent;
            }}
        """)
        separator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(separator)

        # Minutes
        minutes_layout = QVBoxLayout()
        minutes_label = QLabel("Minutes")
        minutes_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_secondary']};
                font-size: 13px;
                font-weight: 600;
                background: transparent;
            }}
        """)
        minutes_layout.addWidget(minutes_label)

        self.minutes_spin = QSpinBox()
        self.minutes_spin.setRange(0, 59)
        self.minutes_spin.setValue(30)
        self.minutes_spin.setMinimumWidth(100)
        self.minutes_spin.setMinimumHeight(50)
        self.minutes_spin.setMaximumHeight(50)
        self.minutes_spin.setButtonSymbols(QSpinBox.ButtonSymbols.PlusMinus)  # Use +/- symbols
        self.minutes_spin.setStyleSheet(f"""
            QSpinBox {{
                background-color: {COLORS['bg_secondary']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 20px;
                font-weight: 600;
            }}
            QSpinBox:focus {{
                border: 2px solid {COLORS['accent_primary']};
            }}
            QSpinBox::up-button {{
                subcontrol-origin: border;
                subcontrol-position: right;
                width: 30px;
                height: 23px;
                border-left: 1px solid {COLORS['border_subtle']};
                border-top-right-radius: 8px;
                background-color: {COLORS['bg_tertiary']};
                font-size: 18px;
                font-weight: bold;
            }}
            QSpinBox::up-button:hover {{
                background-color: {COLORS['accent_primary']};
                color: {COLORS['text_primary']};
            }}
            QSpinBox::up-button:pressed {{
                background-color: {COLORS['accent_pressed']};
            }}
            QSpinBox::down-button {{
                subcontrol-origin: border;
                subcontrol-position: left;
                width: 30px;
                height: 23px;
                border-right: 1px solid {COLORS['border_subtle']};
                border-top-left-radius: 8px;
                border-bottom-left-radius: 8px;
                background-color: {COLORS['bg_tertiary']};
                font-size: 18px;
                font-weight: bold;
            }}
            QSpinBox::down-button:hover {{
                background-color: {COLORS['accent_primary']};
                color: {COLORS['text_primary']};
            }}
            QSpinBox::down-button:pressed {{
                background-color: {COLORS['accent_pressed']};
            }}
        """)
        minutes_layout.addWidget(self.minutes_spin)
        layout.addLayout(minutes_layout)

    def get_total_minutes(self) -> int:
        """Get total time in minutes"""
        return self.hours_spin.value() * 60 + self.minutes_spin.value()

    def set_time(self, hours: int, minutes: int):
        """Set time values"""
        self.hours_spin.setValue(hours)
        self.minutes_spin.setValue(minutes)


class VerticalSidebarLockIn(QWidget):
    """
    Vertical sidebar lock-in screen - taskbar style
    Modern, professional sidebar that docks to the right (or left) side of screen
    """

    emergency_exit_requested = pyqtSignal()

    def __init__(self, session_manager, parent=None):
        super().__init__(parent)
        self.session_manager = session_manager
        self.countdown_mode = True  # True = countdown, False = count-up
        self.position_right = True  # True = right side, False = left side
        self.minimized = False

        self._setup_ui()
        self._setup_window_properties()
        self._connect_signals()

    def _setup_window_properties(self):
        """Setup window to be a floating sidebar"""
        # Make it a frameless, always-on-top window
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool  # Doesn't show in taskbar
        )

        # Set fixed width
        self.setFixedWidth(80)

        # Position on right side of screen
        self._position_sidebar()

    def _position_sidebar(self):
        """Position sidebar on right or left side of screen"""
        from PyQt6.QtWidgets import QApplication
        screen = QApplication.primaryScreen()
        if screen:
            screen_geometry = screen.availableGeometry()

            # Full height
            height = screen_geometry.height()
            self.setFixedHeight(height)

            if self.position_right:
                # Right side
                x = screen_geometry.width() - 80
            else:
                # Left side
                x = 0

            y = 0
            self.move(x, y)

    def _setup_ui(self):
        """Setup the sidebar UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # Sidebar container
        self.sidebar_container = QWidget()
        self.sidebar_container.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['bg_secondary']};
                border-left: 1px solid {COLORS['border_subtle']};
            }}
        """)

        sidebar_layout = QVBoxLayout(self.sidebar_container)
        sidebar_layout.setSpacing(20)
        sidebar_layout.setContentsMargins(10, 20, 10, 20)

        # 1. TIMER DISPLAY (Top)
        self.timer_label = QLabel("00:00:00")
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timer_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['accent_primary']};
                font-size: 20px;
                font-weight: 700;
                background: transparent;
                padding: 10px 5px;
            }}
        """)
        sidebar_layout.addWidget(self.timer_label)

        # Progress bar (vertical)
        self.progress_bar = QProgressBar()
        self.progress_bar.setOrientation(Qt.Orientation.Vertical)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(100)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                border-radius: 4px;
                background-color: {COLORS['bg_tertiary']};
            }}
            QProgressBar::chunk {{
                border-radius: 4px;
                background-color: {COLORS['accent_primary']};
            }}
        """)
        sidebar_layout.addWidget(self.progress_bar)

        # Mode toggle button (countdown/count-up)
        self.mode_button = QPushButton("⏱")
        self.mode_button.setFixedSize(40, 40)
        self.mode_button.setToolTip("Toggle countdown/count-up")
        self.mode_button.setStyleSheet(self._get_icon_button_style())
        self.mode_button.clicked.connect(self._toggle_timer_mode)
        sidebar_layout.addWidget(self.mode_button, 0, Qt.AlignmentFlag.AlignCenter)

        # Spacer
        sidebar_layout.addSpacing(20)

        # 2. ICON BUTTONS (Middle section)

        # Settings button
        self.settings_button = QPushButton("⚙")
        self.settings_button.setFixedSize(40, 40)
        self.settings_button.setToolTip("Settings")
        self.settings_button.setStyleSheet(self._get_icon_button_style())
        sidebar_layout.addWidget(self.settings_button, 0, Qt.AlignmentFlag.AlignCenter)

        # Stats button
        self.stats_button = QPushButton("📊")
        self.stats_button.setFixedSize(40, 40)
        self.stats_button.setToolTip("Quick Stats")
        self.stats_button.setStyleSheet(self._get_icon_button_style())
        sidebar_layout.addWidget(self.stats_button, 0, Qt.AlignmentFlag.AlignCenter)

        # Notes button
        self.notes_button = QPushButton("📝")
        self.notes_button.setFixedSize(40, 40)
        self.notes_button.setToolTip("Session Notes")
        self.notes_button.setStyleSheet(self._get_icon_button_style())
        sidebar_layout.addWidget(self.notes_button, 0, Qt.AlignmentFlag.AlignCenter)

        # Minimize button
        self.minimize_button = QPushButton("➖")
        self.minimize_button.setFixedSize(40, 40)
        self.minimize_button.setToolTip("Minimize to timer only")
        self.minimize_button.setStyleSheet(self._get_icon_button_style())
        self.minimize_button.clicked.connect(self._toggle_minimize)
        sidebar_layout.addWidget(self.minimize_button, 0, Qt.AlignmentFlag.AlignCenter)

        # Spacer to push exit button to bottom
        sidebar_layout.addStretch()

        # 3. EMERGENCY EXIT (Bottom)
        self.exit_button = QPushButton("✕")
        self.exit_button.setFixedSize(50, 50)
        self.exit_button.setToolTip("Emergency Exit Session")
        self.exit_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['danger']};
                color: {COLORS['text_primary']};
                border: none;
                border-radius: 25px;
                font-size: 24px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['danger_hover']};
            }}
            QPushButton:pressed {{
                background-color: {COLORS['danger_pressed']};
            }}
        """)
        self.exit_button.clicked.connect(self._request_emergency_exit)
        sidebar_layout.addWidget(self.exit_button, 0, Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self.sidebar_container)

    def _get_icon_button_style(self) -> str:
        """Get stylesheet for icon buttons"""
        return f"""
            QPushButton {{
                background-color: {COLORS['bg_tertiary']};
                color: {COLORS['text_secondary']};
                border: 1px solid {COLORS['border_subtle']};
                border-radius: 20px;
                font-size: 20px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_primary']};
                color: {COLORS['text_primary']};
                border-color: {COLORS['accent_primary']};
            }}
            QPushButton:pressed {{
                background-color: {COLORS['accent_pressed']};
            }}
        """

    def _connect_signals(self):
        """Connect session manager signals"""
        self.session_manager.session_updated.connect(self._update_display)
        self.session_manager.app_blocked.connect(self._on_app_blocked)

    def _toggle_timer_mode(self):
        """Toggle between countdown and count-up modes"""
        self.countdown_mode = not self.countdown_mode
        # Update immediately
        self._update_timer_display()

    def _toggle_minimize(self):
        """Toggle minimized state"""
        self.minimized = not self.minimized

        # Hide/show middle buttons
        self.settings_button.setVisible(not self.minimized)
        self.stats_button.setVisible(not self.minimized)
        self.notes_button.setVisible(not self.minimized)
        self.progress_bar.setVisible(not self.minimized)
        self.mode_button.setVisible(not self.minimized)

        # Adjust width
        if self.minimized:
            self.setFixedWidth(60)  # Slimmer when minimized
        else:
            self.setFixedWidth(80)

        self._position_sidebar()

    def _update_display(self, elapsed_seconds: int, remaining_seconds: int):
        """Update timer and progress bar"""
        self.elapsed_seconds = elapsed_seconds
        self.remaining_seconds = remaining_seconds

        # Update timer
        self._update_timer_display()

        # Update progress bar
        session_info = self.session_manager.get_session_info()
        if session_info:
            total_duration = session_info['duration']
            if total_duration > 0:
                progress = int((elapsed_seconds / total_duration) * 100)
                self.progress_bar.setValue(min(100, progress))

    def _update_timer_display(self):
        """Update the timer label based on mode"""
        if self.countdown_mode:
            # Countdown mode - show remaining time
            seconds = self.remaining_seconds
        else:
            # Count-up mode - show elapsed time
            seconds = self.elapsed_seconds

        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60

        self.timer_label.setText(f"{hours:02d}:{minutes:02d}:{secs:02d}")

    def _on_app_blocked(self, app_name: str, total_blocked: int):
        """Handle app blocked event"""
        # Could show a notification or update stats button
        pass

    def _request_emergency_exit(self):
        """Request emergency exit with confirmation"""
        from PyQt6.QtWidgets import QMessageBox
        reply = QMessageBox.warning(
            self,
            "Emergency Exit",
            "Are you sure you want to exit this focus session early?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.emergency_exit_requested.emit()

    def start_display(self):
        """Initialize display for session start"""
        session_info = self.session_manager.get_session_info()
        self.elapsed_seconds = 0
        self.remaining_seconds = session_info['duration'] if session_info else 0

        # Initial update
        self._update_timer_display()
        self.progress_bar.setValue(0)

        # Show the sidebar
        self.show()
        self.raise_()
        self.activateWindow()


class QuickStatsPopup(QWidget):
    """Quick stats popup showing current session statistics"""

    view_full_history_requested = pyqtSignal()

    def __init__(self, session_manager, stats_tracker, parent=None):
        super().__init__(parent)
        self.session_manager = session_manager
        self.stats_tracker = stats_tracker
        self._setup_ui()
        self._setup_window_properties()

    def _setup_window_properties(self):
        """Setup window properties"""
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setFixedWidth(350)

    def _setup_ui(self):
        """Setup UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Container with styling
        container = QWidget()
        container.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['bg_secondary']};
                border: 2px solid {COLORS['accent_primary']};
                border-radius: 12px;
            }}
        """)

        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(15)
        container_layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title = QLabel("📊 Quick Stats")
        title.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_primary']};
                font-size: 20px;
                font-weight: 700;
                background: transparent;
            }}
        """)
        container_layout.addWidget(title)

        # Stats labels
        self.elapsed_label = QLabel("Time Elapsed: --:--:--")
        self.remaining_label = QLabel("Time Remaining: --:--:--")
        self.blocked_label = QLabel("Apps Blocked: 0")
        self.completion_label = QLabel("Completion: 0%")
        self.comparison_label = QLabel("")

        for label in [self.elapsed_label, self.remaining_label, self.blocked_label,
                     self.completion_label, self.comparison_label]:
            label.setStyleSheet(f"""
                QLabel {{
                    color: {COLORS['text_primary']};
                    font-size: 14px;
                    padding: 5px;
                    background: transparent;
                }}
            """)
            container_layout.addWidget(label)

        # View Full History button
        history_btn = ModernButton("View Full History", primary=True)
        history_btn.clicked.connect(self._view_full_history)
        container_layout.addWidget(history_btn)

        # Close button
        close_btn = ModernButton("Close")
        close_btn.clicked.connect(self.hide)
        container_layout.addWidget(close_btn)

        layout.addWidget(container)

    def show_stats(self):
        """Update and show stats"""
        session_info = self.session_manager.get_session_info()

        if session_info:
            # Time elapsed
            elapsed = session_info.get('elapsed', 0)
            hours = elapsed // 3600
            minutes = (elapsed % 3600) // 60
            seconds = elapsed % 60
            self.elapsed_label.setText(f"Time Elapsed: {hours:02d}:{minutes:02d}:{seconds:02d}")

            # Time remaining
            remaining = session_info.get('remaining', 0)
            hours = remaining // 3600
            minutes = (remaining % 3600) // 60
            seconds = remaining % 60
            self.remaining_label.setText(f"Time Remaining: {hours:02d}:{minutes:02d}:{seconds:02d}")

            # Apps blocked
            blocked_count = session_info.get('apps_blocked', 0)
            self.blocked_label.setText(f"Apps Blocked: {blocked_count}")

            # Completion percentage
            total_duration = session_info.get('duration', 1)
            if total_duration > 0:
                completion = int((elapsed / total_duration) * 100)
                self.completion_label.setText(f"Completion: {completion}%")

            # Comparison to previous session
            prev_session = self.stats_tracker.get_previous_session()
            if prev_session:
                prev_duration = prev_session.get('time_locked_in_seconds', 0)
                if prev_duration > 0 and elapsed > prev_duration:
                    diff = elapsed - prev_duration
                    diff_mins = diff // 60
                    self.comparison_label.setText(
                        f"🔥 {diff_mins} mins longer than last session!"
                    )
                    self.comparison_label.setStyleSheet(f"""
                        QLabel {{
                            color: {COLORS['accent_primary']};
                            font-size: 14px;
                            font-weight: 600;
                            padding: 5px;
                            background: transparent;
                        }}
                    """)
                else:
                    self.comparison_label.setText("")

        # Position near right side of screen
        from PyQt6.QtWidgets import QApplication
        screen = QApplication.primaryScreen()
        if screen:
            screen_geometry = screen.availableGeometry()
            x = screen_geometry.width() - self.width() - 100
            y = screen_geometry.height() // 2 - self.height() // 2
            self.move(x, y)

        self.show()
        self.raise_()
        self.activateWindow()

    def _view_full_history(self):
        """Request to view full history"""
        self.view_full_history_requested.emit()
        self.hide()


class SessionNotesPopup(QWidget):
    """Session notes popup for taking notes during session"""

    notes_saved = pyqtSignal(str)

    def __init__(self, session_manager, parent=None):
        super().__init__(parent)
        self.session_manager = session_manager
        self._setup_ui()
        self._setup_window_properties()

    def _setup_window_properties(self):
        """Setup window properties"""
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setFixedWidth(400)
        self.setFixedHeight(350)

    def _setup_ui(self):
        """Setup UI"""
        from PyQt6.QtWidgets import QTextEdit

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Container with styling
        container = QWidget()
        container.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['bg_secondary']};
                border: 2px solid {COLORS['accent_primary']};
                border-radius: 12px;
            }}
        """)

        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(15)
        container_layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title = QLabel("📝 Session Notes")
        title.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_primary']};
                font-size: 20px;
                font-weight: 700;
                background: transparent;
            }}
        """)
        container_layout.addWidget(title)

        # Instructions
        instructions = QLabel("What are you working on?")
        instructions.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_secondary']};
                font-size: 13px;
                background: transparent;
            }}
        """)
        container_layout.addWidget(instructions)

        # Text input
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Type your notes here...")
        self.notes_input.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS['bg_tertiary']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border_subtle']};
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
                line-height: 1.5;
            }}
            QTextEdit:focus {{
                border: 2px solid {COLORS['accent_primary']};
            }}
        """)
        container_layout.addWidget(self.notes_input)

        # Button layout
        button_layout = QHBoxLayout()

        # Save button
        save_btn = ModernButton("Save Notes", primary=True)
        save_btn.clicked.connect(self._save_notes)
        button_layout.addWidget(save_btn)

        # Close button
        close_btn = ModernButton("Close")
        close_btn.clicked.connect(self.hide)
        button_layout.addWidget(close_btn)

        container_layout.addLayout(button_layout)

        layout.addWidget(container)

    def show_notes(self):
        """Show notes popup and load existing notes"""
        session_info = self.session_manager.get_session_info()
        if session_info:
            # Load existing notes if any
            existing_notes = session_info.get('notes', '')
            self.notes_input.setPlainText(existing_notes)

        # Position near right side of screen
        from PyQt6.QtWidgets import QApplication
        screen = QApplication.primaryScreen()
        if screen:
            screen_geometry = screen.availableGeometry()
            x = screen_geometry.width() - self.width() - 100
            y = screen_geometry.height() // 2 - self.height() // 2
            self.move(x, y)

        self.show()
        self.raise_()
        self.activateWindow()
        self.notes_input.setFocus()

    def _save_notes(self):
        """Save notes to session"""
        notes = self.notes_input.toPlainText()

        # Update session with notes
        session_info = self.session_manager.get_session_info()
        if session_info and session_info.get('session_id'):
            self.session_manager.update_session_notes(notes)
            self.notes_saved.emit(notes)

            # Show confirmation
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(
                self,
                "Notes Saved",
                "Your session notes have been saved!",
                QMessageBox.StandardButton.Ok
            )

        self.hide()


class MotivationalQuote(QLabel):
    """Premium motivational quote widget"""

    QUOTES = [
        "Stay focused. You've got this!",
        "Deep work requires deep focus.",
        "Eliminate distractions. Embrace productivity.",
        "Your future self will thank you.",
        "Lock in. Level up.",
        "Success is the sum of small efforts repeated.",
        "Focus is your superpower.",
        "Great things take time and focus.",
        "You're doing amazing. Keep going!",
        "One focused hour beats four distracted ones.",
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_index = 0
        self._setup_ui()
        self._start_rotation()

    def _setup_ui(self):
        """Setup UI"""
        self.setText(self.QUOTES[0])
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setWordWrap(True)
        self.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_muted']};
                font-size: 17px;
                font-style: italic;
                padding: 24px;
                background: transparent;
            }}
        """)

    def _start_rotation(self):
        """Start quote rotation timer"""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._next_quote)
        self.timer.start(30000)

    def _next_quote(self):
        """Show next quote"""
        self.current_index = (self.current_index + 1) % len(self.QUOTES)
        self.setText(self.QUOTES[self.current_index])
