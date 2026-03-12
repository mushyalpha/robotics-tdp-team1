"""
Baseline Parameter Sensitivity Analysis
=========================================

For each parameter in the BASELINE profile, this script sweeps a range of
values (keeping all others fixed at baseline), runs N simulated matches,
and plots how key output metrics change.

Output metrics tracked per sweep point:
  - blue_goals_mean       : avg goals scored by the modified team (Blue)
  - red_goals_mean        : avg goals conceded (Red uses fixed BASELINE)
  - goal_diff_mean        : avg (blue - red) goal difference
  - passes_mean           : avg passes completed by Blue
  - win_rate              : fraction of matches Blue won

Statistical logic
-----------------
Each parameter value is tested with RUNS_PER_POINT independent matches
(different random seeds). The reported values are means and std dev bands.
This removes noise from stochastic events (falls, kick accuracy errors,
ball physics). Only the tested team's profile is modified; the opponent
always uses unmodified BASELINE so effects are isolated.
"""

import sys
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from dataclasses import asdict

from behavior_profile import BASELINE, BehaviorProfile
from simple_soccer_sim3 import SoccerSimulator

# =============================================================================
# CONFIG
# =============================================================================

MATCH_DURATION  = 120
RUNS_PER_POINT  = 30
N_SWEEP_POINTS  = 9
ENABLE_FALLS    = True
OUTPUT_DIR      = './outputs'

PARAM_SWEEPS = [
    ('chase_radius',           'Chase Radius',            'm',       np.linspace(0.5, 5.0, N_SWEEP_POINTS)),
    ('intercept_urgency',      'Intercept Urgency',       'cycles',  np.arange(1, 10, dtype=float)),
    ('shoot_distance_max',     'Shoot Distance Max',      'm',       np.linspace(0.5, 5.0, N_SWEEP_POINTS)),
    ('shoot_angle_min',        'Shoot Angle Min',         'deg',     np.linspace(2.0, 30.0, N_SWEEP_POINTS)),
    ('shoot_over_pass_bias',   'Shoot-over-Pass Bias',    '0-1',     np.linspace(0.0, 1.0, N_SWEEP_POINTS)),
    ('min_passes_before_shot', 'Min Passes Before Shot',  'passes',  np.arange(0, 7, dtype=float)),
    ('pass_forward_bias',      'Pass Forward Bias',       'weight',  np.linspace(0.5, 3.0, N_SWEEP_POINTS)),
    ('kick_power',             'Kick Power',              'a.u.',    np.linspace(0.5, 3.5, N_SWEEP_POINTS)),
    ('pass_power',             'Pass Power',              'a.u.',    np.linspace(0.3, 2.5, N_SWEEP_POINTS)),
    ('kick_accuracy',          'Kick Accuracy (noise)',   'rad',     np.linspace(0.02, 0.5, N_SWEEP_POINTS)),
    ('position_x_offset',      'Position X Offset',      'm',       np.linspace(-2.5, 2.5, N_SWEEP_POINTS)),
    ('position_y_spread',      'Position Y Spread',      'mult',    np.linspace(0.3, 2.0, N_SWEEP_POINTS)),
    ('gk_sweep_radius',        'GK Sweep Radius',        'm',       np.linspace(0.3, 3.0, N_SWEEP_POINTS)),
    ('dash_power_multiplier',  'Dash Power Multiplier',  'mult',    np.linspace(0.4, 1.8, N_SWEEP_POINTS)),
    ('fall_probability_mult',  'Fall Probability Mult',  'mult',    np.linspace(0.2, 3.0, N_SWEEP_POINTS)),
    ('defensive_press_offset', 'Defensive Press Offset', 'm',       np.linspace(-2.5, 2.5, N_SWEEP_POINTS)),
    ('tackle_aggression',      'Tackle Aggression',      '0-1',     np.linspace(0.0, 1.0, N_SWEEP_POINTS)),
]

# =============================================================================
# SWEEP RUNNER
# =============================================================================

def run_sweep(param_attr, sweep_values):
    baseline_dict = asdict(BASELINE)
    out = {k: [] for k in ['bg_m','bg_s','rg_m','rg_s','gd_m','gd_s','pa_m','pa_s','wr']}

    for val in sweep_values:
        bg_list, rg_list, pa_list, wins = [], [], [], 0

        for run_idx in range(RUNS_PER_POINT):
            np.random.seed(run_idx * 997 + int(abs(val) * 137) % 9999)
            modified = {**baseline_dict, param_attr: val}
            blue_profile = BehaviorProfile(**modified)
            sim = SoccerSimulator(
                blue_profile=blue_profile,
                red_profile=BASELINE,
                enable_falls=ENABLE_FALLS,
                match_duration=MATCH_DURATION,
                headless=True,
            )
            r = sim.run_headless()
            bg_list.append(r['blue_goals'])
            rg_list.append(r['red_goals'])
            pa_list.append(r['total_passes_blue'])
            if r['winner'] == 'blue':
                wins += 1

        bg = np.array(bg_list); rg = np.array(rg_list)
        gd = bg - rg; ps = np.array(pa_list)
        out['bg_m'].append(bg.mean()); out['bg_s'].append(bg.std())
        out['rg_m'].append(rg.mean()); out['rg_s'].append(rg.std())
        out['gd_m'].append(gd.mean()); out['gd_s'].append(gd.std())
        out['pa_m'].append(ps.mean()); out['pa_s'].append(ps.std())
        out['wr'].append(wins / RUNS_PER_POINT)

    return {k: np.array(v) for k, v in out.items()}

# =============================================================================
# PLOT ONE PARAMETER (2x2 panels)
# =============================================================================

BG_COL  = '#4C9BE8'
RG_COL  = '#E85C5C'
GD_COL  = '#5CCC8A'
PA_COL  = '#F5A623'
WR_COL  = '#C77DFF'

def shade(ax, x, mean, std, color, label, ls='-'):
    ax.fill_between(x, mean-std, mean+std, alpha=0.15, color=color)
    ax.plot(x, mean, color=color, lw=2, ls=ls, label=label)

def style_ax(ax, title, xlabel):
    ax.set_facecolor('#0d1117')
    ax.tick_params(colors='#cccccc', labelsize=9)
    for sp in ax.spines.values(): sp.set_edgecolor('#444')
    ax.set_title(title, color='white', fontsize=10, fontweight='bold', pad=5)
    ax.set_xlabel(xlabel, color='#aaaaaa', fontsize=8)
    leg = ax.legend(fontsize=7.5, loc='best',
                    facecolor='#1a1a2e', edgecolor='#555', labelcolor='#ddd')

def make_param_figure(param_attr, display_name, unit_label, sweep_values, r):
    fig, axes = plt.subplots(2, 2, figsize=(12, 7.5))
    fig.patch.set_facecolor('#1a1a2e')
    baseline_val = getattr(BASELINE, param_attr)
    fig.suptitle(
        f'Baseline Sensitivity  —  {display_name}  [{unit_label}]\n'
        f'({RUNS_PER_POINT} runs × {MATCH_DURATION}s per point | opponent = BASELINE | baseline value = {baseline_val})',
        fontsize=12, fontweight='bold', color='white', y=0.98)

    x = sweep_values
    bv_kw = dict(color='white', lw=1.2, ls='--', alpha=0.65, label=f'Baseline ({baseline_val})')

    # Panel 1: Goals scored vs conceded
    ax = axes[0, 0]
    shade(ax, x, r['bg_m'], r['bg_s'], BG_COL, 'Avg Goals Scored (Blue)')
    shade(ax, x, r['rg_m'], r['rg_s'], RG_COL, 'Avg Goals Conceded (Red)', ls='--')
    ax.axvline(baseline_val, **bv_kw)
    style_ax(ax, 'Goals Scored vs Conceded', f'{display_name} ({unit_label})')

    # Panel 2: Goal difference
    ax = axes[0, 1]
    shade(ax, x, r['gd_m'], r['gd_s'], GD_COL, 'Goal Difference (Blue − Red)')
    ax.axhline(0, color='white', lw=0.8, ls=':', alpha=0.5)
    ax.axvline(baseline_val, **bv_kw)
    style_ax(ax, 'Goal Difference (Blue − Red)', f'{display_name} ({unit_label})')

    # Panel 3: Passes
    ax = axes[1, 0]
    shade(ax, x, r['pa_m'], r['pa_s'], PA_COL, 'Passes Completed (Blue)')
    ax.axvline(baseline_val, **bv_kw)
    style_ax(ax, 'Passes Completed by Blue', f'{display_name} ({unit_label})')

    # Panel 4: Win rate
    ax = axes[1, 1]
    ax.plot(x, r['wr'], color=WR_COL, lw=2, label='Win Rate (Blue)')
    ax.fill_between(x, r['wr'], 0.5, alpha=0.15,
                    color=WR_COL if r['wr'].mean() >= 0.5 else RG_COL)
    ax.axhline(0.5, color='white', lw=0.8, ls=':', alpha=0.5, label='50% line')
    ax.axvline(baseline_val, **bv_kw)
    ax.set_ylim(-0.05, 1.05)
    style_ax(ax, 'Win Rate', f'{display_name} ({unit_label})')

    plt.tight_layout(rect=[0, 0, 1, 0.94])
    return fig

# =============================================================================
# SUMMARY HEATMAP
# =============================================================================

def make_summary_heatmap(all_summaries):
    param_names = [d['display_name'] for d in all_summaries]
    metric_keys  = ['gd_m', 'bg_m', 'rg_m', 'pa_m', 'wr']
    metric_labels = ['Goal Diff', 'Goals Scored', 'Goals Conceded', 'Passes', 'Win Rate']

    matrix = []
    for d in all_summaries:
        r = d['result']
        row = [float(np.ptp(r[mk])) for mk in metric_keys]
        matrix.append(row)

    matrix = np.array(matrix)
    col_max = matrix.max(axis=0); col_max[col_max == 0] = 1.0
    matrix_norm = matrix / col_max

    fig, ax = plt.subplots(figsize=(10, max(6, len(param_names) * 0.5)))
    fig.patch.set_facecolor('#1a1a2e')
    ax.set_facecolor('#1a1a2e')
    im = ax.imshow(matrix_norm, aspect='auto', cmap='YlOrRd', vmin=0, vmax=1)

    ax.set_xticks(range(len(metric_labels)))
    ax.set_xticklabels(metric_labels, color='white', fontsize=10, fontweight='bold')
    ax.set_yticks(range(len(param_names)))
    ax.set_yticklabels(param_names, color='white', fontsize=9)
    ax.tick_params(axis='both', length=0)

    for i in range(len(param_names)):
        for j in range(len(metric_keys)):
            tc = 'black' if matrix_norm[i, j] > 0.6 else 'white'
            ax.text(j, i, f'{matrix[i,j]:.2f}', ha='center', va='center',
                    fontsize=7.5, color=tc, fontweight='bold')

    cbar = plt.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
    cbar.ax.yaxis.set_tick_params(color='white', labelsize=8)
    cbar.set_label('Normalised Sensitivity (column-scaled)', color='white', fontsize=9)
    plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='white')
    ax.set_title(
        'Parameter Sensitivity Heatmap\n(cell = peak-to-peak range across sweep, normalised per metric)',
        color='white', fontsize=12, fontweight='bold', pad=10)
    plt.tight_layout()
    return fig

# =============================================================================
# MAIN
# =============================================================================

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    total = len(PARAM_SWEEPS)
    print(f'\n{"="*60}')
    print(f'  Baseline Parameter Sensitivity Analysis')
    print(f'  {total} parameters  x  {N_SWEEP_POINTS} values  x  {RUNS_PER_POINT} runs')
    print(f'  Match duration: {MATCH_DURATION}s  |  Falls: {ENABLE_FALLS}')
    print(f'{"="*60}\n')

    all_summaries = []
    for idx, (param_attr, display_name, unit_label, sweep_values) in enumerate(PARAM_SWEEPS):
        print(f'[{idx+1}/{total}] {display_name} ...', end=' ', flush=True)
        result = run_sweep(param_attr, sweep_values)
        print('done')
        all_summaries.append({
            'param_attr': param_attr, 'display_name': display_name,
            'unit_label': unit_label, 'sweep_values': sweep_values,
            'result': result,
        })
        fig = make_param_figure(param_attr, display_name, unit_label, sweep_values, result)
        fig.savefig(os.path.join(OUTPUT_DIR, f'sensitivity_{param_attr}.png'),
                    dpi=120, bbox_inches='tight', facecolor=fig.get_facecolor())
        plt.close(fig)

    print('\nGenerating summary heatmap...')
    fig_hm = make_summary_heatmap(all_summaries)
    fig_hm.savefig(os.path.join(OUTPUT_DIR, 'sensitivity_summary_heatmap.png'),
                   dpi=120, bbox_inches='tight', facecolor=fig_hm.get_facecolor())
    plt.close(fig_hm)
    print(f'All plots saved to: {OUTPUT_DIR}')

if __name__ == '__main__':
    main()