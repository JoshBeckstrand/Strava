import sqlite3
import json

# Insert activities from the raw JSON into the SQLite database
def insert_activities(json_path):
    conn = sqlite3.connect("strava.db")
    cursor = conn.cursor()

    # Load data from file
    with open(json_path, "r") as f:
        activities = json.load(f)

    for a in activities:
        cursor.execute("""
            INSERT OR REPLACE INTO activities (
                id, name, distance, moving_time, elapsed_time, 
                total_elevation_gain, sport_type, start_date,
                average_speed, max_speed, average_heartrate, max_heartrate
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            a.get("id"),
            a.get("name"),
            a.get("distance"),
            a.get("moving_time"),
            a.get("elapsed_time"),
            a.get("total_elevation_gain"),
            a.get("sport_type"),
            a.get("start_date"),
            a.get("average_speed"),
            a.get("max_speed"),
            a.get("average_heartrate"),
            a.get("max_heartrate")
        ))

    conn.commit()
    conn.close()
    print("Activities inserted into database!")

if __name__ == "__main__":
    insert_activities("data_raw/activities_raw.json")
