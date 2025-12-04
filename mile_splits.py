import json
import requests
import time
import sys
from math import ceil

ACCESS_TOKEN = "413f27d03a272177e3e6a4db9eb365ab887ba03b"
INPUT_FILE = "strava_raw_data.json"
OUTPUT_FILE = "strava_running_splits.json"

# Load raw Strava data
try:
    with open(INPUT_FILE, "r") as f:
        activities = json.load(f)
except Exception as e:
    print(f"❌ Failed to load raw data: {e}")
    sys.exit(1)

# Filter running activities
running_activities = [act for act in activities if act.get("type") == "Run"]

print(f"Found {len(running_activities)} running activities.")

results = {}
for idx, act in enumerate(running_activities, start=1):
    act_id = act.get("id")
    name = act.get("name", "Unnamed Run")
    date = act.get("start_date", "Unknown Date")
    distance_m = act.get("distance", 0)
    distance_miles = distance_m * 0.000621371

    print(f"\n[{idx}/{len(running_activities)}] Pulling splits for '{name}' ({distance_miles:.2f} miles)...")

    # API endpoint for streams
    url = f"https://www.strava.com/api/v3/activities/{act_id}/streams"
    params = {
        "keys": "time,distance",
        "key_by_type": "true"
    }
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }

    # Retry logic
    retries = 3
    for attempt in range(1, retries+1):
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            if response.status_code == 429:  # Rate limited
                print("⚠️ Rate limited. Waiting 15 seconds...")
                time.sleep(15)
                continue
            elif response.status_code != 200:
                print(f"❌ Error fetching activity {act_id}: {response.status_code} {response.text}")
                raise Exception("API error")
            data = response.json()
            break  # success
        except Exception as e:
            print(f"Attempt {attempt} failed: {e}")
            if attempt < retries:
                print("Retrying in 5 seconds...")
                time.sleep(5)
            else:
                print(f"Skipping activity {act_id} due to repeated errors.")
                data = {}
    
    # Compute mile splits
    mile_splits = []
    try:
        times = data.get("time", {}).get("data", [])
        distances = data.get("distance", {}).get("data", [])
        if not times or not distances:
            mile_splits = ["N/A"]
        else:
            mile_index = 1
            last_time = 0
            for t, d in zip(times, distances):
                if d >= mile_index * 1609.34:
                    split_sec = t - last_time
                    minutes = int(split_sec // 60)
                    seconds = int(split_sec % 60)
                    mile_splits.append(f"{minutes}:{seconds:02d}")
                    last_time = t
                    mile_index += 1
            # If last mile incomplete, include partial
            if mile_index == 1 and distance_miles < 1:
                mile_splits.append(f"{int(times[-1]//60)}:{int(times[-1]%60):02d}")
    except Exception as e:
        print(f"❌ Error computing mile splits for activity {act_id}: {e}")
        mile_splits = ["N/A"]

    results[act_id] = {
        "name": name,
        "date": date,
        "distance_miles": round(distance_miles, 2),
        "mile_splits": mile_splits
    }

    # Prevent hitting rate limits
    time.sleep(0.5)

# Save to output file
try:
    with open(OUTPUT_FILE, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n✅ Mile splits saved to {OUTPUT_FILE}")
except Exception as e:
    print(f"❌ Failed to save output file: {e}")
