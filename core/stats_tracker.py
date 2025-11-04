"""
Stats Tracker - Analytics and statistics for focus sessions
"""

from typing import Dict, List, Any, Tuple
from datetime import datetime, timedelta
from database.db_manager import DatabaseManager


class StatsTracker:
    """Provides analytics and statistics for focus sessions"""

    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize stats tracker

        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager

    def get_total_stats(self) -> Dict[str, Any]:
        """
        Get overall lifetime statistics

        Returns:
            Dictionary with total stats
        """
        stats = self.db_manager.get_total_stats()

        # Add formatted versions
        if stats.get('total_time_seconds'):
            stats['total_time_formatted'] = self._format_duration(
                stats['total_time_seconds']
            )
        else:
            stats['total_time_formatted'] = "0h 0m"

        if stats.get('avg_session_duration'):
            stats['avg_session_formatted'] = self._format_duration(
                int(stats['avg_session_duration'])
            )
        else:
            stats['avg_session_formatted'] = "0h 0m"

        return stats

    def get_session_details(self, session_id: int) -> Dict[str, Any]:
        """
        Get detailed information about a specific session

        Args:
            session_id: Session ID

        Returns:
            Session details with stats
        """
        session = self.db_manager.get_session(session_id)
        if not session:
            return {}

        # Get blocked apps for this session
        blocked_apps = self.db_manager.get_blocked_apps_for_session(session_id)

        # Add formatted time
        session['time_locked_in_formatted'] = self._format_duration(
            session['time_locked_in_seconds']
        )
        session['duration_formatted'] = self._format_duration(
            session['duration_seconds']
        )

        # Calculate completion percentage
        if session['duration_seconds'] > 0:
            completion = (session['time_locked_in_seconds'] /
                         session['duration_seconds']) * 100
            session['completion_percentage'] = min(100, completion)
        else:
            session['completion_percentage'] = 0

        # Add blocked apps
        session['blocked_apps'] = blocked_apps

        return session

    def get_recent_sessions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent sessions with formatted data

        Args:
            limit: Maximum number of sessions to return

        Returns:
            List of session dictionaries
        """
        sessions = self.db_manager.get_all_sessions(limit=limit)

        # Add formatted data to each session
        for session in sessions:
            session['time_locked_in_formatted'] = self._format_duration(
                session['time_locked_in_seconds']
            )
            session['duration_formatted'] = self._format_duration(
                session['duration_seconds']
            )

            # Calculate completion percentage
            if session['duration_seconds'] > 0:
                completion = (session['time_locked_in_seconds'] /
                             session['duration_seconds']) * 100
                session['completion_percentage'] = min(100, completion)
            else:
                session['completion_percentage'] = 0

        return sessions

    def get_weekly_stats(self) -> Dict[str, Any]:
        """
        Get statistics for the past week

        Returns:
            Weekly statistics
        """
        sessions = self.db_manager.get_recent_sessions_summary(days=7)

        total_time = sum(s['time_locked_in_seconds'] for s in sessions)
        total_blocked = sum(s['apps_blocked_count'] for s in sessions)

        return {
            'total_sessions': len(sessions),
            'total_time_seconds': total_time,
            'total_time_formatted': self._format_duration(total_time),
            'total_apps_blocked': total_blocked,
            'avg_session_duration': total_time // len(sessions) if sessions else 0,
            'emergency_exits': sum(s['emergency_exit_used'] for s in sessions),
            'sessions': sessions
        }

    def get_daily_breakdown(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Get daily breakdown of focus time

        Args:
            days: Number of days to look back

        Returns:
            List of daily statistics
        """
        sessions = self.db_manager.get_recent_sessions_summary(days=days)

        # Group by day
        daily_data = {}
        for session in sessions:
            # Parse date (assuming ISO format from SQLite)
            created_at = session['created_at']
            try:
                date_obj = datetime.fromisoformat(created_at)
                date_key = date_obj.strftime('%Y-%m-%d')

                if date_key not in daily_data:
                    daily_data[date_key] = {
                        'date': date_key,
                        'sessions': 0,
                        'total_time_seconds': 0,
                        'apps_blocked': 0
                    }

                daily_data[date_key]['sessions'] += 1
                daily_data[date_key]['total_time_seconds'] += session['time_locked_in_seconds']
                daily_data[date_key]['apps_blocked'] += session['apps_blocked_count']

            except (ValueError, KeyError):
                continue

        # Convert to sorted list
        result = []
        for date_key in sorted(daily_data.keys(), reverse=True):
            day_stats = daily_data[date_key]
            day_stats['total_time_formatted'] = self._format_duration(
                day_stats['total_time_seconds']
            )
            result.append(day_stats)

        return result

    def get_most_productive_times(self) -> Dict[str, Any]:
        """
        Analyze when user is most productive

        Returns:
            Statistics about productive times
        """
        sessions = self.db_manager.get_all_sessions(limit=100)

        hour_stats = {hour: {'count': 0, 'total_time': 0} for hour in range(24)}

        for session in sessions:
            try:
                created_at = datetime.fromisoformat(session['created_at'])
                hour = created_at.hour

                hour_stats[hour]['count'] += 1
                hour_stats[hour]['total_time'] += session['time_locked_in_seconds']

            except (ValueError, KeyError):
                continue

        # Find peak hour
        peak_hour = max(hour_stats.items(),
                       key=lambda x: x[1]['total_time'])[0]

        return {
            'peak_hour': peak_hour,
            'peak_hour_formatted': f"{peak_hour:02d}:00",
            'hour_breakdown': hour_stats
        }

    def get_top_blocked_apps(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get most frequently blocked applications

        Args:
            limit: Maximum number of apps to return

        Returns:
            List of top blocked apps with counts
        """
        # Get all sessions
        sessions = self.db_manager.get_all_sessions(limit=1000)

        app_counts = {}

        for session in sessions:
            blocked_apps = self.db_manager.get_blocked_apps_for_session(
                session['id']
            )

            for app in blocked_apps:
                app_name = app['app_name']
                if app_name not in app_counts:
                    app_counts[app_name] = {
                        'app_name': app_name,
                        'total_blocks': 0,
                        'sessions_blocked_in': 0
                    }

                app_counts[app_name]['total_blocks'] += app['blocked_count']
                app_counts[app_name]['sessions_blocked_in'] += 1

        # Sort by total blocks
        sorted_apps = sorted(
            app_counts.values(),
            key=lambda x: x['total_blocks'],
            reverse=True
        )

        return sorted_apps[:limit]

    def get_streak_info(self) -> Dict[str, Any]:
        """
        Calculate current and longest streak

        Returns:
            Streak information
        """
        sessions = self.db_manager.get_all_sessions(limit=365)

        if not sessions:
            return {
                'current_streak': 0,
                'longest_streak': 0,
                'last_session_date': None
            }

        # Get dates with sessions
        session_dates = set()
        for session in sessions:
            try:
                created_at = datetime.fromisoformat(session['created_at'])
                date_key = created_at.date()
                session_dates.add(date_key)
            except (ValueError, KeyError):
                continue

        # Calculate current streak
        current_streak = 0
        check_date = datetime.now().date()

        while check_date in session_dates:
            current_streak += 1
            check_date -= timedelta(days=1)

        # Calculate longest streak
        sorted_dates = sorted(session_dates)
        longest_streak = 0
        current_run = 1

        for i in range(1, len(sorted_dates)):
            if (sorted_dates[i] - sorted_dates[i-1]).days == 1:
                current_run += 1
                longest_streak = max(longest_streak, current_run)
            else:
                current_run = 1

        longest_streak = max(longest_streak, current_run)

        return {
            'current_streak': current_streak,
            'longest_streak': longest_streak,
            'last_session_date': max(session_dates).isoformat() if session_dates else None
        }

    def compare_to_previous(self, session_id: int) -> Dict[str, Any]:
        """
        Compare a session to the previous one

        Args:
            session_id: Session to compare

        Returns:
            Comparison data
        """
        current = self.db_manager.get_session(session_id)
        if not current:
            return {}

        # Get all sessions before this one
        all_sessions = self.db_manager.get_all_sessions(limit=1000)

        # Find previous session
        previous = None
        for session in all_sessions:
            if session['id'] < session_id:
                previous = session
                break

        if not previous:
            return {'has_previous': False}

        # Calculate differences
        time_diff = current['time_locked_in_seconds'] - previous['time_locked_in_seconds']
        apps_blocked_diff = current['apps_blocked_count'] - previous['apps_blocked_count']

        return {
            'has_previous': True,
            'previous_session': previous,
            'time_difference_seconds': time_diff,
            'time_difference_formatted': self._format_duration(abs(time_diff)),
            'time_improved': time_diff > 0,
            'apps_blocked_difference': apps_blocked_diff,
            'completion_rate': (current['time_locked_in_seconds'] /
                               current['duration_seconds'] * 100)
                               if current['duration_seconds'] > 0 else 0
        }

    @staticmethod
    def _format_duration(seconds: int) -> str:
        """
        Format seconds as human-readable duration

        Args:
            seconds: Duration in seconds

        Returns:
            Formatted string (e.g., "2h 30m")
        """
        if seconds < 0:
            seconds = 0

        hours = seconds // 3600
        minutes = (seconds % 3600) // 60

        if hours > 0:
            return f"{hours}h {minutes}m"
        elif minutes > 0:
            return f"{minutes}m"
        else:
            return f"{seconds}s"
