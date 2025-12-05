import requests
import json
import os

# Pulls ALL Strava activities by looping through pages until no results come back
def get_all_activities(access_token):
    url = "https://www.strava.com/api/v3/athlete/activities"
    headers = {"Authorization": f"Bearer {access_token}"}

    all_activities = []
    page = 1  # start on the first page

    while True:
        params = {
            "per_page": 200,  # max allowed
            "page": page
        }

        response = requests.get(url, headers=headers, params=params)

        if response.status_code != 200:
            print("Error pulling data:", response.text)
            break

        activities = response.json()

        # Stop loop when Strava returns an empty list
        if not activities:
            print(f"No more activities found. Total collected: {len(all_activities)}")
            break

        print(f"Fetched page {page} with {len(activities)} activities")
        all_activities.extend(activities)

        page += 1  # move to the next page

    # Save to data_raw folder
    raw_dir = "data_raw"
    os.makedirs(raw_dir, exist_ok=True)

    file_path = os.path.join(raw_dir, "activities_raw.json")

    with open(file_path, "w") as f:
        json.dump(all_activities, f, indent=2)

    print(f"Saved {len(all_activities)} total activities to {file_path}")
    return all_activities


if __name__ == "__main__":
    ACCESS_TOKEN = "14c4874936c62a7ddfb0fc931f265dd671bbf66f"

    get_all_activities(ACCESS_TOKEN)
