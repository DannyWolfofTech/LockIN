"""
Lock In - Flet Version
Modern, responsive UI using Flet framework (Material Design)

To run this version: python main_flet.py
To run PyQt6 version: python main.py
"""

import flet as ft
import sys
from typing import List, Dict

# Import existing core modules
from core.session_manager import SessionManager, SessionState
from core.stats_tracker import StatsTracker
from database.db_manager import DatabaseManager


def main(page: ft.Page):
    # Initialize backend
    db_manager = DatabaseManager()
    session_manager = SessionManager(db_manager)
    stats_tracker = StatsTracker(db_manager)

    # Page configuration
    page.title = "Lock In - Focus & Productivity"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 1100
    page.window_height = 750
    page.window_min_width = 900
    page.window_min_height = 600
    page.padding = 20
    page.scroll = ft.ScrollMode.AUTO

    # State
    whitelisted_apps = []
    all_available_apps = []
    current_session_id = None

    # UI Controls
    search_text = ft.TextField(
        label="Search apps...",
        prefix_icon=ft.icons.SEARCH,
        border_color="#10b981",
        focused_border_color="#059669",
        on_change=lambda _: update_available_list()
    )

    session_name = ft.TextField(
        label="Session Name",
        hint_text="e.g., Deep Work, Study Time",
        border_color="#10b981",
        focused_border_color="#059669"
    )

    hours_field = ft.TextField(
        width=100,
        value="1",
        label="Hours",
        keyboard_type=ft.KeyboardType.NUMBER,
        border_color="#10b981",
        focused_border_color="#059669"
    )

    mins_field = ft.TextField(
        width=100,
        value="30",
        label="Minutes",
        keyboard_type=ft.KeyboardType.NUMBER,
        border_color="#10b981",
        focused_border_color="#059669"
    )

    duration_presets = ft.Dropdown(
        label="Quick Presets",
        options=[
            ft.dropdown.Option("25 min (Pomodoro)", key="25"),
            ft.dropdown.Option("50 min (Deep Work)", key="50"),
            ft.dropdown.Option("90 min (Ultra Focus)", key="90"),
        ],
        border_color="#10b981",
        focused_border_color="#059669",
        on_change=lambda e: set_preset(e.control.value),
    )

    def set_preset(value):
        if value == "25":
            hours_field.value = "0"
            mins_field.value = "25"
        elif value == "50":
            hours_field.value = "0"
            mins_field.value = "50"
        elif value == "90":
            hours_field.value = "1"
            mins_field.value = "30"
        page.update()

    # Lists
    available_list = ft.ListView(expand=True, spacing=5, padding=10)
    whitelisted_list = ft.ListView(expand=True, spacing=5, padding=10)

    def load_apps():
        """Load all available apps from app_blocker"""
        nonlocal all_available_apps
        try:
            all_apps = session_manager.app_blocker.get_all_installed_apps()
            running_apps = session_manager.app_blocker.get_running_apps()
            running_names = {app['display_name'] for app in running_apps}

            # Sort: running apps first
            all_available_apps = sorted(all_apps, key=lambda x: (
                0 if x['display_name'] in running_names else 1,
                x['display_name'].lower()
            ))
        except Exception as e:
            print(f"Error loading apps: {e}")
            all_available_apps = []

    def get_filtered_apps():
        """Filter apps based on search text"""
        query = search_text.value.lower() if search_text.value else ""
        return [app for app in all_available_apps if query in app['display_name'].lower()]

    def update_available_list():
        """Update the available apps list"""
        available_list.controls.clear()
        filtered = get_filtered_apps()

        if not filtered:
            available_list.controls.append(
                ft.Text("No apps found", color=ft.colors.WHITE70, text_align=ft.TextAlign.CENTER)
            )
        else:
            for app in filtered:
                is_running = "●" in app.get('display_name', '')
                available_list.controls.append(
                    ft.Container(
                        content=ft.ListTile(
                            leading=ft.Icon(ft.icons.APPS, color="#10b981"),
                            title=ft.Text(
                                app['display_name'],
                                color="#10b981" if is_running else ft.colors.WHITE
                            ),
                            trailing=ft.IconButton(
                                icon=ft.icons.ADD_CIRCLE_OUTLINE,
                                icon_color="#10b981",
                                on_click=lambda _, a=app: add_to_whitelist(a)
                            ),
                        ),
                        border=ft.border.all(1, "#404040"),
                        border_radius=8,
                        bgcolor="#2a2a2a",
                    )
                )
        page.update()

    def update_whitelisted_list():
        """Update the whitelisted apps list"""
        whitelisted_list.controls.clear()

        if not whitelisted_apps:
            whitelisted_list.controls.append(
                ft.Text("No apps whitelisted", color=ft.colors.WHITE70, text_align=ft.TextAlign.CENTER)
            )
        else:
            for app in whitelisted_apps:
                whitelisted_list.controls.append(
                    ft.Container(
                        content=ft.ListTile(
                            leading=ft.Icon(ft.icons.APPS, color="#10b981"),
                            title=ft.Text(app['display_name']),
                            trailing=ft.IconButton(
                                icon=ft.icons.REMOVE_CIRCLE_OUTLINE,
                                icon_color="#ef4444",
                                on_click=lambda _, a=app: remove_from_whitelist(a['display_name'])
                            ),
                        ),
                        border=ft.border.all(1, "#10b981"),
                        border_radius=8,
                        bgcolor="#2a2a2a",
                    )
                )
        page.update()

    def add_to_whitelist(app):
        """Add app to whitelist"""
        if app not in whitelisted_apps:
            whitelisted_apps.append(app)
            update_whitelisted_list()

    def remove_from_whitelist(name):
        """Remove app from whitelist"""
        whitelisted_apps[:] = [app for app in whitelisted_apps if app['display_name'] != name]
        update_whitelisted_list()

    def refresh_apps_click(e):
        """Refresh available apps"""
        load_apps()
        update_available_list()
        page.show_snack_bar(
            ft.SnackBar(
                content=ft.Text("Apps refreshed!"),
                bgcolor="#10b981"
            )
        )

    def start_session_click(e):
        """Start a focus session"""
        nonlocal current_session_id

        # Validate inputs
        if not session_name.value or not session_name.value.strip():
            page.show_snack_bar(
                ft.SnackBar(content=ft.Text("Please enter a session name!"), bgcolor="#ef4444")
            )
            return

        if not whitelisted_apps:
            # Show warning dialog
            def close_dlg(e):
                dialog.open = False
                page.update()

            def continue_anyway(e):
                dialog.open = False
                page.update()
                start_session_internal()

            dialog = ft.AlertDialog(
                title=ft.Text("No Whitelisted Apps"),
                content=ft.Text("You haven't whitelisted any apps. This will block ALL applications. Continue?"),
                actions=[
                    ft.TextButton("Cancel", on_click=close_dlg),
                    ft.TextButton("Continue", on_click=continue_anyway),
                ],
            )
            page.dialog = dialog
            dialog.open = True
            page.update()
            return

        start_session_internal()

    def start_session_internal():
        """Actually start the session"""
        nonlocal current_session_id

        try:
            # Calculate duration
            hours = int(hours_field.value or 0)
            mins = int(mins_field.value or 0)
            duration_mins = hours * 60 + mins

            if duration_mins <= 0:
                page.show_snack_bar(
                    ft.SnackBar(content=ft.Text("Please set a duration > 0!"), bgcolor="#ef4444")
                )
                return

            # Get app paths
            app_paths = [app['display_name'] for app in whitelisted_apps]

            # Setup session
            success = session_manager.setup_session(
                name=session_name.value.strip(),
                duration_minutes=duration_mins,
                whitelisted_apps=app_paths
            )

            if not success:
                page.show_snack_bar(
                    ft.SnackBar(content=ft.Text("Failed to setup session!"), bgcolor="#ef4444")
                )
                return

            # Start session
            success = session_manager.start_session()
            if success:
                current_session_id = session_manager.current_session_id
                page.go("/lock-in")
            else:
                page.show_snack_bar(
                    ft.SnackBar(content=ft.Text("Failed to start session!"), bgcolor="#ef4444")
                )

        except Exception as e:
            print(f"Error starting session: {e}")
            page.show_snack_bar(
                ft.SnackBar(content=ft.Text(f"Error: {str(e)}"), bgcolor="#ef4444")
            )

    def emergency_exit_click(e):
        """Emergency exit from session"""
        def close_dlg(e):
            dialog.open = False
            page.update()

        def confirm_exit(e):
            dialog.open = False
            session_manager.end_session(emergency_exit=True)
            page.go("/completion")

        dialog = ft.AlertDialog(
            title=ft.Text("Emergency Exit"),
            content=ft.Text("Are you sure you want to exit early?\n\nThis will end your focus session."),
            actions=[
                ft.TextButton("Cancel", on_click=close_dlg),
                ft.TextButton("Exit", on_click=confirm_exit),
            ],
        )
        page.dialog = dialog
        dialog.open = True
        page.update()

    def setup_route():
        """Setup screen route"""
        page.views.clear()
        page.views.append(
            ft.View(
                "/",
                [
                    ft.Text("Lock In - Start a Focus Session", size=32, weight=ft.FontWeight.BOLD, color="#10b981"),
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column(
                                [
                                    session_name,
                                    duration_presets,
                                    ft.Row([
                                        hours_field,
                                        ft.Text(":", size=24, weight=ft.FontWeight.BOLD, color="#10b981"),
                                        mins_field
                                    ], alignment=ft.MainAxisAlignment.CENTER),
                                ],
                                spacing=15,
                            ),
                            padding=30,
                        ),
                        elevation=4,
                    ),
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column(
                                [
                                    ft.Text("Select Apps to Whitelist", size=18, weight=ft.FontWeight.BOLD, color="#10b981"),
                                    ft.Row(
                                        [
                                            ft.Column(
                                                [
                                                    ft.Text("Available Apps", size=16, weight=ft.FontWeight.BOLD),
                                                    search_text,
                                                    ft.Container(
                                                        content=available_list,
                                                        height=400,
                                                        border=ft.border.all(1, "#10b981"),
                                                        border_radius=12,
                                                        bgcolor="#1a1a1a",
                                                    ),
                                                ],
                                                expand=3,
                                                spacing=10,
                                            ),
                                            ft.Column(
                                                [
                                                    ft.Text("Whitelisted Apps", size=16, weight=ft.FontWeight.BOLD),
                                                    ft.Container(height=45),  # Spacer to align with search box
                                                    ft.Container(
                                                        content=whitelisted_list,
                                                        height=400,
                                                        border=ft.border.all(1, "#10b981"),
                                                        border_radius=12,
                                                        bgcolor="#1a1a1a",
                                                    ),
                                                ],
                                                expand=2,
                                                spacing=10,
                                            ),
                                        ],
                                        spacing=20,
                                        expand=True,
                                    ),
                                ],
                                spacing=15,
                            ),
                            padding=20,
                        ),
                        elevation=4,
                    ),
                    ft.Row(
                        [
                            ft.ElevatedButton(
                                "Refresh Apps",
                                icon=ft.icons.REFRESH,
                                bgcolor="#3a3a3a",
                                color=ft.colors.WHITE,
                                on_click=refresh_apps_click
                            ),
                            ft.ElevatedButton(
                                "Start Session",
                                icon=ft.icons.PLAY_ARROW,
                                bgcolor="#10b981",
                                color=ft.colors.WHITE,
                                on_click=start_session_click
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.END,
                    ),
                ],
                scroll=ft.ScrollMode.AUTO,
                padding=20,
            )
        )
        load_apps()
        update_available_list()
        update_whitelisted_list()
        page.update()

    def lock_in_route():
        """Lock-in screen (simplified - actual blocking happens in background)"""
        page.views.clear()

        session_info = session_manager.get_session_info()

        page.views.append(
            ft.View(
                "/lock-in",
                [
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Text(session_info['name'], size=24, weight=ft.FontWeight.BOLD),
                                ft.Text(
                                    "Session in Progress...",
                                    size=48,
                                    weight=ft.FontWeight.BOLD,
                                    color="#10b981"
                                ),
                                ft.Card(
                                    content=ft.Container(
                                        content=ft.Column(
                                            [
                                                ft.Text("SESSION PROGRESS", color=ft.colors.WHITE70, size=12),
                                                ft.ProgressBar(value=0, color="#10b981", height=20),
                                                ft.Text("0%", size=32, weight=ft.FontWeight.BOLD),
                                            ],
                                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                            spacing=10,
                                        ),
                                        padding=30,
                                    ),
                                    elevation=4,
                                ),
                                ft.Row(
                                    [
                                        ft.Card(
                                            content=ft.Container(
                                                content=ft.Column(
                                                    [
                                                        ft.Text("TIME ELAPSED", color=ft.colors.WHITE70, size=12),
                                                        ft.Text("00:00", size=36, weight=ft.FontWeight.BOLD),
                                                    ],
                                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                                ),
                                                width=180,
                                                padding=20,
                                            ),
                                        ),
                                        ft.Card(
                                            content=ft.Container(
                                                content=ft.Column(
                                                    [
                                                        ft.Text("TIME REMAINING", color=ft.colors.WHITE70, size=12),
                                                        ft.Text(f"{session_info['duration']//60:02d}:{session_info['duration']%60:02d}", size=36, weight=ft.FontWeight.BOLD),
                                                    ],
                                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                                ),
                                                width=180,
                                                padding=20,
                                            ),
                                        ),
                                        ft.Card(
                                            content=ft.Container(
                                                content=ft.Column(
                                                    [
                                                        ft.Text("APPS BLOCKED", color=ft.colors.WHITE70, size=12),
                                                        ft.Text("0", size=36, weight=ft.FontWeight.BOLD),
                                                    ],
                                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                                ),
                                                width=180,
                                                padding=20,
                                            ),
                                        ),
                                    ],
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    spacing=15,
                                ),
                                ft.Text("Stay focused. You've got this! 💪", size=18, color=ft.colors.WHITE70, italic=True),
                                ft.ElevatedButton(
                                    "Emergency Exit",
                                    icon=ft.icons.EXIT_TO_APP,
                                    bgcolor="#ef4444",
                                    color=ft.colors.WHITE,
                                    on_click=emergency_exit_click
                                ),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=30,
                        ),
                        padding=40,
                        alignment=ft.alignment.center,
                    )
                ],
                vertical_alignment=ft.MainAxisAlignment.CENTER,
            )
        )
        page.update()

    def completion_route():
        """Completion screen"""
        page.views.clear()

        if current_session_id:
            session = stats_tracker.get_session_details(current_session_id)
            comparison = stats_tracker.compare_to_previous(current_session_id)
        else:
            # Mock data if no session
            session = {
                'name': 'Test Session',
                'time_locked_in_formatted': '25m',
                'duration_formatted': '25m',
                'apps_blocked_count': 0,
                'completion_percentage': 100.0,
            }
            comparison = {'has_previous': False}

        # Build comparison text
        if comparison.get('has_previous'):
            if comparison['time_improved']:
                comp_text = f"🎉 You locked in {comparison['time_difference_formatted']} longer than last time!\n\nKeep up the great work!"
            else:
                comp_text = f"Last session was {comparison['time_difference_formatted']} longer.\n\nYou'll get it next time!"
        else:
            comp_text = "This is your first session!\n\nGreat start. Keep building the habit."

        page.views.append(
            ft.View(
                "/completion",
                [
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Text("Session Complete!", size=36, weight=ft.FontWeight.BOLD, color="#10b981"),
                                ft.Text(session['name'], size=20, color=ft.colors.WHITE70),
                                ft.Row(
                                    [
                                        ft.Card(
                                            content=ft.Container(
                                                content=ft.Column(
                                                    [
                                                        ft.Text("TIME LOCKED IN", color=ft.colors.WHITE70, size=12),
                                                        ft.Text(session['time_locked_in_formatted'], size=42, weight=ft.FontWeight.BOLD, color="#10b981"),
                                                    ],
                                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                                ),
                                                width=180,
                                                height=140,
                                                padding=20,
                                            ),
                                        ),
                                        ft.Card(
                                            content=ft.Container(
                                                content=ft.Column(
                                                    [
                                                        ft.Text("PLANNED DURATION", color=ft.colors.WHITE70, size=12),
                                                        ft.Text(session['duration_formatted'], size=42, weight=ft.FontWeight.BOLD),
                                                    ],
                                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                                ),
                                                width=180,
                                                height=140,
                                                padding=20,
                                            ),
                                        ),
                                    ],
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    spacing=20,
                                ),
                                ft.Row(
                                    [
                                        ft.Card(
                                            content=ft.Container(
                                                content=ft.Column(
                                                    [
                                                        ft.Text("APPS BLOCKED", color=ft.colors.WHITE70, size=12),
                                                        ft.Text(str(session['apps_blocked_count']), size=42, weight=ft.FontWeight.BOLD),
                                                    ],
                                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                                ),
                                                width=180,
                                                height=140,
                                                padding=20,
                                            ),
                                        ),
                                        ft.Card(
                                            content=ft.Container(
                                                content=ft.Column(
                                                    [
                                                        ft.Text("COMPLETION", color=ft.colors.WHITE70, size=12),
                                                        ft.Text(f"{session['completion_percentage']:.0f}%", size=42, weight=ft.FontWeight.BOLD, color="#10b981"),
                                                    ],
                                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                                ),
                                                width=180,
                                                height=140,
                                                padding=20,
                                            ),
                                        ),
                                    ],
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    spacing=20,
                                ),
                                ft.Card(
                                    content=ft.Container(
                                        content=ft.Text(comp_text, size=15, text_align=ft.TextAlign.CENTER, color=ft.colors.WHITE70),
                                        width=500,
                                        padding=25,
                                    ),
                                ),
                                ft.ElevatedButton(
                                    "Start New Session",
                                    icon=ft.icons.REFRESH,
                                    bgcolor="#10b981",
                                    color=ft.colors.WHITE,
                                    on_click=lambda _: page.go("/")
                                ),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=25,
                        ),
                        padding=40,
                        alignment=ft.alignment.center,
                    )
                ],
                vertical_alignment=ft.MainAxisAlignment.CENTER,
            )
        )
        page.update()

    # Route handler
    def route_change(e):
        page.views.clear()
        if page.route == "/":
            setup_route()
        elif page.route == "/lock-in":
            lock_in_route()
        elif page.route == "/completion":
            completion_route()
        page.update()

    page.on_route_change = route_change
    page.go("/")


if __name__ == "__main__":
    ft.app(target=main)
