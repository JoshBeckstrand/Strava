import json
from collections import defaultdict
import datetime

INPUT_FILE = "strava_raw_data.json"
OUTPUT_FILE = "strava_analysis.json"

# Load raw data
with open(INPUT_FILE, "r") as f:
    activities = json.load(f)

# Organize by activity type and month
activity_summary = defaultdict(lambda: {
    "total_distance": 0, "total_time": 0, "total_elevation": 0,
    "total_hr": 0, "count_hr": 0, "count": 0
})
monthly_summary = defaultdict(lambda: defaultdict(lambda: {
    "total_distance": 0, "total_time": 0, "total_elevation": 0,
    "total_hr": 0, "count_hr": 0, "count": 0
}))

for act in activities:
    type_ = act.get('type', 'Unknown')
    distance_miles = act.get('distance', 0) * 0.000621371
    time_hours = act.get('moving_time', 0) / 3600
    elevation_ft = act.get('total_elevation_gain', 0) * 3.28084
    avg_hr = act.get('average_heartrate', 'N/A')
    max_hr = act.get('max_heartrate', 'N/A')

    date_str = act.get('start_date', None)
    if date_str:
        date = datetime.datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
        month_key = date.strftime("%Y-%m")
    else:
        month_key = "Unknown"

    # Totals per activity type
    activity_summary[type_]["total_distance"] += distance_miles
    activity_summary[type_]["total_time"] += time_hours
    activity_summary[type_]["total_elevation"] += elevation_ft
    activity_summary[type_]["count"] += 1
    if avg_hr != 'N/A':
        activity_summary[type_]["total_hr"] += avg_hr
        activity_summary[type_]["count_hr"] += 1

    # Monthly totals
    monthly_summary[type_][month_key]["total_distance"] += distance_miles
    monthly_summary[type_][month_key]["total_time"] += time_hours
    monthly_summary[type_][month_key]["total_elevation"] += elevation_ft
    monthly_summary[type_][month_key]["count"] += 1
    if avg_hr != 'N/A':
        monthly_summary[type_][month_key]["total_hr"] += avg_hr
        monthly_summary[type_][month_key]["count_hr"] += 1

# Convert defaultdict to dict for JSON
def convert(d):
    if isinstance(d, defaultdict):
        d = {k: convert(v) for k, v in d.items()}
    return d

analysis_data = {
    "activity_summary": convert(activity_summary),
    "monthly_summary": convert(monthly_summary)
}

with open(OUTPUT_FILE, "w") as f:
    json.dump(analysis_data, f, indent=2)

print(f"Analysis saved to {OUTPUT_FILE}")
