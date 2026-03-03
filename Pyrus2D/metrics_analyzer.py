"""
Metrics Analyzer — Process batch match results into comparisons
================================================================

Reads match JSON files from run_behavior_comparison.py output,
computes mean ± std for each metric, generates comparison charts,
and exports a CSV summary.
"""

import json
import os
import csv
import argparse
import numpy as np

# Only import matplotlib when actually generating charts
# (allows headless environments to still process data)
HAS_MATPLOTLIB = True
try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
except ImportError:
    HAS_MATPLOTLIB = False


def load_results(results_dir):
    """Load all match JSON files from a directory, grouped by config."""
    configs = {}
    for fname in os.listdir(results_dir):
        if not fname.endswith('.json'):
            continue
        filepath = os.path.join(results_dir, fname)
        with open(filepath, 'r') as f:
            data = json.load(f)

        mode = data.get('behavior_mode', 'adaptive')
        blue_side = data.get('blue_personality') or data.get('blue_profile', 'unknown')
        red_side = data.get('red_personality') or data.get('red_profile', 'unknown')
        config_key = f"{mode}:{blue_side}_vs_{red_side}"
        if config_key not in configs:
            configs[config_key] = []
        configs[config_key].append(data)

    return configs


def compute_stats(matches):
    """Compute mean ± std for key metrics across a list of matches."""
    if not matches:
        return {}

    metrics = [
        'blue_goals', 'red_goals',
        'falls_per_game',
        'blue_possession_pct', 'red_possession_pct',
        'turnovers_per_min',
        'blue_net_territory_gain', 'red_net_territory_gain', 'net_territory_gain_balance',
        'blue_danger_zone_pct', 'red_danger_zone_pct',
        'blue_danger_entries', 'red_danger_entries',
        'danger_entry_balance', 'danger_zone_balance',
        'blue_shot_quality_sum', 'red_shot_quality_sum',
        'blue_avg_shot_quality', 'red_avg_shot_quality', 'shot_quality_balance',
        'blue_avg_hull_area', 'red_avg_hull_area', 'spacing_area_balance',
        'blue_avg_centroid_x', 'blue_avg_centroid_y',
        'red_avg_centroid_x', 'red_avg_centroid_y',
        'spacing_centroid_progress_balance',
    ]

    stats = {}
    for m in metrics:
        values = [match.get(m, 0) for match in matches]
        stats[m] = {
            'mean': round(np.mean(values), 2),
            'std': round(np.std(values), 2),
            'min': round(np.min(values), 2),
            'max': round(np.max(values), 2),
        }

    # Win rates
    blue_wins = sum(1 for m in matches if m.get('winner') == 'blue')
    red_wins = sum(1 for m in matches if m.get('winner') == 'red')
    draws = sum(1 for m in matches if m.get('winner') == 'draw')
    total = len(matches)
    stats['blue_win_rate'] = round(100 * blue_wins / total, 1)
    stats['red_win_rate'] = round(100 * red_wins / total, 1)
    stats['draw_rate'] = round(100 * draws / total, 1)
    stats['total_matches'] = total

    return stats


def print_comparison(configs):
    """Print a formatted comparison table to console."""
    print("\n" + "=" * 80)
    print("BEHAVIOR COMPARISON RESULTS")
    print("=" * 80)

    for config_name, matches in sorted(configs.items()):
        stats = compute_stats(matches)
        print(f"\n{'─' * 60}")
        print(f"Config: {config_name}  ({stats['total_matches']} matches)")
        print(f"{'─' * 60}")
        print(f"  Win Rate:  Blue {stats['blue_win_rate']}%  |  Red {stats['red_win_rate']}%  |  Draw {stats['draw_rate']}%")
        print(f"  Goals:     Blue {stats['blue_goals']['mean']:.1f}±{stats['blue_goals']['std']:.1f}  |  "
              f"Red {stats['red_goals']['mean']:.1f}±{stats['red_goals']['std']:.1f}")
        print(f"  Falls:     {stats['falls_per_game']['mean']:.2f}/game")
        print(f"  Possess:   Blue {stats['blue_possession_pct']['mean']:.1f}%  |  "
              f"Red {stats['red_possession_pct']['mean']:.1f}%")
        print(f"  Turnovers: {stats['turnovers_per_min']['mean']:.2f}/min")
        print(f"  Territory: Blue {stats['blue_net_territory_gain']['mean']:.2f}m/poss  |  "
              f"Red {stats['red_net_territory_gain']['mean']:.2f}m/poss")
        print(f"  Danger%:   Blue {stats['blue_danger_zone_pct']['mean']:.1f}%  |  "
              f"Red {stats['red_danger_zone_pct']['mean']:.1f}%")
        print(f"  DangerEnt: Blue {stats['blue_danger_entries']['mean']:.1f}  |  "
              f"Red {stats['red_danger_entries']['mean']:.1f}")
        print(f"  ShotQual:  Blue {stats['blue_avg_shot_quality']['mean']:.3f}  |  "
              f"Red {stats['red_avg_shot_quality']['mean']:.3f}")
        print(f"  SpacingA:  Blue {stats['blue_avg_hull_area']['mean']:.2f}m²  |  "
              f"Red {stats['red_avg_hull_area']['mean']:.2f}m²")


def generate_charts(configs, output_dir):
    """Generate comparison bar charts."""
    if not HAS_MATPLOTLIB:
        print("matplotlib not available, skipping charts.")
        return

    os.makedirs(output_dir, exist_ok=True)

    config_names = sorted(configs.keys())
    stats_list = [compute_stats(configs[c]) for c in config_names]

    # --- Chart 1: Win Rates ---
    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(len(config_names))
    width = 0.25
    ax.bar(x - width, [s['blue_win_rate'] for s in stats_list], width, label='Blue Win%', color='#3366FF')
    ax.bar(x, [s['draw_rate'] for s in stats_list], width, label='Draw%', color='#888888')
    ax.bar(x + width, [s['red_win_rate'] for s in stats_list], width, label='Red Win%', color='#FF3333')
    ax.set_ylabel('Win Rate (%)')
    ax.set_title('Win Rates by Configuration')
    ax.set_xticks(x)
    ax.set_xticklabels(config_names, rotation=15, ha='right', fontsize=8)
    ax.legend()
    ax.set_ylim(0, 100)
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, 'win_rates.png'), dpi=150)
    plt.close(fig)

    # --- Chart 2: Territory gain (mean ± std) ---
    fig, ax = plt.subplots(figsize=(10, 5))
    blue_terr = [s['blue_net_territory_gain']['mean'] for s in stats_list]
    blue_std = [s['blue_net_territory_gain']['std'] for s in stats_list]
    red_terr = [s['red_net_territory_gain']['mean'] for s in stats_list]
    red_std = [s['red_net_territory_gain']['std'] for s in stats_list]
    ax.bar(x - 0.15, blue_terr, 0.3, yerr=blue_std, label='Blue', color='#3366FF', alpha=0.8, capsize=3)
    ax.bar(x + 0.15, red_terr, 0.3, yerr=red_std, label='Red', color='#FF3333', alpha=0.8, capsize=3)
    ax.set_ylabel('Net Territory Gain (m/poss)')
    ax.set_title('Average Net Territory Gain per Possession')
    ax.set_xticks(x)
    ax.set_xticklabels(config_names, rotation=15, ha='right', fontsize=8)
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, 'territory_gain.png'), dpi=150)
    plt.close(fig)

    # --- Chart 3: Possession ---
    fig, ax = plt.subplots(figsize=(10, 5))
    blue_poss = [s['blue_possession_pct']['mean'] for s in stats_list]
    red_poss = [s['red_possession_pct']['mean'] for s in stats_list]
    ax.bar(x - 0.15, blue_poss, 0.3, label='Blue', color='#3366FF', alpha=0.8)
    ax.bar(x + 0.15, red_poss, 0.3, label='Red', color='#FF3333', alpha=0.8)
    ax.set_ylabel('Possession (%)')
    ax.set_title('Average Possession')
    ax.set_xticks(x)
    ax.set_xticklabels(config_names, rotation=15, ha='right', fontsize=8)
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, 'possession.png'), dpi=150)
    plt.close(fig)

    # --- Chart 4: Danger balance vs spacing balance ---
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    ax = axes[0]
    ax.bar(x, [s['danger_zone_balance']['mean'] for s in stats_list], 0.5, color='#7c3aed')
    ax.set_ylabel('Danger Zone Balance (%)')
    ax.set_title('Danger Zone Balance (Blue - Red)')
    ax.set_xticks(x)
    ax.set_xticklabels(config_names, rotation=15, ha='right', fontsize=8)

    ax = axes[1]
    ax.bar(x, [s['spacing_area_balance']['mean'] for s in stats_list], 0.5, color='#0ea5e9')
    ax.set_ylabel('Spacing Area Balance (m²)')
    ax.set_title('Spacing Area Balance (Blue - Red)')
    ax.set_xticks(x)
    ax.set_xticklabels(config_names, rotation=15, ha='right', fontsize=8)

    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, 'danger_spacing_balance.png'), dpi=150)
    plt.close(fig)

    print(f"\n✓ Charts saved to {output_dir}/")


def export_csv(configs, output_path):
    """Export per-config stats as CSV."""
    rows = []
    for config_name, matches in sorted(configs.items()):
        stats = compute_stats(matches)
        row = {'config': config_name, 'matches': stats['total_matches']}
        for key in ['blue_win_rate', 'red_win_rate', 'draw_rate']:
            row[key] = stats[key]
        for key in ['blue_goals', 'red_goals', 'falls_per_game', 'blue_possession_pct', 'red_possession_pct',
                     'turnovers_per_min',
                     'blue_net_territory_gain', 'red_net_territory_gain', 'net_territory_gain_balance',
                     'blue_danger_zone_pct', 'red_danger_zone_pct',
                     'blue_danger_entries', 'red_danger_entries',
                     'danger_entry_balance', 'danger_zone_balance',
                     'blue_shot_quality_sum', 'red_shot_quality_sum',
                     'blue_avg_shot_quality', 'red_avg_shot_quality', 'shot_quality_balance']:
            row[f"{key}_mean"] = stats[key]['mean']
            row[f"{key}_std"] = stats[key]['std']
        for key in ['blue_avg_hull_area', 'red_avg_hull_area', 'spacing_area_balance',
                     'blue_avg_centroid_x', 'blue_avg_centroid_y',
                     'red_avg_centroid_x', 'red_avg_centroid_y',
                     'spacing_centroid_progress_balance']:
            row[f"{key}_mean"] = stats[key]['mean']
            row[f"{key}_std"] = stats[key]['std']
        rows.append(row)

    if rows:
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        print(f"✓ CSV exported to {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Analyze behavior comparison results')
    parser.add_argument('--input', '-i', default='behavior_results',
                        help='Directory containing match JSON files')
    parser.add_argument('--output', '-o', default='analysis',
                        help='Output directory for charts and CSV')
    args = parser.parse_args()

    if not os.path.isdir(args.input):
        print(f"Error: Results directory '{args.input}' not found.")
        print("Run run_behavior_comparison.py first to generate results.")
        return

    configs = load_results(args.input)

    if not configs:
        print("No match result files found.")
        return

    print_comparison(configs)
    generate_charts(configs, args.output)
    export_csv(configs, os.path.join(args.output, 'comparison_stats.csv'))


if __name__ == '__main__':
    main()

