"""
Behavior Profile System for Aggressive vs Conservative Strategies
=================================================================

Each BehaviorProfile contains tuning parameters that control how robots
make decisions. The same decision algorithm reads from the profile,
producing different behaviors without separate code paths.

Presets:
  - BASELINE:      Current default behavior (matches v3 passing)
  - AGGRESSIVE:    Shoot-first, chase hard, push forward, high energy
  - CONSERVATIVE:  Pass-first, hold position, stay deep, save energy
"""

from dataclasses import dataclass


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


# =============================================================================
# PRESET PROFILES
# =============================================================================

BASELINE = BehaviorProfile(
    name="baseline",
    # Chase
    chase_radius=2.5,
    intercept_urgency=5,
    # Shooting
    shoot_distance_max=2.5,
    shoot_angle_min=10.0,
    shoot_over_pass_bias=0.5,
    # Passing
    min_passes_before_shot=2,
    pass_forward_bias=1.5,
    # Kick physics
    kick_power=1.8,
    pass_power=1.2,
    kick_accuracy=0.15,
    # Positioning
    position_x_offset=0.0,
    position_y_spread=1.0,
    # Goalkeeper
    gk_sweep_radius=1.0,
    # Physical
    dash_power_multiplier=1.0,
    fall_probability_mult=1.0,
    # Defensive
    defensive_press_offset=0.0,
    tackle_aggression=0.5,
)

AGGRESSIVE = BehaviorProfile(
    name="aggressive",
    # Chase — chase from further away
    chase_radius=3.5,
    intercept_urgency=8,
    # Shooting — shoot first, shoot from distance
    shoot_distance_max=4.0,
    shoot_angle_min=5.0,
    shoot_over_pass_bias=0.8,
    # Passing — minimal passing required
    min_passes_before_shot=0,
    pass_forward_bias=2.0,
    # Kick physics — harder kicks, slightly less accurate
    kick_power=2.2,
    pass_power=1.4,
    kick_accuracy=0.20,
    # Positioning — push everyone forward
    position_x_offset=1.5,
    position_y_spread=1.2,
    # Goalkeeper — come off line
    gk_sweep_radius=2.0,
    # Physical — max effort, higher fall risk
    dash_power_multiplier=1.3,
    fall_probability_mult=1.5,
    # Defensive — press high, tackle often
    defensive_press_offset=2.0,
    tackle_aggression=0.8,
)

CONSERVATIVE = BehaviorProfile(
    name="conservative",
    # Chase — only chase when very close
    chase_radius=1.5,
    intercept_urgency=2,
    # Shooting — rarely shoot, only from close
    shoot_distance_max=1.5,
    shoot_angle_min=20.0,
    shoot_over_pass_bias=0.2,
    # Passing — lots of passing required
    min_passes_before_shot=3,
    pass_forward_bias=1.0,
    # Kick physics — softer but more accurate
    kick_power=1.4,
    pass_power=1.0,
    kick_accuracy=0.10,
    # Positioning — drop everyone back
    position_x_offset=-1.0,
    position_y_spread=0.8,
    # Goalkeeper — stay on line
    gk_sweep_radius=0.5,
    # Physical — conserve energy, fewer falls
    dash_power_multiplier=0.7,
    fall_probability_mult=0.7,
    # Defensive — sit deep, only tackle when safe
    defensive_press_offset=-1.0,
    tackle_aggression=0.3,
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
