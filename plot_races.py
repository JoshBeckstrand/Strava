import json
import matplotlib.pyplot as plt

INPUT_FILE = "running_race_predictions.json"

# Load predictions
with open(INPUT_FILE, "r") as f:
    predictions = json.load(f)

# Distances in miles for x-axis, sorted
race_order = ["1 Mile", "5K", "10K", "Half Marathon", "Marathon", "50K", "50 Mile"]
distances = [predictions[r]["Riegel"] for r in race_order]  # placeholder to get sorted keys

# Convert time string "h:mm:ss" to hours as float
def time_str_to_hours(t):
    if t == "N/A":
        return None
    h, m, s = map(int, t.split(":"))
    return h + m/60 + s/3600

# Prepare data for each formula
formulas = ["Riegel", "Jack Daniels", "Cameron"]
race_miles = [1, 3.10686, 6.21371, 13.1094, 26.2188, 31.07, 50]

plt.figure(figsize=(10,6))

for formula in formulas:
    times_hours = []
    for race in race_order:
        t = time_str_to_hours(predictions[race][formula])
        times_hours.append(t)
    plt.plot(race_miles, times_hours, marker='o', label=formula)

plt.xticks(race_miles, race_order, rotation=45)
plt.xlabel("Race Distance")
plt.ylabel("Predicted Time (hours)")
plt.title("Race Time Predictions by Formula")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()
