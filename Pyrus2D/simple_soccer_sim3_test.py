"""
Simple Soccer Simulation VERSION 3 — Aggressive vs Conservative
================================================================

UPDATED to match provided real-world-ish robot specs:

Walking:
- Max stable step frequency: 1.4 steps/s
- Max velocity: 0.12 m/s
- Average drift: ~0.8 cm per meter (@ max velocity)

Turning (with PID balance):
- Avg yaw speed: 0.424 rad/s
- Max yaw speed: 0.831 rad/s

Kicking:
- Kick distance: ~1.3 m (calibrated via ball friction model)

Recovery:
- From falling: ~26 s
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.animation import FuncAnimation, PillowWriter
from datetime import datetime
from enum import Enum
import os
import json
import sys

from behavior_profile import BehaviorProfile, BASELINE, AGGRESSIVE, CONSERVATIVE, get_profile
from decision_profiled import decide_action_profiled, _get_home_position

# =============================================================================
# CONSTANTS
# =============================================================================

PITCH_LENGTH = 9.0
PITCH_WIDTH = 6.0
GOAL_WIDTH = 2.6
GOAL_DEPTH = 0.6

# Penalty area (KidSize)
PENALTY_AREA_LENGTH = 2.0
PENALTY_AREA_WIDTH = 5.0

# Goal area (KidSize)
GOAL_AREA_LENGTH = 1.0
GOAL_AREA_WIDTH = 3.0

# Timing
DT = 0.05  # seconds per sim step (50ms)
DEFAULT_MATCH_DURATION = 300  # seconds

# Set piece constants
SET_PIECE_WAIT_STEPS = 30  # ~1.5s wait before set piece resumes

# =============================================================================
# "REAL WORLD" PARAMS 
# =============================================================================

# --- Walking model (step-based) ---
MAX_STEP_FREQUENCY = 1.4         # steps/s
MAX_WALK_VELOCITY = 0.12         # m/s (12 cm/s)
MAX_STEP_LENGTH = MAX_WALK_VELOCITY / MAX_STEP_FREQUENCY  # m per step (~0.0857 m)

# How many sim ticks per physical "step"
STEP_INTERVAL_TICKS = max(1, int(round((1.0 / MAX_STEP_FREQUENCY) / DT)))  # ~14

# Drift: RMS ~0.8 cm per meter traveled
DRIFT_STD_PER_M = 0.008  # meters drift per meter forward (RMS)

# --- Turning ---
AVG_YAW_SPEED = 0.424  # rad/s
MAX_YAW_SPEED = 0.831  # rad/s
TURN_STEP = MAX_YAW_SPEED * DT  # rad per sim tick (commanded turn uses max yaw capability)

# --- Geometry for collision separation ---
ROBOT_RADIUS = 0.18
BALL_RADIUS = 0.07
WALL_MARGIN = 0.01
ROBOT_CLAMP_MARGIN = ROBOT_RADIUS + WALL_MARGIN

# --- Ball physics ---
BALL_FRICTION = 0.92
BALL_MIN_VELOCITY = 0.05

# Kick distance calibration:
# Distance ≈ v0 * DT / (1 - friction)  -> v0 ≈ distance * (1 - f) / DT
KICK_DISTANCE_TARGET = 1.3
KICK_BASE_SPEED = KICK_DISTANCE_TARGET * (1.0 - BALL_FRICTION) / DT  # ~2.08 m/s

# Control / touch radius
CONTROL_DIST = 0.33
KICK_DIST = CONTROL_DIST
PASS_DIST = CONTROL_DIST
LAST_TOUCH_DIST = CONTROL_DIST

# Trackback
TRACKBACK_SPEED = MAX_WALK_VELOCITY * 1.2  # m/s, slightly faster jog home
TRACKBACK_THRESHOLD = 0.5

# Collision response tuning
ROBOT_ROBOT_ITERS = 2
BALL_ROBOT_PUSH_EPS = 1e-3
BALL_ROBOT_IMPULSE = 0.25
BALL_ROBOT_MAX_SPEED = 3.5

# Recovery (26s)
RECOVERY_SECONDS = 26.0
RECOVERY_DURATION_STEPS = int(round(RECOVERY_SECONDS / DT))  # ~520


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
    def __init__(self, x, y, team='blue', player_id=1, role=RobotRole.ATTACKER, profile=None):
        self.x = float(x)
        self.y = float(y)
        self.home_x = float(x)
        self.home_y = float(y)
        self.heading = 0.0 if team == 'blue' else np.pi

        self.team = team
        self.id = player_id
        self.role = role
        self.color = '#3366FF' if team == 'blue' else '#FF3333'
        self.profile = profile or BASELINE

        self.state = RobotState.IDLE
        self.previous_state = RobotState.IDLE
        self.state_duration = 0

        # Fall/recovery
        self.fall_probability = 0.002
        self.recovery_time = 0
        self.recovery_duration = RECOVERY_DURATION_STEPS  # UPDATED to ~26s

        # Step-based walking gate (physical step frequency limit)
        self.step_cooldown = 0  # ticks until next physical step allowed

        # Action timing (not central, keep)
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
        return float(np.hypot(target['x'] - self.x, target['y'] - self.y))

    def get_bearing_to(self, target):
        dx = target['x'] - self.x
        dy = target['y'] - self.y
        angle_to_target = np.arctan2(dy, dx)
        bearing = (angle_to_target - self.heading) % (2 * np.pi)
        if bearing > np.pi:
            bearing -= 2 * np.pi
        return float(bearing)

    def simulate_fall(self, profile):
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

    def tick_step_cooldown(self):
        if self.step_cooldown > 0:
            self.step_cooldown -= 1

    def try_step_forward(self, step_length_m):
        """
        Enforce max stable frequency: can only take a physical step every STEP_INTERVAL_TICKS.
        Returns True if a step was executed this tick.
        """
        if self.step_cooldown > 0:
            return False
        self.x += step_length_m * np.cos(self.heading)
        self.y += step_length_m * np.sin(self.heading)
        self.step_cooldown = STEP_INTERVAL_TICKS
        return True

    def move_toward(self, target_x, target_y, speed_mps):
        """Trackback uses continuous velocity; we still keep it physically plausible."""
        dx = target_x - self.x
        dy = target_y - self.y
        dist = float(np.hypot(dx, dy))
        if dist > 0.05:
            step = min(speed_mps * DT, dist)
            self.x += (dx / dist) * step
            self.y += (dy / dist) * step
            self.heading = float(np.arctan2(dy, dx))
            return False
        return True


# =============================================================================
# BALL CLASS
# =============================================================================

class Ball:
    def __init__(self, x=0.0, y=0.0):
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.friction = BALL_FRICTION
        self.min_velocity = BALL_MIN_VELOCITY
        self.spin = 0.0
        self.spin_decay = 0.95

    def update(self, dt=DT):
        speed = float(np.hypot(self.vx, self.vy))

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

        new_speed = float(np.hypot(self.vx, self.vy))
        if new_speed < self.min_velocity:
            self.vx = 0.0
            self.vy = 0.0
            self.spin = 0.0

    def stop(self):
        self.vx = 0.0
        self.vy = 0.0
        self.spin = 0.0

    def is_out_touchline(self):
        return abs(self.y) > PITCH_WIDTH / 2

    def is_out_goal_line_right(self):
        return self.x > PITCH_LENGTH / 2

    def is_out_goal_line_left(self):
        return self.x < -PITCH_LENGTH / 2

    def is_in_goal_right(self):
        return self.x > PITCH_LENGTH / 2 and abs(self.y) < GOAL_WIDTH / 2

    def is_in_goal_left(self):
        return self.x < -PITCH_LENGTH / 2 and abs(self.y) < GOAL_WIDTH / 2


# =============================================================================
# SOCCER SIMULATOR — WITH COLLISION SEPARATION
# =============================================================================

class SoccerSimulator:
    def __init__(self, blue_profile='baseline', red_profile='baseline',
                 enable_falls=True, match_duration=DEFAULT_MATCH_DURATION,
                 headless=False):
        self.headless = headless

        self.blue_profile = get_profile(blue_profile) if isinstance(blue_profile, str) else blue_profile
        self.red_profile = get_profile(red_profile) if isinstance(red_profile, str) else red_profile

        self.ball = Ball(0, 0)

        self.blue_robots = []
        self.red_robots = []
        self._create_teams()
        self.robots = self.blue_robots + self.red_robots

        self.time = 0
        self.match_duration = match_duration
        self.match_duration_steps = int(match_duration / DT)
        self.blue_goals = 0
        self.red_goals = 0
        self.enable_falls = enable_falls

        self.game_state = GameState.KICKOFF
        self.set_piece_timer = SET_PIECE_WAIT_STEPS
        self.kickoff_team = 'blue'
        self.set_piece_team = None
        self.last_touch_team = None

        self.total_passes_blue = 0
        self.total_passes_red = 0
        self.pass_target = None

    def _create_teams(self):
        blue_config = [
            (-3.5,  0.0, RobotRole.GOALKEEPER),
            (-2.0,  0.0, RobotRole.DEFENDER),
            (-0.5, -1.0, RobotRole.ATTACKER),
            (-0.5,  1.0, RobotRole.ATTACKER),
        ]
        for i, (x, y, role) in enumerate(blue_config):
            self.blue_robots.append(Robot(x, y, 'blue', i + 1, role, self.blue_profile))

        red_config = [
            ( 3.5,  0.0, RobotRole.GOALKEEPER),
            ( 2.0,  0.0, RobotRole.DEFENDER),
            ( 0.5, -1.0, RobotRole.ATTACKER),
            ( 0.5,  1.0, RobotRole.ATTACKER),
        ]
        for i, (x, y, role) in enumerate(red_config):
            r = Robot(x, y, 'red', i + 5, role, self.red_profile)
            r.heading = np.pi
            self.red_robots.append(r)

    def _get_profile_for(self, robot):
        return self.blue_profile if robot.team == 'blue' else self.red_profile

    def _get_attack_direction(self, robot):
        return 1 if robot.team == 'blue' else -1

    # -----------------------------------------------------------------
    # COLLISION / CLAMP
    # -----------------------------------------------------------------

    def _clamp_robot_in_field(self, robot):
        x_min = -PITCH_LENGTH/2 + ROBOT_CLAMP_MARGIN
        x_max =  PITCH_LENGTH/2 - ROBOT_CLAMP_MARGIN
        y_min = -PITCH_WIDTH/2  + ROBOT_CLAMP_MARGIN
        y_max =  PITCH_WIDTH/2  - ROBOT_CLAMP_MARGIN
        robot.x = float(np.clip(robot.x, x_min, x_max))
        robot.y = float(np.clip(robot.y, y_min, y_max))

    def _resolve_robot_robot_collisions(self, iters=ROBOT_ROBOT_ITERS):
        for _ in range(iters):
            for i in range(len(self.robots)):
                for j in range(i + 1, len(self.robots)):
                    a, b = self.robots[i], self.robots[j]
                    
                    # Option: slightly smaller radius when fallen to reduce jitter (tweakable)
                    ra = ROBOT_RADIUS * (0.90 if a.is_incapacitated() else 1.00)
                    rb = ROBOT_RADIUS * (0.90 if b.is_incapacitated() else 1.00)
                    min_dist = ra + rb
    
                    dx = b.x - a.x
                    dy = b.y - a.y
                    dist = float(np.hypot(dx, dy))
    
                    if dist < 1e-9:
                        nx, ny = np.random.uniform(-1, 1), np.random.uniform(-1, 1)
                        norm = float(np.hypot(nx, ny)) + 1e-9
                        nx, ny = nx / norm, ny / norm
                        dist = 0.0
                    else:
                        nx, ny = dx / dist, dy / dist
    
                    if dist < min_dist:
                        overlap = (min_dist - dist)
    
                        # Move split: if one is incapacitated, push it a bit more (acts like passive obstacle)
                        if a.is_incapacitated() and (not b.is_incapacitated()):
                            wa, wb = 0.70, 0.30
                        elif b.is_incapacitated() and (not a.is_incapacitated()):
                            wa, wb = 0.30, 0.70
                        else:
                            wa, wb = 0.50, 0.50
    
                        a.x -= nx * overlap * wa
                        a.y -= ny * overlap * wa
                        b.x += nx * overlap * wb
                        b.y += ny * overlap * wb
    
                        self._clamp_robot_in_field(a)
                        self._clamp_robot_in_field(b)

    def _resolve_ball_robot_collisions(self):
        """
        Ball should collide with ALL robots (upright or not).
        Otherwise fallen robots become 'ghosts' and the ball can overlap them.
        """
        for r in self.robots:
            # Keep ball collision volume active for fallen/recovering too
            rr = ROBOT_RADIUS * (0.90 if r.is_incapacitated() else 1.00)
            min_dist = rr + BALL_RADIUS
    
            dx = self.ball.x - r.x
            dy = self.ball.y - r.y
            dist = float(np.hypot(dx, dy))
    
            nx, ny = (1.0, 0.0) if dist < 1e-9 else (dx / dist, dy / dist)
    
            if dist < min_dist:
                push = (min_dist - dist) + BALL_ROBOT_PUSH_EPS
                self.ball.x += nx * push
                self.ball.y += ny * push
    
                self.ball.vx += nx * BALL_ROBOT_IMPULSE
                self.ball.vy += ny * BALL_ROBOT_IMPULSE
    
                sp = float(np.hypot(self.ball.vx, self.ball.vy))
                if sp > BALL_ROBOT_MAX_SPEED:
                    self.ball.vx = (self.ball.vx / sp) * BALL_ROBOT_MAX_SPEED
                    self.ball.vy = (self.ball.vy / sp) * BALL_ROBOT_MAX_SPEED

    # -----------------------------------------------------------------
    # GOAL DETECTION & TRACKBACK
    # -----------------------------------------------------------------

    def _check_goals(self):
        if self.ball.is_in_goal_right():
            self.blue_goals += 1
            self.last_touch_team = 'blue'
            if not self.headless:
                print(f"\n⚽ GOAL! Blue scores! (Blue {self.blue_goals} - {self.red_goals} Red)")
            self._start_trackback('red')
            return True
        if self.ball.is_in_goal_left():
            self.red_goals += 1
            self.last_touch_team = 'red'
            if not self.headless:
                print(f"\n⚽ GOAL! Red scores! (Blue {self.blue_goals} - {self.red_goals} Red)")
            self._start_trackback('blue')
            return True
        return False

    def _start_trackback(self, kickoff_team):
        self.game_state = GameState.TRACKBACK
        self.kickoff_team = kickoff_team
        self.ball.x, self.ball.y = 0.0, 0.0
        self.ball.stop()
        for robot in self.robots:
            robot.set_state(RobotState.TRACKBACK)

    def _update_trackback(self):
        all_home = True
        for robot in self.robots:
            arrived = robot.move_toward(robot.home_x, robot.home_y, TRACKBACK_SPEED)
            if not arrived:
                all_home = False
            self._clamp_robot_in_field(robot)

        self._resolve_robot_robot_collisions()

        if all_home:
            self.game_state = GameState.KICKOFF
            self.set_piece_timer = SET_PIECE_WAIT_STEPS
            for robot in self.robots:
                robot.set_state(RobotState.IDLE)
        return all_home

    # -----------------------------------------------------------------
    # SET PIECES
    # -----------------------------------------------------------------

    def _check_out_of_bounds(self):
        if self.ball.is_out_touchline():
            exit_x = self.ball.x
            exit_y = PITCH_WIDTH / 2 if self.ball.y > 0 else -PITCH_WIDTH / 2

            if self.last_touch_team == 'blue':
                self.set_piece_team = 'red'
            elif self.last_touch_team == 'red':
                self.set_piece_team = 'blue'
            else:
                self.set_piece_team = 'blue'

            self.ball.x = float(np.clip(exit_x, -PITCH_LENGTH / 2 + 0.5, PITCH_LENGTH / 2 - 0.5))
            self.ball.y = float(exit_y)
            self.ball.stop()

            self.game_state = GameState.THROW_IN
            self.set_piece_timer = SET_PIECE_WAIT_STEPS
            if not self.headless:
                print(f"  Throw-in for {self.set_piece_team} at ({self.ball.x:.1f}, {self.ball.y:.1f})")
            return True

        if self.ball.is_out_goal_line_right():
            if self.last_touch_team == 'blue':
                self.set_piece_team = 'red'
                self.ball.x = float(PITCH_LENGTH / 2 - 0.3)
                self.ball.y = float(PITCH_WIDTH / 2 if self.ball.y > 0 else -PITCH_WIDTH / 2)
                self.ball.stop()
                self.game_state = GameState.GOAL_KICK
                if not self.headless:
                    print("  Goal kick for Red")
            else:
                self.set_piece_team = 'blue'
                self.ball.x = float(PITCH_LENGTH / 2 - 0.1)
                self.ball.y = float(PITCH_WIDTH / 2 if self.ball.y > 0 else -PITCH_WIDTH / 2)
                self.ball.stop()
                self.game_state = GameState.CORNER_KICK
                if not self.headless:
                    print("  Corner kick for Blue")

            self.set_piece_timer = SET_PIECE_WAIT_STEPS
            return True

        if self.ball.is_out_goal_line_left():
            if self.last_touch_team == 'red':
                self.set_piece_team = 'blue'
                self.ball.x = float(-PITCH_LENGTH / 2 + 0.3)
                self.ball.y = float(PITCH_WIDTH / 2 if self.ball.y > 0 else -PITCH_WIDTH / 2)
                self.ball.stop()
                self.game_state = GameState.GOAL_KICK
                if not self.headless:
                    print("  Goal kick for Blue")
            else:
                self.set_piece_team = 'red'
                self.ball.x = float(-PITCH_LENGTH / 2 + 0.1)
                self.ball.y = float(PITCH_WIDTH / 2 if self.ball.y > 0 else -PITCH_WIDTH / 2)
                self.ball.stop()
                self.game_state = GameState.CORNER_KICK
                if not self.headless:
                    print("  Corner kick for Red")

            self.set_piece_timer = SET_PIECE_WAIT_STEPS
            return True

        return False

    def _update_set_piece(self):
        self.set_piece_timer -= 1
        if self.set_piece_timer <= 0:
            self.game_state = GameState.PLAYING
            return True
        return False

    # -----------------------------------------------------------------
    # LAST TOUCH
    # -----------------------------------------------------------------

    def _update_last_touch(self):
        for robot in self.robots:
            if robot.is_incapacitated():
                continue
            if robot.get_distance_to({'x': self.ball.x, 'y': self.ball.y}) < LAST_TOUCH_DIST:
                self.last_touch_team = robot.team

    # -----------------------------------------------------------------
    # ACTIONS
    # -----------------------------------------------------------------

    def apply_action(self, robot, action):
        if action in ('incapacitated', 'stay'):
            return

        profile = self._get_profile_for(robot)
        attack_dir = self._get_attack_direction(robot)

        # Decrement walking cooldown every tick so frequency limit is enforced globally
        robot.tick_step_cooldown()

        if action == 'turn_left':
            robot.heading += TURN_STEP
        elif action == 'turn_right':
            robot.heading -= TURN_STEP

        elif action == 'walk_forward':
            # Step-based walking: one physical step every STEP_INTERVAL_TICKS
            # Profile still modulates effective step length (but we keep it sane).
            step_len = MAX_STEP_LENGTH * float(profile.dash_power_multiplier)

            did_step = robot.try_step_forward(step_len)
            if did_step:
                # Drift: perpendicular noise proportional to distance traveled this step
                drift_std = DRIFT_STD_PER_M * abs(step_len)
                # Perpendicular unit vector
                px = -np.sin(robot.heading)
                py =  np.cos(robot.heading)
                drift = float(np.random.normal(0.0, drift_std))
                robot.x += px * drift
                robot.y += py * drift

            self._clamp_robot_in_field(robot)

        elif action == 'kick':
            ball_dist = robot.get_distance_to({'x': self.ball.x, 'y': self.ball.y})
            if ball_dist > KICK_DIST:
                return

            goal_x = (PITCH_LENGTH / 2) * attack_dir
            goal_y = 0.0
            dx_to_goal = goal_x - self.ball.x
            dy_to_goal = goal_y - self.ball.y
            dist_to_goal = float(np.hypot(dx_to_goal, dy_to_goal))
            if dist_to_goal < 1e-9:
                return

            # Place robot behind ball along kick direction (purely kinematic, like before)
            behind_offset = 0.25
            robot.x = self.ball.x - (dx_to_goal / dist_to_goal) * behind_offset
            robot.y = self.ball.y - (dy_to_goal / dist_to_goal) * behind_offset
            robot.heading = float(np.arctan2(dy_to_goal, dx_to_goal))
            self._clamp_robot_in_field(robot)

            intended_angle = float(np.arctan2(dy_to_goal, dx_to_goal))
            angle_error = float(np.random.normal(0, profile.kick_accuracy + dist_to_goal * 0.02))
            actual_angle = intended_angle + angle_error

            # Calibrated kick base speed so that (with friction) it travels ~1.3m on average
            # Keep profile differences by scaling relative to BASELINE.kick_power
            base = KICK_BASE_SPEED
            scale = 1.0
            try:
                scale = float(profile.kick_power) / max(1e-9, float(BASELINE.kick_power))
            except Exception:
                scale = 1.0

            power_variation = float(np.random.uniform(-0.10, 0.10) * base)  # small variability
            kick_speed = base * scale + power_variation

            self.ball.vx = float(np.cos(actual_angle) * kick_speed + self.ball.vx * 0.3)
            self.ball.vy = float(np.sin(actual_angle) * kick_speed + self.ball.vy * 0.3)
            self.ball.spin = float(np.random.uniform(-0.5, 0.5))

            # Cap speed (keep same cap as before)
            max_speed = 3.5
            speed = float(np.hypot(self.ball.vx, self.ball.vy))
            if speed > max_speed:
                self.ball.vx = (self.ball.vx / speed) * max_speed
                self.ball.vy = (self.ball.vy / speed) * max_speed

            self.last_touch_team = robot.team

        elif action == 'pass':
            ball_dist = robot.get_distance_to({'x': self.ball.x, 'y': self.ball.y})
            if ball_dist > PASS_DIST:
                return

            target = getattr(self, 'pass_target', None)
            if target is None:
                teammates = [r for r in self.robots if r.team == robot.team and r.id != robot.id]
                target = None
                best_x = -999 * attack_dir
                for tm in teammates:
                    if tm.role == RobotRole.GOALKEEPER or tm.is_incapacitated():
                        continue
                    if (tm.x * attack_dir) > (best_x * attack_dir):
                        target = tm
                        best_x = tm.x

            if target is None:
                return

            dx = target.x - self.ball.x
            dy = target.y - self.ball.y
            dist = float(np.hypot(dx, dy))
            if dist < 1e-9:
                return

            behind_offset = 0.2
            robot.x = self.ball.x - (dx / dist) * behind_offset
            robot.y = self.ball.y - (dy / dist) * behind_offset
            robot.heading = float(np.arctan2(dy, dx))
            self._clamp_robot_in_field(robot)

            intended_angle = float(np.arctan2(dy, dx))
            angle_error = float(np.random.normal(0, 0.08 + dist * 0.015))
            actual_angle = intended_angle + angle_error

            base_power = float(profile.pass_power + dist * 0.15)
            power_variation = float(np.random.uniform(-0.2, 0.2))
            pass_power = base_power + power_variation

            self.ball.vx = float(np.cos(actual_angle) * pass_power)
            self.ball.vy = float(np.sin(actual_angle) * pass_power)
            self.ball.spin = float(np.random.uniform(-0.3, 0.3))

            if robot.team == 'blue':
                self.total_passes_blue += 1
            else:
                self.total_passes_red += 1
            self.last_touch_team = robot.team

    # -----------------------------------------------------------------
    # MAIN STEP
    # -----------------------------------------------------------------

    def step(self):
        if self.time >= self.match_duration_steps:
            self.game_state = GameState.MATCH_OVER
            return

        if self.game_state == GameState.TRACKBACK:
            self._update_trackback()
            self.time += 1
            return

        if self.game_state in [GameState.KICKOFF, GameState.THROW_IN, GameState.GOAL_KICK, GameState.CORNER_KICK]:
            self._update_set_piece()
            self.time += 1
            return

        # PLAYING
        if self.enable_falls:
            for robot in self.robots:
                robot.update_recovery()
                profile = self._get_profile_for(robot)
                robot.simulate_fall(profile)

        # Decide + act
        for robot in self.robots:
            if robot.is_incapacitated():
                continue
            profile = self._get_profile_for(robot)
            attack_dir = self._get_attack_direction(robot)
            action = decide_action_profiled(self, robot, profile, attack_dir)
            self.apply_action(robot, action)

        # Clamp + collisions
        for r in self.robots:
            self._clamp_robot_in_field(r)

        self._resolve_robot_robot_collisions()
        self._resolve_ball_robot_collisions()

        # Ball update (dt aligned)
        self.ball.update(DT)

        # Last touch
        self._update_last_touch()

        # Goals
        if self._check_goals():
            self.time += 1
            return

        # Out-of-bounds → set piece
        self._check_out_of_bounds()

        self.time += 1

    # -----------------------------------------------------------------
    # RESULTS / TIME
    # -----------------------------------------------------------------

    def run_headless(self):
        while self.game_state != GameState.MATCH_OVER:
            self.step()
        return self.get_match_result()

    def get_match_result(self):
        elapsed = self.time * DT
        winner = 'draw'
        if self.blue_goals > self.red_goals:
            winner = 'blue'
        elif self.red_goals > self.blue_goals:
            winner = 'red'
        return {
            'blue_profile': self.blue_profile.name,
            'red_profile': self.red_profile.name,
            'blue_goals': self.blue_goals,
            'red_goals': self.red_goals,
            'winner': winner,
            'elapsed_seconds': elapsed,
            'total_steps': self.time,
            'total_passes_blue': self.total_passes_blue,
            'total_passes_red': self.total_passes_red,
        }

    def get_elapsed_time_str(self):
        seconds = self.time * DT
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"

    def get_remaining_time_str(self):
        remaining = max(0, self.match_duration - self.time * DT)
        mins = int(remaining // 60)
        secs = int(remaining % 60)
        return f"{mins:02d}:{secs:02d}"


# =============================================================================
# VISUALIZER
# =============================================================================

class Visualizer:
    def __init__(self, simulator):
        self.sim = simulator
        self.fig = plt.figure(figsize=(15, 9))
        self.ax_field = self.fig.add_axes([0.03, 0.08, 0.68, 0.88])
        self.ax_status = self.fig.add_axes([0.73, 0.08, 0.25, 0.88])
        self.ax_status.axis('off')
        self.setup_field()

    def setup_field(self):
        self.ax_field.set_xlim(-PITCH_LENGTH / 2 - 1.0, PITCH_LENGTH / 2 + 1.0)
        self.ax_field.set_ylim(-PITCH_WIDTH / 2 - 0.8, PITCH_WIDTH / 2 + 0.8)
        self.ax_field.set_aspect('equal')

        field = patches.Rectangle((-PITCH_LENGTH / 2, -PITCH_WIDTH / 2),
                                  PITCH_LENGTH, PITCH_WIDTH,
                                  linewidth=2, edgecolor='white',
                                  facecolor='#2d7a3a', alpha=0.85)
        self.ax_field.add_patch(field)

        self.ax_field.plot([0, 0], [-PITCH_WIDTH / 2, PITCH_WIDTH / 2], 'w-', lw=2)

        cc = patches.Circle((0, 0), 0.75, lw=2, edgecolor='white', facecolor='none')
        self.ax_field.add_patch(cc)
        self.ax_field.plot(0, 0, 'wo', markersize=4)

        for sign in [-1, 1]:
            pa = patches.Rectangle(
                (sign * PITCH_LENGTH / 2 - (PENALTY_AREA_LENGTH if sign > 0 else 0),
                 -PENALTY_AREA_WIDTH / 2),
                PENALTY_AREA_LENGTH, PENALTY_AREA_WIDTH,
                lw=2, edgecolor='white', facecolor='none'
            )
            self.ax_field.add_patch(pa)

            ga = patches.Rectangle(
                (sign * PITCH_LENGTH / 2 - (GOAL_AREA_LENGTH if sign > 0 else 0),
                 -GOAL_AREA_WIDTH / 2),
                GOAL_AREA_LENGTH, GOAL_AREA_WIDTH,
                lw=1.5, edgecolor='white', facecolor='none'
            )
            self.ax_field.add_patch(ga)

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

        self.ax_status.text(0.5, 0.97, 'SCOREBOARD', ha='center', va='top',
                            fontsize=13, fontweight='bold', color='white',
                            bbox=dict(boxstyle='round', facecolor='#333', edgecolor='white'))

        score_text = f"{self.sim.blue_goals}  -  {self.sim.red_goals}"
        self.ax_status.text(0.5, 0.91, score_text, ha='center', va='top',
                            fontsize=22, fontweight='bold', color='white')

        self.ax_status.text(0.15, 0.91, 'BLUE', ha='center', va='top',
                            fontsize=10, color='#3366FF', fontweight='bold')
        self.ax_status.text(0.85, 0.91, 'RED', ha='center', va='top',
                            fontsize=10, color='#FF3333', fontweight='bold')

        time_str = self.sim.get_elapsed_time_str()
        remain_str = self.sim.get_remaining_time_str()
        self.ax_status.text(0.5, 0.84, f"TIME: {time_str}  (rem: {remain_str})", ha='center',
                            fontsize=10, color='#CCCCCC')

        gs_text = self.sim.game_state.value
        gs_color = '#00FF00' if self.sim.game_state == GameState.PLAYING else '#FFD700'
        self.ax_status.text(0.5, 0.79, gs_text, ha='center', fontsize=10,
                            fontweight='bold', color=gs_color)

        self.ax_status.text(0.5, 0.74, f"Blue: {self.sim.blue_profile.name.upper()}", ha='center',
                            fontsize=9, color='#6699FF')
        self.ax_status.text(0.5, 0.70, f"Red: {self.sim.red_profile.name.upper()}", ha='center',
                            fontsize=9, color='#FF6666')

        y_pos = 0.63
        self.ax_status.text(0.5, y_pos, '─── BLUE TEAM ───', ha='center',
                            fontsize=9, color='#3366FF')
        y_pos -= 0.04
        for robot in self.sim.blue_robots:
            state_color = STATE_COLORS.get(robot.state, '#808080')
            info = f"R{robot.id} [{robot.role.value}] {STATE_ABBREV.get(robot.state, '?')}"
            self.ax_status.text(0.1, y_pos, info, ha='left', fontsize=8,
                                color=state_color, fontfamily='monospace')
            y_pos -= 0.035

        y_pos -= 0.02
        self.ax_status.text(0.5, y_pos, '─── RED TEAM ───', ha='center',
                            fontsize=9, color='#FF3333')
        y_pos -= 0.04
        for robot in self.sim.red_robots:
            state_color = STATE_COLORS.get(robot.state, '#808080')
            info = f"R{robot.id} [{robot.role.value}] {STATE_ABBREV.get(robot.state, '?')}"
            self.ax_status.text(0.1, y_pos, info, ha='left', fontsize=8,
                                color=state_color, fontfamily='monospace')
            y_pos -= 0.035

        y_pos -= 0.03
        self.ax_status.text(0.5, y_pos, f"Passes: B={self.sim.total_passes_blue}  R={self.sim.total_passes_red}",
                            ha='center', fontsize=9, color='#AAAAAA')

    def update(self, frame):
        self.ax_field.clear()
        self.setup_field()

        self.sim.step()

        for robot in self.sim.robots:
            state_color = STATE_COLORS.get(robot.state, '#808080')
            self.ax_field.plot(robot.x, robot.y, 'o', color=robot.color,
                               markersize=22, markeredgecolor=state_color,
                               markeredgewidth=3.0)

            dx = 0.35 * np.cos(robot.heading)
            dy = 0.35 * np.sin(robot.heading)
            self.ax_field.arrow(robot.x, robot.y, dx, dy,
                                head_width=0.12, head_length=0.08,
                                fc=robot.color, ec='white', lw=0.5)

            self.ax_field.text(robot.x, robot.y, str(robot.id),
                               ha='center', va='center', color='white',
                               fontsize=8, fontweight='bold')

            abbrev = STATE_ABBREV.get(robot.state, '?')
            self.ax_field.text(robot.x, robot.y + 0.4, abbrev,
                               ha='center', va='bottom', color=state_color,
                               fontsize=7, fontweight='bold',
                               bbox=dict(boxstyle='round,pad=0.1',
                                         facecolor='black', alpha=0.7))

        ball_speed = float(np.hypot(self.sim.ball.vx, self.sim.ball.vy))
        ball_alpha = min(1.0, 0.5 + ball_speed * 0.2)
        self.ax_field.plot(self.sim.ball.x, self.sim.ball.y, 'o',
                           color='white', markersize=10,
                           markeredgecolor='black', markeredgewidth=2, alpha=ball_alpha)

        if ball_speed > 0.1:
            vel_scale = 0.4
            self.ax_field.arrow(self.sim.ball.x, self.sim.ball.y,
                                self.sim.ball.vx * vel_scale,
                                self.sim.ball.vy * vel_scale,
                                head_width=0.15, head_length=0.1,
                                fc='yellow', ec='orange', alpha=0.6, lw=1.5)

        score_text = (f"BLUE ({self.sim.blue_profile.name.upper()}) "
                      f"{self.sim.blue_goals} - {self.sim.red_goals} "
                      f"({self.sim.red_profile.name.upper()}) RED  |  "
                      f"{self.sim.get_elapsed_time_str()} / {self.sim.get_remaining_time_str()}  |  "
                      f"{self.sim.game_state.value}")
        self.ax_field.text(0, PITCH_WIDTH / 2 + 0.5, score_text,
                           ha='center', fontsize=10, fontweight='bold', color='white')

        self.draw_status_panel()

        if self.sim.game_state == GameState.MATCH_OVER:
            result = self.sim.get_match_result()
            winner_text = (
                f"FULL TIME! "
                f"{'BLUE WINS!' if result['winner'] == 'blue' else 'RED WINS!' if result['winner'] == 'red' else 'DRAW!'}"
            )
            self.ax_field.text(0, 0, winner_text, ha='center', va='center',
                               fontsize=20, fontweight='bold', color='yellow',
                               bbox=dict(boxstyle='round,pad=0.5',
                                         facecolor='black', alpha=0.8))
        return []

    def run(self, save_gif=False, gif_filename=None):
        self._save_gif = save_gif
        self._gif_filename = gif_filename
        self._gif_params = {
            'blue_profile': self.sim.blue_profile,
            'red_profile': self.sim.red_profile,
            'enable_falls': self.sim.enable_falls,
            'match_duration': self.sim.match_duration,
        }

        if save_gif:
            print("\n[GIF] Will save after live match ends (second headless pass).\n")

        max_frames = self.sim.match_duration_steps + 200
        anim = FuncAnimation(self.fig, self.update, frames=max_frames,
                             interval=int(DT * 1000), blit=False, repeat=False)

        plt.show()

        if save_gif:
            self._save_gif_second_pass()

    def _save_gif_second_pass(self):
        if self._gif_filename is None:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            blue = self._gif_params['blue_profile'].name
            red = self._gif_params['red_profile'].name
            self._gif_filename = f"sim3_{blue}_vs_{red}_{ts}.gif"

        output_dir = "animation_outputs"
        os.makedirs(output_dir, exist_ok=True)
        gif_path = os.path.join(output_dir, self._gif_filename)

        sim2 = SoccerSimulator(
            blue_profile=self._gif_params['blue_profile'],
            red_profile=self._gif_params['red_profile'],
            enable_falls=self._gif_params['enable_falls'],
            match_duration=self._gif_params['match_duration'],
            headless=True,
        )

        skip = 10
        total_steps = sim2.match_duration_steps + 200
        gif_frames = total_steps // skip

        print(f"\nGenerating GIF ({gif_frames} frames, skip={skip}x): {gif_path}")

        fig2 = plt.figure(figsize=(10, 6))
        viz2 = Visualizer(sim2)
        viz2.fig = fig2
        viz2.ax_field = fig2.add_axes([0.03, 0.08, 0.94, 0.88])
        viz2.ax_status = fig2.add_axes([0.0, 0.0, 0.0, 0.0])  # hide status for gif
        viz2.ax_status.axis('off')
        viz2.setup_field()

        def gif_update(frame_idx):
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
    print("Soccer Simulation VERSION 3 — Aggressive vs Conservative")
    print("=" * 70)

    print("\nSelect BLUE team profile:")
    print("  1. Baseline (default behavior)")
    print("  2. Aggressive (shoot-first, push forward)")
    print("  3. Conservative (pass-first, stay deep)")
    blue_choice = input("Choice (1-3, default=1): ").strip()
    blue_profiles = {'1': 'baseline', '2': 'aggressive', '3': 'conservative'}
    blue_name = blue_profiles.get(blue_choice, 'baseline')

    print("\nSelect RED team profile:")
    print("  1. Baseline")
    print("  2. Aggressive")
    print("  3. Conservative")
    red_choice = input("Choice (1-3, default=1): ").strip()
    red_name = blue_profiles.get(red_choice, 'baseline')

    dur_input = input("\nMatch duration in seconds (default=300 for 5 min): ").strip()
    try:
        duration = int(dur_input) if dur_input else DEFAULT_MATCH_DURATION
    except ValueError:
        duration = DEFAULT_MATCH_DURATION

    fall_input = input("Enable fall simulation? (y/n, default=y): ").strip().lower()
    enable_falls = fall_input != 'n'

    save_input = input("Save as GIF? (y/n, default=n): ").strip().lower()
    save_gif = save_input == 'y'

    print(f"\n{'='*70}")
    print(f"  Blue: {blue_name.upper()} vs Red: {red_name.upper()}")
    print(f"  Duration: {duration}s ({duration//60}m {duration%60}s)")
    print(f"  Falls: {'ON' if enable_falls else 'OFF'}")
    print(f"  Walk: v_max={MAX_WALK_VELOCITY:.2f} m/s, f_max={MAX_STEP_FREQUENCY:.1f} steps/s, step={MAX_STEP_LENGTH*100:.1f} cm")
    print(f"  Turn: yaw_max={MAX_YAW_SPEED:.3f} rad/s")
    print(f"  Kick: target≈{KICK_DISTANCE_TARGET:.1f} m (base speed≈{KICK_BASE_SPEED:.2f} m/s)")
    print(f"  Recovery: ≈{RECOVERY_SECONDS:.0f} s")
    print(f"{'='*70}\n")

    sim = SoccerSimulator(
        blue_profile=blue_name,
        red_profile=red_name,
        enable_falls=enable_falls,
        match_duration=duration,
    )
    viz = Visualizer(sim)
    viz.run(save_gif=save_gif)


if __name__ == "__main__":
    if '--headless' in sys.argv:
        blue = 'baseline'
        red = 'baseline'
        duration = DEFAULT_MATCH_DURATION
        for i, arg in enumerate(sys.argv):
            if arg == '--blue' and i + 1 < len(sys.argv):
                blue = sys.argv[i + 1]
            elif arg == '--red' and i + 1 < len(sys.argv):
                red = sys.argv[i + 1]
            elif arg == '--duration' and i + 1 < len(sys.argv):
                duration = int(sys.argv[i + 1])

        sim = SoccerSimulator(blue_profile=blue, red_profile=red,
                              match_duration=duration, headless=True)
        result = sim.run_headless()
        print(json.dumps(result, indent=2))
    else:
        main()