"""
Behavior Profile System — Unified Tactical Architecture
========================================================

Each BehaviorProfile contains tuning parameters that control how robots
make decisions. Profiles are now generated dynamically from a continuous
aggressiveness parameter α ∈ [0,1] via the tactical engine.

Static presets (AGGRESSIVE, CONSERVATIVE) are kept as reference anchors.
The BASELINE preset is removed — use from_alpha(0.5) or the tactical
engine instead.
"""

from dataclasses import dataclass, fields


@dataclass
class BehaviorProfile:
    """Tuning knobs for robot decision-making behavior."""

    name: str

    # --- Chase & Intercept ---
    chase_radius: float         # Max distance (m) a field player will chase the ball
    intercept_urgency: int      # Extra cycles allowed vs teammate before giving up chase

    # --- Shooting ---
    shoot_distance_max: float   # Max distance (m) from goal to attempt a shot
    shoot_angle_min: float      # Min open goal angle (degrees) required to shoot
    shoot_over_pass_bias: float # 0.0 = always pass, 1.0 = always shoot when possible

    # --- Passing ---
    min_passes_before_shot: int # Must complete this many passes before shooting allowed
    pass_forward_bias: float    # Weight for preferring forward passes (higher = more forward)

    # --- Kick Physics ---
    kick_power: float           # Base kick power toward goal
    pass_power: float           # Base pass power to teammate
    kick_accuracy: float        # Angle error std dev (radians) — lower = more accurate

    # --- Positioning ---
    position_x_offset: float    # Shift from home formation (m). + = forward, - = back
    position_y_spread: float    # Width spread multiplier (1.0 = normal)

    # --- Goalkeeper ---
    gk_sweep_radius: float      # How far GK comes off the line to sweep (m)

    # --- Physical / Stamina ---
    dash_power_multiplier: float  # Walk speed multiplier (1.0 = normal)
    fall_probability_mult: float  # Multiplier on fall chance (1.0 = normal, >1 = riskier)

    # --- Defensive ---
    defensive_press_offset: float # DEF position shift (m). + = press forward, - = drop deep
    tackle_aggression: float      # 0.0 = never tackle, 1.0 = always tackle when in range

    # --- Spacing ---
    min_teammate_spacing: float = 1.4   # Min distance (m) between teammates to avoid clumping

    # ─── Class method for α-based generation ──────────────────────
    @classmethod
    def from_alpha(cls, alpha: float, name: str = "dynamic") -> "BehaviorProfile":
        """
        Generate a BehaviorProfile by interpolating keyframe anchors.
        Delegates to tactical_engine.alpha_to_profile().
        """
        from tactical_engine import alpha_to_profile
        return alpha_to_profile(alpha, name=name)


# =============================================================================
# STATIC PRESETS (reference anchors — for direct use or comparison)
# =============================================================================

AGGRESSIVE = BehaviorProfile(
    name="aggressive",
    chase_radius=3.5,
    intercept_urgency=8,
    shoot_distance_max=2.8,
    shoot_angle_min=5.0,
    shoot_over_pass_bias=0.8,
    min_passes_before_shot=0,
    pass_forward_bias=2.0,
    kick_power=1.15,
    pass_power=0.95,
    kick_accuracy=0.20,
    position_x_offset=1.5,
    position_y_spread=1.2,
    gk_sweep_radius=2.0,
    dash_power_multiplier=1.3,
    fall_probability_mult=1.5,
    defensive_press_offset=2.0,
    tackle_aggression=0.8,
    min_teammate_spacing=1.8,
)

CONSERVATIVE = BehaviorProfile(
    name="conservative",
    chase_radius=1.5,
    intercept_urgency=2,
    shoot_distance_max=1.2,
    shoot_angle_min=20.0,
    shoot_over_pass_bias=0.2,
    min_passes_before_shot=3,
    pass_forward_bias=1.0,
    kick_power=0.95,
    pass_power=0.75,
    kick_accuracy=0.10,
    position_x_offset=-1.0,
    position_y_spread=0.8,
    gk_sweep_radius=0.5,
    dash_power_multiplier=0.7,
    fall_probability_mult=0.7,
    defensive_press_offset=-1.0,
    tackle_aggression=0.3,
    min_teammate_spacing=1.0,
)

# Backwards compatibility: BASELINE maps to α=0.5
BASELINE = BehaviorProfile(
    name="baseline",
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
    tackle_aggression=0.5,
    min_teammate_spacing=1.4,
)


def get_profile(name: str) -> BehaviorProfile:
    """Get a BehaviorProfile by name string."""
    profiles = {
        "baseline": BASELINE,
        "aggressive": AGGRESSIVE,
        "conservative": CONSERVATIVE,
    }
    if name.lower() not in profiles:
        raise ValueError(f"Unknown profile '{name}'. Choose from: {list(profiles.keys())}")
    return profiles[name.lower()]
