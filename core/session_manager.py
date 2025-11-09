"""
Session Manager - Manages focus sessions
Coordinates timing, app blocking, and session state
"""

import time
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from core.app_blocker import AppBlocker
from database.db_manager import DatabaseManager


class SessionState:
    """Enum for session states"""
    IDLE = "idle"
    SETUP = "setup"
    ACTIVE = "active"
    PAUSED = "paused"
    ENDING = "ending"
    COMPLETED = "completed"


class SessionManager(QObject):
    """
    Manages focus sessions including timing, blocking, and state

    Signals:
        session_started: Emitted when session starts (session_id)
        session_updated: Emitted on timer updates (elapsed_seconds, remaining_seconds)
        session_ended: Emitted when session ends (session_id, emergency_exit)
        app_blocked: Emitted when an app is blocked (app_name, total_blocked)
        state_changed: Emitted when session state changes (new_state)
    """

    # Signals
    session_started = pyqtSignal(int)  # session_id
    session_updated = pyqtSignal(int, int)  # elapsed_seconds, remaining_seconds
    session_ended = pyqtSignal(int, bool)  # session_id, emergency_exit
    app_blocked = pyqtSignal(str, int)  # app_name, total_blocked
    state_changed = pyqtSignal(str)  # new_state

    def __init__(self, db_manager: DatabaseManager, parent=None):
        """
        Initialize session manager

        Args:
            db_manager: Database manager instance
            parent: Parent QObject
        """
        super().__init__(parent)

        self.db_manager = db_manager
        self.app_blocker = AppBlocker(self)

        # Session state
        self.current_state = SessionState.IDLE
        self.session_id: Optional[int] = None
        self.session_name: str = ""
        self.session_duration: int = 0  # Total duration in seconds
        self.session_start_time: Optional[float] = None
        self.whitelisted_apps: List[str] = []
        self.apps_blocked_count: int = 0

        # Timer for session updates
        self.session_timer = QTimer(self)
        self.session_timer.timeout.connect(self._update_session)
        self.session_timer.setInterval(1000)  # Update every second

        # Connect app blocker signals
        self.app_blocker.app_blocked.connect(self._on_app_blocked)
        self.app_blocker.error_occurred.connect(self._on_blocker_error)

    def setup_session(self, name: str, duration_minutes: int,
                     whitelisted_apps: List[str], description: str = "") -> bool:
        """
        Setup a new session

        Args:
            name: Session name
            duration_minutes: Session duration in minutes
            whitelisted_apps: List of apps to whitelist
            description: Optional description

        Returns:
            True if setup successful
        """
        try:
            if self.current_state != SessionState.IDLE:
                return False

            self.session_name = name
            self.session_duration = duration_minutes * 60  # Convert to seconds
            self.whitelisted_apps = whitelisted_apps
            self.apps_blocked_count = 0

            # Create session in database
            self.session_id = self.db_manager.create_session(
                name=name,
                duration_seconds=self.session_duration,
                apps_whitelisted=whitelisted_apps,
                description=description
            )

            self._change_state(SessionState.SETUP)
            return True

        except Exception as e:
            print(f"Error setting up session: {e}")
            return False

    def start_session(self) -> bool:
        """
        Start the active session

        Returns:
            True if started successfully
        """
        try:
            if self.current_state != SessionState.SETUP:
                return False

            # Configure app blocker
            self.app_blocker.set_whitelisted_apps(self.whitelisted_apps)

            # Close all non-whitelisted apps
            closed_count = self.app_blocker.close_all_non_whitelisted_apps()
            print(f"Closed {closed_count} non-whitelisted apps")

            # Start monitoring
            self.app_blocker.start_monitoring()

            # Start session timer
            self.session_start_time = time.time()
            self.session_timer.start()

            self._change_state(SessionState.ACTIVE)
            self.session_started.emit(self.session_id)

            return True

        except Exception as e:
            print(f"Error starting session: {e}")
            return False

    def end_session(self, emergency_exit: bool = False) -> bool:
        """
        End the current session

        Args:
            emergency_exit: Whether this is an emergency exit

        Returns:
            True if ended successfully
        """
        try:
            if self.current_state not in [SessionState.ACTIVE, SessionState.PAUSED]:
                return False

            self._change_state(SessionState.ENDING)

            # Stop monitoring and timer
            self.app_blocker.stop_monitoring()
            self.session_timer.stop()

            # Calculate actual time spent
            if self.session_start_time:
                time_spent = int(time.time() - self.session_start_time)
            else:
                time_spent = 0

            # Update database
            self.db_manager.end_session(
                session_id=self.session_id,
                time_locked_in=time_spent,
                emergency_exit=emergency_exit
            )

            # Update apps blocked count
            self.db_manager.update_session(
                session_id=self.session_id,
                apps_blocked_count=self.apps_blocked_count
            )

            self._change_state(SessionState.COMPLETED)
            self.session_ended.emit(self.session_id, emergency_exit)

            return True

        except Exception as e:
            print(f"Error ending session: {e}")
            return False

    def pause_session(self) -> bool:
        """Pause the current session (if needed)"""
        if self.current_state != SessionState.ACTIVE:
            return False

        self.session_timer.stop()
        self.app_blocker.stop_monitoring()
        self._change_state(SessionState.PAUSED)
        return True

    def resume_session(self) -> bool:
        """Resume a paused session"""
        if self.current_state != SessionState.PAUSED:
            return False

        self.session_timer.start()
        self.app_blocker.start_monitoring()
        self._change_state(SessionState.ACTIVE)
        return True

    def get_elapsed_time(self) -> int:
        """
        Get elapsed time in seconds

        Returns:
            Elapsed seconds
        """
        if self.session_start_time is None:
            return 0
        return int(time.time() - self.session_start_time)

    def get_remaining_time(self) -> int:
        """
        Get remaining time in seconds

        Returns:
            Remaining seconds
        """
        elapsed = self.get_elapsed_time()
        remaining = self.session_duration - elapsed
        return max(0, remaining)

    def get_progress_percentage(self) -> float:
        """
        Get session progress as percentage

        Returns:
            Progress percentage (0-100)
        """
        if self.session_duration == 0:
            return 0.0

        elapsed = self.get_elapsed_time()
        return min(100.0, (elapsed / self.session_duration) * 100)

    def is_session_active(self) -> bool:
        """Check if a session is currently active"""
        return self.current_state == SessionState.ACTIVE

    def get_session_info(self) -> Dict[str, Any]:
        """
        Get current session information

        Returns:
            Dictionary with session info
        """
        # Get notes from database if session exists
        notes = ""
        if self.session_id:
            try:
                session_data = self.db_manager.get_session(self.session_id)
                if session_data:
                    notes = session_data.get('notes', '')
            except Exception as e:
                print(f"Error getting session notes: {e}")

        return {
            'session_id': self.session_id,
            'name': self.session_name,
            'state': self.current_state,
            'duration': self.session_duration,
            'elapsed': self.get_elapsed_time(),
            'remaining': self.get_remaining_time(),
            'progress': self.get_progress_percentage(),
            'apps_blocked': self.apps_blocked_count,
            'whitelisted_apps': self.whitelisted_apps.copy(),
            'notes': notes
        }

    def update_session_notes(self, notes: str) -> bool:
        """
        Update session notes in real-time

        Args:
            notes: Notes text to save

        Returns:
            True if updated successfully
        """
        try:
            if self.session_id:
                self.db_manager.update_session(
                    session_id=self.session_id,
                    notes=notes
                )
                return True
            return False
        except Exception as e:
            print(f"Error updating session notes: {e}")
            return False

    def reset(self) -> None:
        """Reset session manager to idle state"""
        if self.current_state == SessionState.ACTIVE:
            self.end_session(emergency_exit=True)

        self.session_timer.stop()
        self.app_blocker.stop_monitoring()

        self.session_id = None
        self.session_name = ""
        self.session_duration = 0
        self.session_start_time = None
        self.whitelisted_apps.clear()
        self.apps_blocked_count = 0

        self._change_state(SessionState.IDLE)

    def _update_session(self) -> None:
        """Update session timer (called every second)"""
        if self.current_state != SessionState.ACTIVE:
            return

        elapsed = self.get_elapsed_time()
        remaining = self.get_remaining_time()

        # Emit update signal
        self.session_updated.emit(elapsed, remaining)

        # Check if session time is up
        if remaining <= 0:
            self.end_session(emergency_exit=False)

    def _on_app_blocked(self, app_name: str, app_path: str) -> None:
        """
        Handle app blocked event

        Args:
            app_name: Name of blocked app
            app_path: Path of blocked app
        """
        self.apps_blocked_count += 1

        # Record in database
        if self.session_id:
            try:
                self.db_manager.record_blocked_app(
                    session_id=self.session_id,
                    app_name=app_name,
                    app_path=app_path
                )
            except Exception as e:
                print(f"Error recording blocked app: {e}")

        # Emit signal
        self.app_blocked.emit(app_name, self.apps_blocked_count)

    def _on_blocker_error(self, error_message: str) -> None:
        """
        Handle app blocker error

        Args:
            error_message: Error message
        """
        print(f"App blocker error: {error_message}")

    def _change_state(self, new_state: str) -> None:
        """
        Change session state and emit signal

        Args:
            new_state: New state
        """
        if self.current_state != new_state:
            self.current_state = new_state
            self.state_changed.emit(new_state)

    @staticmethod
    def format_time(seconds: int) -> str:
        """
        Format seconds as HH:MM:SS

        Args:
            seconds: Time in seconds

        Returns:
            Formatted time string
        """
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"
