"""
App Blocker - Core application blocking logic
Handles process detection, blocking, and management
"""

import psutil
import time
import sys
import os
from typing import List, Set, Callable, Optional, Dict
from pathlib import Path
from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QFileIconProvider, QStyle, QApplication

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

    # Critical system processes that should NEVER be terminated
    CRITICAL_PROCESSES = {
        # Windows System Processes
        'system', 'smss.exe', 'csrss.exe', 'wininit.exe', 'services.exe',
        'lsass.exe', 'winlogon.exe', 'svchost.exe', 'explorer.exe',
        'dwm.exe', 'taskmgr.exe', 'conhost.exe', 'fontdrvhost.exe',
        'wmi provider host', 'wmiprvse.exe', 'sihost.exe', 'taskhostw.exe',
        'registry', 'memory compression', 'system idle process',

        # Linux System Processes
        'systemd', 'init', 'kthreadd', 'bash', 'sh', 'zsh', 'fish',
        'ssh', 'sshd', 'dbus-daemon', 'systemd-logind',

        # macOS System Processes
        'launchd', 'kernel_task', 'loginwindow', 'WindowServer',
        'Dock', 'Finder', 'SystemUIServer',

        # Python/PyQt (don't kill ourselves!)
        'python', 'python.exe', 'python3', 'python3.exe', 'pythonw.exe',
    }

    # Additional processes to always whitelist - system services and background tasks
    # AGGRESSIVE FILTERING - Hide from Available Apps list (but don't terminate)
    SYSTEM_WHITELIST = {
        # Security and System Tools
        'antimalware service executable', 'windows defender',
        'securityhealthservice.exe', 'msmpeng.exe', 'msedge_pwahelper.exe',
        'windows security notification icon', 'sgrmbroker.exe', 'securityhealthsystray.exe',
        'securityhealthhost.exe',

        # Essential Windows Services
        'runtimebroker.exe', 'searchindexer.exe', 'spoolsv.exe',
        'audiodg.exe', 'consent.exe', 'ctfmon.exe', 'dllhost.exe',
        'backgroundtaskhost.exe', 'applicationframehost.exe',

        # Windows System Apps (hide from user)
        'textinputhost.exe', 'shellexperiencehost.exe', 'searchapp.exe',
        'searchhost.exe', 'startmenuexperiencehost.exe', 'runtimebroker.exe',
        'lockapp.exe', 'windows.warp.jitservice.exe', 'usocoreworker.exe',
        'mobsync.exe', 'unsecapp.exe', 'wermgr.exe', 'winrshost.exe',

        # Windows Update and Maintenance
        'windows update', 'usoclient.exe', 'tiworker.exe', 'trustedinstaller.exe',
        'musnotification.exe', 'musnotifyicon.exe',

        # Drivers and Hardware
        'nvdisplay.container.exe', 'nvcontainer.exe', 'amdrsserv.exe',
        'radiergw.exe', 'igfxem.exe', 'igfxtray.exe', 'hkcmd.exe',
        'atkexcomsvc.exe', 'asustptloader.exe', 'winring0', 'winring0.exe',
        'winring0x64.sys', 'winring0_1_2_0', 'frameviewsdk.exe',

        # Background System Tasks
        'useroobebroker.exe', 'searchprotocolhost.exe', 'searchfilterhost.exe',
        'compattelrunner.exe', 'oobe.exe', 'cloudexperiencehostbroker.exe',

        # Chromium Embedded Framework (CEF) - used by apps like Discord, VS Code
        'cef', 'cefsharp.browsersubprocess.exe', 'cefsharp', 'libcef.dll',

        # .NET and Runtime Components
        'mscorsvw.exe', 'ngen.exe', 'ngentask.exe', 'clr.dll',
        'dotnet.exe', 'msbuild.exe',

        # Windows Background Services
        'gamebarpresencewriter.exe', 'gamebar.exe', 'xboxstat.exe',
        'smartscreen.exe', 'fmapi.exe', 'phoneexperiencehost.exe',
        'yourphone.exe', 'windowsinternalshellexperiencehost.exe',

        # Windows Notifications & UI
        'notificationcontroller.exe', 'notificationplatform.exe',
        'actioncenter.exe', 'cortana.exe', 'msteams', 'skype',

        # System Utilities (hide from user)
        'perfmon.exe', 'resmon.exe', 'mmc.exe', 'eventvwr.exe',
        'certutil.exe', 'netsh.exe', 'powershell.exe', 'cmd.exe',
        'powershell_ise.exe', 'wscript.exe', 'cscript.exe',

        # Driver Framework & Support
        'wudfhost.exe', 'wudfrd.exe', 'sdiagnhost.exe', 'systemsettingsbroker.exe',
        'systemsettings.exe', 'settingssynchost.exe',

        # Windows Subsystem for Linux
        'wsl.exe', 'wslhost.exe', 'wslconfig.exe',

        # Third-Party Background Processes (common utilities that auto-start)
        'teamviewer', 'anydesk', 'logmein', 'ammyy', 'vnc',
        'googlecrashhandler.exe', 'googleupdate.exe',
        'adobearm.exe', 'adobeupdater.exe', 'acrotray.exe',
        'dropbox.exe', 'onedrive.exe', 'icloud', 'googledrive',
        'carbonblack', 'crowdstrike', 'sentinelone', 'cylance',

        # GPU and Display Management
        'nvstreamservice.exe', 'nvstreamsvc.exe', 'nvprofileupdaterservice64.exe',
        'nvidia web helper.exe', 'nvidia share.exe', 'shadowplay',
        'amd', 'radeon', 'ati', 'amdow.exe', 'radeonsoftware.exe',

        # Audio/Video Services
        'iastoricon.exe', 'realtekhdaudiomanager.exe', 'nahimicservice.exe',

        # Antivirus and Security (hide background processes)
        'avast', 'avg', 'malwarebytes', 'norton', 'mcafee',
        'kaspersky', 'bitdefender', 'avira', 'eset', 'sophos',
        'trendmicro', 'webroot', 'comodo',

        # System Management (Dell, HP, Lenovo, etc.)
        'dell', 'hp', 'lenovo', 'asus', 'acer', 'toshiba',
        'samsungmagician', 'intelrapidstoragetechnology',
    }

    # System paths to exclude (processes in these folders are usually system processes)
    SYSTEM_PATHS = [
        'c:\\windows\\system32',
        'c:\\windows\\syswow64',
        'c:\\windows\\systemapps',
        'c:\\windows\\immersivecontrolpanel',
        '/usr/bin',
        '/usr/sbin',
        '/usr/lib',
        '/lib',
        '/System/Library',
    ]

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

    def _is_system_process(self, name: str, exe_path: str) -> bool:
        """
        Check if a process is a system process that should be hidden from the user

        Args:
            name: Process name
            exe_path: Full executable path

        Returns:
            True if it's a system process
        """
        if not name:
            return True

        name_lower = name.lower()

        # Check if it's in critical or system whitelist
        if name_lower in {p.lower() for p in self.CRITICAL_PROCESSES}:
            return True

        if name_lower in {p.lower() for p in self.SYSTEM_WHITELIST}:
            return True

        # Check if exe path is in system paths
        if exe_path:
            exe_path_lower = exe_path.lower()
            for sys_path in self.SYSTEM_PATHS:
                if exe_path_lower.startswith(sys_path.lower()):
                    return True

        # AGGRESSIVE FILTERING - Filter out common background processes and services
        system_keywords = [
            'service', 'host', 'broker', 'helper', 'installer', 'update',
            'driver', 'daemon', 'agent', 'notif', 'manager', 'loader',
            'crash', 'reporter', 'handler', 'sync', 'protocol', 'filter',
            'compatibility', 'telemetry', 'diagnostics', 'feedback',
            'framework', 'sdk', 'runtime', 'subprocess', 'wrapper',
            'watchdog', 'monitor', 'launcher', 'bootstrapper', 'pwa',
        ]
        for keyword in system_keywords:
            if keyword in name_lower:
                return True

        # Filter out processes with certain patterns (more aggressive)
        # Filter CEF (Chromium Embedded Framework) subprocesses
        if 'cef' in name_lower or 'renderer' in name_lower or 'gpu-process' in name_lower:
            return True

        # Filter crash/error handlers
        if 'crash' in name_lower or 'dump' in name_lower or 'error' in name_lower:
            return True

        # Filter updaters
        if 'updat' in name_lower or 'download' in name_lower:
            return True

        return False

    def _get_friendly_app_name(self, process_name: str, exe_path: str) -> str:
        """
        Get a friendly display name for an application

        Args:
            process_name: Process name (e.g., "chrome.exe")
            exe_path: Full path to executable

        Returns:
            Friendly name (e.g., "Chrome")
        """
        # Remove .exe extension
        name = process_name
        if name.lower().endswith('.exe'):
            name = name[:-4]

        # Try to extract from path if available
        if exe_path:
            path_obj = Path(exe_path)
            parent_name = path_obj.parent.name

            # Use parent folder name for better clarity
            # e.g., "Google\\Chrome\\Application\\chrome.exe" -> use "Chrome"
            if parent_name.lower() not in ['bin', 'application', 'app', 'program files', 'program files (x86)']:
                name = parent_name

        # Capitalize properly
        # Handle camelCase (e.g., "msedge" -> "MS Edge")
        if name.islower() or name.isupper():
            name = name.title()

        return name

    def _get_app_icon(self, exe_path: str) -> Optional[QIcon]:
        """
        Try to extract icon from executable

        Args:
            exe_path: Path to executable

        Returns:
            QIcon if found, None otherwise
        """
        if not exe_path or not os.path.exists(exe_path):
            return None

        try:
            # Use Qt's file icon provider (works cross-platform)
            icon_provider = QFileIconProvider()
            icon = icon_provider.icon(QFileIconProvider.IconType.File)

            # Try to get specific file icon
            from PyQt6.QtCore import QFileInfo
            file_info = QFileInfo(exe_path)
            file_icon = icon_provider.icon(file_info)

            if not file_icon.isNull():
                return file_icon

            return icon if not icon.isNull() else None

        except Exception:
            return None

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

                    # Skip system processes
                    if self._is_system_process(name, exe_path):
                        continue

                    seen.add(name.lower())

                    # Get friendly display name
                    display_name = self._get_friendly_app_name(name, exe_path)

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
            List of dicts with 'name', 'display_name', 'path', and 'icon' keys
        """
        apps = {}  # Use dict to avoid duplicates, keyed by display_name

        # First, get all running apps
        running_apps = self.get_running_apps()
        for app in running_apps:
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
                            if file.lower().endswith('.exe') and file.lower() != 'uninstall.exe':
                                exe_path = os.path.join(root, file)

                                # Skip system processes
                                if self._is_system_process(file, exe_path):
                                    continue

                                # Get friendly name
                                display_name = self._get_friendly_app_name(file, exe_path)

                                # Skip if already in our list
                                if display_name in apps:
                                    continue

                                # Try to get icon
                                icon = self._get_app_icon(exe_path)

                                apps[display_name] = {
                                    'name': file,
                                    'display_name': display_name,
                                    'path': exe_path,
                                    'icon': icon
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
                                            'icon': icon
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
                                    'icon': icon
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
        """Get the number of processes that have been blocked"""
        return len([p for p in self.known_processes.values() if p])
