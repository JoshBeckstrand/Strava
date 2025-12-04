import json
import math
import datetime

INPUT_FILE = "strava_running_clean.json"
OUTPUT_FILE = "running_race_predictions2.json"

# Target races in miles
RACES = {
    "1 Mile": 1,
    "5K": 3.10686,
    "10K": 6.21371,
    "Half Marathon": 13.1094,
    "Marathon": 26.2188,
    "50K": 31.07,
    "50 Mile": 50,
    "100 Mile": 100
}

# Load cleaned running data
with open(INPUT_FILE, "r") as f:
    runs = json.load(f)

# Convert pace "m:ss min/mile" or "mm min/mile" to minutes
def pace_to_minutes(pace_str):
    if pace_str == "N/A":
        return None
    pace_str = pace_str.replace(" min/mile", "")
    if ":" in pace_str:
        m, s = pace_str.split(":")
        return int(m) + int(s)/60
    else:
        return float(pace_str)

# Get fastest pace from all runs
fastest_pace_min = min(
    [pace_to_minutes(run["average_pace"]) for run in runs if pace_to_minutes(run["average_pace"])],
    default=None
)

# Get longest run distance and time
longest_run = max(runs, key=lambda x: float(x["distance"].split()[0]), default=None)
if longest_run:
    longest_distance = float(longest_run["distance"].split()[0])
    longest_time_hm = longest_run["time"].split()[0]  # "h:mm"
    h, m = map(int, longest_time_hm.split(":"))
    longest_time_hours = h + m/60
else:
    longest_distance = 0
    longest_time_hours = 0

# Riegel formula
def riegel(time_hours, distance_miles, target_miles):
    if distance_miles == 0:
        return "N/A"
    predicted_time_hours = time_hours * (target_miles / distance_miles)**1.06
    h = int(predicted_time_hours)
    m = int((predicted_time_hours - h)*60)
    s = int(((predicted_time_hours - h)*60 - m)*60)
    return f"{h}:{m:02d}:{s:02d}"

# Jack Daniels formula
def jack_daniels(fastest_pace_min, target_miles):
    if fastest_pace_min is None:
        return "N/A"
    predicted_pace = fastest_pace_min * (target_miles/3.10686)**0.07
    total_minutes = predicted_pace * target_miles
    h = int(total_minutes // 60)
    m = int(total_minutes % 60)
    s = int((total_minutes - int(total_minutes))*60)
    return f"{h}:{m:02d}:{s:02d}"

# Cameron formula
def cameron(time_hours, distance_miles, target_miles):
    if distance_miles == 0:
        return "N/A"
    predicted_time_hours = time_hours * (target_miles / distance_miles)**1.077
    h = int(predicted_time_hours)
    m = int((predicted_time_hours - h)*60)
    s = int(((predicted_time_hours - h)*60 - m)*60)
    return f"{h}:{m:02d}:{s:02d}"

# Weighted standard deviation
def weighted_std(values, weights):
    avg = sum(v*w for v,w in zip(values, weights)) / sum(weights)
    variance = sum(w*(v-avg)**2 for v,w in zip(values, weights)) / sum(weights)
    return math.sqrt(variance)

# Beckstrand formula
def beckstrand_formula(runs, target_miles):
    now = datetime.datetime.now()
    weighted_paces = []
    weighted_distances = []

    for run in runs:
        pace_str = run.get("average_pace", "N/A")
        if pace_str == "N/A":
            continue
        pace = pace_str.replace(" min/mile","")
        if ":" in pace:
            m,s = pace.split(":")
            pace_min = int(m) + int(s)/60
        else:
            pace_min = float(pace)

        dist = float(run["distance"].split()[0])
        date = datetime.datetime.strptime(run["date"], "%Y-%m-%dT%H:%M:%SZ")


        days_ago = (now - date).days
        if days_ago <= 180:       # 0-6 months
            weight = 1.0
        elif days_ago <= 365:     # 6-12 months
            weight = 0.5
        else:
            weight = 0.2

        weighted_paces.append((pace_min, weight))
        weighted_distances.append((dist, pace_min, weight))

    if not weighted_paces:
        return "N/A", "0%", "N/A"

    # Short race: mostly pace
    if target_miles <= 5:
        pace_total = sum(p*weight for p,weight in weighted_paces)
        weight_sum = sum(weight for _,weight in weighted_paces)
        predicted_pace = pace_total / weight_sum
        predicted_time_min = predicted_pace * target_miles
    else:
        # Long races: distance & pace
        closest = min(weighted_distances, key=lambda x: abs(x[0]-target_miles))
        closest_dist, closest_pace, weight = closest
        scaling_exponent = 1.06
        predicted_time_min = closest_pace * target_miles * (target_miles/closest_dist)**(scaling_exponent-1)

    # Calculate weighted standard deviation of pace
    paces = [p for p,_ in weighted_paces]
    weights = [w for _,w in weighted_paces]
    pace_std = weighted_std(paces, weights)

    # Best/worst-case times
    best_time_min = predicted_time_min - pace_std * target_miles
    worst_time_min = predicted_time_min + pace_std * target_miles
    delta_seconds = int((worst_time_min - best_time_min)/2 * 60)
    range_str = f"+/-{delta_seconds}s"

    # Convert predicted time to h:mm:ss
    hours = int(predicted_time_min // 60)
    minutes = int(predicted_time_min % 60)
    seconds = int((predicted_time_min - int(predicted_time_min))*60)
    time_str = f"{hours}:{minutes:02d}:{seconds:02d}"

    # Confidence %
    recent_count = sum(1 for _,weight in weighted_paces if weight >= 0.5)
    total_count = len(weighted_paces)
    confidence = min(100, int((recent_count/total_count)*100)) if total_count>0 else 50

    return time_str, f"{confidence}%", range_str

# Generate predictions
predictions = {}
for race, miles in RACES.items():
    predictions[race] = {
        "Riegel": riegel(longest_time_hours, longest_distance, miles),
        "Jack Daniels": jack_daniels(fastest_pace_min, miles),
        "Cameron": cameron(longest_time_hours, longest_distance, miles),
        "Beckstrand": beckstrand_formula(runs, miles)
    }

# Save predictions
with open(OUTPUT_FILE, "w") as f:
    json.dump(predictions, f, indent=2)

print(f"Race predictions saved to {OUTPUT_FILE}")
