Strava Pro


strava_pro/
│
|
|
├── database/
│   ├── database.py          ← creates DB + tables
│   └── insert_data.py       ← puts Strava data into DB
│
|
|
├── data_raw/               # Raw JSON files from Strava API (untouched)
│   ├── activities_raw.json
│   ├── detailed_activity_*.json
│   ├── streams_*.json
│   └── segments_*.json
│
├── data_processed/         # Cleaned & structured data
│   ├── activities_clean.json
│   ├── runs_with_metrics.json
│   └── training_dataset.csv
│
├── ingestion/              # All API pulling scripts
│   ├── get_activities.py
│   ├── get_detailed_activity.py
│   ├── get_activity_streams.py
│   ├── get_segment_efforts.py
│   └── get_athlete_profile.py   ← (the new one I’ll give)
│
├── processing/             # Transformations & calculations
│   ├── compute_metrics.py
│   ├── create_split_data.py
│   ├── run_classifier.py
│   └── training_load.py
│
├── models/                 # ML models
│   ├── race_predictor.py
│   ├── fatigue_model.py
│   └── model_utils.py
│
├── backend/                # Your web API
│   ├── app.py
│   ├── routes/
│   └── auth/
│
├── frontend/               # UI
│   ├── src/
│   └── public/
│
├── utils/                  # Shared helpers
│   ├── auth_utils.py
│   └── plotting.py
│
└── README.md
