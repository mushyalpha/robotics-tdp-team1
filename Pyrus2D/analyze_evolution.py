"""
Analyze the evolution results and generate comparison metrics
"""
import os
import json
from pathlib import Path
import re

def extract_metrics_from_logs(log_dir):
    """Extract performance metrics from log files"""
    metrics = {
        "passes_attempted": 0,
        "shots_attempted": 0,
        "ball_possessions": 0,
        "goals_scored": 0,
        "distance_covered": 0,
    }
    
    # Parse log files (you'll need to adjust based on actual log format)
    for log_file in Path(log_dir).glob("*.log"):
        with open(log_file, 'r') as f:
            content = f.read()
            
            # Count specific actions (adjust regex based on your logs)
            metrics["passes_attempted"] += len(re.findall(r'pass', content, re.IGNORECASE))
            metrics["shots_attempted"] += len(re.findall(r'shoot', content, re.IGNORECASE))
            metrics["ball_possessions"] += len(re.findall(r'kickable', content, re.IGNORECASE))
    
    return metrics

def analyze_version(version_name):
    """Analyze all games for a version"""
    version_dir = Path(f"evolution_results/{version_name}")
    
    if not version_dir.exists():
        return None
    
    all_metrics = []
    
    for game_dir in sorted(version_dir.iterdir()):
        if game_dir.is_dir():
            metrics = extract_metrics_from_logs(game_dir)
            all_metrics.append(metrics)
    
    # Calculate averages
    if not all_metrics:
        return None
    
    avg_metrics = {}
    for key in all_metrics[0].keys():
        avg_metrics[key] = sum(m[key] for m in all_metrics) / len(all_metrics)
    
    return avg_metrics

def main():
    versions = [
        ("v1_basic", "Basic: Random kicks"),
        ("v2_positioning", "With positioning"),
        ("v3_passing", "With passing"),
        ("v4_shooting", "With smart shooting"),
        ("v5_full", "Full algorithms"),
    ]
    
    print("\n" + "="*80)
    print("DECISION TREE EVOLUTION ANALYSIS")
    print("="*80 + "\n")
    
    results = {}
    
    for version_name, description in versions:
        print(f"\nAnalyzing: {description}")
        print("-" * 60)
        
        metrics = analyze_version(version_name)
        
        if metrics:
            results[version_name] = metrics
            print(f"  Passes attempted:    {metrics['passes_attempted']:.1f}")
            print(f"  Shots attempted:     {metrics['shots_attempted']:.1f}")
            print(f"  Ball possessions:    {metrics['ball_possessions']:.1f}")
            print(f"  Goals scored:        {metrics['goals_scored']:.1f}")
        else:
            print("  No data found")
    
    # Save results
    with open("evolution_results/summary.json", 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\n" + "="*80)
    print("Analysis complete! Results saved to evolution_results/summary.json")
    print("="*80 + "\n")
    
    # Print improvement percentages
    if "v1_basic" in results and "v5_full" in results:
        print("\nIMPROVEMENT FROM BASIC TO FULL:")
        print("-" * 60)
        for metric in results["v1_basic"].keys():
            basic = results["v1_basic"][metric]
            full = results["v5_full"][metric]
            if basic > 0:
                improvement = ((full - basic) / basic) * 100
                print(f"  {metric:20s}: {improvement:+.1f}%")

if __name__ == "__main__":
    main()
