import requests
import json
import sqlite3
import os
import time

# ---------------------------------------------------------
# Pulls *detailed* Strava activity data for every activity
# stored in the SQLite database. Each activity is saved as
# a separate JSON file in data_raw/detailed_activities/.
# ---------------------------------------------------------


# Pull detailed activity from Strava
def get_detailed_activity(access_token, activity_id):
    url = f"https://www.strava.com/api/v3/activities/{activity_id}"
    headers = {"Authorization": f"Bearer {access_token}"}

    response = requests.get(url, headers=headers)

    # Handle rate limit error (429 = too many requests)
    if response.status_code == 429:
        return {"message": "Rate Limit Exceeded"}

    # Handle other errors
    if response.status_code != 200:
        print(f"Error fetching activity {activity_id}: {response.text}")
        return None

    # Normal successful response
    return response.json()


# Load activity IDs from SQLite
def load_activity_ids():
    conn = sqlite3.connect("strava.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM activities")
    rows = cursor.fetchall()
    conn.close()

    # Flatten rows into list of IDs
    return [row[0] for row in rows]


# Main function to pull all detailed activities
def pull_all_detailed(access_token):
    output_dir = "data_raw/detailed_activities"
    os.makedirs(output_dir, exist_ok=True)

    activity_ids = load_activity_ids()
    print(f"Found {len(activity_ids)} activities in the database.\n")

    for activity_id in activity_ids:
        file_path = os.path.join(output_dir, f"detailed_{activity_id}.json")

        # Skip if this detailed file already exists
        if os.path.exists(file_path):
            print(f"Skipping {activity_id} (already downloaded)")
            continue

        print(f"Fetching detailed data for activity {activity_id}...")

        data = get_detailed_activity(access_token, activity_id)

        # If API returned None, skip
        if data is None:
            continue

        # Detect Strava rate limit error
        if isinstance(data, dict) and data.get("message") == "Rate Limit Exceeded":
            print("\n🚫 Rate Limit Reached — Sleeping for 15 minutes...\n")
            time.sleep(15 * 60)
            continue  # after sleep, move to next activity

        # Save the detailed JSON file
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)

        # Friendly delay to avoid hitting limits too quickly
        time.sleep(0.3)

    print("\nAll detailed activity data downloaded successfully!")


# Run script directly
if __name__ == "__main__":
    ACCESS_TOKEN = "14c4874936c62a7ddfb0fc931f265dd671bbf66f"
    pull_all_detailed(ACCESS_TOKEN)
