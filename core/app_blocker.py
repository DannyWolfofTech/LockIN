"""
App Blocker - Core application blocking logic
Handles process detection, blocking, and management
"""

import psutil
import sys
import os
from typing import List, Set, Optional, Dict
from pathlib import Path
from PyQt6.QtCore import QObject, QTimer, pyqtSignal, QFileInfo
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QFileIconProvider

from core.app_filter import (
    is_displayable, is_protected, is_garbage_name, friendly_name,
)

# Optional imports for Windows icon extraction
try:
    import win32api
    import win32con
    import win32gui
    WINDOWS_ICONS_AVAILABLE = True
except ImportError:
    WINDOWS_ICONS_AVAILABLE = False


class AppBlocker(QObject):
    """
    Manages application blocking and monitoring

    Signals:
        app_blocked: Emitted when an app is blocked (app_name, app_path)
        app_launched: Emitted when a whitelisted app is launched (app_name)
        error_occurred: Emitted when an error occurs (error_message)
    """

    # Signals
    app_blocked = pyqtSignal(str, str)  # app_name, app_path
    app_launched = pyqtSignal(str)  # app_name
    error_occurred = pyqtSignal(str)  # error_message

    def __init__(self, parent=None):
        """Initialize the app blocker"""
        super().__init__(parent)

        self.whitelisted_apps: Set[str] = set()
        self.whitelisted_processes: Set[int] = set()  # PIDs of whitelisted apps
        self.is_monitoring = False
        self.monitor_interval = 1000  # Check every 1 second

        # Timer for monitoring
        self.monitor_timer = QTimer(self)
        self.monitor_timer.timeout.connect(self._check_processes)

        # Cache of known processes to avoid repeated blocking attempts
        self.known_processes: Dict[int, str] = {}

        # PIDs that were sent terminate() and get force-killed on the
        # next tick if still alive - never block the event loop waiting.
        self._pending_kill: Set[int] = set()
        self.blocked_count = 0

        # Icon lookups are expensive on large scans - share one provider
        # and cache per executable path.
        self._icon_provider: Optional[QFileIconProvider] = None
        self._icon_cache: Dict[str, Optional[QIcon]] = {}

    def set_whitelisted_apps(self, apps: List[str]) -> None:
        """
        Set the list of whitelisted applications

        Args:
            apps: List of app names or paths to whitelist
        """
        self.whitelisted_apps = set()

        # Normalize app names/paths. Only USER choices live here -
        # system safety is handled separately by app_filter.is_protected,
        # so a stray short token can't accidentally whitelist the world.
        for app in apps:
            app_lower = app.lower()
            self.whitelisted_apps.add(app_lower)

            # Also add just the filename if a full path was provided
            if '/' in app or '\\' in app:
                filename = Path(app).name.lower()
                self.whitelisted_apps.add(filename)

    def start_monitoring(self) -> None:
        """Start monitoring and blocking processes"""
        if self.is_monitoring:
            return

        self.is_monitoring = True
        self.known_processes.clear()
        self._pending_kill.clear()
        self.blocked_count = 0

        # Scan current processes and mark whitelisted ones
        self._scan_initial_processes()

        # Start the monitoring timer
        self.monitor_timer.start(self.monitor_interval)

    def stop_monitoring(self) -> None:
        """Stop monitoring processes"""
        self.is_monitoring = False
        self.monitor_timer.stop()
        self.known_processes.clear()
        self._pending_kill.clear()

    def _scan_initial_processes(self) -> None:
        """Record currently running whitelisted processes.

        Non-whitelisted processes are deliberately NOT marked known:
        anything that survived the initial close sweep (slow shutdown,
        ignored terminate) gets picked up and blocked by the first
        monitoring tick instead of being grandfathered in.
        """
        try:
            for proc in psutil.process_iter(['pid', 'name', 'exe']):
                try:
                    pid = proc.info['pid']
                    name = proc.info['name'] or ''

                    if self._is_whitelisted(name, proc.info.get('exe', '')):
                        self.known_processes[pid] = name
                        self.whitelisted_processes.add(pid)

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

        except Exception as e:
            self.error_occurred.emit(f"Error scanning initial processes: {str(e)}")

    def _check_processes(self) -> None:
        """Check all running processes and block non-whitelisted ones"""
        if not self.is_monitoring:
            return

        try:
            # Force-kill anything that ignored terminate() last tick
            for pid in list(self._pending_kill):
                self._pending_kill.discard(pid)
                try:
                    psutil.Process(pid).kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            current_pids = set()

            for proc in psutil.process_iter(['pid', 'name', 'exe']):
                try:
                    pid = proc.info['pid']
                    current_pids.add(pid)

                    # Skip if already known and whitelisted
                    if pid in self.whitelisted_processes:
                        continue

                    # Skip if already known and processed
                    if pid in self.known_processes:
                        continue

                    name = proc.info['name'] or ''
                    exe_path = proc.info.get('exe', '') or ''

                    # Check if this process should be whitelisted
                    if self._is_whitelisted(name, exe_path):
                        self.known_processes[pid] = name
                        self.whitelisted_processes.add(pid)
                        continue

                    # This is a new non-whitelisted process - block it
                    self._block_process(proc, name, exe_path)

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            # Clean up tracking for processes that no longer exist
            self._cleanup_dead_processes(current_pids)

        except Exception as e:
            self.error_occurred.emit(f"Error checking processes: {str(e)}")

    def _is_whitelisted(self, name: str, exe_path: str) -> bool:
        """
        Check if a process is whitelisted

        Args:
            name: Process name
            exe_path: Full executable path

        Returns:
            True if whitelisted
        """
        if not name:
            return True  # Skip unnamed processes

        # Safety net: critical processes, system paths, security software
        if is_protected(name, exe_path):
            return True

        name_lower = name.lower()
        stem = name_lower[:-4] if name_lower.endswith('.exe') else name_lower
        path_lower = (exe_path or '').lower()

        # Match against the user's whitelist: exact name/stem, or the
        # whitelisted entry (e.g. a display name like "chrome") appearing
        # in the process name or its install path.
        for entry in self.whitelisted_apps:
            if entry in (name_lower, stem):
                return True
            if entry in name_lower:
                return True
            if path_lower and entry in path_lower:
                return True

        return False

    def _block_process(self, proc: psutil.Process, name: str, exe_path: str) -> None:
        """
        Block (terminate) a process

        Args:
            proc: psutil Process object
            name: Process name
            exe_path: Process executable path
        """
        try:
            pid = proc.pid

            # Double-check we're not killing a critical process
            if self._is_whitelisted(name, exe_path):
                return

            # Terminate without waiting - blocking the event loop here
            # froze the UI for up to a second per process. If it's still
            # alive next tick, _check_processes force-kills it.
            proc.terminate()
            self._pending_kill.add(pid)

            # Mark as known (blocked)
            self.known_processes[pid] = name
            self.blocked_count += 1

            # Emit signal
            self.app_blocked.emit(name, exe_path)

        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            # Process already gone or can't access - that's fine
            pass
        except Exception as e:
            self.error_occurred.emit(f"Error blocking {name}: {str(e)}")

    def _cleanup_dead_processes(self, current_pids: Set[int]) -> None:
        """
        Remove tracking for processes that no longer exist

        Args:
            current_pids: Set of currently active PIDs
        """
        # Clean up known processes
        dead_pids = set(self.known_processes.keys()) - current_pids
        for pid in dead_pids:
            self.known_processes.pop(pid, None)
            self.whitelisted_processes.discard(pid)
            self._pending_kill.discard(pid)

    def _get_app_icon(self, exe_path: str) -> Optional[QIcon]:
        """
        Try to extract icon from executable

        Args:
            exe_path: Path to executable

        Returns:
            QIcon if found, None otherwise
        """
        if not exe_path:
            return None
        if exe_path in self._icon_cache:
            return self._icon_cache[exe_path]

        icon = None
        try:
            if os.path.exists(exe_path):
                if self._icon_provider is None:
                    self._icon_provider = QFileIconProvider()
                file_icon = self._icon_provider.icon(QFileInfo(exe_path))
                if not file_icon.isNull():
                    icon = file_icon
        except Exception:
            icon = None

        self._icon_cache[exe_path] = icon
        return icon

    def get_running_apps(self) -> List[Dict[str, str]]:
        """
        Get list of all currently running USER applications (filters out system processes)

        Returns:
            List of dicts with 'name', 'display_name', 'path', and 'icon' keys
        """
        apps = []
        seen = set()

        try:
            for proc in psutil.process_iter(['name', 'exe']):
                try:
                    name = proc.info['name']
                    exe_path = proc.info.get('exe', '') or ''

                    if not name or name.lower() in seen:
                        continue

                    # Positive heuristic: must look like a real user app
                    if not is_displayable(name, exe_path):
                        continue

                    # Friendly display name (climbs out of version dirs);
                    # if even that comes out as garbage, drop the entry.
                    display_name = friendly_name(name, exe_path)
                    if is_garbage_name(display_name):
                        continue

                    seen.add(name.lower())

                    # Try to get icon
                    icon = self._get_app_icon(exe_path)

                    apps.append({
                        'name': name,  # Original process name
                        'display_name': display_name,  # Friendly name to show user
                        'path': exe_path,
                        'icon': icon
                    })

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

        except Exception as e:
            self.error_occurred.emit(f"Error getting running apps: {str(e)}")

        return sorted(apps, key=lambda x: x['display_name'].lower())

    def get_all_installed_apps(self) -> List[Dict[str, str]]:
        """
        Get ALL installed applications on the system (running + installed)

        Returns:
            List of dicts with 'name', 'display_name', 'path', 'icon',
            and 'running' keys. Callers should use the 'running' flag
            instead of doing a second process scan.
        """
        apps = {}  # Use dict to avoid duplicates, keyed by display_name

        # First, get all running apps
        running_apps = self.get_running_apps()
        for app in running_apps:
            app['running'] = True
            apps[app['display_name']] = app

        # Then scan common installation directories
        install_dirs = []

        if sys.platform == 'win32':
            # Windows installation directories
            install_dirs = [
                'C:\\Program Files',
                'C:\\Program Files (x86)',
                os.path.expanduser('~\\AppData\\Local\\Programs'),
                os.path.expanduser('~\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs'),
            ]
        elif sys.platform.startswith('linux'):
            # Linux application directories
            install_dirs = [
                '/usr/share/applications',
                '/usr/local/share/applications',
                os.path.expanduser('~/.local/share/applications'),
            ]
        elif sys.platform == 'darwin':
            # macOS application directories
            install_dirs = [
                '/Applications',
                '/System/Applications',
                os.path.expanduser('~/Applications'),
            ]

        # Scan installation directories
        for base_dir in install_dirs:
            if not os.path.exists(base_dir):
                continue

            try:
                # For Windows, look for .exe files
                if sys.platform == 'win32':
                    for root, dirs, files in os.walk(base_dir):
                        # Limit depth to avoid scanning too deep
                        depth = root[len(base_dir):].count(os.sep)
                        if depth > 2:
                            continue

                        for file in files:
                            if file.lower().endswith('.exe'):
                                exe_path = os.path.join(root, file)

                                # Must look like a real user app
                                if not is_displayable(file, exe_path):
                                    continue

                                # Friendly name; drop if it resolves to garbage
                                display_name = friendly_name(file, exe_path)
                                if is_garbage_name(display_name):
                                    continue

                                # Skip if already in our list
                                if display_name in apps:
                                    continue

                                # Try to get icon
                                icon = self._get_app_icon(exe_path)

                                apps[display_name] = {
                                    'name': file,
                                    'display_name': display_name,
                                    'path': exe_path,
                                    'icon': icon,
                                    'running': False
                                }

                # For Linux, look for .desktop files
                elif sys.platform.startswith('linux'):
                    for file in os.listdir(base_dir):
                        if file.endswith('.desktop'):
                            desktop_path = os.path.join(base_dir, file)
                            # Parse .desktop file to get app name and executable
                            try:
                                with open(desktop_path, 'r') as f:
                                    lines = f.readlines()
                                    app_name = None
                                    exec_path = None
                                    for line in lines:
                                        if line.startswith('Name='):
                                            app_name = line.split('=', 1)[1].strip()
                                        elif line.startswith('Exec='):
                                            exec_path = line.split('=', 1)[1].strip()

                                    if app_name and app_name not in apps:
                                        icon = self._get_app_icon(exec_path if exec_path else '')
                                        apps[app_name] = {
                                            'name': app_name,
                                            'display_name': app_name,
                                            'path': exec_path or '',
                                            'icon': icon,
                                            'running': False
                                        }
                            except:
                                continue

                # For macOS, look for .app bundles
                elif sys.platform == 'darwin':
                    for item in os.listdir(base_dir):
                        if item.endswith('.app'):
                            app_path = os.path.join(base_dir, item)
                            app_name = item[:-4]  # Remove .app extension

                            if app_name not in apps:
                                icon = self._get_app_icon(app_path)
                                apps[app_name] = {
                                    'name': item,
                                    'display_name': app_name,
                                    'path': app_path,
                                    'icon': icon,
                                    'running': False
                                }

            except Exception as e:
                # Continue on error, don't break the whole scan
                continue

        # Convert dict to sorted list
        return sorted(apps.values(), key=lambda x: x['display_name'].lower())

    def close_all_non_whitelisted_apps(self) -> int:
        """
        Close all non-whitelisted applications immediately

        Returns:
            Number of apps closed
        """
        closed_count = 0

        try:
            for proc in psutil.process_iter(['pid', 'name', 'exe']):
                try:
                    pid = proc.info['pid']
                    name = proc.info['name'] or ''
                    exe_path = proc.info.get('exe', '') or ''

                    # Skip whitelisted
                    if self._is_whitelisted(name, exe_path):
                        self.whitelisted_processes.add(pid)
                        continue

                    # Try to terminate
                    proc.terminate()
                    closed_count += 1

                    # Emit signal
                    self.app_blocked.emit(name, exe_path)

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

        except Exception as e:
            self.error_occurred.emit(f"Error closing apps: {str(e)}")

        return closed_count

    def get_blocked_count(self) -> int:
        """Get the number of processes blocked since monitoring started"""
        return self.blocked_count
