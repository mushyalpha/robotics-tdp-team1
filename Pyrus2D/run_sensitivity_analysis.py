"""
Parameter Sensitivity Analysis
================================

Systematically varies each BehaviorProfile parameter one at a time
across 5 levels (all others held at BASELINE), runs N headless mirror
matches per level, and generates one normalised heatmap per metric.

Both teams always use the SAME static profile — no dynamic tactical
switching.  This isolates the effect of each parameter.

Usage:
    python run_sensitivity_analysis.py --trials 30 --workers 6
    python run_sensitivity_analysis.py --trials 5 --params chase_radius kick_power

Output (default: sensitivity_results/):
    raw_data.csv, summary.json
    heatmap_win_rate.png, heatmap_possession.png, heatmap_goal_difference.png,
    heatmap_territory_gain.png, heatmap_centroid_x.png
"""

import os
import sys
import json
import csv
import argparse
import time
import copy
import multiprocessing as mp
from dataclasses import fields, asdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from simple_soccer_sim3 import SoccerSimulator, DEFAULT_MATCH_DURATION
from metrics_collector import MetricsCollector
from behavior_profile import BehaviorProfile, BASELINE

# =====================================================================
# PARAMETER SWEEP TABLE
# =====================================================================
# Each entry: parameter_name -> list of 5 values (low → high)
# Ranges span from conservative → aggressive anchors.

SWEEP_TABLE = {
    "chase_radius":          [1.3,  2.0,  2.5,  3.0,  3.5],
    "intercept_urgency":     [2,    4,    5,    7,    9],
    "shoot_distance_max":    [1.0,  1.4,  1.8,  2.2,  2.8],
    "shoot_angle_min":       [4.0,  8.0,  12.0, 18.0, 25.0],
    "shoot_over_pass_bias":  [0.1,  0.3,  0.5,  0.7,  0.9],
    "min_passes_before_shot":[0,    1,    2,    3,    4],
    "pass_forward_bias":     [0.8,  1.2,  1.5,  1.8,  2.2],
    "kick_power":            [0.85, 0.95, 1.05, 1.15, 1.25],
    "pass_power":            [0.65, 0.75, 0.85, 0.95, 1.05],
    "kick_accuracy":         [0.05, 0.10, 0.15, 0.20, 0.25],
    "position_x_offset":     [-1.2, -0.5, 0.0,  0.8,  1.5],
    "position_y_spread":     [0.6,  0.8,  1.0,  1.2,  1.4],
    "gk_sweep_radius":       [0.3,  0.7,  1.0,  1.5,  2.0],
    "dash_power_multiplier": [0.7,  0.85, 1.0,  1.15, 1.3],
    "fall_probability_mult": [0.5,  0.75, 1.0,  1.3,  1.6],
    "defensive_press_offset":[-1.2, -0.5, 0.0,  1.0,  2.0],
    "tackle_aggression":     [0.2,  0.35, 0.5,  0.7,  0.85],
}

# Pretty labels for the heatmap axes
PARAM_LABELS = {
    "chase_radius": "Chase Radius",
    "intercept_urgency": "Intercept Urgency",
    "shoot_distance_max": "Shoot Dist Max",
    "shoot_angle_min": "Shoot Angle Min",
    "shoot_over_pass_bias": "Shoot-over-Pass",
    "min_passes_before_shot": "Min Passes B4 Shot",
    "pass_forward_bias": "Pass Fwd Bias",
    "kick_power": "Kick Power",
    "pass_power": "Pass Power",
    "kick_accuracy": "Kick Accuracy (noise)",
    "position_x_offset": "Pos X Offset",
    "position_y_spread": "Pos Y Spread",
    "gk_sweep_radius": "GK Sweep Radius",
    "dash_power_multiplier": "Dash Power Mult",
    "fall_probability_mult": "Fall Prob Mult",
    "defensive_press_offset": "Def Press Offset",
    "tackle_aggression": "Tackle Aggression",
}


def _make_profile(param_name, value):
    """Create a copy of BASELINE with one parameter overridden."""
    d = asdict(BASELINE)
    d[param_name] = value
    d["name"] = f"sens_{param_name}={value}"
    return BehaviorProfile(**d)


# =====================================================================
# WORKER — runs one match
# =====================================================================

def _run_one(args_tuple):
    """Worker function for multiprocessing."""
    param_name, value, match_idx, match_duration, enable_falls = args_tuple
    try:
        profile = _make_profile(param_name, value)

        sim = SoccerSimulator(
            blue_static_profile=profile,   # tweaked parameter → experimental team
            red_static_profile=BASELINE,   # pure baseline → control team
            enable_falls=enable_falls,
            match_duration=match_duration,
            headless=True,
        )
        collector = MetricsCollector(sim)

        while sim.game_state.value != "MATCH_OVER":
            sim.step()
            collector.record_step()

        summary = collector.get_summary()
        return (param_name, value, match_idx, True, summary, None)

    except Exception as e:
        return (param_name, value, match_idx, False, None, str(e))


# =====================================================================
# AGGREGATION — compute metric averages over N trials
# =====================================================================

def _aggregate(results_list):
    """
    Given a list of match summaries, compute aggregate metrics.
    Returns a dict with the 5 target metrics.
    """
    n = len(results_list)
    if n == 0:
        return {}

    blue_wins = sum(1 for s in results_list if s["winner"] == "blue")
    red_wins  = sum(1 for s in results_list if s["winner"] == "red")

    goal_diffs = [s["blue_goals"] - s["red_goals"] for s in results_list]
    possessions = [s["blue_possession_pct"] for s in results_list]
    territory = [
        s["blue_danger_zone_pct"] - s["red_danger_zone_pct"]
        for s in results_list
    ]
    centroids = [s.get("blue_avg_centroid_x", 0.0) for s in results_list]
    shots      = [s.get("blue_shots", 0) for s in results_list]
    shots_ot   = [s.get("blue_shots_on_target", 0) for s in results_list]

    return {
        "win_rate":           round(100 * blue_wins / n, 1),
        "possession":         round(float(np.mean(possessions)), 1),
        "goal_difference":    round(float(np.mean(goal_diffs)), 2),
        "territory_gain":     round(float(np.mean(territory)), 1),
        "centroid_x":         round(float(np.mean(centroids)), 3),
        "total_shots":        round(float(np.mean(shots)), 1),
        "shots_on_target":    round(float(np.mean(shots_ot)), 1),
        "n_matches":          n,
    }


# =====================================================================
# HEATMAP GENERATION
# =====================================================================

def _generate_heatmaps(agg_data, param_order, output_dir):
    """
    Generate one heatmap per metric.

    agg_data: dict[param_name][value_index] -> aggregate dict
    param_order: list of param names (column order)
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    metrics = [
        ("win_rate",         "Win Rate (%)",              "heatmap_win_rate.png"),
        ("possession",       "Possession (%)",            "heatmap_possession.png"),
        ("goal_difference",  "Goal Difference (mean)",    "heatmap_goal_difference.png"),
        ("territory_gain",   "Net Territory Gain (%)",    "heatmap_territory_gain.png"),
        ("centroid_x",       "Team Centroid X (m)",       "heatmap_centroid_x.png"),
        ("total_shots",      "Total Shots (mean)",        "heatmap_total_shots.png"),
        ("shots_on_target",  "Shots on Target (mean)",    "heatmap_shots_on_target.png"),
    ]

    n_params = len(param_order)
    n_levels = 5

    for metric_key, metric_label, filename in metrics:
        # Build the raw matrix (rows = sweep levels, cols = params)
        raw = np.zeros((n_levels, n_params))
        for col, param in enumerate(param_order):
            for row in range(n_levels):
                raw[row, col] = agg_data[param][row].get(metric_key, 0)

        # Column-normalise (min-max per parameter)
        normed = np.zeros_like(raw)
        for col in range(n_params):
            col_min = raw[:, col].min()
            col_max = raw[:, col].max()
            rng = col_max - col_min
            if rng > 1e-9:
                normed[:, col] = (raw[:, col] - col_min) / rng
            else:
                normed[:, col] = 0.5  # all same

        # Build y-tick labels (the actual sweep values for each level)
        # Since each column has different values, we use level indices
        y_labels = [f"Level {i+1}" for i in range(n_levels)]

        # X labels
        x_labels = [PARAM_LABELS.get(p, p) for p in param_order]

        # Plot
        fig, ax = plt.subplots(figsize=(max(14, n_params * 0.9), n_levels * 1.1 + 2))
        im = ax.imshow(normed, cmap="YlOrRd", aspect="auto", vmin=0, vmax=1)

        # Annotate cells with actual values + sweep value
        for row in range(n_levels):
            for col in range(n_params):
                param = param_order[col]
                sweep_val = SWEEP_TABLE[param][row]
                cell_val = raw[row, col]
                # Format: "actual_metric\n(sweep_val)"
                txt = f"{cell_val:.1f}\n({sweep_val})"
                text_color = "white" if normed[row, col] > 0.65 else "black"
                ax.text(col, row, txt, ha="center", va="center",
                        fontsize=6.5, color=text_color, fontweight="bold")

        ax.set_xticks(range(n_params))
        ax.set_xticklabels(x_labels, rotation=45, ha="right", fontsize=8)
        ax.set_yticks(range(n_levels))
        ax.set_yticklabels(y_labels, fontsize=9)

        ax.set_title(f"Parameter Sensitivity: {metric_label}\n"
                     f"(cell = mean over trials, colour = column-normalised)",
                     fontsize=11, fontweight="bold", pad=12)

        cbar = fig.colorbar(im, ax=ax, shrink=0.7, pad=0.02)
        cbar.set_label("Normalised (per-parameter min→max)", fontsize=8)

        fig.tight_layout()
        path = os.path.join(output_dir, filename)
        fig.savefig(path, dpi=180)
        plt.close(fig)
        print(f"  ✓ Saved {filename}")


# =====================================================================
# MAIN
# =====================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Parameter sensitivity analysis — one-at-a-time sweep"
    )
    parser.add_argument("--trials", "-n", type=int, default=30,
                        help="Matches per parameter-value combo (default: 30)")
    parser.add_argument("--duration", "-d", type=int, default=1200,
                        help="Match duration in seconds (default: 1200 = 20 min)")
    parser.add_argument("--output", "-o", default="sensitivity_results",
                        help="Output directory (default: sensitivity_results/)")
    parser.add_argument("--workers", "-w", type=int,
                        default=min(6, mp.cpu_count()),
                        help=f"Parallel workers (default: min(6, {mp.cpu_count()}))")
    parser.add_argument("--params", nargs="*", default=None,
                        help="Run only specific params (e.g. chase_radius kick_power)")
    parser.add_argument("--no-falls", action="store_true",
                        help="Disable fall simulation")
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)

    # Determine which parameters to sweep
    if args.params:
        param_order = [p for p in args.params if p in SWEEP_TABLE]
        unknown = [p for p in args.params if p not in SWEEP_TABLE]
        if unknown:
            print(f"  ⚠ Unknown params (skipped): {unknown}")
    else:
        param_order = list(SWEEP_TABLE.keys())

    total_combos = len(param_order) * 5
    total_matches = total_combos * args.trials
    workers = min(args.workers, total_matches)

    print("=" * 70)
    print("PARAMETER SENSITIVITY ANALYSIS")
    print("=" * 70)
    print(f"  Parameters     : {len(param_order)}")
    print(f"  Sweep levels   : 5 per parameter")
    print(f"  Trials each    : {args.trials}")
    print(f"  Total matches  : {total_matches}")
    print(f"  Match duration : {args.duration}s")
    print(f"  Workers        : {workers}")
    print(f"  Falls          : {'OFF' if args.no_falls else 'ON'}")
    print(f"  Output         : {args.output}/")
    print(f"  Est. wall time : ~{max(1, total_matches // max(1, workers))}s")
    print("=" * 70)

    # Build work items
    work_items = []
    for param in param_order:
        for val in SWEEP_TABLE[param]:
            for trial in range(args.trials):
                work_items.append(
                    (param, val, trial + 1, args.duration, not args.no_falls)
                )

    # Run in parallel
    # Structure: results[param][value_index] -> list of summaries
    raw_summaries = {p: {i: [] for i in range(5)} for p in param_order}

    start_time = time.time()
    completed = 0
    errors = 0

    with mp.Pool(processes=workers) as pool:
        for result in pool.imap_unordered(_run_one, work_items):
            param_name, value, match_idx, success, summary, err = result
            completed += 1

            if success:
                # Find value index
                vi = SWEEP_TABLE[param_name].index(value)
                raw_summaries[param_name][vi].append(summary)

                elapsed = time.time() - start_time
                eta = (elapsed / completed) * (total_matches - completed)
                if completed % max(1, total_matches // 20) == 0 or completed == total_matches:
                    print(f"  [{completed:5d}/{total_matches}]  "
                          f"{param_name}={value}  trial {match_idx}  "
                          f"(ETA {eta:.0f}s)")
            else:
                errors += 1
                print(f"  [{completed:5d}/{total_matches}]  "
                      f"{param_name}={value}  ERROR: {err}")

    total_time = time.time() - start_time
    print(f"\n{'=' * 70}")
    print(f"✓ Completed {completed - errors}/{total_matches} matches "
          f"in {total_time:.1f}s  ({total_time / 60:.1f} min)")
    if errors:
        print(f"  ⚠ {errors} errors")
    print("=" * 70)

    # ── Aggregate ─────────────────────────────────────────────────
    print("\nAggregating results...")
    agg_data = {}
    for param in param_order:
        agg_data[param] = {}
        for vi in range(5):
            agg_data[param][vi] = _aggregate(raw_summaries[param][vi])

    # ── Save raw CSV ──────────────────────────────────────────────
    csv_path = os.path.join(args.output, "raw_data.csv")
    csv_rows = []
    for param in param_order:
        for vi in range(5):
            val = SWEEP_TABLE[param][vi]
            agg = agg_data[param][vi]
            csv_rows.append({
                "parameter": param,
                "value": val,
                "level": vi + 1,
                **agg
            })
    if csv_rows:
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=csv_rows[0].keys())
            writer.writeheader()
            writer.writerows(csv_rows)
        print(f"  ✓ Saved raw_data.csv  ({len(csv_rows)} rows)")

    # ── Save summary JSON ─────────────────────────────────────────
    json_path = os.path.join(args.output, "summary.json")
    # Convert int keys to strings for JSON
    json_agg = {}
    for param in param_order:
        json_agg[param] = {
            "sweep_values": SWEEP_TABLE[param],
            "results": [agg_data[param][vi] for vi in range(5)]
        }
    with open(json_path, "w") as f:
        json.dump(json_agg, f, indent=2)
    print(f"  ✓ Saved summary.json")

    # ── Generate heatmaps ─────────────────────────────────────────
    print("\nGenerating heatmaps...")
    _generate_heatmaps(agg_data, param_order, args.output)

    print(f"\n✓ All outputs saved to {args.output}/")
    print("=" * 70)


if __name__ == "__main__":
    mp.freeze_support()
    main()
