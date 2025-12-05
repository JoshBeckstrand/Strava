import requests
import json
import os

# This script pulls all activities from the Strava API
# and saves them into data_raw/activities_raw.json.

def get_all_activities(access_token):
    url = "https://www.strava.com/api/v3/athlete/activities"
    headers = {"Authorization": f"Bearer {access_token}"}

    # Pull as many activities as possible on one page
    params = {
        "per_page": 200,   # max results per page
        "page": 1
    }

    response = requests.get(url, headers=headers, params=params)

    # Ensure we got a valid response before writing to file
    if response.status_code != 200:
        print("Error pulling data from Strava:", response.text)
        return None

    activities = response.json()

    # Save result to data_raw/ folder
    raw_dir = "data_raw"
    os.makedirs(raw_dir, exist_ok=True)

    file_path = os.path.join(raw_dir, "activities_raw.json")

    with open(file_path, "w") as f:
        json.dump(activities, f, indent=2)

    print(f"Saved {len(activities)} activities to {file_path}")
    return activities


if __name__ == "__main__":
    # Replace YOUR_ACCESS_TOKEN with your actual Strava token
    ACCESS_TOKEN = "c1efb1e8e5daec9b9b0ef232830b2f1f1f3784f0"

    # Pull the full activity list
    get_all_activities(ACCESS_TOKEN)
