"""
Script to test different decision tree versions and collect results

Usage:
1. Start rcssserver in WSL
2. Run this script: python run_evolution_test.py
3. It will automatically test all versions and collect logs
"""
import subprocess
import time
import shutil
import os
import sys
from pathlib import Path

VERSIONS = [
    ("v1_basic", "base/decision_v1_basic.py", "Basic: Random kicks only"),
    ("v2_positioning", "base/decision_v2_positioning.py", "Add: Formation positioning"),
    ("v3_passing", "base/decision_v3_passing.py", "Add: Passing algorithm"),
    ("v4_shooting", "base/decision_v4_shooting.py", "Add: Smart shooting"),
    ("v5_full", "base/decision.py", "Full: All algorithms (dribble, block, etc)"),
]

NUM_GAMES = 5  # Run 5 games per version

def backup_decision():
    """Backup current decision.py"""
    shutil.copy("base/decision.py", "base/decision_backup.py")

def restore_decision():
    """Restore original decision.py"""
    if os.path.exists("base/decision_backup.py"):
        shutil.copy("base/decision_backup.py", "base/decision.py")
        os.remove("base/decision_backup.py")

def use_version(version_file):
    """Switch to a specific decision version"""
    shutil.copy(version_file, "base/decision.py")

def run_game(version_name, game_num):
    """Run a single game and collect logs"""
    print(f"\n{'='*60}")
    print(f"Running {version_name} - Game {game_num}/{NUM_GAMES}")
    print(f"{'='*60}\n")
    
    # Run the team (this will generate logs)
    # Note: You need the server running separately
    process = subprocess.Popen(
        ["python", "main.py", "--player"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Let it run for a bit (adjust time as needed)
    time.sleep(60)  # 60 seconds per game
    
    process.terminate()
    process.wait()
    
    # Move logs to version-specific folder
    log_dir = Path("logs")
    latest_log = max(log_dir.iterdir(), key=os.path.getctime)
    
    results_dir = Path(f"evolution_results/{version_name}")
    results_dir.mkdir(parents=True, exist_ok=True)
    
    shutil.move(str(latest_log), str(results_dir / f"game_{game_num}"))
    
    print(f"Logs saved to {results_dir / f'game_{game_num}'}")

def main():
    print("Decision Tree Evolution Testing")
    print("="*60)
    print("This will test 5 versions of the decision tree")
    print(f"Running {NUM_GAMES} games per version")
    print("="*60)
    
    # Backup original
    backup_decision()
    
    try:
        for version_name, version_file, description in VERSIONS:
            print(f"\n\nTesting: {description}")
            
            # Switch to this version
            use_version(version_file)
            
            # Run multiple games
            for game_num in range(1, NUM_GAMES + 1):
                run_game(version_name, game_num)
                time.sleep(5)  # Brief pause between games
        
        print("\n\n" + "="*60)
        print("Evolution testing complete!")
        print(f"Results saved in: evolution_results/")
        print("="*60)
        
    finally:
        # Restore original
        restore_decision()

if __name__ == "__main__":
    main()
