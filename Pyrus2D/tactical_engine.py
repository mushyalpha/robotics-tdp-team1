"""
Tactical Engine — Unified Behavioral Architecture
===================================================

Merges role-level aggressiveness (conservative / aggressive) with
team-level tactics (park-the-bus, possession, counter-attack, etc.)
under a single continuous aggressiveness parameter α ∈ [0, 1].

Architecture
------------
Personality (Conservative / Aggressive) → sets β bias + switching table
    ↓
Game-State Monitor (score, time, ball zone, possession)
    ↓
HTSM (one per team) → target α + tactic label
    ↓
α Drift (low-pass filter + hysteresis) → current α
    ↓
from_alpha(current_α) → BehaviorProfile → Role-level FSM

Design principles:
  • α drift prevents motor-jitter on NAO6 hardware.
  • Keyframe anchors give non-linear mapping (pressing stays low until α > 0.7).
  • Personality sets *trigger thresholds*, not just bias.
  • Temporal lock prevents flickering, with a fast-break override for
    ball-recovery counter-attacks.
  • position_x_offset retreats faster than chase_radius shrinks during
    downward drift — defenders return before they stop pressing.
"""

from __future__ import annotations

from enum import Enum
from dataclasses import dataclass, fields
from typing import Dict, List, Optional, Tuple

import numpy as np


# ═══════════════════════════════════════════════════════════════════════
# TACTIC ENUM
# ═══════════════════════════════════════════════════════════════════════

class Tactic(Enum):
    PARK_THE_BUS   = "PARK THE BUS"
    POSSESSION     = "POSSESSION"
    BALANCED       = "BALANCED"
    COUNTER_ATTACK = "COUNTER ATTACK"
    ALL_OUT_ATTACK = "ALL OUT ATTACK"


TACTIC_COLORS = {
    Tactic.PARK_THE_BUS:   "#60a5fa",   # blue — defensive
    Tactic.POSSESSION:     "#4ade80",   # green — controlled
    Tactic.BALANCED:       "#facc15",   # yellow — neutral
    Tactic.COUNTER_ATTACK: "#f97316",   # orange — transitional
    Tactic.ALL_OUT_ATTACK: "#f43f5e",   # red — maximum aggression
}


# ═══════════════════════════════════════════════════════════════════════
# PERSONALITY-SPECIFIC SWITCHING TABLES
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class _SwitchRule:
    """One row in the switching table."""
    tactic: Tactic
    target_alpha: float


def _conservative_table(
    score_diff: int,
    time_remaining: float,
    ball_recovered_own_half: bool,
) -> _SwitchRule:
    """
    Conservative personality — "wait and see", stubborn in defence.
    score_diff > 0 means *this* team is leading.
    """
    # --- Trailing scenarios ---
    if score_diff <= -2:
        if time_remaining < 90:
            return _SwitchRule(Tactic.ALL_OUT_ATTACK, 0.85)
        return _SwitchRule(Tactic.COUNTER_ATTACK, 0.65)

    if score_diff == -1:
        if time_remaining < 90:
            return _SwitchRule(Tactic.COUNTER_ATTACK, 0.70)
        return _SwitchRule(Tactic.BALANCED, 0.50)        # wait and see

    # --- Leading scenarios ---
    if score_diff >= 2:
        return _SwitchRule(Tactic.PARK_THE_BUS, 0.10)

    if score_diff == 1:
        return _SwitchRule(Tactic.PARK_THE_BUS, 0.15)

    # --- Level score ---
    if ball_recovered_own_half:
        return _SwitchRule(Tactic.BALANCED, 0.40)         # slow build-up

    return _SwitchRule(Tactic.BALANCED, 0.45)


def _aggressive_table(
    score_diff: int,
    time_remaining: float,
    ball_recovered_own_half: bool,
) -> _SwitchRule:
    """
    Aggressive personality — "panic early, press hard", stubborn in attack.
    """
    # --- Trailing scenarios ---
    if score_diff <= -2:
        return _SwitchRule(Tactic.ALL_OUT_ATTACK, 0.95)

    if score_diff == -1:
        if time_remaining < 90:
            return _SwitchRule(Tactic.ALL_OUT_ATTACK, 0.95)
        return _SwitchRule(Tactic.COUNTER_ATTACK, 0.75)

    # --- Leading scenarios ---
    if score_diff >= 2:
        return _SwitchRule(Tactic.POSSESSION, 0.35)

    if score_diff == 1:
        return _SwitchRule(Tactic.POSSESSION, 0.45)       # go for 2nd goal

    # --- Level score ---
    if ball_recovered_own_half:
        return _SwitchRule(Tactic.COUNTER_ATTACK, 0.80)   # immediate counter

    return _SwitchRule(Tactic.BALANCED, 0.55)


# ═══════════════════════════════════════════════════════════════════════
# KEYFRAME ANCHORS — non-linear α → profile-field mapping
# ═══════════════════════════════════════════════════════════════════════
# Each anchor maps an α value to the BehaviorProfile numeric fields.
# See behavior_profile.py for field definitions.
# Kick / pass power is already Webots-calibrated to ~1.3 m range;
# the variation here is intentionally narrow.

ANCHORS: Dict[float, dict] = {
    0.00: dict(
        chase_radius=1.3,
        intercept_urgency=2,
        shoot_distance_max=1.0,
        shoot_angle_min=25.0,
        shoot_over_pass_bias=0.15,
        min_passes_before_shot=3,
        pass_forward_bias=0.8,
        kick_power=0.90,
        pass_power=0.70,
        kick_accuracy=0.08,
        position_x_offset=-1.2,
        position_y_spread=0.7,
        gk_sweep_radius=0.4,
        dash_power_multiplier=0.70,
        fall_probability_mult=0.6,
        defensive_press_offset=-1.2,
        tackle_aggression=0.20,
        min_teammate_spacing=1.0,
    ),
    0.35: dict(
        chase_radius=2.0,
        intercept_urgency=3,
        shoot_distance_max=1.4,
        shoot_angle_min=18.0,
        shoot_over_pass_bias=0.30,
        min_passes_before_shot=2,
        pass_forward_bias=1.2,
        kick_power=0.95,
        pass_power=0.78,
        kick_accuracy=0.12,
        position_x_offset=-0.4,
        position_y_spread=0.85,
        gk_sweep_radius=0.7,
        dash_power_multiplier=0.85,
        fall_probability_mult=0.8,
        defensive_press_offset=-0.5,
        tackle_aggression=0.35,
        min_teammate_spacing=1.2,
    ),
    0.50: dict(
        chase_radius=2.5,
        intercept_urgency=5,
        shoot_distance_max=1.8,
        shoot_angle_min=12.0,
        shoot_over_pass_bias=0.50,
        min_passes_before_shot=1,
        pass_forward_bias=1.5,
        kick_power=1.05,
        pass_power=0.85,
        kick_accuracy=0.15,
        position_x_offset=0.0,
        position_y_spread=1.0,
        gk_sweep_radius=1.0,
        dash_power_multiplier=1.0,
        fall_probability_mult=1.0,
        defensive_press_offset=0.0,
        tackle_aggression=0.50,
        min_teammate_spacing=1.4,
    ),
    0.70: dict(
        chase_radius=3.0,
        intercept_urgency=7,
        shoot_distance_max=2.2,
        shoot_angle_min=8.0,
        shoot_over_pass_bias=0.65,
        min_passes_before_shot=0,
        pass_forward_bias=1.8,
        kick_power=1.10,
        pass_power=0.90,
        kick_accuracy=0.18,
        position_x_offset=0.8,
        position_y_spread=1.1,
        gk_sweep_radius=1.5,
        dash_power_multiplier=1.15,
        fall_probability_mult=1.3,
        defensive_press_offset=1.2,
        tackle_aggression=0.70,
        min_teammate_spacing=1.6,
    ),
    1.00: dict(
        chase_radius=3.5,
        intercept_urgency=9,
        shoot_distance_max=2.8,
        shoot_angle_min=4.0,
        shoot_over_pass_bias=0.85,
        min_passes_before_shot=0,
        pass_forward_bias=2.2,
        kick_power=1.15,
        pass_power=0.95,
        kick_accuracy=0.22,
        position_x_offset=1.5,
        position_y_spread=1.3,
        gk_sweep_radius=2.0,
        dash_power_multiplier=1.30,
        fall_probability_mult=1.6,
        defensive_press_offset=2.0,
        tackle_aggression=0.85,
        min_teammate_spacing=1.8,
    ),
}

# Pre-sort keys for binary-search interpolation
_ANCHOR_KEYS = sorted(ANCHORS.keys())
_ANCHOR_FIELDS = list(ANCHORS[0.0].keys())


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def interpolate_profile_fields(alpha: float) -> dict:
    """
    Piecewise-linear interpolation between the nearest keyframe anchors.

    Returns a dict of profile-field values for the given α.
    """
    alpha = float(np.clip(alpha, 0.0, 1.0))

    # Find bounding anchors
    lo_key = _ANCHOR_KEYS[0]
    hi_key = _ANCHOR_KEYS[-1]
    for i in range(len(_ANCHOR_KEYS) - 1):
        if _ANCHOR_KEYS[i] <= alpha <= _ANCHOR_KEYS[i + 1]:
            lo_key = _ANCHOR_KEYS[i]
            hi_key = _ANCHOR_KEYS[i + 1]
            break

    if lo_key == hi_key:
        return dict(ANCHORS[lo_key])

    t = (alpha - lo_key) / (hi_key - lo_key)
    lo_vals = ANCHORS[lo_key]
    hi_vals = ANCHORS[hi_key]

    result = {}
    for field in _ANCHOR_FIELDS:
        lo_v = lo_vals[field]
        hi_v = hi_vals[field]
        if isinstance(lo_v, int) and isinstance(hi_v, int):
            result[field] = int(round(_lerp(lo_v, hi_v, t)))
        else:
            result[field] = _lerp(lo_v, hi_v, t)
    return result


def alpha_to_profile(alpha: float, name: str = "dynamic"):
    """
    Convert a continuous α value to a full BehaviorProfile instance.
    Uses keyframe-anchor piecewise-linear interpolation.
    """
    from behavior_profile import BehaviorProfile
    vals = interpolate_profile_fields(alpha)
    return BehaviorProfile(name=name, **vals)


# ═══════════════════════════════════════════════════════════════════════
# TACTICAL STATE MACHINE (one per team)
# ═══════════════════════════════════════════════════════════════════════

# Drift speeds (per simulation step = 0.05 s)
_DRIFT_CONSERVATIVE = 0.005   # ~3 s to shift full range
_DRIFT_AGGRESSIVE   = 0.015   # ~1 s to shift full range

# Temporal lock: steps before next tactic switch is allowed
_TEMPORAL_LOCK_STEPS = 200    # 10 s

# Fast-break override: COUNTER_ATTACK on ball recovery can break any
# defensive-state temporal lock.
_FAST_BREAK_TACTICS = {Tactic.COUNTER_ATTACK}
_DEFENSIVE_TACTICS  = {Tactic.PARK_THE_BUS, Tactic.POSSESSION}


@dataclass
class TacticEvent:
    """Logged when a tactic switch occurs."""
    step: int
    old_tactic: Tactic
    new_tactic: Tactic
    trigger: str            # human-readable reason
    target_alpha: float


class TacticalStateMachine:
    """
    High-Level Tactical State Machine for one team.

    Call update() every simulation step.  The machine:
      1. Evaluates the switching table for the personality.
      2. Applies hysteresis (temporal lock + fast-break override).
      3. Drifts current_alpha toward target_alpha.
      4. Returns the live BehaviorProfile.
    """

    def __init__(self, personality: str = "aggressive"):
        if personality not in ("aggressive", "conservative"):
            raise ValueError(f"Unknown personality: {personality!r}")

        self.personality: str = personality

        # Strategic bias
        self.beta: float = 0.15 if personality == "aggressive" else -0.15

        # Drift speed
        self.drift_speed: float = (
            _DRIFT_AGGRESSIVE if personality == "aggressive"
            else _DRIFT_CONSERVATIVE
        )

        # State
        self.current_tactic: Tactic = Tactic.BALANCED
        self.target_alpha: float = 0.50
        self.current_alpha: float = 0.50
        self._lock_remaining: int = 0       # steps until next switch allowed

        # Retreat-priority flag: when α is drifting *down*, position fields
        # should lead (update faster) so defenders get back first.
        self.retreating: bool = False

        # Event log (most recent first)
        self.events: List[TacticEvent] = []

        # Ball-recovery counter (temporary counter-attack window)
        self._counter_window: int = 0       # steps remaining

    # ─── public API ────────────────────────────────────────────────

    def update(
        self,
        step: int,
        score_diff: int,
        time_remaining: float,
        ball_zone: str,             # "own_half" | "mid" | "opp_half"
        possession_team: Optional[str],   # "blue"/"red"/None
        own_team: str,
        ball_recovered_own_half: bool,
    ) -> None:
        """
        Evaluate switching rules, apply hysteresis, drift α.

        Args:
            step:                   current sim step
            score_diff:             own_goals − opponent_goals (positive = leading)
            time_remaining:         seconds left
            ball_zone:              where the ball is relative to *this* team
            possession_team:        which team last touched the ball
            own_team:               "blue" or "red"
            ball_recovered_own_half: True on the step the ball changes
                                     possession to own team in own half
        """
        # 1. Evaluate switching table
        if self.personality == "conservative":
            rule = _conservative_table(score_diff, time_remaining,
                                       ball_recovered_own_half)
        else:
            rule = _aggressive_table(score_diff, time_remaining,
                                     ball_recovered_own_half)

        new_tactic = rule.tactic
        raw_target = rule.target_alpha

        # 2. Apply strategic bias β
        biased_target = float(np.clip(raw_target + self.beta, 0.0, 1.0))

        # 3. Hysteresis — temporal lock
        self._lock_remaining = max(0, self._lock_remaining - 1)

        want_switch = (new_tactic != self.current_tactic)
        allowed = (self._lock_remaining <= 0)

        # Fast-break override: COUNTER_ATTACK on ball recovery can break
        # a *defensive* temporal lock.
        fast_break = (
            want_switch
            and new_tactic in _FAST_BREAK_TACTICS
            and ball_recovered_own_half
            and self.current_tactic in _DEFENSIVE_TACTICS
        )

        # Goal override: any goal resets the lock
        # (handled externally by calling reset_lock_on_goal)

        if want_switch and (allowed or fast_break):
            old = self.current_tactic
            self.current_tactic = new_tactic
            self.target_alpha = biased_target
            self._lock_remaining = _TEMPORAL_LOCK_STEPS

            # Determine trigger reason
            trigger = self._describe_trigger(
                score_diff, time_remaining, ball_recovered_own_half
            )
            evt = TacticEvent(step, old, new_tactic, trigger, biased_target)
            self.events.insert(0, evt)
            if len(self.events) > 20:
                self.events.pop()
        else:
            # Even if tactic doesn't switch, always update target α
            # (the *magnitude* may change within the same tactic)
            self.target_alpha = biased_target

        # 4. α Drift (low-pass filter)
        self.retreating = (self.target_alpha < self.current_alpha)

        if self.current_alpha < self.target_alpha:
            self.current_alpha = min(
                self.current_alpha + self.drift_speed,
                self.target_alpha,
            )
        elif self.current_alpha > self.target_alpha:
            self.current_alpha = max(
                self.current_alpha - self.drift_speed,
                self.target_alpha,
            )

    def reset_lock_on_goal(self):
        """Call when a goal is scored — immediately unlocks switching."""
        self._lock_remaining = 0

    def get_profile(self) -> "BehaviorProfile":
        """Return a BehaviorProfile for the current α."""
        label = f"{self.personality}_{self.current_tactic.name}"
        profile = alpha_to_profile(self.current_alpha, name=label)

        # --- Retreat-priority: during downward drift, make position_x_offset
        #     retreat *faster* than chase_radius shrinks.
        if self.retreating:
            # Blend position_x_offset toward target faster
            target_fields = interpolate_profile_fields(self.target_alpha)
            fast_factor = 0.6  # 60% toward target already
            profile.position_x_offset = _lerp(
                profile.position_x_offset,
                target_fields["position_x_offset"],
                fast_factor,
            )
            profile.defensive_press_offset = _lerp(
                profile.defensive_press_offset,
                target_fields["defensive_press_offset"],
                fast_factor,
            )
        return profile

    # ─── helpers ───────────────────────────────────────────────────

    @staticmethod
    def _describe_trigger(score_diff, time_remaining, ball_recovered):
        parts = []
        if score_diff > 0:
            parts.append(f"Leading +{score_diff}")
        elif score_diff < 0:
            parts.append(f"Trailing {score_diff}")
        else:
            parts.append("Level")
        if time_remaining < 90:
            parts.append(f"{int(time_remaining)}s left")
        if ball_recovered:
            parts.append("ball recovered")
        return ", ".join(parts)

    @property
    def recent_events(self) -> List[TacticEvent]:
        """Last 4 tactic switch events (most recent first)."""
        return self.events[:4]


# ═══════════════════════════════════════════════════════════════════════
# FORMATION LABEL (ported from simshu1.py)
# ═══════════════════════════════════════════════════════════════════════

def compute_formation_label(robots, attack_direction: int) -> str:
    """
    Compute a formation string like '1-2-1' from current player positions.

    Layers:
      0 — goalkeeper zone (within penalty area depth of own goal)
      1 — defensive / own half
      2 — attacking / opponent half
    """
    PITCH_LENGTH = 9.0
    PENALTY_DEPTH = 2.0
    own_goal_x = -(PITCH_LENGTH / 2) * attack_direction

    layers = [0, 0, 0]
    for r in robots:
        depth = (r.x - own_goal_x) * attack_direction
        if depth < PENALTY_DEPTH + 0.3:
            layers[0] += 1
        elif depth < PITCH_LENGTH / 2:
            layers[1] += 1
        else:
            layers[2] += 1

    parts = [str(c) for c in layers if c > 0]
    if len(parts) < 2:
        parts = [str(c) for c in layers]
    return "-".join(parts)
