import requests
import json
import sqlite3
import os
import time

# ----------------------------
# Fetch per-second Strava streams
# ----------------------------
#
# Saves files to: data_raw/streams_{activity_id}.json
#
# Notes:
# - Default filters to sport_type == "Run" to save API calls.
# - Honors rate-limit responses (429) by sleeping 15 minutes.
# - Retries network/SSL errors with exponential backoff.
# - Keeps code simple and well-commented.
# ----------------------------


# Which sport to download streams for. Set to None to download for all activities.
FILTER_SPORT = "Run"  # change to None to pull for all sports

# Which stream keys to request
STREAM_KEYS = ",".join([
    "time",
    "latlng",
    "altitude",
    "heartrate",
    "velocity_smooth",
    "distance",
    "cadence",
    "grade_smooth"
])


def get_streams(access_token, activity_id, max_retries=5):
    """
    Fetch streams for a single activity with retries.
    Returns dict for successful response, {"message":"Rate Limit Exceeded"} for 429,
    or None for other failures.
    """
    url = f"https://www.strava.com/api/v3/activities/{activity_id}/streams"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"keys": STREAM_KEYS, "key_by_type": "true"}

    for attempt in range(max_retries):
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=15)

            # Rate limit
            if resp.status_code == 429:
                # Optionally you can parse headers here: X-RateLimit-Limit and X-RateLimit-Usage
                return {"message": "Rate Limit Exceeded"}

            # If stream not found or not available, Strava returns 404 or empty content
            if resp.status_code == 404:
                print(f"Streams not available for activity {activity_id} (404).")
                return None

            if resp.status_code != 200:
                print(f"Unexpected status for {activity_id}: {resp.status_code} - {resp.text}")
                return None

            # Success
            return resp.json()

        except requests.exceptions.ConnectionError:
            print(f"Connection error for {activity_id}. Retrying (attempt {attempt + 1})...")
            time.sleep(2 + attempt * 2)  # backoff

        except requests.exceptions.SSLError:
            print(f"SSL error for {activity_id}. Retrying (attempt {attempt + 1})...")
            time.sleep(2 + attempt * 2)

        except requests.exceptions.Timeout:
            print(f"Timeout for {activity_id}. Retrying (attempt {attempt + 1})...")
            time.sleep(2 + attempt * 2)

        except Exception as e:
            print(f"Unexpected error for {activity_id}: {e}")
            return None

    print(f"Failed to fetch streams for {activity_id} after {max_retries} retries.")
    return None


def load_activity_ids_and_sports():
    """Load (id, sport_type) tuples from the activities table."""
    conn = sqlite3.connect("strava.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, sport_type FROM activities")
    rows = cursor.fetchall()
    conn.close()
    return rows


def pull_all_streams(access_token):
    output_dir = "data_raw/activity_streams"
    os.makedirs(output_dir, exist_ok=True)

    rows = load_activity_ids_and_sports()
    print(f"Found {len(rows)} activities in the database.")

    for activity_id, sport_type in rows:
        # If filtering by sport, skip non-matching activities
        if FILTER_SPORT and sport_type is not None and sport_type.lower() != FILTER_SPORT.lower():
            continue

        file_path = os.path.join(output_dir, f"streams_{activity_id}.json")

        # Skip if already downloaded
        if os.path.exists(file_path):
            print(f"Skipping streams for {activity_id} (already downloaded)")
            continue

        print(f"Fetching streams for activity {activity_id} (sport: {sport_type}) ...")

        data = get_streams(access_token, activity_id)

        if data is None:
            # None indicates either streams not available, 404, or persistent error
            # we continue to next activity
            continue

        # Handle rate limit
        if isinstance(data, dict) and data.get("message") == "Rate Limit Exceeded":
            print("\n🚫 Rate limit reached. Sleeping for 15 minutes...\n")
            time.sleep(15 * 60)
            continue  # resume with same—script will move to next id after wake

        # Save streams JSON
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)

        # Friendly delay so we don't hammer the API
        time.sleep(0.3)

    print("\nFinished pulling streams for activities.")


if __name__ == "__main__":
    ACCESS_TOKEN = "14c4874936c62a7ddfb0fc931f265dd671bbf66f"  # Replace with your token
    pull_all_streams(ACCESS_TOKEN)
