import sqlite3
import json
import os

# Inserts all activities from the raw JSON file into the SQLite database
def insert_activities(json_path="data_raw/activities_raw.json"):
    # Connect to SQLite database
    conn = sqlite3.connect("strava.db")
    cursor = conn.cursor()

    # Ensure the JSON file exists
    if not os.path.exists(json_path):
        print(f"Error: {json_path} not found.")
        return

    # Load activities from file
    with open(json_path, "r") as f:
        activities = json.load(f)

    print(f"Inserting {len(activities)} activities...")

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

    print("Activities inserted successfully!")


if __name__ == "__main__":
    insert_activities()
