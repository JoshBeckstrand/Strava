import json
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict

def parse_pace(pace_str):
    """Convert pace string (MM:SS) to seconds per mile"""
    try:
        parts = pace_str.split(':')
        pace_seconds = int(parts[0]) * 60 + int(parts[1])
        # Filter out unrealistic paces (under 4:00/mile or over 20:00/mile)
        if pace_seconds < 240 or pace_seconds > 1200:
            return None
        return pace_seconds
    except:
        return None

def format_time(total_seconds):
    """Format seconds into H:MM:SS"""
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)
    return f"{hours}:{minutes:02d}:{seconds:02d}"

def format_pace(seconds_per_mile):
    """Format pace as MM:SS/mile"""
    minutes = int(seconds_per_mile // 60)
    seconds = int(seconds_per_mile % 60)
    return f"{minutes}:{seconds:02d}"

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
            if pace_secs:
                paces.append(pace_secs)
        
        if paces and len(paces) >= 1:
            runs.append({
                'date': date,
                'distance': distance,
                'paces': paces,
                'avg_pace': np.mean(paces),
                'fastest_mile': min(paces),
                'name': run_data['name']
            })
    
    return sorted(runs, key=lambda x: x['date'])

def calculate_best_performances(runs):
    """Calculate best performances across all data"""
    fastest_mile = min([r['fastest_mile'] for r in runs])
    best_avg_pace = min([r['avg_pace'] for r in runs])
    
    # Best paces at various distances
    best_5k = min([r['avg_pace'] for r in runs if 3.0 <= r['distance'] <= 3.5], default=None)
    best_10k = min([r['avg_pace'] for r in runs if 5.5 <= r['distance'] <= 7.0], default=None)
    best_half = min([r['avg_pace'] for r in runs if 12.5 <= r['distance'] <= 13.5], default=None)
    best_marathon = min([r['avg_pace'] for r in runs if 26.0 <= r['distance'] <= 26.5], default=None)
    
    total_miles = sum([r['distance'] for r in runs])
    total_runs = len(runs)
    longest_run = max([r['distance'] for r in runs])
    
    return {
        'fastest_mile': fastest_mile,
        'best_avg_pace': best_avg_pace,
        'best_5k': best_5k,
        'best_10k': best_10k,
        'best_half': best_half,
        'best_marathon': best_marathon,
        'total_miles': total_miles,
        'total_runs': total_runs,
        'longest_run': longest_run
    }

def calculate_speed_score(runs, days=60):
    """Calculate raw speed capability from recent fast runs"""
    cutoff = datetime.now() - timedelta(days=days)
    recent = [r for r in runs if r['date'] >= cutoff]
    
    if not recent:
        recent = runs[-20:]  # Use last 20 runs if no recent data
    
    # Get fastest miles from runs under 8 miles (speed work)
    speed_runs = [r for r in recent if r['distance'] <= 8]
    if speed_runs:
        fastest_miles = [r['fastest_mile'] for r in speed_runs]
        # Average of top 5 fastest miles
        top_miles = sorted(fastest_miles)[:5]
        speed_score = np.mean(top_miles)
    else:
        speed_score = min([r['fastest_mile'] for r in recent])
    
    return speed_score

def calculate_endurance_score(runs, days=90):
    """Calculate endurance capability from long runs"""
    cutoff = datetime.now() - timedelta(days=days)
    recent = [r for r in runs if r['date'] >= cutoff]
    
    if not recent:
        recent = runs[-30:]
    
    # Get paces from long runs (10+ miles)
    long_runs = [r for r in recent if r['distance'] >= 10]
    
    if long_runs:
        # Average pace of best 3 long runs
        best_long_paces = sorted([r['avg_pace'] for r in long_runs])[:3]
        endurance_score = np.mean(best_long_paces)
    else:
        # Use medium distance runs
        medium_runs = [r for r in recent if 6 <= r['distance'] < 10]
        if medium_runs:
            endurance_score = np.mean([r['avg_pace'] for r in medium_runs])
        else:
            endurance_score = np.mean([r['avg_pace'] for r in recent])
    
    return endurance_score

def calculate_fatigue_resistance(runs):
    """Calculate how well runner maintains pace when fatigued"""
    fatigue_scores = []
    
    # Look at runs 10+ miles
    long_runs = [r for r in runs if r['distance'] >= 10 and len(r['paces']) >= 8]
    
    for run in long_runs:
        # Compare last 25% to first 25% pace
        split_point = max(2, len(run['paces']) // 4)
        first_portion = np.mean(run['paces'][:split_point])
        last_portion = np.mean(run['paces'][-split_point:])
        
        # Calculate slowdown percentage
        slowdown = (last_portion - first_portion) / first_portion
        fatigue_scores.append(slowdown)
    
    avg_slowdown = np.mean(fatigue_scores) if fatigue_scores else 0.05
    # Convert to resistance score (0-1, higher is better)
    resistance = max(0, 1 - (avg_slowdown * 5))
    return resistance

def calculate_training_volume(runs, days=90):
    """Calculate recent training volume and consistency"""
    cutoff = datetime.now() - timedelta(days=days)
    recent = [r for r in runs if r['date'] >= cutoff]
    
    if not recent:
        return 0, 0
    
    total_miles = sum([r['distance'] for r in recent])
    weeks = days / 7
    avg_weekly_miles = total_miles / weeks
    
    # Long run capability
    long_runs = [r['distance'] for r in recent if r['distance'] >= 13]
    max_long_run = max(long_runs) if long_runs else max([r['distance'] for r in recent])
    
    return avg_weekly_miles, max_long_run

def calculate_training_metrics(runs):
    """Calculate training metrics from all data"""
    cutoff_90 = datetime.now() - timedelta(days=90)
    recent_90 = [r for r in runs if r['date'] >= cutoff_90]
    
    cutoff_30 = datetime.now() - timedelta(days=30)
    recent_30 = [r for r in runs if r['date'] >= cutoff_30]
    
    weekly_miles_90 = sum([r['distance'] for r in recent_90]) / (90/7) if recent_90 else 0
    weekly_miles_30 = sum([r['distance'] for r in recent_30]) / (30/7) if recent_30 else 0
    
    long_runs = [r['distance'] for r in recent_90 if r['distance'] >= 10]
    max_long_run = max(long_runs) if long_runs else 0
    
    return {
        'weekly_miles_90': weekly_miles_90,
        'weekly_miles_30': weekly_miles_30,
        'max_long_run': max_long_run,
        'recent_runs_90': len(recent_90),
        'recent_runs_30': len(recent_30)
    }

def calculate_fitness_trend(runs):
    """Calculate recent fitness trend"""
    cutoff = datetime.now() - timedelta(days=60)
    recent = [r for r in runs if r['date'] >= cutoff]
    
    if len(recent) < 10:
        return 1.0
    
    split = len(recent) // 4
    first_quarter_pace = np.mean([r['avg_pace'] for r in recent[:split]])
    last_quarter_pace = np.mean([r['avg_pace'] for r in recent[-split:]])
    
    trend = first_quarter_pace / last_quarter_pace
    return trend

def predict_race_times(json_file):
    """Main prediction function using custom algorithm"""
    runs = load_strava_data(json_file)
    
    if not runs:
        print("No valid run data found")
        return
    
    # Calculate all metrics
    best_perfs = calculate_best_performances(runs)
    training_metrics = calculate_training_metrics(runs)
    fitness_trend = calculate_fitness_trend(runs)
    
    # Core performance indicators
    speed_score = calculate_speed_score(runs)  # Best recent speed capability
    endurance_score = calculate_endurance_score(runs)  # Best recent endurance
    fatigue_resistance = calculate_fatigue_resistance(runs)  # How well you hold pace
    weekly_volume, max_long = calculate_training_volume(runs)  # Training load
    
    # Calculate base fitness from speed and endurance
    # Faster runners have lower pace numbers, so lower is better
    base_fitness = (speed_score * 0.4 + endurance_score * 0.6)
    
    # Volume readiness (0-1 scale)
    volume_readiness = min(1.0, weekly_volume / 50)  # 50+ mpw = fully ready
    
    # Long run readiness (0-1 scale)
    long_run_readiness = min(1.0, max_long / 20)  # 20+ mile long run = fully ready
    
    # Ultra experience (0-1 scale)
    ultra_readiness = min(1.0, max_long / 26)  # 26+ mile run = ultra ready
    
    # Race predictions with custom formula
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
        if race_name == 'Mile':
            # Pure speed - use best recent mile with small fatigue buffer
            predicted_pace = speed_score * 1.15
            
        elif race_name == '5K':
            # Mostly speed, slight endurance factor
            predicted_pace = speed_score * 1.35 + (1 - fatigue_resistance) * 5
            
        elif race_name == '10K':
            # Balance of speed and endurance
            predicted_pace = (speed_score * 0.7 + endurance_score * 0.3) * 1.20 + (1 - fatigue_resistance) * 8
            
        elif race_name == 'Half Marathon':
            # More endurance, speed still matters
            predicted_pace = (speed_score * 0.3 + endurance_score * 0.7) * 1.15
            predicted_pace += (1 - fatigue_resistance) * 15
            predicted_pace *= (1 + (1 - volume_readiness) * 0.05)
            
        elif race_name == 'Marathon':
            # Heavily endurance and volume dependent
            predicted_pace = endurance_score * 1.20
            predicted_pace += (1 - fatigue_resistance) * 20
            predicted_pace *= (1 + (1 - volume_readiness * long_run_readiness) * 0.12)
            
        elif race_name == '50K':
            # Ultra begins - conservative pacing
            predicted_pace = endurance_score * 1.25
            predicted_pace += (1 - fatigue_resistance) * 25
            predicted_pace *= (1 + (1 - volume_readiness * ultra_readiness) * 0.15)
            
        elif race_name == '50 Mile':
            # Serious ultra territory
            predicted_pace = endurance_score * 1.35
            predicted_pace += (1 - fatigue_resistance) * 30
            predicted_pace *= (1 + (1 - volume_readiness * ultra_readiness) * 0.20)
            
        else:  # 100 Mile
            # Ultimate endurance test
            predicted_pace = endurance_score * 1.50
            predicted_pace += (1 - fatigue_resistance) * 40
            predicted_pace *= (1 + (1 - volume_readiness * ultra_readiness) * 0.30)
        
        # Calculate total time (predicted_pace is in seconds per mile)
        total_time = predicted_pace * race_dist
        predictions[race_name] = total_time
    
    # Print and save results
    print_results(runs, best_perfs, training_metrics, fatigue_resistance, 
                  fitness_trend, predictions, races, speed_score, endurance_score,
                  volume_readiness, long_run_readiness, ultra_readiness)
    write_predictions_to_file(runs, best_perfs, training_metrics, 
                              fatigue_resistance, fitness_trend, 
                              predictions, races)
    
    return predictions

def print_results(runs, best_perfs, training_metrics, fatigue_resistance, 
                 fitness_trend, predictions, races, speed_score, endurance_score,
                 volume_readiness, long_run_readiness, ultra_readiness):
    """Print results to console"""
    print("=" * 70)
    print("RACE TIME PREDICTIONS")
    print("=" * 70)
    print(f"\nBased on {best_perfs['total_runs']} runs from {runs[0]['date'].date()} to {runs[-1]['date'].date()}")
    print(f"Total Miles: {best_perfs['total_miles']:.1f}")
    
    print(f"\nAll-Time Best Performances:")
    print(f"  Fastest Mile: {format_pace(best_perfs['fastest_mile'])}")
    print(f"  Best Average Pace: {format_pace(best_perfs['best_avg_pace'])}")
    if best_perfs['best_5k']:
        print(f"  Best 5K Pace: {format_pace(best_perfs['best_5k'])}")
    if best_perfs['best_10k']:
        print(f"  Best 10K Pace: {format_pace(best_perfs['best_10k'])}")
    if best_perfs['best_half']:
        print(f"  Best Half Marathon Pace: {format_pace(best_perfs['best_half'])}")
    if best_perfs['best_marathon']:
        print(f"  Best Marathon Pace: {format_pace(best_perfs['best_marathon'])}")
    print(f"  Longest Run: {best_perfs['longest_run']:.1f} miles")
    
    print(f"\nRecent Training:")
    print(f"  Weekly Mileage (Last 90 days): {training_metrics['weekly_miles_90']:.1f} miles")
    print(f"  Weekly Mileage (Last 30 days): {training_metrics['weekly_miles_30']:.1f} miles")
    print(f"  Longest Run (Last 90 days): {training_metrics['max_long_run']:.1f} miles")
    
    print(f"\nReadiness Scores:")
    print(f"  Speed Score: {format_pace(speed_score)} (recent best mile capability)")
    print(f"  Endurance Score: {format_pace(endurance_score)} (long run pace capability)")
    print(f"  Fatigue Resistance: {fatigue_resistance*100:.1f}%")
    print(f"  Volume Readiness: {volume_readiness*100:.1f}%")
    print(f"  Long Run Readiness: {long_run_readiness*100:.1f}%")
    print(f"  Ultra Readiness: {ultra_readiness*100:.1f}%")
    print(f"  Fitness Trend: {'+' if fitness_trend > 1 else ''}{(fitness_trend-1)*100:.1f}%")
    
    print(f"\n{'Race':<20} {'Predicted Time':<15} {'Pace'}")
    print("-" * 70)
    
    for race_name, total_seconds in predictions.items():
        pace_per_mile = total_seconds / races[race_name]
        print(f"{race_name:<20} {format_time(total_seconds):<15} {format_pace(pace_per_mile)}/mile")
    
    print("\n" + "=" * 70)
    print("Note: Predictions assume optimal conditions and proper race execution.")
    print("Ultra predictions require appropriate training and race-day nutrition.")
    print("=" * 70)

def write_predictions_to_file(runs, best_perfs, training_metrics, 
                              fatigue_resistance, fitness_trend, 
                              predictions, races):
    """Write predictions to output file"""
    with open('race_predictions.txt', 'w') as f:
        f.write("=" * 70 + "\n")
        f.write("RACE TIME PREDICTIONS\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Based on {best_perfs['total_runs']} runs from {runs[0]['date'].date()} to {runs[-1]['date'].date()}\n")
        f.write(f"Total Miles: {best_perfs['total_miles']:.1f}\n\n")
        
        f.write("All-Time Best Performances:\n")
        f.write(f"  Fastest Mile: {format_pace(best_perfs['fastest_mile'])}\n")
        f.write(f"  Best Average Pace: {format_pace(best_perfs['best_avg_pace'])}\n")
        if best_perfs['best_5k']:
            f.write(f"  Best 5K Pace: {format_pace(best_perfs['best_5k'])}\n")
        if best_perfs['best_10k']:
            f.write(f"  Best 10K Pace: {format_pace(best_perfs['best_10k'])}\n")
        if best_perfs['best_half']:
            f.write(f"  Best Half Marathon Pace: {format_pace(best_perfs['best_half'])}\n")
        if best_perfs['best_marathon']:
            f.write(f"  Best Marathon Pace: {format_pace(best_perfs['best_marathon'])}\n")
        f.write(f"  Longest Run: {best_perfs['longest_run']:.1f} miles\n\n")
        
        f.write("Recent Training:\n")
        f.write(f"  Weekly Mileage (Last 90 days): {training_metrics['weekly_miles_90']:.1f} miles\n")
        f.write(f"  Weekly Mileage (Last 30 days): {training_metrics['weekly_miles_30']:.1f} miles\n")
        f.write(f"  Longest Run (Last 90 days): {training_metrics['max_long_run']:.1f} miles\n")
        f.write(f"  Fatigue Resistance: {fatigue_resistance*100:.1f}%\n")
        f.write(f"  Fitness Trend: {'+' if fitness_trend > 1 else ''}{(fitness_trend-1)*100:.1f}%\n\n")
        
        f.write("=" * 70 + "\n")
        f.write("PREDICTED RACE TIMES\n")
        f.write("=" * 70 + "\n\n")
        
        for race_name, total_seconds in predictions.items():
            pace_per_mile = total_seconds / races[race_name]
            f.write(f"{race_name}: {format_time(total_seconds)} (Pace: {format_pace(pace_per_mile)}/mile)\n")
        
        f.write("\n" + "=" * 70 + "\n")
        f.write("Note: Predictions assume optimal conditions and proper race execution.\n")
        f.write("Ultra predictions require appropriate training and race-day nutrition.\n")
        f.write("=" * 70 + "\n")
    
    print("\nPredictions saved to 'race_predictions.txt'")

# Run the analysis
if __name__ == "__main__":
    predict_race_times('strava_running_splits.json')