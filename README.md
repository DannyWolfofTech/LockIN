# Lock In - Focus & Productivity Desktop Application

Tool that allows you to lock-in! Focus on your projects and work without doomscrolling and brainrot to distract and procrastinate your work!

## Overview

Lock In is a desktop application designed to help you maintain deep focus by blocking all applications except those you whitelist. When you start a focus session, the app goes fullscreen, closes all non-whitelisted apps, and prevents them from being reopened until your session ends.

## Features

- **Focus Sessions**: Set a duration and list of allowed apps for distraction-free work
- **App Blocking**: Automatically closes and prevents non-whitelisted apps from running
- **Real-time Monitoring**: Continuously monitors and blocks attempts to open distracting apps
- **Session Tracking**: Stores all session data including duration, apps blocked, and completion rate
- **Statistics Dashboard**: View your productivity trends, total focus time, and most blocked apps
- **Emergency Exit**: Safe way to exit a session early if needed
- **Modern UI**: Clean, dark-themed interface with real-time updates

## Tech Stack

- **Language**: Python 3.11+
- **GUI Framework**: PyQt6
- **Process Management**: psutil
- **Database**: SQLite

## Project Structure

```
LockIN/
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── ui/                     # UI components
│   ├── main_window.py     # Main window with all screens
│   └── widgets.py         # Custom reusable widgets
├── core/                   # Business logic
│   ├── app_blocker.py     # Process management & blocking
│   ├── session_manager.py # Session coordination
│   └── stats_tracker.py   # Statistics & analytics
├── database/               # Database layer
│   ├── db_manager.py      # SQLite operations
│   └── schema.sql         # Database schema
└── assets/                 # Icons and images
```

## Installation

### Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- Administrative/root privileges (required to manage other applications)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/LockIN.git
   cd LockIN
   ```

2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv

   # On Windows:
   venv\Scripts\activate

   # On Linux/macOS:
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Running the Application

**On Windows (Run as Administrator):**
```bash
# Right-click on Command Prompt and select "Run as Administrator"
python main.py
```

**On Linux/macOS (Run with sudo):**
```bash
sudo python main.py
```

**Note**: Administrative privileges are required to manage and close other applications.

### Starting a Focus Session

1. **Session Setup Screen**:
   - Enter a session name (e.g., "Deep Work", "Study Time")
   - Set duration using the hours and minutes picker
   - Select apps to whitelist from the running apps list
   - Click "Add to Whitelist" to allow specific apps
   - Click "Start Session" when ready

2. **During Session**:
   - The timer counts down your remaining time
   - All non-whitelisted apps are closed and blocked
   - Progress bar shows session completion
   - Stats update in real-time (time elapsed, apps blocked)
   - Emergency Exit button available if needed

3. **Session End**:
   - View session statistics and completion rate
   - See comparison with previous sessions
   - Start a new session or view overall statistics

### Whitelisting Apps

Common apps you might want to whitelist:
- Code editors (VS Code, PyCharm, Sublime Text)
- Browsers (for documentation/research)
- Development tools (Terminal, Git clients)
- Communication apps (Slack, Discord - if needed for work)
- Note-taking apps (Notion, Obsidian, OneNote)

**Tip**: Start with minimal whitelisted apps for maximum focus!

## How It Works

### App Blocking System

1. **Initial Scan**: On session start, scans all running processes
2. **Whitelist Check**: Identifies whitelisted apps vs. apps to block
3. **Immediate Closure**: Closes all non-whitelisted applications
4. **Continuous Monitoring**: Every second, checks for new processes
5. **Auto-Block**: Automatically terminates any non-whitelisted app that starts
6. **Safe Guards**: Never blocks critical system processes

### Database Schema

- **sessions**: Stores session metadata, duration, completion status
- **blocked_apps**: Tracks which apps were blocked during each session
- **settings**: User preferences and configuration

### Safety Features

- Critical system processes are never terminated
- Emergency exit available at any time
- Session data is saved even if app crashes
- Graceful termination of blocked processes

## Development

### Project Architecture

- **UI Layer** (`ui/`): PyQt6 widgets and screens
- **Core Logic** (`core/`): Session management, app blocking, statistics
- **Data Layer** (`database/`): SQLite database operations

### Key Classes

- `SessionManager`: Orchestrates focus sessions, timing, and state
- `AppBlocker`: Handles process detection and termination
- `DatabaseManager`: Manages all database operations
- `StatsTracker`: Provides analytics and statistics

### Adding New Features

1. **New UI Screen**: Add to `ui/main_window.py` and connect to stack widget
2. **Core Logic**: Extend classes in `core/` directory
3. **Database Changes**: Update `schema.sql` and `db_manager.py`

## Troubleshooting

### App won't close other applications
- **Solution**: Make sure you're running with administrative/root privileges
- On Windows: Right-click and "Run as Administrator"
- On Linux/macOS: Use `sudo python main.py`

### Database errors
- **Solution**: Delete the database file at `~/.lockin/lockin.db` to reset
- Note: This will delete all session history

### UI not responding
- Check if session is active (app blocks closing during active sessions)
- Use Emergency Exit to end session first

### Apps keep restarting
- Some apps have auto-restart mechanisms
- The blocker will continue blocking them as they restart

## Roadmap

Future features planned:
- [ ] Statistics dashboard screen with charts
- [ ] Customizable motivational quotes
- [ ] Scheduled sessions (auto-start at specific times)
- [ ] Break reminders and Pomodoro mode
- [ ] Website blocking (browser extension)
- [ ] macOS and Linux full support
- [ ] Portable executable builds
- [ ] Cloud sync for statistics

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - See LICENSE file for details

## Disclaimer

This application terminates running processes. Use responsibly and save your work before starting a session. The developers are not responsible for any data loss.

## Support

For issues, questions, or suggestions, please open an issue on GitHub.

---

**Stay focused. Lock in. Level up.** 🚀
