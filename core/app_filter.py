"""
Pure heuristics for deciding what is a real user application.

No Qt, no psutil - just names and paths in, booleans and strings out.
This keeps the logic unit-testable and in one place. AppBlocker
delegates here for everything except actual process management.

Two separate questions, two separate answers:

    is_displayable(...)  - should this appear in the app picker?
                           (positive heuristic: prove you're a user app)
    is_protected(...)    - must this never be terminated?
                           (safety net: critical names + system paths)
"""

import os
import re
import sys

# ---------------------------------------------------------------- constants

# Processes that must NEVER be terminated, on any platform.
CRITICAL_PROCESSES = {
    # Windows
    'system', 'smss.exe', 'csrss.exe', 'wininit.exe', 'services.exe',
    'lsass.exe', 'winlogon.exe', 'svchost.exe', 'explorer.exe',
    'dwm.exe', 'taskmgr.exe', 'conhost.exe', 'fontdrvhost.exe',
    'wmiprvse.exe', 'sihost.exe', 'taskhostw.exe',
    'registry', 'memory compression', 'system idle process',
    # Linux
    'systemd', 'init', 'kthreadd', 'bash', 'sh', 'zsh', 'fish',
    'ssh', 'sshd', 'dbus-daemon', 'systemd-logind',
    # macOS
    'launchd', 'kernel_task', 'loginwindow', 'windowserver',
    'dock', 'finder', 'systemuiserver',
    # Ourselves
    'python', 'python.exe', 'python3', 'python3.exe', 'pythonw.exe',
}

# Exact process names that are system noise: never shown, never killed.
SYSTEM_NOISE = {
    'msmpeng.exe', 'securityhealthservice.exe', 'securityhealthsystray.exe',
    'securityhealthhost.exe', 'sgrmbroker.exe', 'runtimebroker.exe',
    'searchindexer.exe', 'spoolsv.exe', 'audiodg.exe', 'consent.exe',
    'ctfmon.exe', 'dllhost.exe', 'backgroundtaskhost.exe',
    'applicationframehost.exe', 'textinputhost.exe',
    'shellexperiencehost.exe', 'searchapp.exe', 'searchhost.exe',
    'startmenuexperiencehost.exe', 'lockapp.exe', 'usocoreworker.exe',
    'mobsync.exe', 'unsecapp.exe', 'wermgr.exe', 'usoclient.exe',
    'tiworker.exe', 'trustedinstaller.exe', 'musnotification.exe',
    'nvdisplay.container.exe', 'nvcontainer.exe', 'amdrsserv.exe',
    'igfxem.exe', 'igfxtray.exe', 'hkcmd.exe', 'frameviewsdk.exe',
    'useroobebroker.exe', 'searchprotocolhost.exe', 'searchfilterhost.exe',
    'compattelrunner.exe', 'mscorsvw.exe', 'ngen.exe', 'ngentask.exe',
    'gamebarpresencewriter.exe', 'gamebar.exe', 'smartscreen.exe',
    'phoneexperiencehost.exe', 'yourphone.exe', 'wudfhost.exe',
    'sdiagnhost.exe', 'systemsettingsbroker.exe', 'systemsettings.exe',
    'settingssynchost.exe', 'wsl.exe', 'wslhost.exe', 'wslconfig.exe',
    'googlecrashhandler.exe', 'googleupdate.exe', 'adobearm.exe',
    'adobeupdater.exe', 'acrotray.exe', 'perfmon.exe', 'resmon.exe',
    'mmc.exe', 'eventvwr.exe', 'powershell.exe', 'cmd.exe',
    'wscript.exe', 'cscript.exe',
}

# Substring tokens (>= 5 chars, name only) protecting security software
# that lives outside the Windows system directories.
PROTECTED_NAME_TOKENS = (
    'defender', 'avast', 'mcafee', 'norton', 'kaspersky', 'bitdefender',
    'malwarebytes', 'avira', 'sophos', 'trendmicro', 'webroot',
    'crowdstrike', 'sentinelone', 'carbonblack', 'cylance',
)

# Exe-stem tokens that mark helper/subprocess executables of real apps.
HELPER_TOKENS = (
    'crashpad', 'crashhandler', 'crashreport', 'crash_handler',
    'updater', 'update', 'setup', 'install', 'unins',
    'watchdog', 'telemetry', 'diagnostic', 'reporter', 'elevat',
    'broker', 'daemon', 'browsersubprocess', 'renderer', 'gpu-process',
    'plugin-container', 'notification_helper', 'helper',
)

# Directory names that say nothing about which app this is.
GENERIC_DIRS = {
    'bin', 'app', 'apps', 'application', 'applications', 'current',
    'dist', 'release', 'x64', 'x86', 'win32', 'win64', 'resources',
    'program files', 'program files (x86)', 'programs', 'common files',
    'windowsapps', 'local', 'roaming', 'appdata',
}

_VERSION_TRIPLET = re.compile(r'\d+\.\d+\.\d+')
_NUMERIC_ONLY = re.compile(r'^[\d.,_\-]+$')


# ---------------------------------------------------------------- helpers

def _stem(name: str) -> str:
    """Process name without a trailing .exe/.app extension."""
    lower = name.lower()
    for ext in ('.exe', '.app'):
        if lower.endswith(ext):
            return name[: -len(ext)]
    return name


def is_garbage_name(name: str) -> bool:
    """True for version strings, package IDs, and similar non-names.

    Careful to keep legit digit-led apps ("7-Zip", "1Password").
    """
    s = _stem(name).strip()
    if not s:
        return True
    if len(s) > 40:
        return True
    if _NUMERIC_ONLY.match(s):                  # "142.0.3595.53"
        return True
    if _VERSION_TRIPLET.search(s):              # "app-1.0.9", "2.2543.1.0_x64"
        return True
    if '__' in s or s.count('_') >= 2:          # store package IDs
        return True
    return False


def is_helper_name(name: str) -> bool:
    """True for crash handlers, updaters, and other app subprocesses."""
    s = _stem(name).lower()
    return any(token in s for token in HELPER_TOKENS)


def _windows_user_path(path_lower: str) -> bool:
    """Path patterns where user-installed apps live on Windows.

    Pattern-based on purpose (not env vars) so behaviour doesn't
    depend on the environment of the process doing the asking.
    """
    return (
        '\\program files' in path_lower      # any drive
        or '\\users\\' in path_lower         # AppData, Desktop, scoop, ...
        or '\\programdata\\' in path_lower
    )


def _is_under(path_lower: str, roots) -> bool:
    return any(path_lower.startswith(root) for root in roots)


def is_system_path(exe_path: str, platform: str = sys.platform) -> bool:
    """True if the executable lives in an OS-owned location."""
    if not exe_path:
        return False
    p = exe_path.lower().replace('/', os.sep).replace('\\', os.sep)
    if platform == 'win32':
        return _is_under(p, ('c:' + os.sep + 'windows',))
    if platform == 'darwin':
        return _is_under(p, ('/system', '/usr/libexec', '/sbin'))
    return _is_under(p, ('/usr/lib', '/usr/libexec', '/lib', '/sbin'))


def is_displayable(name: str, exe_path: str,
                   platform: str = sys.platform) -> bool:
    """Should this process/executable appear in the app picker?

    Positive heuristic: a candidate must *prove* it is a user app
    (sane name + installed in a user-app location) rather than us
    trying to enumerate every kind of garbage.
    """
    if not name:
        return False
    lower = name.lower()
    if lower in CRITICAL_PROCESSES or lower in SYSTEM_NOISE:
        return False
    if is_garbage_name(name) or is_helper_name(name):
        return False

    if platform == 'win32':
        if not exe_path:
            return False                # unverifiable -> almost always noise
        if is_system_path(exe_path, platform):
            return False
        return _windows_user_path(exe_path.lower().replace('/', '\\'))

    if platform == 'darwin':
        return bool(exe_path) and '.app' in exe_path.lower()

    # Linux: paths are uninformative (/usr/bin holds everything);
    # rely on the name checks above.
    return not is_system_path(exe_path, platform)


def is_protected(name: str, exe_path: str,
                 platform: str = sys.platform) -> bool:
    """Must this process never be terminated?"""
    lower = (name or '').lower()
    if lower in CRITICAL_PROCESSES or lower in SYSTEM_NOISE:
        return True
    if any(token in lower for token in PROTECTED_NAME_TOKENS):
        return True
    return is_system_path(exe_path, platform)


def friendly_name(process_name: str, exe_path: str = '') -> str:
    """Human display name for an executable.

    Walks up the path past version folders and generic directories:
        ...\\Discord\\app-1.0.9\\Discord.exe          -> Discord
        ...\\Google\\Chrome\\Application\\chrome.exe  -> Chrome
        ...\\WindowsApps\\Pub.App_1.2_x64__h\\Spotify.exe -> Spotify
    """
    fallback = _stem(process_name)

    candidate = ''
    if exe_path:
        parts = [p for p in re.split(r'[\\/]+', exe_path)[:-1] if p]
        for part in reversed(parts[-4:]):       # look up to 4 levels up
            if part.lower() in GENERIC_DIRS:
                continue
            if is_garbage_name(part) or ':' in part:
                continue
            candidate = part
            break

    name = candidate or fallback
    if name.islower() or name.isupper():
        name = name.title()
    return name
