import json
import datetime

INPUT_FILE = "strava_raw_data.json"
OUTPUT_FILE = "strava_running_clean.json"

def time_hours_to_hm(hours):
    total_minutes = int(round(hours * 60))
    h = total_minutes // 60
    m = total_minutes % 60
    return f"{h}:{m:02d} h"

def pace_minutes_per_mile(time_hours, distance_miles):
    if distance_miles == 0:
        return "N/A"
    total_seconds = time_hours * 3600 / distance_miles
    m = int(total_seconds // 60)
    s = int(total_seconds % 60)
    return f"{m}:{s:02d} min/mile"

def round_str(value, unit):
    return f"{round(value, 2)} {unit}"

def month_name(date_str):
    date = datetime.datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
    return date.strftime("%B %Y")  # e.g., "January 2024"

# Load raw data
with open(INPUT_FILE, "r") as f:
    activities = json.load(f)

running_data = []

for act in activities:
    if act.get("type") != "Run":
        continue  # Skip non-running activities

    distance_miles = act.get('distance', 0) * 0.000621371
    time_hours = act.get('moving_time', 0) / 3600
    elevation_ft = act.get('total_elevation_gain', 0) * 3.28084
    avg_hr = act.get('average_heartrate', 'N/A')
    max_hr = act.get('max_heartrate', 'N/A')
    start_date = act.get('start_date', None)
    month_key = month_name(start_date) if start_date else "Unknown"

    cleaned = {
        "name": act.get("name", "Unnamed Run"),
        "date": start_date,
        "month": month_key,
        "distance": round_str(distance_miles, "miles"),
        "time": time_hours_to_hm(time_hours),
        "average_pace": pace_minutes_per_mile(time_hours, distance_miles),
        "total_elevation": round_str(elevation_ft, "ft"),
        "average_hr": round_str(avg_hr, "bpm") if avg_hr != 'N/A' else "N/A",
        "max_hr": round_str(max_hr, "bpm") if max_hr != 'N/A' else "N/A"
    }

    running_data.append(cleaned)

# Save cleaned running data
with open(OUTPUT_FILE, "w") as f:
    json.dump(running_data, f, indent=2)

print(f"Cleaned running data saved to {OUTPUT_FILE}")
