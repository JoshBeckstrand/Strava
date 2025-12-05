import json
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict

def parse_pace(pace_str):
    """Convert pace string (MM:SS) to seconds per mile"""
    try:
        parts = pace_str.split(':')
        return int(parts[0]) * 60 + int(parts[1])
    except:
        return None

def load_strava_data(json_file):
    """Load and parse Strava data from JSON file"""
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    runs = []
    for run_id, run_data in data.items():
        date = datetime.strptime(run_data['date'], '%Y-%m-%dT%H:%M:%SZ')
        distance = run_data['distance_miles']
        
        # Parse mile splits
        paces = []
        for pace in run_data['mile_splits']:
            pace_secs = parse_pace(pace)
            if pace_secs and pace_secs < 1200:  # Filter outliers (< 20 min/mile)
                paces.append(pace_secs)
        
        if paces:
            runs.append({
                'date': date,
                'distance': distance,
                'paces': paces,
                'avg_pace': np.mean(paces),
                'name': run_data['name']
            })
    
    return sorted(runs, key=lambda x: x['date'])

def calculate_fatigue_resistance(runs):
    """Calculate how well runner maintains pace when fatigued"""
    fatigue_scores = []
    
    for run in runs:
        if len(run['paces']) >= 3:
            # Compare last third to first third pace
            first_third = np.mean(run['paces'][:len(run['paces'])//3])
            last_third = np.mean(run['paces'][-len(run['paces'])//3:])
            
            # Lower is better (less slowdown)
            slowdown = (last_third - first_third) / first_third
            fatigue_scores.append(slowdown)
    
    return np.mean(fatigue_scores) if fatigue_scores else 0.05

def calculate_training_consistency(runs, days=90):
    """Calculate recent training consistency and volume"""
    cutoff = datetime.now() - timedelta(days=days)
    recent_runs = [r for r in runs if r['date'] >= cutoff]
    
    if not recent_runs:
        return 0, 0, 0
    
    weekly_miles = defaultdict(float)
    for run in recent_runs:
        week = run['date'].isocalendar()[1]
        weekly_miles[week] += run['distance']
    
    avg_weekly_miles = np.mean(list(weekly_miles.values()))
    consistency = len(weekly_miles) / (days / 7)
    
    # Long run capability
    long_runs = [r['distance'] for r in recent_runs if r['distance'] >= 10]
    max_long_run = max(long_runs) if long_runs else 0
    
    return avg_weekly_miles, consistency, max_long_run

def calculate_speed_endurance(runs):
    """Calculate speed at different distances"""
    distance_paces = defaultdict(list)
    
    for run in runs:
        if 2 <= run['distance'] <= 3:
            distance_paces['short'].append(run['avg_pace'])
        elif 4 <= run['distance'] <= 6:
            distance_paces['medium'].append(run['avg_pace'])
        elif 10 <= run['distance'] <= 15:
            distance_paces['long'].append(run['avg_pace'])
        elif run['distance'] >= 18:
            distance_paces['ultra'].append(run['avg_pace'])
    
    return {k: np.percentile(v, 25) if v else None 
            for k, v in distance_paces.items()}

def calculate_fitness_trend(runs, days=60):
    """Calculate recent fitness trend"""
    cutoff = datetime.now() - timedelta(days=days)
    recent = [r for r in runs if r['date'] >= cutoff]
    
    if len(recent) < 5:
        return 1.0
    
    # Calculate pace improvement over time
    mid_point = len(recent) // 2
    first_half_pace = np.mean([r['avg_pace'] for r in recent[:mid_point]])
    second_half_pace = np.mean([r['avg_pace'] for r in recent[mid_point:]])
    
    # Positive trend if getting faster
    trend = first_half_pace / second_half_pace
    return trend

def riegel_formula(time_sec, dist1, dist2, fatigue_factor=1.06):
    """Modified Riegel formula with fatigue adjustment"""
    return time_sec * ((dist2 / dist1) ** fatigue_factor)

def predict_race_times(json_file):
    """Main prediction function"""
    runs = load_strava_data(json_file)
    
    if not runs:
        print("No valid run data found")
        return
    
    # Calculate key metrics
    fatigue_resistance = calculate_fatigue_resistance(runs)
    avg_weekly_miles, consistency, max_long_run = calculate_training_consistency(runs)
    speed_profile = calculate_speed_endurance(runs)
    fitness_trend = calculate_fitness_trend(runs)
    
    # Get recent best performances
    recent_60 = [r for r in runs if r['date'] >= datetime.now() - timedelta(days=60)]
    
    # Find best recent paces
    best_5k_pace = min([r['avg_pace'] for r in recent_60 if 3 <= r['distance'] <= 4], default=None)
    best_10k_pace = min([r['avg_pace'] for r in recent_60 if 5 <= r['distance'] <= 7], default=None)
    best_half_pace = min([r['avg_pace'] for r in recent_60 if 12 <= r['distance'] <= 14], default=None)
    best_long_pace = min([r['avg_pace'] for r in recent_60 if r['distance'] >= 16], default=None)
    
    # Calculate base VDOT (running fitness level)
    base_paces = [p for p in [best_5k_pace, best_10k_pace] if p]
    if not base_paces:
        base_paces = [speed_profile.get('short'), speed_profile.get('medium')]
        base_paces = [p for p in base_paces if p]
    
    if not base_paces:
        print("Insufficient data for predictions")
        return
    
    base_pace = min(base_paces)
    
    # Adjustment factors
    fatigue_factor = 1.06 + (fatigue_resistance * 0.15)  # 1.06-1.09 range
    endurance_bonus = min(1.0, (avg_weekly_miles / 50) * (consistency / 0.85))
    fitness_adjustment = fitness_trend
    
    # Distance-specific experience adjustments
    ultra_experience = min(1.0, max_long_run / 20) if max_long_run > 0 else 0.6
    
    # Race predictions
    races = {
        'Mile': 1.0,
        '5K': 3.1,
        '10K': 6.2,
        'Half Marathon': 13.1,
        'Marathon': 26.2,
        '50K': 31.0,
        '50 Mile': 50.0,
        '100 Mile': 100.0
    }
    
    predictions = {}
    
    for race_name, race_dist in races.items():
        # Base prediction from 5K equivalent
        base_time = riegel_formula(base_pace * 3.1 * 60, 3.1, race_dist, fatigue_factor)
        
        # Apply adjustments
        if race_dist <= 6.2:
            # Short races - rely on speed
            adjusted_time = base_time * (1 / fitness_adjustment)
        elif race_dist <= 13.1:
            # Medium races - balance of speed and endurance
            adjusted_time = base_time * (1 / fitness_adjustment) * (2 - endurance_bonus * 0.3)
        elif race_dist <= 26.2:
            # Marathon - heavily endurance dependent
            marathon_ready = endurance_bonus * (1 + (max_long_run / 20) * 0.2)
            adjusted_time = base_time * (2.1 - marathon_ready)
        else:
            # Ultra distances - experience and endurance critical
            ultra_ready = ultra_experience * endurance_bonus
            adjusted_time = base_time * (2.5 - ultra_ready * 0.8)
        
        predictions[race_name] = adjusted_time
    
    # Print results
    print("=" * 70)
    print("RACE TIME PREDICTIONS")
    print("=" * 70)
    print(f"\nBased on {len(runs)} runs from {runs[0]['date'].date()} to {runs[-1]['date'].date()}")
    print(f"\nRecent Training (Last 90 days):")
    print(f"  Average Weekly Mileage: {avg_weekly_miles:.1f} miles")
    print(f"  Training Consistency: {consistency*100:.0f}%")
    print(f"  Longest Recent Run: {max_long_run:.1f} miles")
    print(f"  Fatigue Resistance: {(1-fatigue_resistance)*100:.1f}%")
    print(f"  Fitness Trend: {'+' if fitness_trend > 1 else ''}{(fitness_trend-1)*100:.1f}%")
    
    print(f"\n{'Race':<20} {'Predicted Time':<15} {'Pace/Mile'}")
    print("-" * 70)
    
    for race_name, total_seconds in predictions.items():
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = int(total_seconds % 60)
        
        pace_per_mile = total_seconds / races[race_name]
        pace_min = int(pace_per_mile // 60)
        pace_sec = int(pace_per_mile % 60)
        
        if hours > 0:
            time_str = f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            time_str = f"{minutes}:{seconds:02d}"
        
        print(f"{race_name:<20} {time_str:<15} {pace_min}:{pace_sec:02d}")
    
    print("\n" + "=" * 70)
    print("Note: Predictions assume optimal conditions and proper race execution.")
    print("Ultra predictions require appropriate training and race-day nutrition.")
    print("=" * 70)
    
    # Write predictions to output file
    write_predictions_to_file(predictions, races, runs, avg_weekly_miles, 
                             consistency, max_long_run, fatigue_resistance, 
                             fitness_trend)
    
    return predictions

def write_predictions_to_file(predictions, races, runs, avg_weekly_miles, 
                              consistency, max_long_run, fatigue_resistance, 
                              fitness_trend):
    """Write predictions to output file"""
    with open('race_predictions.txt', 'w') as f:
        f.write("=" * 70 + "\n")
        f.write("RACE TIME PREDICTIONS\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Based on {len(runs)} runs from {runs[0]['date'].date()} to {runs[-1]['date'].date()}\n\n")
        
        f.write("Recent Training (Last 90 days):\n")
        f.write(f"  Average Weekly Mileage: {avg_weekly_miles:.1f} miles\n")
        f.write(f"  Training Consistency: {consistency*100:.0f}%\n")
        f.write(f"  Longest Recent Run: {max_long_run:.1f} miles\n")
        f.write(f"  Fatigue Resistance: {(1-fatigue_resistance)*100:.1f}%\n")
        f.write(f"  Fitness Trend: {'+' if fitness_trend > 1 else ''}{(fitness_trend-1)*100:.1f}%\n\n")
        
        f.write("=" * 70 + "\n")
        f.write("PREDICTED RACE TIMES\n")
        f.write("=" * 70 + "\n\n")
        
        for race_name, total_seconds in predictions.items():
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            seconds = int(total_seconds % 60)
            
            pace_per_mile = total_seconds / races[race_name]
            pace_min = int(pace_per_mile // 60)
            pace_sec = int(pace_per_mile % 60)
            
            if hours > 0:
                time_str = f"{hours}:{minutes:02d}:{seconds:02d}"
            else:
                time_str = f"{minutes}:{seconds:02d}"
            
            f.write(f"{race_name}: {time_str} (Pace: {pace_min}:{pace_sec:02d}/mile)\n")
        
        f.write("\n" + "=" * 70 + "\n")
        f.write("Note: Predictions assume optimal conditions and proper race execution.\n")
        f.write("Ultra predictions require appropriate training and race-day nutrition.\n")
        f.write("=" * 70 + "\n")
    
    print("\nPredictions saved to 'race_predictions.txt'")

# Run the analysis
if __name__ == "__main__":
    # Replace with your JSON file path
    predict_race_times('strava_running_splits.json')