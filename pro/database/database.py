import sqlite3

# This function creates the SQLite database and required tables
def init_db():
    # Connect to SQLite (creates file if it doesn't exist)
    conn = sqlite3.connect("strava.db")
    cursor = conn.cursor()

    # Create table for high-level activity info
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY,
            name TEXT,
            distance REAL,
            moving_time INTEGER,
            elapsed_time INTEGER,
            total_elevation_gain REAL,
            sport_type TEXT,
            start_date TEXT,
            average_speed REAL,
            max_speed REAL,
            average_heartrate REAL,
            max_heartrate REAL
        );
    """)

    # Table for split data (mile splits, etc.)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS splits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            activity_id INTEGER,
            split_index INTEGER,
            distance REAL,
            moving_time INTEGER,
            pace REAL,
            FOREIGN KEY(activity_id) REFERENCES activities(id)
        );
    """)

    # Table for per-second stream data
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS streams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            activity_id INTEGER,
            time INTEGER,
            heartrate REAL,
            pace REAL,
            cadence REAL,
            lat REAL,
            lng REAL,
            elevation REAL,
            FOREIGN KEY(activity_id) REFERENCES activities(id)
        );
    """)

    # Table for computed metrics later
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            activity_id INTEGER,
            hr_drift REAL,
            efficiency REAL,
            variability REAL,
            fatigue_score REAL,
            FOREIGN KEY(activity_id) REFERENCES activities(id)
        );
    """)

    # Save changes and close connection
    conn.commit()
    conn.close()

    print("SQLite database initialized successfully!")

if __name__ == "__main__":
    init_db()
