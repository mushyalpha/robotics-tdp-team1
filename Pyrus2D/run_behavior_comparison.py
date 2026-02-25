"""
Behavior Comparison Runner — Automated batch testing (PARALLEL)
===============================================================

Runs multiple matches for each configuration (profile pair) and saves
per-match metric JSONs for analysis by metrics_analyzer.py.

Each match runs in ~1 second (headless, no animation).
Uses multiprocessing for true parallelism across CPU cores.

Example:
    python run_behavior_comparison.py --matches 20 --duration 300 --workers 6
    python metrics_analyzer.py --input behavior_results --output analysis

Configurations (7 total):
  1. aggressive vs baseline  (fixed baseline test)
  2. conservative vs baseline (fixed baseline test)
  3. baseline vs baseline    (control)
  4. aggressive vs aggressive (mirror match)
  5. conservative vs conservative (mirror match)
  6. aggressive vs conservative  (key: aggressive beats conservative?)
  7. conservative vs aggressive  (reverse: eliminate side bias)
"""

import os
import sys
import json
import argparse
import time
import multiprocessing as mp
from functools import partial

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from simple_soccer_sim3 import SoccerSimulator, DEFAULT_MATCH_DURATION
from metrics_collector import MetricsCollector


CONFIGURATIONS = [
    ('aggressive',   'baseline'),
    ('conservative', 'baseline'),
    ('baseline',     'baseline'),
    ('aggressive',   'aggressive'),
    ('conservative', 'conservative'),
    ('aggressive',   'conservative'),
    ('conservative', 'aggressive'),
]


def _run_one(args_tuple):
    """Worker function (must be top-level for multiprocessing)."""
    blue, red, match_duration, enable_falls, output_dir, match_idx = args_tuple
    config_name = f"{blue}_vs_{red}"
    try:
        sim = SoccerSimulator(
            blue_profile=blue,
            red_profile=red,
            enable_falls=enable_falls,
            match_duration=match_duration,
            headless=True,
        )
        collector = MetricsCollector(sim)

        while sim.game_state.value != 'MATCH_OVER':
            sim.step()
            collector.record_step()

        summary = collector.get_summary()

        filename = f"{config_name}_match{match_idx:03d}.json"
        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'w') as f:
            json.dump(summary, f, indent=2)

        return (config_name, match_idx, True,
                summary['blue_goals'], summary['red_goals'], None)

    except Exception as e:
        return (config_name, match_idx, False, 0, 0, str(e))


def main():
    parser = argparse.ArgumentParser(description='Run parallel behavior comparison matches')
    parser.add_argument('--matches', '-m', type=int, default=20,
                        help='Matches per configuration (default: 20). '
                             '7 configs × 20 = 140 total, ~30s with 6 workers.')
    parser.add_argument('--duration', '-d', type=int, default=300,
                        help='Match duration in seconds (default: 300 = 5 min). '
                             'Each match runs in ~1s headless regardless of duration.')
    parser.add_argument('--output', '-o', default='behavior_results',
                        help='Output directory for match JSONs (default: behavior_results/)')
    parser.add_argument('--workers', '-w', type=int,
                        default=min(6, mp.cpu_count()),
                        help=f'Parallel workers (default: min(6, cpu_count)='
                             f'{min(6, mp.cpu_count())})')
    parser.add_argument('--no-falls', action='store_true',
                        help='Disable fall simulation (faster, more deterministic)')
    parser.add_argument('--configs', '-c', nargs='*',
                        help='Run only specific configs, e.g. aggressive_vs_conservative')
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)

    # Build config list
    configs = CONFIGURATIONS
    if args.configs:
        configs = []
        for c in args.configs:
            parts = c.split('_vs_')
            if len(parts) == 2:
                configs.append((parts[0], parts[1]))
            else:
                print(f"  Warning: skipping invalid config '{c}' (use format 'blue_vs_red')")

    total_matches = len(configs) * args.matches
    workers = min(args.workers, total_matches)

    print("=" * 70)
    print("BEHAVIOR COMPARISON RUNNER  (parallel headless)")
    print("=" * 70)
    print(f"  Configurations : {len(configs)}")
    print(f"  Matches each   : {args.matches}")
    print(f"  Total matches  : {total_matches}")
    print(f"  Match duration : {args.duration}s  "
          f"(~{args.duration/60:.1f} sim-minutes each)")
    print(f"  Worker threads : {workers}")
    print(f"  Falls          : {'OFF' if args.no_falls else 'ON'}")
    print(f"  Output dir     : {args.output}/")
    print(f"  Est. wall time : ~{max(1, total_matches // workers)}s")
    print("=" * 70)

    # Build work items
    work_items = []
    for blue, red in configs:
        for i in range(args.matches):
            work_items.append((blue, red, args.duration,
                               not args.no_falls, args.output, i + 1))

    start_time = time.time()
    completed = 0
    errors = 0

    # Run in parallel
    with mp.Pool(processes=workers) as pool:
        for result in pool.imap_unordered(_run_one, work_items):
            config_name, match_idx, success, bg, rg, err = result
            completed += 1

            if success:
                result_str = f"B{bg}-{rg}R"
                elapsed = time.time() - start_time
                remaining = (elapsed / completed) * (total_matches - completed)
                print(f"  [{completed:3d}/{total_matches}]  {config_name:<35s}  "
                      f"match {match_idx:03d}  {result_str}  "
                      f"(ETA {remaining:.0f}s)")
            else:
                errors += 1
                print(f"  [{completed:3d}/{total_matches}]  {config_name}  "
                      f"match {match_idx:03d}  ERROR: {err}")

    total_time = time.time() - start_time
    print(f"\n{'=' * 70}")
    print(f"✓ DONE: {completed - errors}/{total_matches} matches "
          f"in {total_time:.1f}s  ({total_time / 60:.1f} min)")
    if errors:
        print(f"  ⚠ {errors} errors")
    print(f"\n  Now run analysis:")
    print(f"    python metrics_analyzer.py --input {args.output} --output analysis")
    print("=" * 70)


if __name__ == '__main__':
    # Required on Windows for multiprocessing
    mp.freeze_support()
    main()
