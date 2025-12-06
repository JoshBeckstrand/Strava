import sqlite3
import json
import os

# ---------------------------------------------------------
# Inserts per-second stream data from JSON files into SQLite
#
# Each JSON file looks like:
# {
#   "time": {"data": [...]},
#   "heartrate": {"data": [...]},
#   "latlng": {"data": [[lat, lng], ...]},
#   "velocity_smooth": {"data": [...]},
#   "altitude": {"data": [...]},
#   "cadence": {"data": [...]},
#   "grade_smooth": {"data": [...]},
#   "distance": {"data": [...]}
# }
#
# The script:
# - Loads each file
# - Expands each stream into per-point rows
# - Inserts into "streams" table
# ---------------------------------------------------------


def insert_streams():
    conn = sqlite3.connect("strava.db")
    cursor = conn.cursor()

    streams_dir = "data_raw/activity_streams"

    if not os.path.isdir(streams_dir):
        print(f"Error: directory {streams_dir} not found.")
        return

    files = [f for f in os.listdir(streams_dir) if f.startswith("streams_")]

    print(f"Found {len(files)} stream files to process.\n")

    for filename in files:
        # Extract activity ID from filename: streams_12345.json
        activity_id = filename.replace("streams_", "").replace(".json", "")

        file_path = os.path.join(streams_dir, filename)

        # Load JSON data
        with open(file_path, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                print(f"Skipping {filename} (JSON decode error)")
                continue

        # Skip empty or unavailable streams
        if not isinstance(data, dict) or len(data) == 0:
            print(f"Skipping {filename} (no stream data)")
            continue

        # Get the streams (each is a dict with .get("data"))
        t = data.get("time", {}).get("data", [])
        hr = data.get("heartrate", {}).get("data", [])
        latlng = data.get("latlng", {}).get("data", [])
        pace = data.get("velocity_smooth", {}).get("data", [])
        alt = data.get("altitude", {}).get("data", [])
        cad = data.get("cadence", {}).get("data", [])
        dist = data.get("distance", {}).get("data", [])
        grade = data.get("grade_smooth", {}).get("data", [])

        # Determine how many data points we actually have
        # (Use the time array as the primary length)
        n = len(t)

        if n == 0:
            print(f"Skipping {filename} (no time data)")
            continue

        print(f"Inserting streams for activity {activity_id} ({n} points)...")

        # Insert row-by-row
        for i in range(n):
            # Each stream may be missing some values
            time_val = t[i] if i < len(t) else None
            hr_val = hr[i] if i < len(hr) else None
            pace_val = pace[i] if i < len(pace) else None
            alt_val = alt[i] if i < len(alt) else None
            cad_val = cad[i] if i < len(cad) else None
            dist_val = dist[i] if i < len(dist) else None
            grade_val = grade[i] if i < len(grade) else None

            # lat/lng is a pair
            if i < len(latlng) and isinstance(latlng[i], list) and len(latlng[i]) == 2:
                lat_val = latlng[i][0]
                lng_val = latlng[i][1]
            else:
                lat_val = None
                lng_val = None

            cursor.execute("""
                INSERT INTO streams (
                    activity_id,
                    time,
                    heartrate,
                    pace,
                    cadence,
                    lat,
                    lng,
                    elevation,
                    grade
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                activity_id,
                time_val,
                hr_val,
                pace_val,
                cad_val,
                lat_val,
                lng_val,
                alt_val,
                grade_val
            ))

        conn.commit()

    conn.close()
    print("\nStream data inserted successfully!")


if __name__ == "__main__":
    insert_streams()
