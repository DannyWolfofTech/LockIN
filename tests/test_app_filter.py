"""
Unit tests for core.app_filter (pure logic - no Qt, no psutil).

Run:  python -m tests.test_app_filter
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.app_filter import (
    is_garbage_name, is_helper_name, is_displayable, is_protected,
    friendly_name,
)

WIN = 'win32'


def test_garbage_names_rejected():
    # Exact strings reported from a real machine
    for bad in [
        '142.0.3595.53',
        '25.199.1012.0002_1',
        '5319275A.WhatsAppDesktop_2.2543.1.0_x64__cv1g1gvanyjgm',
        'SpotifyAB.SpotifyMusic_1.275.5.100_x64__zpdnekdrzrea0',
        'app-1.0.9',
        '',
        'x' * 41,
    ]:
        assert is_garbage_name(bad), f"should be garbage: {bad!r}"


def test_legit_digit_led_apps_kept():
    # The old "starts with a digit" rule wrongly hid these
    for good in ['7zFM.exe', '7-Zip', '1Password.exe', 'Notepad++.exe',
                 'chrome.exe', 'Code.exe', 'msedge.exe']:
        assert not is_garbage_name(good), f"should NOT be garbage: {good!r}"


def test_helpers_rejected():
    for helper in ['chrome_crashpad_handler.exe', 'Discord Update.exe',
                   'GoogleCrashHandler64.exe', 'unins000.exe',
                   'CefSharp.BrowserSubprocess.exe', 'setup.exe']:
        assert is_helper_name(helper) or is_garbage_name(helper), helper


def test_displayable_requires_user_path_on_windows():
    assert is_displayable('chrome.exe',
                          r'C:\Program Files\Google\Chrome\Application\chrome.exe', WIN)
    assert is_displayable('Discord.exe',
                          r'C:\Users\u\AppData\Local\Discord\app-1.0.9\Discord.exe', WIN)
    # system dir -> hidden
    assert not is_displayable('notepad.exe', r'C:\Windows\System32\notepad.exe', WIN)
    # no path (access denied) -> hidden: that's where the noise came from
    assert not is_displayable('WinRing0.exe', '', WIN)
    # critical / noise names -> hidden
    assert not is_displayable('svchost.exe', r'C:\Windows\System32\svchost.exe', WIN)
    assert not is_displayable('RuntimeBroker.exe',
                              r'C:\Windows\System32\RuntimeBroker.exe', WIN)


def test_protected_is_about_safety_not_display():
    assert is_protected('svchost.exe', r'C:\Windows\System32\svchost.exe', WIN)
    assert is_protected('anything.exe', r'C:\Windows\System32\anything.exe', WIN)
    assert is_protected('MsMpEng.exe', r'C:\ProgramData\Microsoft\MsMpEng.exe', WIN)
    assert is_protected('AvastSvc.exe', r'C:\Program Files\Avast\AvastSvc.exe', WIN)
    # a normal user app is NOT protected -> blockable
    assert not is_protected('Discord.exe',
                            r'C:\Users\u\AppData\Local\Discord\Discord.exe', WIN)
    # regression: 'ati'/'amd'/'hp' substrings must not protect everything
    assert not is_protected('application.exe',
                            r'C:\Program Files\Foo\application.exe', WIN)


def test_friendly_name_climbs_version_and_generic_dirs():
    cases = [
        (r'C:\Users\u\AppData\Local\Discord\app-1.0.9\Discord.exe',
         'Discord.exe', 'Discord'),
        (r'C:\Program Files\Google\Chrome\Application\chrome.exe',
         'chrome.exe', 'Chrome'),
        (r'C:\Program Files\WindowsApps'
         r'\SpotifyAB.SpotifyMusic_1.275.5.100_x64__zpdnekdrzrea0\Spotify.exe',
         'Spotify.exe', 'Spotify'),
        (r'C:\Program Files (x86)\Microsoft\Edge\Application'
         r'\142.0.3595.53\msedge.exe',
         'msedge.exe', 'Edge'),
        (r'C:\Program Files\Microsoft VS Code\Code.exe',
         'Code.exe', 'Microsoft VS Code'),
    ]
    for path, proc, expected in cases:
        got = friendly_name(proc, path)
        assert got == expected, f"{proc}: expected {expected!r}, got {got!r}"
    # no path at all -> clean stem
    assert friendly_name('obsidian.exe', '') == 'Obsidian'


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for test in tests:
        test()
        print(f"  ok  {test.__name__}")
    print(f"\n{len(tests)} tests passed.")


if __name__ == '__main__':
    main()
