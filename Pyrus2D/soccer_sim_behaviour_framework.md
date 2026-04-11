# RoboCup Soccer Simulation — Behaviour Optimisation Framework
### Parameter Sensitivity Analysis → Optimal Tactic Selection
**Team 1 | ENG5326 Robotics M | University of Glasgow**

---

## Table of Contents
1. [System Architecture Overview](#1-system-architecture-overview)
2. [Level 1 — Parameter Sensitivity Analysis](#2-level-1--parameter-sensitivity-analysis)
3. [Outcome Metrics](#3-outcome-metrics)
4. [Robot Decision Logic — `_decide_with_ball()`](#4-robot-decision-logic--_decide_with_ball)
5. [Key Engineering Fixes During Development](#5-key-engineering-fixes-during-development)
6. [Level 2 — Team Tactics and HTSM](#6-level-2--team-tactics-and-htsm)
7. [End-to-End Data Flow Summary](#7-end-to-end-data-flow-summary)

---

## 1. System Architecture Overview

The soccer simulation framework is structured around a **two-level optimisation hierarchy**. The lower level isolates individual robot behaviour parameters and measures their causal impact on match outcomes via controlled sensitivity analysis. The upper level uses those findings to configure team-wide tactical profiles that govern collective behaviour during live matches.

> **Core principle:** The best individual parameter values — discovered empirically through simulation — are fed directly into the tactical engine that governs team strategy. This ensures tactics are grounded in quantified evidence, not guesswork.

### 1.1 Two-Level Framework

| | **Level 1 — Individual Parameter Optimisation** | **Level 2 — Team Tactic Composition** |
|---|---|---|
| **What it does** | Varies one parameter at a time across N trials | Dynamically selects tactics based on game state |
| **Experiment setup** | Blue team uses tweaked value; Red uses BASELINE | HTSM switches tactic profile for all robots |
| **Measurements** | Win rate, goal differential, shots on target | Match outcomes under live tactic transitions |
| **Key constraint** | Asymmetric design — only one side is modified | Each tactic profile uses values from Level 1 |
| **Output** | Best parameter value per metric | Optimised tactic profiles embedded in HTSM |

> **Data flows upward:** Level 1 produces optimal values → Level 2 consumes them as tactic configurations.

---

## 2. Level 1 — Parameter Sensitivity Analysis

Sensitivity analysis is the mechanism by which the system determines which individual robot behaviour parameters most strongly influence match outcomes. The experiment is deliberately designed to be **causal**: only one side receives a modified parameter value at a time, while the other side plays with a fixed BASELINE profile.

### 2.1 Experiment Design

> **KEY RULE:** Blue team always uses the tweaked (candidate) profile. Red team always uses the fixed BASELINE. This asymmetric design is what makes results interpretable — any performance change is attributable solely to the varied parameter.

#### Why Asymmetric Design Matters

An early implementation flaw used identical profiles for both teams — a "mirror match". Mirror matches always deadlock because both sides have the same decision tendencies, producing 0–0 draws regardless of parameter values. All sensitivity signal is destroyed. The fix was simple: **blue gets the tweaked profile, red stays on BASELINE**.

### 2.2 Parameters Under Test

| Parameter | BASELINE | Test Range | Influences |
|---|---|---|---|
| `kick_power` | 1.0× | 0.5 – 2.0× | Shot velocity, dribble advance rate, clearance distance |
| `chase_radius` | 2.0 m | 1.0 – 4.0 m | Pressing intensity, ball recovery speed, defensive shape |
| `shoot_distance_max` | 1.8 m | 1.0 – 3.5 m | Shot frequency, scoring rate, attacking range |
| `shoot_over_pass_bias` | 0.5 | 0.1 – 0.9 | Shoot vs. pass decision probability within shooting range |
| `position_x_offset` | 0.0 m | -1.0 – +1.5 m | Team's average pitch position; aggressiveness of formation |
| `min_passes_before_shot` | 2 | 0 – 5 | Build-up play depth; tendency to shoot early vs. recycle |
| `dash_power_multiplier` | 1.0× | 0.5 – 1.5× | Overall robot speed; time to reach the ball; pressing effectiveness |

### 2.3 Trial Protocol

Each parameter is evaluated across **5 evenly-spaced levels** within its test range. For each level, N trials are run (default: 5). Results are aggregated into a sensitivity heatmap showing win rate and goal differential as a function of parameter value.

> **Match Setup:** 4v4 robots | Pitch: 9 m × 6 m | Robot speed: 12 cm/s | Match duration: 1200s (20 min) | Falls: disabled by default | Workers: 4 parallel processes

**Output files per run:**
- `sensitivity_results.csv` — raw per-match data
- `win_rate_heatmap.png` — win rate by parameter × level
- `goal_diff_heatmap.png` — goal differential by parameter × level

---

## 3. Outcome Metrics

Three primary outcome metrics are recorded per match and used to evaluate parameter impact. A parameter value that consistently improves all three metrics is a strong candidate for adoption in the tactic profile.

| Metric | Definition | Interpretation |
|---|---|---|
| **Win Rate** | Fraction of matches won by Blue over N trials at a given parameter level | Primary success indicator. Win rate > 0.5 means the parameter value gives a competitive advantage over BASELINE. |
| **Goal Differential** | Blue goals minus Red goals, averaged over N trials | Magnitude of advantage. A parameter that increases goal differential without increasing win rate may indicate inconsistency. |
| **Shots on Target** | Number of valid shot attempts that reached the goal area | Proxy metric for offensive pressure. Useful when matches produce few goals — high shot counts with low goals may indicate a goalkeeping or accuracy issue. |

### 3.1 Reading the Heatmaps

The sensitivity analysis outputs two heatmaps: one for win rate and one for goal differential. Each row corresponds to a parameter; each column corresponds to a value level. Cells are colour-coded from cold (low) to hot (high).

- A **vertical hot column** indicates a parameter level that consistently outperforms BASELINE across all parameters tested alongside it.
- A **flat row** (same colour across all columns) indicates the parameter has no significant effect on outcomes — it is not a useful tuning target.
- **Diverging results** between win rate and goal differential heatmaps indicate high variance — more trials are needed.

> **INTERPRETATION RULE:** The optimal parameter value is the one that maximises win rate. If multiple values yield similar win rates, select the one with the highest goal differential as the tiebreaker. This value is then written directly into the team's tactic profile.

---

## 4. Robot Decision Logic — `_decide_with_ball()`

Each robot's in-possession decision-making follows a strict priority hierarchy implemented in `decision_profiled.py`. The parameter values from the `BehaviorProfile` directly gate which branch of this hierarchy is entered.

### 4.1 Decision Priority Order

When a robot has possession of the ball, it evaluates the following conditions **in order**:

1. **SHOOT** — if all four conditions hold:
   - (a) within `shoot_distance_max` of the goal
   - (b) angle to goal ≥ `shoot_angle_min`
   - (c) `min_passes_before_shot` threshold met
   - (d) random draw beats `shoot_over_pass_bias`

2. **PASS** — if a teammate has pass score > 3.0 (opponent's half) or > 0.5 (own half). The `pass_forward_bias` parameter rewards forward passes.

3. **DRIBBLE** — if no shoot or pass condition is met, walk forward toward the goal with the ball. The ball is placed 0.15 m ahead of the robot in its facing direction on each step.

> **BUG NOTE:** An early version used a pass threshold of 0.5 regardless of field position. Since the typical pass score is ~6.0 (due to `pass_forward_bias=1.5` and proximity bonuses), robots always passed and never dribbled — producing 14,000+ passes per match with 0 shots. The fix raised the threshold to 3.0 on the opponent's half, forcing dribble behaviour.

### 4.2 How Parameters Gate Each Branch

| Parameter | Decision Branch Affected | Effect of Increasing Value |
|---|---|---|
| `shoot_distance_max` | SHOOT (condition a) | Robot can shoot from further out → more shot attempts → more goals (if `kick_power` sufficient) |
| `shoot_over_pass_bias` | SHOOT (condition d) | Higher probability of choosing SHOOT over PASS when in range → faster scoring but less build-up play |
| `min_passes_before_shot` | SHOOT (condition c) | Requires more passes before shooting → more build-up but delays first shot |
| `kick_power` | SHOOT & PASS | Ball travels further per kick → longer passes, harder shots, greater scoring probability from distance |
| `chase_radius` | All (when not in possession) | Larger radius means robot actively contests the ball earlier → more interceptions, tighter defence |
| `position_x_offset` | DRIBBLE target position | Shifts the robot's home position forward → whole team plays higher up the pitch → more pressure on opponent goal |

---

## 5. Key Engineering Fixes During Development

During development of the sensitivity analysis pipeline, five critical bugs were identified and resolved. Understanding these fixes is important context for interpreting the simulation's reliability.

| # | Bug | Root Cause | Fix Applied |
|---|---|---|---|
| 1 | `_check_goals()` crash | In static profile mode, `blue_htsm` is `None`. `_check_goals()` called `self.blue_htsm.reset_lock_on_goal()` unconditionally — crashing on the first goal attempt. | Added None-guard: `if self.blue_htsm is not None` before all HTSM method calls in `_check_goals()`. |
| 2 | Mirror match deadlock | Both teams received the tweaked profile. Identical profiles produce identical decisions → 0–0 deadlock every match → sensitivity signal = 0. | Separated `blue_static_profile` and `red_static_profile` constructor args. Red always uses BASELINE. |
| 3 | Match too short (300s) | At 12 cm/s, robots needed ~10–20 min just to reach shooting range. 5-min matches produced zero shots. | Increased default match duration from 300s to 1200s (20 min). |
| 4 | Endless passing loop | Pass score (~6.0) always exceeded the 0.5 threshold → robots passed 14,000+ times per match, never dribbling into shooting range. | Raised pass threshold to 3.0 on the opponent's half, forcing dribble behaviour when no clear pass is available. |
| 5 | **No dribble mechanic** (critical) | `walk_forward` moved the robot but NOT the ball. Robot would take 2 steps, leave the ball 0.3 m behind, lose possession, and repeat. Ball never advanced. | Added ball-follow logic to `walk_forward`: when robot is within 0.3 m of ball, ball is placed 0.15 m ahead of the robot in its facing direction on each step. |

### Diagnostic Evidence for Fix 5

| Condition | Max Blue X | Max Ball X | Passes | Shots | Goals (10 min) |
|---|---|---|---|---|---|
| Before dribble fix | 0.80 m | 1.35 m | 14,400 | 0 | 0 |
| After dribble fix | **4.48 m** | **3.91 m** | 239 | 76+ | **1** |

The ball went from never reaching the opponent half to consistently reaching the goal area (goal is at x = 4.5 m).

---

## 6. Level 2 — Team Tactics and HTSM

The upper level of the framework is the team tactic engine. Tactics define how the whole team behaves collectively — formation shape, pressing intensity, attacking vs. defensive priority — and they switch dynamically in response to game state via a **Hierarchical Tactic State Machine (HTSM)**.

### 6.1 From Parameter Values to Tactic Profiles

The key insight of this framework is that individual parameter optimisation (Level 1) directly informs tactic configuration (Level 2). For each tactic, a `BehaviorProfile` is constructed using the optimal values identified by sensitivity analysis.

| Tactic | Game State Trigger | Key Profile Parameters (Example) |
|---|---|---|
| **Pressing** | Opponent has ball in their half; score is level or team is losing | `chase_radius = 3.5`, `position_x_offset = +0.8`, `kick_power = 1.2` |
| **Build-up / Possession** | Team has ball in own half; no immediate scoring opportunity | `min_passes_before_shot = 4`, `shoot_over_pass_bias = 0.2`, `pass_forward_bias = 2.0` |
| **Direct Attack** | Ball in opponent half; attacking robot within `shoot_distance_max` | `shoot_distance_max = 3.0`, `shoot_over_pass_bias = 0.85`, `kick_power = 1.5` |
| **Counter-Attack** | Won ball in own half; opponent's formation is high | `dash_power_multiplier = 1.3`, `position_x_offset = +1.2`, `chase_radius = 1.5` |
| **Defensive Hold** | Team is winning; protecting the lead | `chase_radius = 2.0`, `position_x_offset = -0.5`, `shoot_over_pass_bias = 0.3` |

### 6.2 HTSM — Tactic Switching Logic

The HTSM monitors game state events and transitions the team between tactics. It operates at the **team level**, not the individual robot level. Once a tactic is selected, all robots on the team receive the corresponding `BehaviorProfile` for the next decision cycle.

- **Game state inputs:** current score, ball position, possession side, time remaining, recent event history (goals, turnovers).
- **HTSM transitions are event-driven:** a goal conceded triggers a transition to Pressing; regaining the lead triggers a transition back to Holding or Build-up.
- **`reset_lock_on_goal()`** is called when a goal is scored to cancel any in-progress tactic lock and re-evaluate the game state from scratch.

> **DESIGN PRINCIPLE:** The parameter values written into each tactic profile are not manually tuned. They are the output of the Level 1 sensitivity analysis. This closes the loop: simulation → optimal parameters → tactic profiles → live match behaviour → measurable outcomes → updated simulation.

---

## 7. End-to-End Data Flow Summary

| Step | Action | Output / Feeds Into |
|---|---|---|
| 1 | Define BASELINE `BehaviorProfile` | Starting point for all comparisons. Red team always plays at BASELINE. |
| 2 | Run `run_sensitivity_analysis.py --params [list]` | 50–75 matches per parameter set. CSV of per-match results. |
| 3 | Read `win_rate_heatmap.png` and `goal_diff_heatmap.png` | Identify optimal value per parameter (hot cell in heatmap). |
| 4 | Construct tactic-specific `BehaviorProfile` | Each tactic (Pressing, Attack, Hold…) gets a profile with optimal values. |
| 5 | Load profiles into HTSM | HTSM assigns profiles to all robots when a tactic transition fires. |
| 6 | Run live match / further validation | Verify that HTSM-driven matches with optimised profiles outperform BASELINE vs BASELINE. |
| 7 | Iterate: update BASELINE, re-run analysis | Continuous improvement loop — new BASELINE reflects current best known configuration. |

### 7.1 What This Architecture Solves

- **Removes manual parameter guessing:** every value in a tactic profile is empirically justified.
- **Isolates causality:** asymmetric experiment design ensures sensitivity results are interpretable, not confounded.
- **Separates concerns:** individual behaviour optimisation is independent of team tactic logic, making both easier to reason about and improve.
- **Enables iterative improvement:** running more trials narrows confidence intervals; discovering new parameters just requires adding them to the sensitivity sweep.

### 7.2 Example Pipeline Run

```bash
python run_sensitivity_analysis.py \
  --trials 10 \
  --params kick_power shoot_distance_max shoot_over_pass_bias \
  --output results_v1 \
  --no-falls \
  --workers 4
```

Read heatmaps → Identify `kick_power=1.4`, `shoot_distance_max=2.8`, `shoot_over_pass_bias=0.7` as optimal → Write these into `DirectAttack` tactic profile → Validate in HTSM match.

---

*Team 1 | ENG5326 Robotics M | University of Glasgow*
