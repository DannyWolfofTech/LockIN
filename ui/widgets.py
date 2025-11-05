"""
Custom UI Widgets for Lock In Application
Reusable UI components with modern styling
"""

from PyQt6.QtWidgets import (
    QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QSpinBox, QLineEdit,
    QProgressBar, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import QFont, QPalette, QColor, QIcon, QPixmap
from typing import List, Dict
import sys

# Modern Color Scheme - Clean and Professional
COLORS = {
    'bg_primary': '#1a1a1a',      # Dark charcoal background
    'bg_secondary': '#2a2a2a',    # Slightly lighter charcoal
    'bg_tertiary': '#3a3a3a',     # Card/widget background
    'accent_primary': '#10b981',  # Clean emerald green
    'accent_hover': '#059669',    # Darker green on hover
    'accent_pressed': '#047857',  # Even darker green when pressed
    'danger': '#ef4444',          # Red for danger/exit
    'danger_hover': '#dc2626',
    'danger_pressed': '#b91c1c',
    'text_primary': '#ffffff',    # White text
    'text_secondary': '#a1a1aa',  # Gray text
    'text_muted': '#71717a',      # Muted gray
    'border': '#404040',          # Border color
    'border_focus': '#10b981',    # Focused border (green)
}


class ModernButton(QPushButton):
    """Modern styled button with clean flat design"""

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
                    border-radius: 6px;
                    padding: 12px 24px;
                    font-size: 14px;
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
                    border-radius: 6px;
                    padding: 12px 24px;
                    font-size: 14px;
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
                    border: 1px solid {COLORS['border']};
                    border-radius: 6px;
                    padding: 10px 20px;
                    font-size: 14px;
                    font-weight: 500;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['bg_secondary']};
                    border-color: {COLORS['border_focus']};
                }}
                QPushButton:pressed {{
                    background-color: {COLORS['bg_primary']};
                }}
            """)


class TimerDisplay(QLabel):
    """Large timer display widget"""

    def __init__(self, parent=None):
        super().__init__("00:00:00", parent)
        self._setup_style()

    def _setup_style(self):
        """Setup timer styling"""
        font = QFont("Segoe UI", 72, QFont.Weight.Bold)
        self.setFont(font)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['accent_primary']};
                padding: 20px;
                background: transparent;
            }}
        """)

    def set_time(self, hours: int, minutes: int, seconds: int):
        """Update timer display"""
        self.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")


class AppListWidget(QWidget):
    """Widget for displaying and managing whitelisted apps"""

    app_removed = pyqtSignal(str)  # Emitted when app is removed

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
                font-size: 14px;
                font-weight: 600;
                padding: 8px;
                background: transparent;
            }}
        """)
        layout.addWidget(title)

        # List widget
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet(f"""
            QListWidget {{
                background-color: {COLORS['bg_tertiary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 8px;
                color: {COLORS['text_primary']};
                font-size: 13px;
            }}
            QListWidget::item {{
                padding: 10px;
                border-radius: 4px;
                margin: 2px 0;
            }}
            QListWidget::item:hover {{
                background-color: {COLORS['bg_secondary']};
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

            # Create list item with just the app name
            item = QListWidgetItem(app_name)
            item.setData(Qt.ItemDataRole.UserRole, app_name)

            # Add icon if provided
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


class SessionInfoCard(QFrame):
    """Card widget for displaying session information"""

    def __init__(self, title: str, value: str = "", parent=None):
        super().__init__(parent)
        self.title_label = None
        self.value_label = None
        self._setup_ui(title, value)

    def _setup_ui(self, title: str, value: str):
        """Setup UI"""
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setMinimumHeight(120)  # Ensure adequate height
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_tertiary']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 20px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title
        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.title_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_secondary']};
                font-size: 11px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                background: transparent;
                padding: 0;
                margin: 0;
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
                font-size: 32px;
                font-weight: 700;
                background: transparent;
                padding: 0;
                margin: 0;
            }}
        """)
        layout.addWidget(self.value_label)
        layout.addStretch()

    def set_value(self, value: str):
        """Update card value"""
        self.value_label.setText(value)


class ProgressCard(QFrame):
    """Card widget with progress bar"""

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.progress_bar = None
        self.label = None
        self._setup_ui(title)

    def _setup_ui(self, title: str):
        """Setup UI"""
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setMinimumHeight(140)  # Ensure adequate height
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_tertiary']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 20px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_secondary']};
                font-size: 11px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                background: transparent;
                padding: 0;
                margin: 0;
            }}
        """)
        layout.addWidget(title_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setMinimumHeight(16)
        self.progress_bar.setMaximumHeight(16)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                border-radius: 8px;
                background-color: {COLORS['bg_secondary']};
            }}
            QProgressBar::chunk {{
                border-radius: 8px;
                background-color: {COLORS['accent_primary']};
            }}
        """)
        layout.addWidget(self.progress_bar)

        # Percentage label
        self.label = QLabel("0%")
        self.label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_primary']};
                font-size: 24px;
                font-weight: 700;
                background: transparent;
                padding: 0;
                margin: 0;
            }}
        """)
        layout.addWidget(self.label)
        layout.addStretch()

    def set_progress(self, value: int):
        """Set progress value (0-100)"""
        self.progress_bar.setValue(value)
        self.label.setText(f"{value}%")


class TimePickerWidget(QWidget):
    """Widget for picking hours and minutes with compact, professional controls"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.hours_spin = None
        self.minutes_spin = None
        self._setup_ui()

    def _setup_ui(self):
        """Setup UI"""
        layout = QHBoxLayout(self)
        layout.setSpacing(15)

        # Hours
        hours_layout = QVBoxLayout()
        hours_label = QLabel("Hours")
        hours_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px; font-weight: 600; background: transparent;")
        hours_layout.addWidget(hours_label)

        self.hours_spin = QSpinBox()
        self.hours_spin.setRange(0, 23)
        self.hours_spin.setValue(1)
        self.hours_spin.setMinimumWidth(80)
        self.hours_spin.setMinimumHeight(36)
        self.hours_spin.setMaximumHeight(36)
        self.hours_spin.setButtonSymbols(QSpinBox.ButtonSymbols.PlusMinus)
        self.hours_spin.setStyleSheet(f"""
            QSpinBox {{
                background-color: {COLORS['bg_tertiary']};
                color: {COLORS['text_primary']};
                border: 2px solid {COLORS['border']};
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 18px;
                font-weight: 600;
            }}
            QSpinBox:focus {{
                border-color: {COLORS['border_focus']};
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                width: 18px;
                border: none;
                background-color: {COLORS['bg_secondary']};
                border-radius: 3px;
            }}
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
                background-color: {COLORS['accent_primary']};
            }}
            QSpinBox::up-button {{
                subcontrol-position: right;
            }}
            QSpinBox::down-button {{
                subcontrol-position: left;
            }}
        """)
        hours_layout.addWidget(self.hours_spin)
        layout.addLayout(hours_layout)

        # Separator
        separator = QLabel(":")
        separator.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 24px; font-weight: bold; padding: 18px 6px 0 6px; background: transparent;")
        separator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(separator)

        # Minutes
        minutes_layout = QVBoxLayout()
        minutes_label = QLabel("Minutes")
        minutes_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px; font-weight: 600; background: transparent;")
        minutes_layout.addWidget(minutes_label)

        self.minutes_spin = QSpinBox()
        self.minutes_spin.setRange(0, 59)
        self.minutes_spin.setValue(30)
        self.minutes_spin.setMinimumWidth(80)
        self.minutes_spin.setMinimumHeight(36)
        self.minutes_spin.setMaximumHeight(36)
        self.minutes_spin.setButtonSymbols(QSpinBox.ButtonSymbols.PlusMinus)
        self.minutes_spin.setStyleSheet(f"""
            QSpinBox {{
                background-color: {COLORS['bg_tertiary']};
                color: {COLORS['text_primary']};
                border: 2px solid {COLORS['border']};
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 18px;
                font-weight: 600;
            }}
            QSpinBox:focus {{
                border-color: {COLORS['border_focus']};
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                width: 18px;
                border: none;
                background-color: {COLORS['bg_secondary']};
                border-radius: 3px;
            }}
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
                background-color: {COLORS['accent_primary']};
            }}
            QSpinBox::up-button {{
                subcontrol-position: right;
            }}
            QSpinBox::down-button {{
                subcontrol-position: left;
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
    """Widget that displays rotating motivational quotes"""

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
                font-size: 16px;
                font-style: italic;
                padding: 20px;
                background: transparent;
            }}
        """)

    def _start_rotation(self):
        """Start quote rotation timer"""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._next_quote)
        self.timer.start(30000)  # Change every 30 seconds

    def _next_quote(self):
        """Show next quote"""
        self.current_index = (self.current_index + 1) % len(self.QUOTES)
        self.setText(self.QUOTES[self.current_index])
