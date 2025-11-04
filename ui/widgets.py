"""
Custom UI Widgets for Lock In Application
Reusable UI components with modern styling
"""

from PyQt6.QtWidgets import (
    QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QSpinBox, QLineEdit,
    QProgressBar, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPalette, QColor
from typing import List, Dict


class ModernButton(QPushButton):
    """Modern styled button"""

    def __init__(self, text: str, primary: bool = False, danger: bool = False):
        super().__init__(text)
        self.primary = primary
        self.danger = danger
        self._setup_style()

    def _setup_style(self):
        """Setup button styling"""
        if self.primary:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #3b82f6;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 12px 24px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #2563eb;
                }
                QPushButton:pressed {
                    background-color: #1d4ed8;
                }
                QPushButton:disabled {
                    background-color: #64748b;
                }
            """)
        elif self.danger:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #ef4444;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 12px 24px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #dc2626;
                }
                QPushButton:pressed {
                    background-color: #b91c1c;
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #334155;
                    color: white;
                    border: 1px solid #475569;
                    border-radius: 8px;
                    padding: 10px 20px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #475569;
                }
                QPushButton:pressed {
                    background-color: #1e293b;
                }
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
        self.setStyleSheet("""
            QLabel {
                color: #3b82f6;
                padding: 20px;
            }
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
        title.setStyleSheet("""
            QLabel {
                color: #e2e8f0;
                font-size: 14px;
                font-weight: bold;
                padding: 8px;
            }
        """)
        layout.addWidget(title)

        # List widget
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 8px;
                color: #e2e8f0;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 4px;
            }
            QListWidget::item:hover {
                background-color: #334155;
            }
            QListWidget::item:selected {
                background-color: #3b82f6;
            }
        """)
        layout.addWidget(self.list_widget)

        # Remove button
        self.remove_btn = ModernButton("Remove Selected")
        self.remove_btn.clicked.connect(self._remove_selected)
        layout.addWidget(self.remove_btn)

    def add_app(self, app_name: str, app_path: str = ""):
        """Add an app to the list"""
        if app_name not in self.apps:
            self.apps.append(app_name)

            # Create list item
            display_text = app_name
            if app_path:
                display_text += f"\n{app_path}"

            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, app_name)
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
        self.setStyleSheet("""
            QFrame {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 12px;
                padding: 16px;
            }
        """)

        layout = QVBoxLayout(self)

        # Title
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("""
            QLabel {
                color: #94a3b8;
                font-size: 12px;
                font-weight: bold;
                text-transform: uppercase;
            }
        """)
        layout.addWidget(self.title_label)

        # Value
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet("""
            QLabel {
                color: #e2e8f0;
                font-size: 24px;
                font-weight: bold;
                margin-top: 8px;
            }
        """)
        layout.addWidget(self.value_label)

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
        self.setStyleSheet("""
            QFrame {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 12px;
                padding: 16px;
            }
        """)

        layout = QVBoxLayout(self)

        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            QLabel {
                color: #94a3b8;
                font-size: 12px;
                font-weight: bold;
                text-transform: uppercase;
            }
        """)
        layout.addWidget(title_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 8px;
                background-color: #334155;
                height: 8px;
                margin-top: 8px;
            }
            QProgressBar::chunk {
                border-radius: 8px;
                background-color: #3b82f6;
            }
        """)
        layout.addWidget(self.progress_bar)

        # Percentage label
        self.label = QLabel("0%")
        self.label.setStyleSheet("""
            QLabel {
                color: #e2e8f0;
                font-size: 18px;
                font-weight: bold;
                margin-top: 8px;
            }
        """)
        layout.addWidget(self.label)

    def set_progress(self, value: int):
        """Set progress value (0-100)"""
        self.progress_bar.setValue(value)
        self.label.setText(f"{value}%")


class TimePickerWidget(QWidget):
    """Widget for picking hours and minutes"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.hours_spin = None
        self.minutes_spin = None
        self._setup_ui()

    def _setup_ui(self):
        """Setup UI"""
        layout = QHBoxLayout(self)

        # Hours
        hours_layout = QVBoxLayout()
        hours_label = QLabel("Hours")
        hours_label.setStyleSheet("color: #94a3b8; font-size: 12px;")
        hours_layout.addWidget(hours_label)

        self.hours_spin = QSpinBox()
        self.hours_spin.setRange(0, 23)
        self.hours_spin.setValue(1)
        self.hours_spin.setStyleSheet("""
            QSpinBox {
                background-color: #1e293b;
                color: #e2e8f0;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 8px;
                font-size: 18px;
                font-weight: bold;
            }
        """)
        hours_layout.addWidget(self.hours_spin)
        layout.addLayout(hours_layout)

        # Separator
        separator = QLabel(":")
        separator.setStyleSheet("color: #94a3b8; font-size: 24px; padding: 0 8px;")
        separator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(separator)

        # Minutes
        minutes_layout = QVBoxLayout()
        minutes_label = QLabel("Minutes")
        minutes_label.setStyleSheet("color: #94a3b8; font-size: 12px;")
        minutes_layout.addWidget(minutes_label)

        self.minutes_spin = QSpinBox()
        self.minutes_spin.setRange(0, 59)
        self.minutes_spin.setValue(0)
        self.minutes_spin.setStyleSheet("""
            QSpinBox {
                background-color: #1e293b;
                color: #e2e8f0;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 8px;
                font-size: 18px;
                font-weight: bold;
            }
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
        self.setStyleSheet("""
            QLabel {
                color: #94a3b8;
                font-size: 16px;
                font-style: italic;
                padding: 20px;
            }
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
