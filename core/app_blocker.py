"""
App Blocker - Core application blocking logic
Handles process detection, blocking, and management
"""

import psutil
import time
import sys
from typing import List, Set, Callable, Optional, Dict
from pathlib import Path
from PyQt6.QtCore import QObject, QTimer, pyqtSignal


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

    # Critical system processes that should NEVER be terminated
    CRITICAL_PROCESSES = {
        # Windows System Processes
        'system', 'smss.exe', 'csrss.exe', 'wininit.exe', 'services.exe',
        'lsass.exe', 'winlogon.exe', 'svchost.exe', 'explorer.exe',
        'dwm.exe', 'taskmgr.exe', 'conhost.exe', 'fontdrvhost.exe',

        # Linux System Processes
        'systemd', 'init', 'kthreadd', 'bash', 'sh', 'zsh', 'fish',
        'ssh', 'sshd', 'dbus-daemon', 'systemd-logind',

        # macOS System Processes
        'launchd', 'kernel_task', 'loginwindow', 'WindowServer',
        'Dock', 'Finder', 'SystemUIServer',

        # Python/PyQt (don't kill ourselves!)
        'python', 'python.exe', 'python3', 'python3.exe', 'pythonw.exe',
    }

    # Additional processes to always whitelist
    SYSTEM_WHITELIST = {
        # Security and System Tools
        'antimalware service executable', 'windows defender',
        'securityhealthservice.exe', 'msmpeng.exe',

        # Essential Windows Services
        'runtimebroker.exe', 'searchindexer.exe', 'spoolsv.exe',
        'audiodg.exe', 'consent.exe', 'ctfmon.exe',
    }

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

    def set_whitelisted_apps(self, apps: List[str]) -> None:
        """
        Set the list of whitelisted applications

        Args:
            apps: List of app names or paths to whitelist
        """
        self.whitelisted_apps = set()

        # Normalize app names/paths
        for app in apps:
            app_lower = app.lower()
            self.whitelisted_apps.add(app_lower)

            # Also add just the filename if a full path was provided
            if '/' in app or '\\' in app:
                filename = Path(app).name.lower()
                self.whitelisted_apps.add(filename)

        # Always include critical and system processes
        self.whitelisted_apps.update(
            p.lower() for p in self.CRITICAL_PROCESSES
        )
        self.whitelisted_apps.update(
            p.lower() for p in self.SYSTEM_WHITELIST
        )

    def start_monitoring(self) -> None:
        """Start monitoring and blocking processes"""
        if self.is_monitoring:
            return

        self.is_monitoring = True
        self.known_processes.clear()

        # Scan current processes and mark whitelisted ones
        self._scan_initial_processes()

        # Start the monitoring timer
        self.monitor_timer.start(self.monitor_interval)

    def stop_monitoring(self) -> None:
        """Stop monitoring processes"""
        self.is_monitoring = False
        self.monitor_timer.stop()
        self.known_processes.clear()

    def _scan_initial_processes(self) -> None:
        """Scan and whitelist all currently running processes"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'exe']):
                try:
                    pid = proc.info['pid']
                    name = proc.info['name'] or ''

                    # Add to known processes
                    self.known_processes[pid] = name

                    # If it's whitelisted, mark it
                    if self._is_whitelisted(name, proc.info.get('exe', '')):
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
            current_pids = set()

            for proc in psutil.process_iter(['pid', 'name', 'exe', 'create_time']):
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

        name_lower = name.lower()

        # Check if name matches any whitelisted app
        if name_lower in self.whitelisted_apps:
            return True

        # Check if exe path matches
        if exe_path:
            exe_path_lower = exe_path.lower()

            # Check full path
            if exe_path_lower in self.whitelisted_apps:
                return True

            # Check if any whitelisted app is in the path
            for whitelisted in self.whitelisted_apps:
                if whitelisted in exe_path_lower or whitelisted in name_lower:
                    return True

        # Check if it's a critical process
        if name_lower in {p.lower() for p in self.CRITICAL_PROCESSES}:
            return True

        if name_lower in {p.lower() for p in self.SYSTEM_WHITELIST}:
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

            # Try to terminate gracefully first
            proc.terminate()

            # Wait briefly for termination
            try:
                proc.wait(timeout=1)
            except psutil.TimeoutExpired:
                # Force kill if needed
                proc.kill()

            # Mark as known (blocked)
            self.known_processes[pid] = name

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

    def get_running_apps(self) -> List[Dict[str, str]]:
        """
        Get list of all currently running applications

        Returns:
            List of dicts with 'name' and 'path' keys
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

                    seen.add(name.lower())
                    apps.append({
                        'name': name,
                        'path': exe_path
                    })

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

        except Exception as e:
            self.error_occurred.emit(f"Error getting running apps: {str(e)}")

        return sorted(apps, key=lambda x: x['name'].lower())

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
        """Get the number of processes that have been blocked"""
        return len([p for p in self.known_processes.values() if p])
