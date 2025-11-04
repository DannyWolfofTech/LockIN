-- Lock In Database Schema
-- SQLite database for tracking focus sessions and statistics

-- Sessions table: stores information about each focus session
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    duration_seconds INTEGER NOT NULL,
    time_locked_in_seconds INTEGER NOT NULL DEFAULT 0,
    apps_whitelisted TEXT NOT NULL, -- JSON string of whitelisted apps
    apps_blocked_count INTEGER DEFAULT 0,
    emergency_exit_used BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    ended_at TIMESTAMP,
    status TEXT DEFAULT 'completed' -- completed, emergency_exit, interrupted
);

-- Blocked apps table: tracks which apps were blocked during each session
CREATE TABLE IF NOT EXISTS blocked_apps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    app_name TEXT NOT NULL,
    app_path TEXT,
    blocked_count INTEGER DEFAULT 1,
    first_blocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_blocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

-- Settings table: stores user preferences and app settings
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON sessions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);
CREATE INDEX IF NOT EXISTS idx_blocked_apps_session_id ON blocked_apps(session_id);
CREATE INDEX IF NOT EXISTS idx_blocked_apps_name ON blocked_apps(app_name);

-- Insert default settings
INSERT OR IGNORE INTO settings (key, value) VALUES ('theme', 'dark');
INSERT OR IGNORE INTO settings (key, value) VALUES ('emergency_password_enabled', 'false');
INSERT OR IGNORE INTO settings (key, value) VALUES ('emergency_password_hash', '');
INSERT OR IGNORE INTO settings (key, value) VALUES ('fullscreen_mode', 'false');
INSERT OR IGNORE INTO settings (key, value) VALUES ('show_motivational_quotes', 'true');
