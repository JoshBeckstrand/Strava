import json
import math
import datetime

INPUT_FILE = "strava_running_clean.json"
OUTPUT_FILE = "running_race_predictions4.json"

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

# Helper: Find best time at or near a target distance
def find_best_time_near_distance(runs, target_miles, tolerance=0.25):
    """Find the fastest run within tolerance of target distance (default 25%)"""
    candidates = []
    for run in runs:
        dist = float(run["distance"].split()[0])
        if abs(dist - target_miles) / target_miles <= tolerance:
            pace = pace_to_minutes(run["average_pace"])
            if pace:
                time_str = run["time"].split()[0]
                h, m = map(int, time_str.split(":"))
                total_minutes = h * 60 + m
                candidates.append((total_minutes, dist, pace))
    
    if not candidates:
        return None, None, None
    
    # Return the fastest total time (total_minutes, distance, pace)
    return min(candidates, key=lambda x: x[0])

# Improved Beckstrand formula
def beckstrand_formula(runs, target_miles):
    now = datetime.datetime.now()
    
    # Find current PR at this distance
    pr_time, pr_dist, pr_pace = find_best_time_near_distance(runs, target_miles)
    
    # Collect weighted recent runs
    recent_runs = []
    for run in runs:
        pace_str = run.get("average_pace", "N/A")
        if pace_str == "N/A":
            continue
        
        pace = pace_str.replace(" min/mile","")
        if ":" in pace:
            m, s = pace.split(":")
            pace_min = int(m) + int(s)/60
        else:
            pace_min = float(pace)

        dist = float(run["distance"].split()[0])
        date = datetime.datetime.strptime(run["date"], "%Y-%m-%dT%H:%M:%SZ")
        days_ago = (now - date).days
        
        # Weight by recency
        if days_ago <= 90:        # 0-3 months
            weight = 1.0
        elif days_ago <= 180:     # 3-6 months
            weight = 0.6
        elif days_ago <= 365:     # 6-12 months
            weight = 0.3
        else:
            weight = 0.1

        recent_runs.append({
            'pace': pace_min,
            'distance': dist,
            'weight': weight,
            'days_ago': days_ago
        })

    if not recent_runs:
        return "N/A", "0%", "N/A"

    # Find best pace in recent runs (weighted by distance similarity)
    best_recent_pace = None
    for run in recent_runs:
        if run['weight'] >= 0.6:  # Only recent runs
            dist_ratio = min(run['distance'], target_miles) / max(run['distance'], target_miles)
            if dist_ratio >= 0.7:  # Similar distance
                if best_recent_pace is None or run['pace'] < best_recent_pace:
                    best_recent_pace = run['pace']

    # Calculate predicted pace
    if target_miles <= 1.5:
        # Mile: Use absolute fastest pace from any distance with aggressive improvement
        fastest_recent = min(r['pace'] for r in recent_runs if r['weight'] >= 0.6)
        # Assume you can sustain 95% of fastest pace for a mile all-out
        predicted_pace = fastest_recent * 0.95
        
    elif target_miles <= 5:
        # 5K and under: use best recent pace with moderate adjustment
        if best_recent_pace and pr_pace:
            # Use the better of: PR pace or best recent pace
            base_pace = min(best_recent_pace, pr_pace)
        elif pr_pace:
            base_pace = pr_pace
        elif best_recent_pace:
            base_pace = best_recent_pace
        else:
            # Average of fastest 25% of recent paces
            sorted_paces = sorted([r['pace'] for r in recent_runs if r['weight'] >= 0.6])
            top_25_percent = sorted_paces[:max(1, len(sorted_paces)//4)]
            base_pace = sum(top_25_percent) / len(top_25_percent)
        
        # Optimistic adjustment for short races (1-3% improvement potential)
        if pr_pace:
            predicted_pace = base_pace * 0.99  # 1% improvement if you have a PR
        else:
            predicted_pace = base_pace * 0.97  # 3% improvement if no PR yet
        
    else:
        # Long races: scale from closest distance PR or best long run
        closest_runs = sorted(recent_runs, key=lambda x: abs(x['distance'] - target_miles))[:5]
        
        # Find best weighted pace from similar distances
        best_weighted_pace = min(r['pace'] for r in closest_runs if r['weight'] >= 0.3)
        closest_dist = closest_runs[0]['distance']
        
        # Scale using Riegel-like formula but more optimistic
        scaling_factor = (target_miles / closest_dist) ** 1.05  # Slightly less penalty
        predicted_pace = best_weighted_pace * scaling_factor * 0.98  # 2% optimistic

    predicted_time_min = predicted_pace * target_miles

    # Ensure prediction is at least as fast as current PR (or slightly faster)
    if pr_time:
        # For short races, be more aggressive (predict 1-2% faster than PR)
        if target_miles <= 5:
            predicted_time_min = min(predicted_time_min, pr_time * 0.98)
        else:
            predicted_time_min = min(predicted_time_min, pr_time * 0.99)

    # Calculate confidence score
    confidence = 50  # Base confidence
    
    # Factor 1: Recent training volume (more recent runs = higher confidence)
    recent_count = sum(1 for r in recent_runs if r['days_ago'] <= 90)
    if recent_count >= 20:
        confidence += 20
    elif recent_count >= 10:
        confidence += 10
    elif recent_count >= 5:
        confidence += 5
    
    # Factor 2: Experience at target distance
    if pr_time:
        confidence += 15  # Have done this distance before
    
    # Factor 3: Long run experience (for longer races)
    max_recent_distance = max(r['distance'] for r in recent_runs if r['days_ago'] <= 90)
    if target_miles <= max_recent_distance:
        confidence += 15
    elif target_miles <= max_recent_distance * 1.3:
        confidence += 10
    elif target_miles <= max_recent_distance * 1.5:
        confidence += 5
    
    # Factor 4: Pace consistency
    recent_paces = [r['pace'] for r in recent_runs if r['days_ago'] <= 90]
    if len(recent_paces) >= 5:
        pace_std = math.sqrt(sum((p - sum(recent_paces)/len(recent_paces))**2 for p in recent_paces) / len(recent_paces))
        if pace_std < 0.5:  # Very consistent
            confidence += 10
        elif pace_std < 1.0:  # Moderately consistent
            confidence += 5
    
    confidence = min(100, confidence)

    # Calculate time variability based on distance
    if target_miles <= 5:
        # Short races: tight range (3-5 seconds per mile)
        seconds_per_mile_variance = 4
    elif target_miles <= 15:
        # Medium races: moderate range (5-8 seconds per mile)
        seconds_per_mile_variance = 6
    else:
        # Long races: wider range (8-12 seconds per mile)
        seconds_per_mile_variance = 10
    
    total_variance_seconds = seconds_per_mile_variance * target_miles
    range_str = f"+/-{int(total_variance_seconds)}s"

    # Convert predicted time to h:mm:ss
    hours = int(predicted_time_min // 60)
    minutes = int(predicted_time_min % 60)
    seconds = int((predicted_time_min - int(predicted_time_min)) * 60)
    time_str = f"{hours}:{minutes:02d}:{seconds:02d}"

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