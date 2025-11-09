"""
Database Manager for Lock In Application
Handles all SQLite database operations
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path


class DatabaseManager:
    """Manages all database operations for the Lock In application"""

    def __init__(self, db_path: str = None):
        """
        Initialize database manager

        Args:
            db_path: Path to SQLite database file. If None, uses default location.
        """
        if db_path is None:
            # Default to user's home directory or current directory
            app_dir = Path.home() / '.lockin'
            app_dir.mkdir(exist_ok=True)
            db_path = str(app_dir / 'lockin.db')

        self.db_path = db_path
        self.connection: Optional[sqlite3.Connection] = None
        self._initialize_database()

    def _initialize_database(self) -> None:
        """Initialize database with schema if it doesn't exist"""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row  # Access columns by name

            # Read and execute schema file
            schema_path = Path(__file__).parent / 'schema.sql'
            with open(schema_path, 'r') as f:
                schema_sql = f.read()

            cursor = self.connection.cursor()
            cursor.executescript(schema_sql)
            self.connection.commit()

            # Run migrations for existing databases
            self._run_migrations()

        except sqlite3.Error as e:
            print(f"Database initialization error: {e}")
            raise

    def _run_migrations(self) -> None:
        """Run database migrations for schema updates"""
        try:
            cursor = self.connection.cursor()

            # Migration 1: Add notes column if it doesn't exist
            cursor.execute("PRAGMA table_info(sessions)")
            columns = [column[1] for column in cursor.fetchall()]

            if 'notes' not in columns:
                cursor.execute("ALTER TABLE sessions ADD COLUMN notes TEXT DEFAULT ''")
                self.connection.commit()
                print("Migration: Added 'notes' column to sessions table")

        except sqlite3.Error as e:
            print(f"Migration error: {e}")
            # Don't raise - migrations are optional upgrades

    def close(self) -> None:
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.connection = None

    # ==================== SESSION OPERATIONS ====================

    def create_session(self, name: str, duration_seconds: int,
                      apps_whitelisted: List[str], description: str = "") -> int:
        """
        Create a new session

        Args:
            name: Session name/description
            duration_seconds: Planned duration in seconds
            apps_whitelisted: List of whitelisted app names/paths
            description: Optional detailed description

        Returns:
            Session ID
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO sessions (name, description, duration_seconds,
                                    apps_whitelisted, started_at)
                VALUES (?, ?, ?, ?, ?)
            """, (name, description, duration_seconds,
                  json.dumps(apps_whitelisted), datetime.now()))

            self.connection.commit()
            return cursor.lastrowid

        except sqlite3.Error as e:
            print(f"Error creating session: {e}")
            raise

    def update_session(self, session_id: int, **kwargs) -> None:
        """
        Update session fields

        Args:
            session_id: Session ID to update
            **kwargs: Fields to update (time_locked_in_seconds, apps_blocked_count, etc.)
        """
        try:
            if not kwargs:
                return

            # Build UPDATE query dynamically
            fields = ', '.join([f"{key} = ?" for key in kwargs.keys()])
            values = list(kwargs.values()) + [session_id]

            cursor = self.connection.cursor()
            cursor.execute(f"""
                UPDATE sessions
                SET {fields}
                WHERE id = ?
            """, values)

            self.connection.commit()

        except sqlite3.Error as e:
            print(f"Error updating session: {e}")
            raise

    def end_session(self, session_id: int, time_locked_in: int,
                   emergency_exit: bool = False) -> None:
        """
        Mark session as ended

        Args:
            session_id: Session ID
            time_locked_in: Actual time spent in seconds
            emergency_exit: Whether session ended via emergency exit
        """
        try:
            status = 'emergency_exit' if emergency_exit else 'completed'
            cursor = self.connection.cursor()
            cursor.execute("""
                UPDATE sessions
                SET time_locked_in_seconds = ?,
                    emergency_exit_used = ?,
                    ended_at = ?,
                    status = ?
                WHERE id = ?
            """, (time_locked_in, emergency_exit, datetime.now(), status, session_id))

            self.connection.commit()

        except sqlite3.Error as e:
            print(f"Error ending session: {e}")
            raise

    def get_session(self, session_id: int) -> Optional[Dict[str, Any]]:
        """
        Get session by ID

        Args:
            session_id: Session ID

        Returns:
            Session data as dictionary or None
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
            row = cursor.fetchone()

            if row:
                session_dict = dict(row)
                # Parse JSON fields
                session_dict['apps_whitelisted'] = json.loads(session_dict['apps_whitelisted'])
                return session_dict
            return None

        except sqlite3.Error as e:
            print(f"Error getting session: {e}")
            return None

    def get_all_sessions(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all sessions ordered by most recent

        Args:
            limit: Maximum number of sessions to return

        Returns:
            List of session dictionaries
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT * FROM sessions
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))

            sessions = []
            for row in cursor.fetchall():
                session_dict = dict(row)
                session_dict['apps_whitelisted'] = json.loads(session_dict['apps_whitelisted'])
                sessions.append(session_dict)

            return sessions

        except sqlite3.Error as e:
            print(f"Error getting sessions: {e}")
            return []

    # ==================== BLOCKED APPS OPERATIONS ====================

    def record_blocked_app(self, session_id: int, app_name: str,
                          app_path: str = "") -> None:
        """
        Record a blocked app attempt

        Args:
            session_id: Current session ID
            app_name: Name of the blocked app
            app_path: Full path to the app executable
        """
        try:
            cursor = self.connection.cursor()

            # Check if app already blocked in this session
            cursor.execute("""
                SELECT id, blocked_count FROM blocked_apps
                WHERE session_id = ? AND app_name = ?
            """, (session_id, app_name))

            existing = cursor.fetchone()

            if existing:
                # Update existing record
                cursor.execute("""
                    UPDATE blocked_apps
                    SET blocked_count = blocked_count + 1,
                        last_blocked_at = ?
                    WHERE id = ?
                """, (datetime.now(), existing['id']))
            else:
                # Create new record
                cursor.execute("""
                    INSERT INTO blocked_apps (session_id, app_name, app_path)
                    VALUES (?, ?, ?)
                """, (session_id, app_name, app_path))

            # Update session's blocked count
            cursor.execute("""
                UPDATE sessions
                SET apps_blocked_count = apps_blocked_count + 1
                WHERE id = ?
            """, (session_id,))

            self.connection.commit()

        except sqlite3.Error as e:
            print(f"Error recording blocked app: {e}")
            raise

    def get_blocked_apps_for_session(self, session_id: int) -> List[Dict[str, Any]]:
        """
        Get all blocked apps for a session

        Args:
            session_id: Session ID

        Returns:
            List of blocked app records
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT * FROM blocked_apps
                WHERE session_id = ?
                ORDER BY blocked_count DESC
            """, (session_id,))

            return [dict(row) for row in cursor.fetchall()]

        except sqlite3.Error as e:
            print(f"Error getting blocked apps: {e}")
            return []

    # ==================== STATISTICS ====================

    def get_total_stats(self) -> Dict[str, Any]:
        """
        Get overall statistics across all sessions

        Returns:
            Dictionary with total stats
        """
        try:
            cursor = self.connection.cursor()

            # Total time locked in
            cursor.execute("""
                SELECT
                    COUNT(*) as total_sessions,
                    SUM(time_locked_in_seconds) as total_time_seconds,
                    SUM(apps_blocked_count) as total_apps_blocked,
                    SUM(emergency_exit_used) as total_emergency_exits,
                    AVG(time_locked_in_seconds) as avg_session_duration
                FROM sessions
                WHERE status IN ('completed', 'emergency_exit')
            """)

            stats = dict(cursor.fetchone())

            # Most common whitelisted apps
            cursor.execute("""
                SELECT apps_whitelisted FROM sessions
            """)

            all_apps = []
            for row in cursor.fetchall():
                apps = json.loads(row['apps_whitelisted'])
                all_apps.extend(apps)

            from collections import Counter
            app_counts = Counter(all_apps)
            stats['most_common_whitelisted'] = app_counts.most_common(10)

            return stats

        except sqlite3.Error as e:
            print(f"Error getting total stats: {e}")
            return {}

    def get_recent_sessions_summary(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Get summary of recent sessions

        Args:
            days: Number of days to look back

        Returns:
            List of recent session summaries
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT
                    id, name, duration_seconds, time_locked_in_seconds,
                    apps_blocked_count, emergency_exit_used, created_at
                FROM sessions
                WHERE created_at >= datetime('now', '-' || ? || ' days')
                ORDER BY created_at DESC
            """, (days,))

            return [dict(row) for row in cursor.fetchall()]

        except sqlite3.Error as e:
            print(f"Error getting recent sessions: {e}")
            return []

    # ==================== SETTINGS ====================

    def get_setting(self, key: str, default: str = None) -> Optional[str]:
        """
        Get a setting value

        Args:
            key: Setting key
            default: Default value if setting doesn't exist

        Returns:
            Setting value or default
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row['value'] if row else default

        except sqlite3.Error as e:
            print(f"Error getting setting: {e}")
            return default

    def set_setting(self, key: str, value: str) -> None:
        """
        Set a setting value

        Args:
            key: Setting key
            value: Setting value
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO settings (key, value, updated_at)
                VALUES (?, ?, ?)
            """, (key, value, datetime.now()))

            self.connection.commit()

        except sqlite3.Error as e:
            print(f"Error setting value: {e}")
            raise

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
