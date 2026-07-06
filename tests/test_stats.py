"""
Tests for the database layer and stats tracker.

Uses a throwaway SQLite file per test - no Qt, no psutil.
"""

import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager
from core.stats_tracker import StatsTracker

try:
    # Needs PyQt6 + psutil; skipped in environments without them.
    from core.session_manager import SessionManager
    HAS_QT = True
except ImportError:
    HAS_QT = False


class StatsTestCase(unittest.TestCase):

    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        self.db = DatabaseManager(db_path=self.db_path)
        self.stats = StatsTracker(self.db)

    def tearDown(self):
        self.db.close()
        os.unlink(self.db_path)

    # ---- helpers

    def _finished_session(self, name='s', locked=600, created_at=None) -> int:
        sid = self.db.create_session(name, 1500, ['code.exe'])
        self.db.end_session(sid, time_locked_in=locked)
        if created_at is not None:
            cur = self.db.connection.cursor()
            cur.execute("UPDATE sessions SET created_at = ? WHERE id = ?",
                        (created_at, sid))
            self.db.connection.commit()
        return sid

    # ---- created_at is local time

    def test_created_at_is_local_time(self):
        sid = self._finished_session()
        session = self.db.get_session(sid)
        created = datetime.fromisoformat(session['created_at'])
        # Must be within a minute of local now - not shifted by a UTC offset.
        self.assertLess(abs((datetime.now() - created).total_seconds()), 60)

    # ---- top blocked apps aggregate

    def test_top_blocked_apps_aggregates_across_sessions(self):
        s1 = self._finished_session('a')
        s2 = self._finished_session('b')
        for _ in range(3):
            self.db.record_blocked_app(s1, 'discord.exe')
        self.db.record_blocked_app(s1, 'steam.exe')
        for _ in range(2):
            self.db.record_blocked_app(s2, 'discord.exe')

        top = self.db.get_top_blocked_apps(limit=5)
        self.assertEqual(top[0]['app_name'], 'discord.exe')
        self.assertEqual(top[0]['total_blocks'], 5)
        self.assertEqual(top[0]['sessions_blocked_in'], 2)
        self.assertEqual(top[1]['app_name'], 'steam.exe')
        self.assertEqual(top[1]['total_blocks'], 1)

    # ---- previous-session lookup

    def test_get_session_before_skips_unfinished(self):
        first = self._finished_session('first', locked=300)
        # An unfinished session in between must not count as "previous".
        self.db.create_session('abandoned', 1500, [])
        current = self._finished_session('current', locked=900)

        prev = self.db.get_session_before(current)
        self.assertIsNotNone(prev)
        self.assertEqual(prev['id'], first)

    def test_get_session_before_none_for_first(self):
        sid = self._finished_session()
        self.assertIsNone(self.db.get_session_before(sid))

    def test_compare_to_previous(self):
        self._finished_session('first', locked=300)
        current = self._finished_session('current', locked=900)
        comp = self.stats.compare_to_previous(current)
        self.assertTrue(comp['has_previous'])
        self.assertEqual(comp['time_difference_seconds'], 600)
        self.assertTrue(comp['time_improved'])

    # ---- streaks

    def _session_on(self, day):
        self._finished_session(created_at=datetime.combine(
            day, datetime.min.time().replace(hour=10)))

    def test_streak_survives_today_without_session(self):
        today = datetime.now().date()
        self._session_on(today - timedelta(days=2))
        self._session_on(today - timedelta(days=1))

        info = self.stats.get_streak_info()
        self.assertEqual(info['current_streak'], 2)

    def test_streak_includes_today(self):
        today = datetime.now().date()
        self._session_on(today - timedelta(days=1))
        self._session_on(today)

        info = self.stats.get_streak_info()
        self.assertEqual(info['current_streak'], 2)

    def test_streak_broken_by_gap(self):
        today = datetime.now().date()
        self._session_on(today - timedelta(days=5))
        self._session_on(today - timedelta(days=4))
        self._session_on(today)

        info = self.stats.get_streak_info()
        self.assertEqual(info['current_streak'], 1)
        self.assertEqual(info['longest_streak'], 2)

    # ---- timestamps stored as plain strings (no deprecated adapters)

    def test_timestamps_are_strings(self):
        sid = self._finished_session()
        session = self.db.get_session(sid)
        for field in ('created_at', 'started_at', 'ended_at'):
            self.assertIsInstance(session[field], str)
            datetime.fromisoformat(session[field])  # must parse

    # ---- settings roundtrip

    def test_settings_roundtrip(self):
        self.assertEqual(self.db.get_setting('missing', 'fallback'), 'fallback')
        self.db.set_setting('theme', 'dark')
        self.assertEqual(self.db.get_setting('theme'), 'dark')
        self.db.set_setting('theme', 'light')
        self.assertEqual(self.db.get_setting('theme'), 'light')

    def test_fresh_database_defaults_to_light_theme(self):
        self.assertEqual(self.db.get_setting('theme'), 'light')

    # ---- update_session guard

    def test_update_session_rejects_unknown_field(self):
        sid = self._finished_session()
        with self.assertRaises(ValueError):
            self.db.update_session(sid, no_such_column=1)

    # ---- blocked count written once at session end

    def test_apps_blocked_count_not_double_counted(self):
        sid = self._finished_session()
        for _ in range(4):
            self.db.record_blocked_app(sid, 'discord.exe')
        # record_blocked_app must not touch the session row counter ...
        self.assertEqual(self.db.get_session(sid)['apps_blocked_count'], 0)
        # ... that is written once, at session end.
        self.db.update_session(sid, apps_blocked_count=4)
        self.assertEqual(self.db.get_session(sid)['apps_blocked_count'], 4)


@unittest.skipUnless(HAS_QT, "PyQt6/psutil not installed")
class PauseClockTestCase(unittest.TestCase):
    """The session clock must freeze while paused."""

    def setUp(self):
        import time as _time
        self._time = _time
        fd, self.db_path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        self.db = DatabaseManager(db_path=self.db_path)
        self.sm = SessionManager(self.db)

    def tearDown(self):
        self.db.close()
        os.unlink(self.db_path)

    def test_elapsed_excludes_paused_time(self):
        now = self._time.time()
        self.sm.session_start_time = now - 100
        self.sm.total_paused = 40.0
        self.assertAlmostEqual(self.sm.get_elapsed_time(), 60, delta=2)

    def test_elapsed_frozen_while_paused(self):
        now = self._time.time()
        self.sm.session_start_time = now - 100
        self.sm.paused_at = now - 10  # clock stopped 10s ago
        self.assertAlmostEqual(self.sm.get_elapsed_time(), 90, delta=2)


if __name__ == '__main__':
    unittest.main()
