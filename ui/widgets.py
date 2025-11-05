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

# Modern Premium Color Scheme
COLORS = {
    'bg_primary': '#1a1a1a',      # Dark charcoal background
    'bg_secondary': '#2a2a2a',    # Card/elevated background
    'bg_tertiary': '#3a3a3a',     # Input fields
    'accent_primary': '#10b981',  # Emerald green accent
    'accent_hover': '#059669',    # Darker green on hover
    'accent_pressed': '#047857',  # Even darker green when pressed
    'danger': '#ef4444',          # Red for danger/exit
    'danger_hover': '#dc2626',
    'danger_pressed': '#b91c1c',
    'text_primary': '#ffffff',    # White text
    'text_secondary': '#a1a1aa',  # Light gray text
    'text_muted': '#71717a',      # Muted gray
    'border': '#10b981',          # Emerald green borders
    'border_subtle': '#404040',   # Subtle borders
}


class ModernCard(QFrame):
    """Base card widget with modern design - border, shadow, elevation"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_style()

    def _setup_style(self):
        """Setup modern card styling"""
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
            }}
        """)

        # Add shadow effect for depth
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 4)
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
                    transform: scale(1.02);
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
        self.remove_btn = ModernButton("Remove Selected")
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
        self.hours_spin.setMinimumWidth(90)
        self.hours_spin.setMinimumHeight(42)
        self.hours_spin.setMaximumHeight(42)
        self.hours_spin.setButtonSymbols(QSpinBox.ButtonSymbols.UpDownArrows)
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
                subcontrol-position: top right;
                width: 24px;
                border-left: 1px solid {COLORS['border_subtle']};
                border-top-right-radius: 8px;
                background-color: {COLORS['bg_tertiary']};
            }}
            QSpinBox::up-button:hover {{
                background-color: {COLORS['accent_primary']};
            }}
            QSpinBox::down-button {{
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                width: 24px;
                border-left: 1px solid {COLORS['border_subtle']};
                border-bottom-right-radius: 8px;
                background-color: {COLORS['bg_tertiary']};
            }}
            QSpinBox::down-button:hover {{
                background-color: {COLORS['accent_primary']};
            }}
            QSpinBox::up-arrow {{
                image: none;
                width: 0;
                height: 0;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-bottom: 8px solid {COLORS['text_primary']};
            }}
            QSpinBox::down-arrow {{
                image: none;
                width: 0;
                height: 0;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 8px solid {COLORS['text_primary']};
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
        self.minutes_spin.setMinimumWidth(90)
        self.minutes_spin.setMinimumHeight(42)
        self.minutes_spin.setMaximumHeight(42)
        self.minutes_spin.setButtonSymbols(QSpinBox.ButtonSymbols.UpDownArrows)
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
                subcontrol-position: top right;
                width: 24px;
                border-left: 1px solid {COLORS['border_subtle']};
                border-top-right-radius: 8px;
                background-color: {COLORS['bg_tertiary']};
            }}
            QSpinBox::up-button:hover {{
                background-color: {COLORS['accent_primary']};
            }}
            QSpinBox::down-button {{
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                width: 24px;
                border-left: 1px solid {COLORS['border_subtle']};
                border-bottom-right-radius: 8px;
                background-color: {COLORS['bg_tertiary']};
            }}
            QSpinBox::down-button:hover {{
                background-color: {COLORS['accent_primary']};
            }}
            QSpinBox::up-arrow {{
                image: none;
                width: 0;
                height: 0;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-bottom: 8px solid {COLORS['text_primary']};
            }}
            QSpinBox::down-arrow {{
                image: none;
                width: 0;
                height: 0;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 8px solid {COLORS['text_primary']};
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
