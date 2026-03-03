"""
Simple Soccer Simulation VERSION 3 — Unified Tactical Architecture
================================================================

Full 2D soccer simulation with:
  - Two teams (Blue vs Red), 4 players each (1 GK, 1 DEF, 2 ATK)
  - BehaviorProfile-driven decisions (aggressive / conservative / baseline)
  - Match clock (configurable, default 5 minutes)
  - RoboCup-compliant set pieces: kick-off, throw-in, goal kick, corner kick
  - Trackback animation after goals
  - Realistic ball physics (spin, friction, accuracy errors)
  - Fall/recovery simulation
  - Per-step metrics logging for analysis

Field: 9m × 6m, goals 2.6m wide (KidSize RoboCup rules)
Blue attacks RIGHT goal (+x), Red attacks LEFT goal (-x).
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.animation import FuncAnimation, PillowWriter
from datetime import datetime
from enum import Enum
import matplotlib.transforms as mtransforms
import time
import os
import json
import sys

from behavior_profile import BehaviorProfile, BASELINE, AGGRESSIVE, CONSERVATIVE, get_profile
from tactical_engine import (
    TacticalStateMachine, Tactic, TACTIC_COLORS,
    compute_formation_label,
)
from decision_profiled import decide_action_profiled, _get_home_position

# =============================================================================
# CONSTANTS
# =============================================================================

PITCH_LENGTH = 9.0
PITCH_WIDTH = 6.0
GOAL_WIDTH = 2.6
GOAL_DEPTH = 0.6

# Penalty area (KidSize)
PENALTY_AREA_LENGTH = 2.0   # extends into the field
PENALTY_AREA_WIDTH = 5.0    # width (centered on goal)

# Goal area (KidSize)
GOAL_AREA_LENGTH = 1.0





















































































































GOAL_AREA_WIDTH = 3.0

# Timing
DT = 0.05           # seconds per step (50ms, matching animation interval)
DEFAULT_MATCH_DURATION = 300  # 5 minutes in seconds
TURN_RATE_RAD_PER_SEC = 0.5
TURN_STEP_RAD = TURN_RATE_RAD_PER_SEC * DT
MAX_PLAYER_SPEED_M_PER_S = 0.12
MAX_PLAYER_SPEED_M_PER_STEP = MAX_PLAYER_SPEED_M_PER_S * DT
RECOVERY_DURATION_SECONDS = 26.0
RECOVERY_DURATION_STEPS = int(RECOVERY_DURATION_SECONDS / DT)

# Set piece constants
SET_PIECE_WAIT_STEPS = 30     # ~1.5s wait before set piece resumes
TRACKBACK_SPEED = 0.0072      # Walk speed during trackback (~14.4 cm/s, slightly faster than normal 12 cm/s)
TRACKBACK_THRESHOLD = 0.5     # Distance threshold to consider "at home"

# Robot collision — approximate each robot as a circle for overlap resolution
# Real dimensions: 311 mm × 275 mm → average radius ≈ (0.311 + 0.275) / 4 ≈ 0.147 m
ROBOT_COLLISION_RADIUS = 0.147  # metres
COLLISION_FALL_MIN_OVERLAP = 0.04  # m, ignore light contacts
COLLISION_FALL_MAX_PROB = 0.35     # cap fall chance from a single collision

# =============================================================================
# ENUMS
# =============================================================================

class RobotState(Enum):
    IDLE = "IDLE"
    CHASING_BALL = "CHASING_BALL"
    KICKING = "KICKING"
    PASSING = "PASSING"
    POSITIONING = "POSITIONING"
    FALLEN = "FALLEN"
    RECOVERING = "RECOVERING"
    GOALKEEPING = "GOALKEEPING"
    TRACKBACK = "TRACKBACK"

class RobotRole(Enum):
    GOALKEEPER = "GK"
    DEFENDER = "DEF"
    ATTACKER = "ATK"

class GameState(Enum):
    KICKOFF = "KICKOFF"
    PLAYING = "PLAYING"
    THROW_IN = "THROW_IN"
    GOAL_KICK = "GOAL_KICK"
    CORNER_KICK = "CORNER_KICK"
    TRACKBACK = "TRACKBACK"
    MATCH_OVER = "MATCH_OVER"

# Visual helpers
STATE_COLORS = {
    RobotState.IDLE: '#808080',
    RobotState.CHASING_BALL: '#00FF00',
    RobotState.KICKING: '#FF0000',
    RobotState.PASSING: '#FFA500',
    RobotState.POSITIONING: '#00BFFF',
    RobotState.FALLEN: '#8B0000',
    RobotState.RECOVERING: '#FFD700',
    RobotState.GOALKEEPING: '#9400D3',
    RobotState.TRACKBACK: '#ADD8E6',
}

STATE_ABBREV = {
    RobotState.IDLE: "IDL",
    RobotState.CHASING_BALL: "CHS",
    RobotState.KICKING: "KCK",
    RobotState.PASSING: "PAS",
    RobotState.POSITIONING: "POS",
    RobotState.FALLEN: "FAL",
    RobotState.RECOVERING: "REC",
    RobotState.GOALKEEPING: "GKP",
    RobotState.TRACKBACK: "TBK",
}


# =============================================================================
# ROBOT CLASS
# =============================================================================

class Robot:
    def __init__(self, x, y, team='blue', player_id=1, role=RobotRole.ATTACKER,
                 profile=None):
        self.x = x
        self.y = y
        self.home_x = x
        self.home_y = y
        self.heading = 0.0 if team == 'blue' else np.pi  # Face toward opponent goal

        self.team = team
        self.id = player_id
        self.role = role
        self.color = '#3366FF' if team == 'blue' else '#FF3333'
        self.profile = profile or BASELINE

        # State machine
        self.state = RobotState.IDLE
        self.previous_state = RobotState.IDLE
        self.state_duration = 0

        # Fall/recovery
        self.fall_probability = 0.0
        self.recovery_time = 0
        self.recovery_duration = RECOVERY_DURATION_STEPS

        # Action timing
        self.action_timer = 0
        self.kick_duration = 5
        self.pass_duration = 5

    def set_state(self, new_state, log=False):
        if new_state != self.state:
            self.previous_state = self.state
            self.state = new_state
            self.state_duration = 0
            if log:
                print(f"  Robot {self.team[0].upper()}{self.id} ({self.role.value}): "
                      f"{self.previous_state.value} -> {new_state.value}")
        else:
            self.state_duration += 1

    def get_distance_to(self, target):
        dx = target['x'] - self.x
        dy = target['y'] - self.y
        return np.sqrt(dx**2 + dy**2)

    def get_bearing_to(self, target):
        dx = target['x'] - self.x
        dy = target['y'] - self.y
        angle_to_target = np.arctan2(dy, dx)
        bearing = angle_to_target - self.heading
        bearing = bearing % (2 * np.pi)
        if bearing > np.pi:
            bearing -= 2 * np.pi
        return bearing

    def simulate_fall(self, profile):
        if self.fall_probability <= 0.0:
            return False
        if self.state not in [RobotState.FALLEN, RobotState.RECOVERING]:
            fall_chance = self.fall_probability * profile.fall_probability_mult
            if self.state in [RobotState.KICKING, RobotState.PASSING]:
                fall_chance *= 3
            if self.state == RobotState.CHASING_BALL:
                fall_chance *= 1.5
            if np.random.random() < fall_chance:
                self.set_state(RobotState.FALLEN)
                self.recovery_time = self.recovery_duration
                return True
        return False

    def update_recovery(self):
        if self.state == RobotState.FALLEN:
            self.recovery_time -= 1
            if self.recovery_time <= self.recovery_duration // 2:
                self.set_state(RobotState.RECOVERING)
        elif self.state == RobotState.RECOVERING:
            self.recovery_time -= 1
            if self.recovery_time <= 0:
                self.set_state(RobotState.IDLE)
                return True
        return False

    def is_incapacitated(self):
        return self.state in [RobotState.FALLEN, RobotState.RECOVERING]

    def move_toward(self, target_x, target_y, speed=0.006):
        """Move directly toward a point (used for trackback)."""
        dx = target_x - self.x
        dy = target_y - self.y
        dist = np.sqrt(dx**2 + dy**2)
        if dist > 0.05:
            self.x += (dx / dist) * min(speed, dist)
            self.y += (dy / dist) * min(speed, dist)
            self.heading = np.arctan2(dy, dx)
            return False  # Not arrived yet
        return True  # Arrived


# =============================================================================
# BALL CLASS
# =============================================================================

class Ball:
    def __init__(self, x=0.0, y=0.0):
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0
        self.friction = 0.92
        self.min_velocity = 0.05
        self.spin = 0.0
        self.spin_decay = 0.95

    def update(self, dt=0.1):
        speed = np.sqrt(self.vx**2 + self.vy**2)

        # Magnus effect (spin)
        if speed > 0.1 and abs(self.spin) > 0.01:
            vx_norm = self.vx / speed
            vy_norm = self.vy / speed
            perp_x = -vy_norm
            perp_y = vx_norm
            spin_force = self.spin * speed * 0.05
            self.vx += perp_x * spin_force * dt
            self.vy += perp_y * spin_force * dt

        # Environmental perturbations
        if speed > 0.1:
            wind_factor = 0.02 * speed
            self.vx += np.random.uniform(-wind_factor, wind_factor) * dt
            self.vy += np.random.uniform(-wind_factor, wind_factor) * dt

        self.x += self.vx * dt
        self.y += self.vy * dt

        self.vx *= self.friction
        self.vy *= self.friction
        self.spin *= self.spin_decay

        if speed < self.min_velocity:
            self.vx = 0.0
            self.vy = 0.0
            self.spin = 0.0

    def stop(self):
        self.vx = 0.0
        self.vy = 0.0
        self.spin = 0.0

    def is_out_touchline(self):
        """Ball crossed a sideline (touch line)."""
        return abs(self.y) > PITCH_WIDTH / 2

    def is_out_goal_line_right(self):
        """Ball crossed the right goal line."""
        return self.x > PITCH_LENGTH / 2

    def is_out_goal_line_left(self):
        """Ball crossed the left goal line."""
        return self.x < -PITCH_LENGTH / 2

    def is_in_goal_right(self):
        """Ball is in the right goal."""
        return self.x > PITCH_LENGTH / 2 and abs(self.y) < GOAL_WIDTH / 2

    def is_in_goal_left(self):
        """Ball is in the left goal."""
        return self.x < -PITCH_LENGTH / 2 and abs(self.y) < GOAL_WIDTH / 2


# =============================================================================
# SOCCER SIMULATOR (VERSION 3)
# =============================================================================

class SoccerSimulator:
    def __init__(self, blue_personality='aggressive', red_personality='conservative',
                 enable_falls=True, match_duration=DEFAULT_MATCH_DURATION,
                 headless=False, adaptive=True):
        """
        Args:
            blue_personality: 'aggressive' or 'conservative' — sets HTSM switching table
            red_personality:  'aggressive' or 'conservative'
            enable_falls: Toggle fall simulation
            match_duration: Match length in seconds
            headless: If True, skip all print output
            adaptive: If False, disable HTSM updates (static behavior for full match)
        """
        self.headless = headless
        self.adaptive = bool(adaptive)
        self.behavior_mode = 'adaptive' if self.adaptive else 'static'

        # --- Tactical State Machines (one per team) ---
        self.blue_personality = blue_personality
        self.red_personality = red_personality
        self.blue_htsm = TacticalStateMachine(blue_personality)
        self.red_htsm = TacticalStateMachine(red_personality)

        # Live profiles — updated every step by the HTSM's current α
        self.blue_profile = self.blue_htsm.get_profile()
        self.red_profile = self.red_htsm.get_profile()

        # Ball
        self.ball = Ball(0, 0)

        # Teams
        self.blue_robots = []
        self.red_robots = []
        self._create_teams()
        self.robots = self.blue_robots + self.red_robots  # All robots

        # Match state
        self.time = 0
        self.match_duration = match_duration
        self.match_duration_steps = int(match_duration / DT)
        self.blue_goals = 0
        self.red_goals = 0
        self.enable_falls = enable_falls

        # Game flow
        self.game_state = GameState.KICKOFF
        self.set_piece_timer = SET_PIECE_WAIT_STEPS
        self.kickoff_team = 'blue'  # Which team takes kick-off
        self.set_piece_team = None  # Which team takes the set piece
        self.last_touch_team = None  # Last team to touch the ball
        self._prev_touch_team = None  # For ball-recovery detection

        # Passing stats (per team)
        self.pass_count = 0
        self.last_passer_id = None
        self.total_passes_blue = 0
        self.total_passes_red = 0
        self.pass_target = None

        # Kickoff robot (the attacker standing at centre circle)
        self.kickoff_robot = None

        # Metrics logging
        self.step_log = []

        # Event log (for display)
        self.event_log = []

        # Position the first kickoff
        self._setup_kickoff()

    def _create_teams(self):
        """Create both teams with mirrored positions."""
        # Blue team: attacks RIGHT (+x direction)
        # All players start on blue's own half (negative x)
        blue_config = [
            (-3.5,  0.0, RobotRole.GOALKEEPER),
            (-2.0,  0.0, RobotRole.DEFENDER),
            (-0.5, -1.0, RobotRole.ATTACKER),
            (-0.5,  1.0, RobotRole.ATTACKER),
        ]
        for i, (x, y, role) in enumerate(blue_config):
            r = Robot(x, y, 'blue', i + 1, role, self.blue_profile)
            self.blue_robots.append(r)

        # Red team: attacks LEFT (-x direction)
        # All players start on red's own half (positive x)
        red_config = [
            ( 3.5,  0.0, RobotRole.GOALKEEPER),
            ( 2.0,  0.0, RobotRole.DEFENDER),
            ( 0.5, -1.0, RobotRole.ATTACKER),
            ( 0.5,  1.0, RobotRole.ATTACKER),
        ]
        for i, (x, y, role) in enumerate(red_config):
            r = Robot(x, y, 'red', i + 5, role, self.red_profile)
            r.heading = np.pi  # Face left
            self.red_robots.append(r)

    def _get_profile_for(self, robot):
        return self.blue_profile if robot.team == 'blue' else self.red_profile

    def _get_attack_direction(self, robot):
        return 1 if robot.team == 'blue' else -1

    # -----------------------------------------------------------------
    # KICKOFF SETUP
    # -----------------------------------------------------------------

    def _setup_kickoff(self):
        """Place the frontmost attacker of the kickoff team at the centre spot."""
        team_robots = self.blue_robots if self.kickoff_team == 'blue' else self.red_robots
        attack_dir  = 1 if self.kickoff_team == 'blue' else -1

        # Pick the attacker who is furthest forward (closest to opponent goal)
        attackers = [r for r in team_robots if r.role == RobotRole.ATTACKER]
        if not attackers:
            attackers = team_robots  # fallback: use any robot

        centre_robot = max(attackers, key=lambda r: r.x * attack_dir)

        # Move that robot to the centre spot and face the opponent goal
        centre_robot.x = 0.0
        centre_robot.y = 0.0
        centre_robot.heading = 0.0 if self.kickoff_team == 'blue' else np.pi
        centre_robot.set_state(RobotState.IDLE)

        self.kickoff_robot = centre_robot
        if not self.headless:
            print(f"  Kickoff: {self.kickoff_team} robot {centre_robot.id} at centre")


    # -----------------------------------------------------------------
    # GOAL DETECTION & TRACKBACK
    # -----------------------------------------------------------------

    def _check_goals(self):
        """Check if ball entered either goal."""
        if self.ball.is_in_goal_right():
            # Blue scored (attacks right)
            self.blue_goals += 1
            self.last_touch_team = 'blue'
            if not self.headless:
                print(f"\n⚽ GOAL! Blue scores! (Blue {self.blue_goals} - {self.red_goals} Red)")
            self.blue_htsm.reset_lock_on_goal()
            self.red_htsm.reset_lock_on_goal()
            self._add_event(f"⚽ BLUE GOAL ({self.blue_goals}-{self.red_goals})")
            self._start_trackback('red')  # Red gets kick-off
            return True

        if self.ball.is_in_goal_left():
            # Red scored (attacks left)
            self.red_goals += 1
            self.last_touch_team = 'red'
            if not self.headless:
                print(f"\n⚽ GOAL! Red scores! (Blue {self.blue_goals} - {self.red_goals} Red)")
            self.blue_htsm.reset_lock_on_goal()
            self.red_htsm.reset_lock_on_goal()
            self._add_event(f"⚽ RED GOAL ({self.blue_goals}-{self.red_goals})")
            self._start_trackback('blue')  # Blue gets kick-off
            return True

        return False

    def _add_event(self, msg):
        """Add an event to the display log."""
        time_str = self.get_elapsed_time_str()
        self.event_log.insert(0, f"[{time_str}] {msg}")
        if len(self.event_log) > 8:
            self.event_log.pop()

    def _start_trackback(self, kickoff_team):
        """Begin trackback: all players jog back to home positions."""
        self.game_state = GameState.TRACKBACK
        self.kickoff_team = kickoff_team
        self.ball.x = 0.0
        self.ball.y = 0.0
        self.ball.stop()
        # Reset passing
        self.pass_count = 0
        self.last_passer_id = None
        for robot in self.robots:
            robot.set_state(RobotState.TRACKBACK)

    def _update_trackback(self):
        """Move all robots toward home positions. Return True when done."""
        all_home = True
        for robot in self.robots:
            arrived = robot.move_toward(robot.home_x, robot.home_y, TRACKBACK_SPEED)
            if not arrived:
                all_home = False

        if all_home:
            # Transition to kick-off
            self.game_state = GameState.KICKOFF
            self.set_piece_timer = SET_PIECE_WAIT_STEPS
            for robot in self.robots:
                robot.set_state(RobotState.IDLE)
            # Place the kicking team's attacker at the centre
            self._setup_kickoff()
        return all_home

    # -----------------------------------------------------------------
    # SET PIECES
    # -----------------------------------------------------------------

    def _check_out_of_bounds(self):
        """Check if ball went out of bounds and handle set pieces."""
        # --- Touch line (sideline) → Throw-in ---
        if self.ball.is_out_touchline():
            exit_x = self.ball.x
            exit_y = PITCH_WIDTH / 2 if self.ball.y > 0 else -PITCH_WIDTH / 2

            # Awarded to opponent of last touch
            if self.last_touch_team == 'blue':
                self.set_piece_team = 'red'
            elif self.last_touch_team == 'red':
                self.set_piece_team = 'blue'
            else:
                self.set_piece_team = 'blue'  # Default

            self.ball.x = np.clip(exit_x, -PITCH_LENGTH / 2 + 0.5, PITCH_LENGTH / 2 - 0.5)
            self.ball.y = exit_y
            self.ball.stop()

            self.game_state = GameState.THROW_IN
            self.set_piece_timer = SET_PIECE_WAIT_STEPS
            if not self.headless:
                print(f"  Throw-in for {self.set_piece_team} at ({self.ball.x:.1f}, {self.ball.y:.1f})")
            return True

        # --- Goal line (right side) ---
        if self.ball.is_out_goal_line_right():
            if self.last_touch_team == 'blue':
                # Blue (attacking team) put it out → Goal kick for Red
                self.set_piece_team = 'red'
                # Ball placed at touch-centre line intersection on the side it went out
                self.ball.x = PITCH_LENGTH / 2 - 0.3
                self.ball.y = PITCH_WIDTH / 2 if self.ball.y > 0 else -PITCH_WIDTH / 2
                self.ball.stop()
                self.game_state = GameState.GOAL_KICK
                if not self.headless:
                    print(f"  Goal kick for Red")
            else:
                # Red (defending team) put it out → Corner kick for Blue
                self.set_piece_team = 'blue'
                self.ball.x = PITCH_LENGTH / 2 - 0.1
                self.ball.y = PITCH_WIDTH / 2 if self.ball.y > 0 else -PITCH_WIDTH / 2
                self.ball.stop()
                self.game_state = GameState.CORNER_KICK
                if not self.headless:
                    print(f"  Corner kick for Blue")

            self.set_piece_timer = SET_PIECE_WAIT_STEPS
            return True

        # --- Goal line (left side) ---
        if self.ball.is_out_goal_line_left():
            if self.last_touch_team == 'red':
                # Red (attacking left) put it out → Goal kick for Blue
                self.set_piece_team = 'blue'
                self.ball.x = -PITCH_LENGTH / 2 + 0.3
                self.ball.y = PITCH_WIDTH / 2 if self.ball.y > 0 else -PITCH_WIDTH / 2
                self.ball.stop()
                self.game_state = GameState.GOAL_KICK
                if not self.headless:
                    print(f"  Goal kick for Blue")
            else:
                # Blue put it out → Corner kick for Red
                self.set_piece_team = 'red'
                self.ball.x = -PITCH_LENGTH / 2 + 0.1
                self.ball.y = PITCH_WIDTH / 2 if self.ball.y > 0 else -PITCH_WIDTH / 2
                self.ball.stop()
                self.game_state = GameState.CORNER_KICK
                if not self.headless:
                    print(f"  Corner kick for Red")

            self.set_piece_timer = SET_PIECE_WAIT_STEPS
            return True

        return False

    def _update_set_piece(self):
        """Handle set piece wait timer. Returns True when set piece ends."""
        self.set_piece_timer -= 1
        if self.set_piece_timer <= 0:
            self.game_state = GameState.PLAYING
            self.pass_count = 0
            self.last_passer_id = None

            # For KICKOFF specifically: the centre robot immediately passes to a teammate
            if self.kickoff_robot is not None:
                kr = self.kickoff_robot
                attack_dir = self._get_attack_direction(kr)
                teammates = [
                    r for r in self.robots
                    if r.team == kr.team and r.id != kr.id
                    and r.role != RobotRole.GOALKEEPER
                    and not r.is_incapacitated()
                ]
                if teammates:
                    # Target the nearest forward teammate
                    target = max(teammates, key=lambda r: r.x * attack_dir)
                    dx = target.x - self.ball.x
                    dy = target.y - self.ball.y
                    dist = np.sqrt(dx**2 + dy**2)
                    if dist > 0:
                        profile = self._get_profile_for(kr)
                        intended_angle = np.arctan2(dy, dx)
                        angle_error = np.random.normal(0, 0.06)
                        actual_angle = intended_angle + angle_error
                        pass_power = profile.pass_power + dist * 0.15
                        self.ball.vx = np.cos(actual_angle) * pass_power
                        self.ball.vy = np.sin(actual_angle) * pass_power
                        self.ball.spin = np.random.uniform(-0.2, 0.2)
                        self.last_touch_team = kr.team
                        if kr.team == 'blue':
                            self.total_passes_blue += 1
                        else:
                            self.total_passes_red += 1
                        if not self.headless:
                            print(f"  Kickoff pass: {kr.team} robot {kr.id} → robot {target.id}")
                self.kickoff_robot = None  # Done with kickoff
            return True
        return False

    # -----------------------------------------------------------------
    # ROBOT-TO-ROBOT COLLISION RESOLUTION
    # -----------------------------------------------------------------

    def _maybe_fall_from_collision(self, robot, overlap, min_dist):
        """Apply collision-induced fall with probability based on overlap severity."""
        if robot.is_incapacitated() or overlap < COLLISION_FALL_MIN_OVERLAP:
            return False

        severity = (overlap - COLLISION_FALL_MIN_OVERLAP) / max(1e-9, (min_dist - COLLISION_FALL_MIN_OVERLAP))
        severity = float(np.clip(severity, 0.0, 1.0))
        fall_prob = COLLISION_FALL_MAX_PROB * severity

        if np.random.random() < fall_prob:
            robot.set_state(RobotState.FALLEN)
            robot.recovery_time = robot.recovery_duration
            return True
        return False

    def _resolve_collisions(self):
        """Push apart any overlapping robots so they cannot occupy the same space."""
        min_dist = ROBOT_COLLISION_RADIUS * 2  # minimum centre-to-centre distance
        n = len(self.robots)
        for i in range(n):
            for j in range(i + 1, n):
                ra = self.robots[i]
                rb = self.robots[j]
                dx = rb.x - ra.x
                dy = rb.y - ra.y
                dist = np.sqrt(dx**2 + dy**2)
                if dist < min_dist and dist > 1e-6:
                    # Overlap — push each robot half the overlap distance apart
                    overlap = min_dist - dist
                    nx = dx / dist  # unit vector from a to b
                    ny = dy / dist
                    ra.x -= nx * overlap / 2
                    ra.y -= ny * overlap / 2
                    rb.x += nx * overlap / 2
                    rb.y += ny * overlap / 2
                elif dist <= 1e-6:
                    # Exactly on top of each other — nudge apart randomly
                    overlap = min_dist
                    angle = np.random.uniform(0, 2 * np.pi)
                    ra.x -= np.cos(angle) * min_dist / 2
                    ra.y -= np.sin(angle) * min_dist / 2
                    rb.x += np.cos(angle) * min_dist / 2
                    rb.y += np.sin(angle) * min_dist / 2
                # Clamp both to pitch boundaries
                for r in (ra, rb):
                    r.x = np.clip(r.x, -PITCH_LENGTH / 2 + 0.1, PITCH_LENGTH / 2 - 0.1)
                    r.y = np.clip(r.y, -PITCH_WIDTH / 2 + 0.1, PITCH_WIDTH / 2 - 0.1)

                # Collision consequence: overlap may knock players down
                if self.enable_falls and dist < min_dist:
                    self._maybe_fall_from_collision(ra, overlap, min_dist)
                    self._maybe_fall_from_collision(rb, overlap, min_dist)

    # -----------------------------------------------------------------
    # LAST TOUCH TRACKING
    # -----------------------------------------------------------------

    def _update_last_touch(self):
        """Track which team last touched the ball."""
        for robot in self.robots:
            if robot.is_incapacitated():
                continue
            dist = robot.get_distance_to({'x': self.ball.x, 'y': self.ball.y})
            if dist < 0.4:
                self.last_touch_team = robot.team

    # -----------------------------------------------------------------
    # ACTIONS
    # -----------------------------------------------------------------

    def apply_action(self, robot, action):
        """Execute the chosen action for a robot."""
        if action == 'incapacitated' or action == 'stay':
            return

        profile = self._get_profile_for(robot)
        attack_dir = self._get_attack_direction(robot)
        walk_speed = min(
            MAX_PLAYER_SPEED_M_PER_STEP,
            MAX_PLAYER_SPEED_M_PER_STEP * profile.dash_power_multiplier,
        )

        if action == 'turn_left':
            robot.heading += TURN_STEP_RAD
        elif action == 'turn_right':
            robot.heading -= TURN_STEP_RAD
        elif action == 'walk_forward':
            robot.x += walk_speed * np.cos(robot.heading)
            robot.y += walk_speed * np.sin(robot.heading)
            # Clamp to pitch
            robot.x = np.clip(robot.x, -PITCH_LENGTH / 2 + 0.1, PITCH_LENGTH / 2 - 0.1)
            robot.y = np.clip(robot.y, -PITCH_WIDTH / 2 + 0.1, PITCH_WIDTH / 2 - 0.1)

        elif action == 'kick':
            # Robot must be close to ball and approach from behind it
            ball_dist = robot.get_distance_to({'x': self.ball.x, 'y': self.ball.y})
            if ball_dist > 0.5:
                # Too far — move toward ball instead of kicking
                return

            # Position robot behind the ball (between ball and own goal)
            goal_x = (PITCH_LENGTH / 2) * attack_dir
            goal_y = 0.0
            dx_to_goal = goal_x - self.ball.x
            dy_to_goal = goal_y - self.ball.y
            dist_to_goal = np.sqrt(dx_to_goal**2 + dy_to_goal**2)

            if dist_to_goal > 0:
                # Snap robot slightly behind ball relative to the kick direction
                behind_offset = 0.25
                robot.x = self.ball.x - (dx_to_goal / dist_to_goal) * behind_offset
                robot.y = self.ball.y - (dy_to_goal / dist_to_goal) * behind_offset
                intended_angle = np.arctan2(dy_to_goal, dx_to_goal)

                # Enforce finite turn speed before shooting
                angle_diff = (intended_angle - robot.heading + np.pi) % (2 * np.pi) - np.pi
                if abs(angle_diff) > TURN_STEP_RAD:
                    robot.heading += np.sign(angle_diff) * TURN_STEP_RAD
                    return

                robot.heading = intended_angle
                angle_error = np.random.normal(0, profile.kick_accuracy + dist_to_goal * 0.02)
                actual_angle = intended_angle + angle_error

                power_variation = np.random.uniform(-0.3, 0.3)
                kick_power = profile.kick_power + power_variation

                self.ball.vx = np.cos(actual_angle) * kick_power + self.ball.vx * 0.3
                self.ball.vy = np.sin(actual_angle) * kick_power + self.ball.vy * 0.3
                self.ball.spin = np.random.uniform(-0.5, 0.5)

                # Cap speed
                max_speed = 3.5
                speed = np.sqrt(self.ball.vx**2 + self.ball.vy**2)
                if speed > max_speed:
                    self.ball.vx = (self.ball.vx / speed) * max_speed
                    self.ball.vy = (self.ball.vy / speed) * max_speed

                self.last_touch_team = robot.team

        elif action == 'pass':
            # Robot must be close to ball for a pass
            ball_dist = robot.get_distance_to({'x': self.ball.x, 'y': self.ball.y})
            if ball_dist > 0.5:
                return

            target = getattr(self, 'pass_target', None)
            if target is None:
                # Fallback: find nearest forward teammate
                teammates = [r for r in self.robots if r.team == robot.team and r.id != robot.id]
                target = None
                best_x = -999 * attack_dir
                for tm in teammates:
                    if tm.role == RobotRole.GOALKEEPER or tm.is_incapacitated():
                        continue
                    if (tm.x * attack_dir) > (best_x * attack_dir):
                        target = tm
                        best_x = tm.x

            if target:
                dx = target.x - self.ball.x
                dy = target.y - self.ball.y
                dist = np.sqrt(dx**2 + dy**2)
                if dist > 0:
                    # Position robot behind ball relative to pass direction
                    behind_offset = 0.2
                    robot.x = self.ball.x - (dx / dist) * behind_offset
                    robot.y = self.ball.y - (dy / dist) * behind_offset
                    intended_angle = np.arctan2(dy, dx)

                    # Enforce finite turn speed before passing
                    angle_diff = (intended_angle - robot.heading + np.pi) % (2 * np.pi) - np.pi
                    if abs(angle_diff) > TURN_STEP_RAD:
                        robot.heading += np.sign(angle_diff) * TURN_STEP_RAD
                        return

                    robot.heading = intended_angle
                    angle_error = np.random.normal(0, 0.08 + dist * 0.015)
                    actual_angle = intended_angle + angle_error

                    base_power = profile.pass_power + dist * 0.15
                    power_variation = np.random.uniform(-0.2, 0.2)
                    pass_power = base_power + power_variation

                    self.ball.vx = np.cos(actual_angle) * pass_power
                    self.ball.vy = np.sin(actual_angle) * pass_power
                    self.ball.spin = np.random.uniform(-0.3, 0.3)

                    if robot.team == 'blue':
                        self.total_passes_blue += 1
                    else:
                        self.total_passes_red += 1
                    self.last_touch_team = robot.team

    # -----------------------------------------------------------------
    # MAIN STEP
    # -----------------------------------------------------------------

    def step(self):
        """One simulation step."""
        # Check match over
        if self.time >= self.match_duration_steps:
            self.game_state = GameState.MATCH_OVER
            return

        # --- TRACKBACK STATE ---
        if self.game_state == GameState.TRACKBACK:
            self._update_trackback()
            self._resolve_collisions()
            self.time += 1
            return

        # --- SET PIECE STATES (KICKOFF, THROW_IN, GOAL_KICK, CORNER) ---
        if self.game_state in [GameState.KICKOFF, GameState.THROW_IN,
                                GameState.GOAL_KICK, GameState.CORNER_KICK]:
            self._update_set_piece()
            self.time += 1
            return

        # --- PLAYING STATE ---

        # HTSM update: evaluate tactics, drift alpha, generate profiles
        if self.adaptive:
            self._update_tactics()

        # Update falls
        if self.enable_falls:
            for robot in self.robots:
                robot.update_recovery()
                profile = self._get_profile_for(robot)
                robot.simulate_fall(profile)

        # Each robot decides and acts
        for robot in self.robots:
            if robot.is_incapacitated():
                continue

            profile = self._get_profile_for(robot)
            attack_dir = self._get_attack_direction(robot)
            action = decide_action_profiled(self, robot, profile, attack_dir)
            self.apply_action(robot, action)

        # Resolve robot-to-robot collisions after all movement
        self._resolve_collisions()

        # Update ball physics (no wall bounces — we handle out-of-bounds via set pieces)
        self.ball.update()

        # Track last touch
        self._update_last_touch()

        # Check for goals
        if self._check_goals():
            self.time += 1
            return

        # Check out of bounds → set pieces
        self._check_out_of_bounds()

        self.time += 1

    # -----------------------------------------------------------------
    # TACTICAL ENGINE INTEGRATION
    # -----------------------------------------------------------------

    def _update_tactics(self):
        """Update both teams' HTSM — evaluate switching rules, drift α."""
        time_remaining = max(0, self.match_duration - self.time * DT)

        # Ball recovery detection
        blue_recovered_own_half = (
            self.last_touch_team == 'blue'
            and self._prev_touch_team == 'red'
            and self.ball.x < 0
        )
        red_recovered_own_half = (
            self.last_touch_team == 'red'
            and self._prev_touch_team == 'blue'
            and self.ball.x > 0
        )
        self._prev_touch_team = self.last_touch_team

        blue_score_diff = self.blue_goals - self.red_goals
        red_score_diff = self.red_goals - self.blue_goals

        old_blue_tactic = self.blue_htsm.current_tactic
        old_red_tactic = self.red_htsm.current_tactic

        self.blue_htsm.update(
            step=self.time, score_diff=blue_score_diff,
            time_remaining=time_remaining,
            ball_zone='opp_half' if self.ball.x > 0 else 'own_half',
            possession_team=self.last_touch_team, own_team='blue',
            ball_recovered_own_half=blue_recovered_own_half,
        )
        self.red_htsm.update(
            step=self.time, score_diff=red_score_diff,
            time_remaining=time_remaining,
            ball_zone='opp_half' if self.ball.x < 0 else 'own_half',
            possession_team=self.last_touch_team, own_team='red',
            ball_recovered_own_half=red_recovered_own_half,
        )

        self.blue_profile = self.blue_htsm.get_profile()
        self.red_profile = self.red_htsm.get_profile()

        if self.blue_htsm.current_tactic != old_blue_tactic:
            self._add_event(f"BLUE → {self.blue_htsm.current_tactic.value}")
        if self.red_htsm.current_tactic != old_red_tactic:
            self._add_event(f"RED → {self.red_htsm.current_tactic.value}")

    # -----------------------------------------------------------------
    # MATCH RUNNER (HEADLESS)
    # -----------------------------------------------------------------

    def run_headless(self):
        """Run the full match without visualization. Returns match result dict."""
        while self.game_state != GameState.MATCH_OVER:
            self.step()

        return self.get_match_result()

    def get_match_result(self):
        """Get a summary dict of the match result."""
        elapsed = self.time * DT
        if self.blue_goals > self.red_goals:
            winner = 'blue'
        elif self.red_goals > self.blue_goals:
            winner = 'red'
        else:
            winner = 'draw'

        return {
            'blue_personality': self.blue_personality,
            'red_personality': self.red_personality,
            'blue_final_tactic': self.blue_htsm.current_tactic.value,
            'red_final_tactic': self.red_htsm.current_tactic.value,
            'blue_goals': self.blue_goals,
            'red_goals': self.red_goals,
            'winner': winner,
            'elapsed_seconds': elapsed,
            'total_steps': self.time,
            'total_passes_blue': self.total_passes_blue,
            'total_passes_red': self.total_passes_red,
            'blue_tactic_switches': len(self.blue_htsm.events),
            'red_tactic_switches': len(self.red_htsm.events),
        }

    def get_elapsed_time_str(self):
        """Get formatted elapsed time string."""
        seconds = self.time * DT
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"

    def get_remaining_time_str(self):
        """Get formatted remaining time string."""
        remaining = max(0, self.match_duration - self.time * DT)
        mins = int(remaining // 60)
        secs = int(remaining % 60)
        return f"{mins:02d}:{secs:02d}"


# =============================================================================
# VISUALIZER
# =============================================================================

class Visualizer:
    def __init__(self, simulator, frame_interval=10):
        self.sim = simulator
        self.frame_interval = frame_interval  # ms between frames (lower = faster)
        self.fig = plt.figure(figsize=(15, 9))

        # Main field
        self.ax_field = self.fig.add_axes([0.03, 0.08, 0.68, 0.88])

        # Status panel
        self.ax_status = self.fig.add_axes([0.73, 0.08, 0.25, 0.88])
        self.ax_status.axis('off')

        self.setup_field()

    def setup_field(self):
        self.ax_field.set_xlim(-PITCH_LENGTH / 2 - 1.0, PITCH_LENGTH / 2 + 1.0)
        self.ax_field.set_ylim(-PITCH_WIDTH / 2 - 0.8, PITCH_WIDTH / 2 + 0.8)
        self.ax_field.set_aspect('equal')

        # Pitch
        field = patches.Rectangle((-PITCH_LENGTH / 2, -PITCH_WIDTH / 2),
                                  PITCH_LENGTH, PITCH_WIDTH,
                                  linewidth=2, edgecolor='white',
                                  facecolor='#2d7a3a', alpha=0.85)
        self.ax_field.add_patch(field)

        # Centre line
        self.ax_field.plot([0, 0], [-PITCH_WIDTH / 2, PITCH_WIDTH / 2], 'w-', lw=2)

        # Centre circle
        cc = patches.Circle((0, 0), 0.75, lw=2, edgecolor='white', facecolor='none')
        self.ax_field.add_patch(cc)

        # Centre spot
        self.ax_field.plot(0, 0, 'wo', markersize=4)

        # Penalty areas
        for sign in [-1, 1]:
            pa_x = sign * (PITCH_LENGTH / 2) - (sign > 0) * PENALTY_AREA_LENGTH
            if sign < 0:
                pa_x = sign * PITCH_LENGTH / 2
            pa = patches.Rectangle(
                (sign * PITCH_LENGTH / 2 - (PENALTY_AREA_LENGTH if sign > 0 else 0),
                 -PENALTY_AREA_WIDTH / 2),
                PENALTY_AREA_LENGTH, PENALTY_AREA_WIDTH,
                lw=2, edgecolor='white', facecolor='none'
            )
            self.ax_field.add_patch(pa)

            # Goal areas
            ga = patches.Rectangle(
                (sign * PITCH_LENGTH / 2 - (GOAL_AREA_LENGTH if sign > 0 else 0),
                 -GOAL_AREA_WIDTH / 2),
                GOAL_AREA_LENGTH, GOAL_AREA_WIDTH,
                lw=1.5, edgecolor='white', facecolor='none'
            )
            self.ax_field.add_patch(ga)

        # Goals
        goal_left = patches.Rectangle((-PITCH_LENGTH / 2 - GOAL_DEPTH, -GOAL_WIDTH / 2),
                                      GOAL_DEPTH, GOAL_WIDTH,
                                      lw=2, edgecolor='white', facecolor='#333333', alpha=0.5)
        goal_right = patches.Rectangle((PITCH_LENGTH / 2, -GOAL_WIDTH / 2),
                                       GOAL_DEPTH, GOAL_WIDTH,
                                       lw=2, edgecolor='white', facecolor='#333333', alpha=0.5)
        self.ax_field.add_patch(goal_left)
        self.ax_field.add_patch(goal_right)

        self.ax_field.set_facecolor('#1a4d26')
        self.ax_field.set_xticks([])
        self.ax_field.set_yticks([])

    def draw_status_panel(self):
        self.ax_status.clear()
        self.ax_status.axis('off')
        self.ax_status.set_xlim(0, 1)
        self.ax_status.set_ylim(0, 1)
        sim = self.sim

        # Scoreboard
        self.ax_status.text(0.5, 0.98, 'SCOREBOARD', ha='center', va='top',
                            fontsize=12, fontweight='bold', color='white',
                            bbox=dict(boxstyle='round', facecolor='#333', edgecolor='white'))
        score_text = f"{sim.blue_goals}  -  {sim.red_goals}"
        self.ax_status.text(0.5, 0.92, score_text, ha='center', va='top',
                            fontsize=20, fontweight='bold', color='white')
        self.ax_status.text(0.15, 0.92, 'BLUE', ha='center', va='top',
                            fontsize=9, color='#3366FF', fontweight='bold')
        self.ax_status.text(0.85, 0.92, 'RED', ha='center', va='top',
                            fontsize=9, color='#FF3333', fontweight='bold')

        # Timer (countdown only)
        remain_str = sim.get_remaining_time_str()
        self.ax_status.text(0.5, 0.86, f"Remaining: {remain_str}",
                            ha='center', fontsize=9, color='#CCCCCC')

        # Game state
        gs_text = sim.game_state.value
        gs_color = '#00FF00' if sim.game_state == GameState.PLAYING else '#FFD700'
        self.ax_status.text(0.5, 0.82, gs_text, ha='center', fontsize=9,
                            fontweight='bold', color=gs_color)

        # Tactical info
        y = 0.77
        bt = sim.blue_htsm.current_tactic
        bt_color = TACTIC_COLORS.get(bt, '#FFFFFF')
        self.ax_status.text(0.5, y,
            f"BLUE ({sim.blue_personality.upper()})",
            ha='center', fontsize=8, color='#6699FF', fontweight='bold')
        y -= 0.03
        self.ax_status.text(0.5, y, f"{bt.value}",
            ha='center', fontsize=8, color=bt_color, fontfamily='monospace')
        y -= 0.025
        blue_form = compute_formation_label(sim.blue_robots, 1)
        self.ax_status.text(0.5, y, f"Formation: {blue_form}",
            ha='center', fontsize=7, color='#99AACC', fontfamily='monospace')

        y -= 0.035
        rt = sim.red_htsm.current_tactic
        rt_color = TACTIC_COLORS.get(rt, '#FFFFFF')
        self.ax_status.text(0.5, y,
            f"RED ({sim.red_personality.upper()})",
            ha='center', fontsize=8, color='#FF6666', fontweight='bold')
        y -= 0.03
        self.ax_status.text(0.5, y, f"{rt.value}",
            ha='center', fontsize=8, color=rt_color, fontfamily='monospace')
        y -= 0.025
        red_form = compute_formation_label(sim.red_robots, -1)
        self.ax_status.text(0.5, y, f"Formation: {red_form}",
            ha='center', fontsize=7, color='#CCAA99', fontfamily='monospace')

        # Possession
        y -= 0.035
        poss = sim.last_touch_team or '—'
        poss_color = '#3366FF' if poss == 'blue' else '#FF3333' if poss == 'red' else '#808080'
        self.ax_status.text(0.5, y, f"Possession: {poss.upper()}",
                            ha='center', fontsize=8, color=poss_color)

        # Robot states
        y -= 0.03
        self.ax_status.text(0.5, y, '─── BLUE ───', ha='center', fontsize=8, color='#3366FF')
        y -= 0.03
        for robot in sim.blue_robots:
            state_color = STATE_COLORS.get(robot.state, '#808080')
            info = f"R{robot.id} [{robot.role.value}] {STATE_ABBREV.get(robot.state, '?')}"
            self.ax_status.text(0.08, y, info, ha='left', fontsize=7,
                                color=state_color, fontfamily='monospace')
            y -= 0.028

        y -= 0.015
        self.ax_status.text(0.5, y, '─── RED ───', ha='center', fontsize=8, color='#FF3333')
        y -= 0.03
        for robot in sim.red_robots:
            state_color = STATE_COLORS.get(robot.state, '#808080')
            info = f"R{robot.id} [{robot.role.value}] {STATE_ABBREV.get(robot.state, '?')}"
            self.ax_status.text(0.08, y, info, ha='left', fontsize=7,
                                color=state_color, fontfamily='monospace')
            y -= 0.028

        # Stats
        y -= 0.02
        self.ax_status.text(0.5, y,
            f"Passes  B:{sim.total_passes_blue}  R:{sim.total_passes_red}",
            ha='center', fontsize=7, color='#AAAAAA', fontfamily='monospace')

        # Event log
        y -= 0.035
        self.ax_status.text(0.5, y, '─── EVENTS ───', ha='center', fontsize=7, color='#888888')
        y -= 0.025
        for msg in sim.event_log[:4]:
            self.ax_status.text(0.05, y, msg, ha='left', fontsize=6,
                                color='#AAAAAA', fontfamily='monospace')
            y -= 0.022

    def update(self, frame):
        self.ax_field.clear()
        self.setup_field()

        # Step simulation
        self.sim.step()

        # Draw robots — scaled to real dimensions: 311 mm × 275 mm
        ROBOT_LENGTH = 0.311   # metres (front-back)
        ROBOT_WIDTH  = 0.275   # metres (left-right)

        for robot in self.sim.robots:
            state_color = STATE_COLORS.get(robot.state, '#808080')

            # Robot body as a rotated rectangle centred on (robot.x, robot.y)
            rect = patches.Rectangle(
                (-ROBOT_LENGTH / 2, -ROBOT_WIDTH / 2),   # lower-left corner relative to centre
                ROBOT_LENGTH, ROBOT_WIDTH,
                linewidth=2.5,
                edgecolor=state_color,
                facecolor=robot.color,
                alpha=0.85 if not robot.is_incapacitated() else 0.4,
                zorder=3
            )
            # Rotate around robot centre then translate to world position
            t = (mtransforms.Affine2D()
                 .rotate(robot.heading)
                 .translate(robot.x, robot.y)
                 + self.ax_field.transData)
            rect.set_transform(t)
            self.ax_field.add_patch(rect)

            # Heading arrow (short, from centre toward front)
            dx = (ROBOT_LENGTH / 2 + 0.08) * np.cos(robot.heading)
            dy = (ROBOT_LENGTH / 2 + 0.08) * np.sin(robot.heading)
            self.ax_field.arrow(robot.x, robot.y, dx, dy,
                                head_width=0.09, head_length=0.07,
                                fc='white', ec='white', lw=0.5, zorder=4)

            # Player number
            self.ax_field.text(robot.x, robot.y, str(robot.id),
                               ha='center', va='center', color='white',
                               fontsize=7, fontweight='bold', zorder=5)


        # Draw ball — real diameter 14 cm → radius 0.07 m
        BALL_RADIUS = 0.07   # metres
        ball_speed = np.sqrt(self.sim.ball.vx**2 + self.sim.ball.vy**2)
        ball_alpha = min(1.0, 0.5 + ball_speed * 0.2)
        ball_patch = patches.Circle(
            (self.sim.ball.x, self.sim.ball.y), BALL_RADIUS,
            linewidth=1.5, edgecolor='black', facecolor='white',
            alpha=ball_alpha, zorder=6
        )
        self.ax_field.add_patch(ball_patch)

        # Ball velocity vector
        if ball_speed > 0.1:
            vel_scale = 0.4
            self.ax_field.arrow(self.sim.ball.x, self.sim.ball.y,
                                self.sim.ball.vx * vel_scale,
                                self.sim.ball.vy * vel_scale,
                                head_width=0.15, head_length=0.1,
                                fc='yellow', ec='orange', alpha=0.6, lw=1.5)

        # Score bar at top — countdown only
        remain_str = self.sim.get_remaining_time_str()
        score_text = (f"Blue {self.sim.blue_goals}  -  {self.sim.red_goals} Red   |   "
                      f"{remain_str}  |  "
                      f"{self.sim.game_state.value}")
        self.ax_field.text(0, PITCH_WIDTH / 2 + 0.5, score_text,
                           ha='center', fontsize=10, fontweight='bold', color='white')

        # Update status panel
        self.draw_status_panel()

        # Check match over
        if self.sim.game_state == GameState.MATCH_OVER:
            result = self.sim.get_match_result()
            winner_text = f"FULL TIME! {'BLUE WINS!' if result['winner'] == 'blue' else 'RED WINS!' if result['winner'] == 'red' else 'DRAW!'}"
            self.ax_field.text(0, 0, winner_text, ha='center', va='center',
                               fontsize=20, fontweight='bold', color='yellow',
                               bbox=dict(boxstyle='round,pad=0.5',
                                         facecolor='black', alpha=0.8))

        return []

    def run(self, save_gif=False, gif_filename=None):
        """
        Run the live animation — window opens immediately.

        If save_gif=True, the live match plays first in the window,
        then a second headless pass generates the GIF file afterward.
        This means the window ALWAYS appears immediately.
        """
        # --- Stash GIF settings for the post-match save ---
        self._save_gif = save_gif
        self._gif_filename = gif_filename
        self._gif_params = {
            'enable_falls': self.sim.enable_falls,
            'match_duration': self.sim.match_duration,
        }

        if save_gif:
            print("\n[GIF] Will save after live match ends (second headless pass).\n")

        max_frames = self.sim.match_duration_steps + 200
        anim = FuncAnimation(self.fig, self.update, frames=max_frames,
                             interval=self.frame_interval, blit=False, repeat=False)

        # === Live window opens immediately ===
        plt.show()

        # === After plt.show() returns (match over / window closed) ===
        if save_gif:
            self._save_gif_second_pass()

    def _save_gif_second_pass(self):
        """
        Run the simulator a second time (headless) and save as GIF.
        Skips frames (renders every 10th step) to avoid MemoryError.
        ~600 frames instead of 6000 for a 5-min match.
        """
        if self._gif_filename is None:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            blue = self.sim.blue_personality
            red = self.sim.red_personality
            self._gif_filename = f"sim3_{blue}_vs_{red}_{ts}.gif"

        output_dir = "animation_outputs"
        os.makedirs(output_dir, exist_ok=True)
        gif_path = os.path.join(output_dir, self._gif_filename)

        # Fresh simulator with same settings
        sim2 = SoccerSimulator(
            blue_personality=self.sim.blue_personality,
            red_personality=self.sim.red_personality,
            enable_falls=self._gif_params['enable_falls'],
            match_duration=self._gif_params['match_duration'],
            headless=True,
        )

        # Step skipping: render every Nth step to keep GIF manageable
        skip = 10  # Render every 10th frame → ~600 frames for 5 min
        total_steps = sim2.match_duration_steps + 200
        gif_frames = total_steps // skip

        print(f"\nGenerating GIF ({gif_frames} frames, skip={skip}x): {gif_path}")
        print("This may take 30-60 seconds...")

        # Smaller figure for GIF to save memory
        fig2, ax2 = plt.subplots(figsize=(10, 6))
        viz2 = Visualizer(sim2)
        viz2.fig = fig2
        viz2.ax_field = fig2.add_axes([0.03, 0.08, 0.94, 0.88])
        viz2.setup_field()

        def gif_update(frame_idx):
            """Step the sim multiple times, then render one frame."""
            for _ in range(skip):
                if sim2.game_state != GameState.MATCH_OVER:
                    sim2.step()
            return viz2.update(frame_idx)

        anim2 = FuncAnimation(fig2, gif_update, frames=gif_frames,
                              interval=100, blit=False, repeat=False)

        writer = PillowWriter(fps=10)
        anim2.save(gif_path, writer=writer, dpi=80)
        plt.close(fig2)

        size_mb = os.path.getsize(gif_path) / (1024 * 1024)
        print(f"Saved: {gif_path}  ({size_mb:.1f} MB)")


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 70)
    print("Soccer Simulation — Unified Tactical Architecture")
    print("=" * 70)

    # Personality selection
    print("\nSelect BLUE team personality:")
    print("  1. Aggressive (high-risk, early press, shoot-first)")
    print("  2. Conservative (low-risk, hold shape, pass-first)")
    blue_choice = input("Choice (1-2, default=1): ").strip()
    blue_name = 'conservative' if blue_choice == '2' else 'aggressive'

    print("\nSelect RED team personality:")
    print("  1. Aggressive")
    print("  2. Conservative")
    red_choice = input("Choice (1-2, default=2): ").strip()
    red_name = 'aggressive' if red_choice == '1' else 'conservative'

    # Match duration
    dur_input = input("\nMatch duration in seconds (default=300 for 5 min): ").strip()
    try:
        duration = int(dur_input) if dur_input else DEFAULT_MATCH_DURATION
    except ValueError:
        duration = DEFAULT_MATCH_DURATION

    # Falls
    fall_input = input("Enable fall simulation? (y/n, default=y): ").strip().lower()
    enable_falls = fall_input != 'n'

    # Frame rate
    print("\nFrame rate (ms between frames):")
    print("    10 = fast (default, ~6x real-time)")
    print("    50 = real-time (1 sim second ≈ 1 real second)")
    print("   100 = slow motion")
    fps_input = input("Frame interval in ms (default=10): ").strip()
    try:
        frame_interval = int(fps_input) if fps_input else 10
        frame_interval = max(1, frame_interval)
    except ValueError:
        frame_interval = 10

    # Save GIF
    save_input = input("Save as GIF? (y/n, default=n): ").strip().lower()
    save_gif = save_input == 'y'

    real_ratio = frame_interval / 50.0
    print(f"\n{'='*70}")
    print(f"  Blue: {blue_name.upper()} personality")
    print(f"  Red:  {red_name.upper()} personality")
    print(f"  Duration: {duration}s ({duration//60}m {duration%60}s)")
    print(f"  Falls: {'ON' if enable_falls else 'OFF'}")
    print(f"  Speed: {frame_interval}ms/frame ({real_ratio:.1f}x real-time)")
    print(f"  Dynamic tactics: ON (HTSM with hysteresis)")
    print(f"{'='*70}\n")

    sim = SoccerSimulator(
        blue_personality=blue_name,
        red_personality=red_name,
        enable_falls=enable_falls,
        match_duration=duration,
    )
    viz = Visualizer(sim, frame_interval=frame_interval)
    viz.run(save_gif=save_gif)


if __name__ == "__main__":
    # Support command-line args for headless/automated use
    if '--headless' in sys.argv:
        # Parse args
        blue = 'aggressive'
        red = 'conservative'
        duration = DEFAULT_MATCH_DURATION
        for i, arg in enumerate(sys.argv):
            if arg == '--blue' and i + 1 < len(sys.argv):
                blue = sys.argv[i + 1]
            elif arg == '--red' and i + 1 < len(sys.argv):
                red = sys.argv[i + 1]
            elif arg == '--duration' and i + 1 < len(sys.argv):
                duration = int(sys.argv[i + 1])

        sim = SoccerSimulator(blue_personality=blue, red_personality=red,
                              match_duration=duration, headless=True)
        result = sim.run_headless()
        print(json.dumps(result, indent=2))
    else:
        main()
