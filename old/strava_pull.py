import requests
import datetime
import time
import json
import sys

ACCESS_TOKEN = "413f27d03a272177e3e6a4db9eb365ab887ba03b"
OUTPUT_FILE = "strava_raw_data.json"

# Time range: Jan 1, 2024 → now
start_date = datetime.datetime(2024, 1, 1)
end_date = datetime.datetime.now()
after_ts = int(start_date.timestamp())
before_ts = int(end_date.timestamp())

print("=== Strava Data Pull Started ===")
print(f"Pulling activities from {start_date.date()} to {end_date.date()}")
print("This may take a few seconds...\n")

activities = []
page = 1

while True:
    print(f"Requesting page {page}...")

    try:
        response = requests.get(
            "https://www.strava.com/api/v3/athlete/activities",
            headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
            params={
                "after": after_ts,
                "before": before_ts,
                "page": page,
                "per_page": 200
            },
            timeout=8   # <--- prevents hanging forever
        )
    except requests.exceptions.Timeout:
        print("⏳ Request timed out. Retrying in 5 seconds...\n")
        time.sleep(5)
        continue
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

    print(f"Status: {response.status_code}")

    # Unauthorized token
    if response.status_code == 401:
        print("❌ Unauthorized. Your access token may be expired.")
        print("Generate a new one and update ACCESS_TOKEN.")
        sys.exit(1)

    # Rate-limited
    if response.status_code == 429:
        print("⚠️ Rate limited by Strava. Waiting 15 seconds...\n")
        time.sleep(15)
        continue

    # Other non-OK response
    if response.status_code != 200:
        print("❌ Error response from Strava:")
        print(response.text)
        sys.exit(1)

    # Parse response data
    try:
        data = response.json()
    except Exception:
        print("❌ Failed to parse JSON:")
        print(response.text)
        sys.exit(1)

    print(f"Received {len(data)} activities\n")

    # If page returns empty array, stop
    if not data:
        print("No more pages. Finished downloading.")
        break

    activities.extend(data)
    page += 1

    # prevent rate-limit issues
    time.sleep(0.3)

# Save file
with open(OUTPUT_FILE, "w") as f:
    json.dump(activities, f, indent=2)

print("=== Strava Data Pull Complete ===")
print(f"Total activities saved: {len(activities)}")
print(f"Saved to: {OUTPUT_FILE}")
