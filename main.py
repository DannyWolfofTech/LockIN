#!/usr/bin/env python3
"""
Lock In - Focus & Productivity Desktop Application
Main entry point

A desktop application that helps users focus by blocking all applications
except whitelisted ones during focus sessions.
"""

import sys
import os
from pathlib import Path

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ui.main_window import MainWindow


def check_admin_privileges() -> bool:
    """
    Check if running with administrative privileges
    Note: Required for closing other applications

    Returns:
        True if running as admin
    """
    try:
        if sys.platform == 'win32':
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        elif sys.platform.startswith('linux'):
            return os.geteuid() == 0
        elif sys.platform == 'darwin':  # macOS
            return os.geteuid() == 0
        return False
    except Exception:
        return False


def show_admin_warning():
    """Show warning about admin privileges"""
    app = QApplication(sys.argv)

    msg = QMessageBox()
    msg.setIcon(QMessageBox.Icon.Warning)
    msg.setWindowTitle("Administrative Privileges Required")
    msg.setText("Lock In requires administrative privileges to manage applications.")
    msg.setInformativeText(
        "The app may not be able to close all applications without admin rights.\n\n"
        "On Windows: Right-click and 'Run as Administrator'\n"
        "On Linux/macOS: Run with sudo or as root\n\n"
        "Continue anyway?"
    )
    msg.setStandardButtons(
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    )
    msg.setDefaultButton(QMessageBox.StandardButton.No)

    return msg.exec() == QMessageBox.StandardButton.Yes


def main():
    """Main application entry point"""
    # Check for admin privileges
    if not check_admin_privileges():
        # For development/testing, we can continue, but show warning
        print("WARNING: Not running with administrative privileges.")
        print("The application may not be able to close all applications.")

        # Uncomment the following to enforce admin check:
        # if not show_admin_warning():
        #     sys.exit(1)

    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("Lock In")
    app.setOrganizationName("LockIn")

    # Enable high DPI scaling
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)

    # Create and show main window
    try:
        window = MainWindow()
        window.show()

        # Start event loop
        sys.exit(app.exec())

    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()

        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("Fatal Error")
        msg.setText("An unexpected error occurred.")
        msg.setInformativeText(str(e))
        msg.setDetailedText(traceback.format_exc())
        msg.exec()

        sys.exit(1)


if __name__ == '__main__':
    main()
