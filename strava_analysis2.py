import json
from collections import defaultdict
import datetime

INPUT_FILE = "strava_raw_data.json"
OUTPUT_FILE = "strava_analysis2.json"

# Helper functions
def round_str(value, unit):
    return f"{round(value, 2)} {unit}"

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

def month_name(date_str):
    date = datetime.datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
    return date.strftime("%B %Y")  # e.g., "January 2024"

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

    date_str = act.get('start_date', None)
    month_key = month_name(date_str) if date_str else "Unknown"

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

# Convert to readable format with pace
def convert_readable(summary, is_monthly=False):
    result = {}
    for act_type, data in summary.items():
        if is_monthly:
            # sort months chronologically
            sorted_months = sorted(data.keys(), key=lambda x: datetime.datetime.strptime(x, "%B %Y"))
            month_data = {}
            for month in sorted_months:
                d = data[month]
                month_data[month] = {
                    "total_distance": round_str(d["total_distance"], "miles"),
                    "total_time": time_hours_to_hm(d["total_time"]),
                    "average_pace": pace_minutes_per_mile(d["total_time"], d["total_distance"]),
                    "total_elevation": round_str(d["total_elevation"], "ft"),
                    "average_hr": round_str(d["total_hr"]/d["count_hr"], "bpm") if d["count_hr"] else "N/A",
                    "activities_count": str(d["count"])
                }
            result[act_type] = month_data
        else:
            d = data
            result[act_type] = {
                "total_distance": round_str(d["total_distance"], "miles"),
                "total_time": time_hours_to_hm(d["total_time"]),
                "average_pace": pace_minutes_per_mile(d["total_time"], d["total_distance"]),
                "total_elevation": round_str(d["total_elevation"], "ft"),
                "average_hr": round_str(d["total_hr"]/d["count_hr"], "bpm") if d["count_hr"] else "N/A",
                "activities_count": str(d["count"])
            }
    return result

analysis_data = {
    "activity_summary": convert_readable(activity_summary),
    "monthly_summary": convert_readable(monthly_summary, is_monthly=True)
}

with open(OUTPUT_FILE, "w") as f:
    json.dump(analysis_data, f, indent=2)

print(f"Analysis saved to {OUTPUT_FILE}")
