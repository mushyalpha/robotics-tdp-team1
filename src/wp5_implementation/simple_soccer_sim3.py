"""
2D Soccer (Blue vs Red) — Rationalized Simulation Upgrades
----------------------------------------------------------
Relative to the very first static prototype, this version adds:
1) Walk-to-kickoff (no teleport) + kickoff legality checks
2) Kickoff cannot stall: safe back/side pass (fallback kick)
3) Explicit possession + protect frames
4) Roles per team: 1 GK, 2 DEF, 1 ATT + simple coordination
5) Goalie SAVE state after shots: opponents cannot steal during SAVE
6) Shot aiming varies inside goal mouth (not always center)
7) Deadlock breaker: POKE if ball is stuck near two opponents
8) Collision volumes: robot/ball radii + separation
9) Probabilistic fall + get-up animation (F/U labels)
10) Advantage pressing: if opponent is down near ball, more movers press

This patch fixes:
- Goalie decision branch indentation/returns (previously broken)
- Goalie passing: allow_back=True when GK passes
- Cleanup decide_action() flow (no unreachable code)
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.animation import FuncAnimation

# ---------------- Field ----------------
PITCH_LENGTH = 9.0
PITCH_WIDTH = 6.0
GOAL_WIDTH = 2.6

# ---------------- Kickoff rules (scaled) ----------------
CENTER_CIRCLE_RADIUS = 0.5
KICKOFF_OPP_MIN_DIST = 0.55
KICKER_MAX_DIST_TO_CENTER = 0.25
HALF_EPS = 0.02
BALL_MOVED_EPS = 0.08

# ---------------- Ball control / tackle ----------------
CONTROL_DIST = 0.33
PROTECT_FRAMES_ON_GAIN = 18
PROTECT_FRAMES_ON_RECEIVE = 12
TACKLE_COOLDOWN = 10
BASE_TACKLE_P = 0.18

# ---------------- Goalie save ----------------
GOALIE_SAVE_FRAMES = 16
GOALIE_REACH = 0.45
GOAL_AREA_X = 1.3

# ---------------- Motion ----------------
TURN_STEP = 0.15
WALK_STEP = 0.10
DRIBBLE_STEP = 0.06

# ---------------- Deadlock breaker ----------------
DEADLOCK_BALL_SPEED = 0.03
DEADLOCK_DIST = 0.22
DEADLOCK_FRAMES = 8
TURN_STUCK_FRAMES = 10

# ---------------- Collision volumes ----------------
ROBOT_RADIUS = 0.18
BALL_RADIUS = 0.07
WALL_MARGIN = 0.01

# ---------------- Fall / Get-up ----------------
FALL_MIN_OVERLAP = 0.035
FALL_P_BASE = 0.03
FALL_P_SCALE = 1.10
FALL_P_MAX = 0.35
FALL_FRAMES = 22
GETUP_FRAMES = 18

# ---------------- Goal banner ----------------
GOAL_BANNER_FRAMES = 40  # ~2 seconds at 50ms interval


class Robot:
    def __init__(self, x, y, team='blue', player_id=1, role='defender'):
        self.x = float(x)
        self.y = float(y)
        self.home_x = float(x)
        self.home_y = float(y)
        self.heading = 0.0
        self.team = team
        self.id = player_id
        self.role = role

        self.tackle_cd = 0
        self.stuck_turn_frames = 0

        # posture: upright / fallen / getting_up
        self.posture = 'upright'
        self.down_frames = 0
        self.up_frames = 0

    def is_upright(self):
        return self.posture == 'upright'

    def get_distance_to(self, target):
        return float(np.hypot(target['x'] - self.x, target['y'] - self.y))

    def get_bearing_to(self, target):
        dx = target['x'] - self.x
        dy = target['y'] - self.y
        ang = np.arctan2(dy, dx)
        bearing = (ang - self.heading) % (2 * np.pi)
        if bearing > np.pi:
            bearing -= 2 * np.pi
        return float(bearing)


class Ball:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.friction = 0.92
        self.min_velocity = 0.05

    def speed(self):
        return float(np.hypot(self.vx, self.vy))

    def update(self, dt=0.1):
        self.x += self.vx * dt
        self.y += self.vy * dt

        self.vx *= self.friction
        self.vy *= self.friction

        if self.speed() < self.min_velocity:
            self.vx = 0.0
            self.vy = 0.0

        # bounce + energy loss
        if self.x < -PITCH_LENGTH / 2:
            self.x = -PITCH_LENGTH / 2
            self.vx = -self.vx * 0.6
        elif self.x > PITCH_LENGTH / 2:
            self.x = PITCH_LENGTH / 2
            self.vx = -self.vx * 0.6

        if self.y < -PITCH_WIDTH / 2:
            self.y = -PITCH_WIDTH / 2
            self.vy = -self.vy * 0.6
        elif self.y > PITCH_WIDTH / 2:
            self.y = PITCH_WIDTH / 2
            self.vy = -self.vy * 0.6


class SoccerSimulator:
    def __init__(self):
        self.ball = Ball(0, 0)
        self.robots = []
        self.time = 0
        self.score = {'blue': 0, 'red': 0}

        # 1 GK, 2 DEF, 1 ATT per team
        blue_players = [
            (-3.6,  0.0, 'goalie'),
            (-2.8, -1.3, 'defender'),
            (-2.8,  1.3, 'defender'),
            ( 0.8,  0.0, 'attacker'),
        ]
        red_players = [
            ( 3.6,  0.0, 'goalie'),
            ( 2.8, -1.3, 'defender'),
            ( 2.8,  1.3, 'defender'),
            (-0.8,  0.0, 'attacker'),
        ]
        for i, (x, y, role) in enumerate(blue_players):
            self.robots.append(Robot(x, y, 'blue', i + 1, role=role))
        for i, (x, y, role) in enumerate(red_players):
            self.robots.append(Robot(x, y, 'red', i + 1, role=role))

        # possession
        self.pos_team = None
        self.pos_idx = None
        self.protect_frames = 0

        # goalie save
        self.save_team = None
        self.save_frames = 0

        # restart state machine: None / 'goal_pause' / 'kickoff'
        self.restart_mode = None

        # kickoff
        self.kickoff_team = None
        self.kickoff_targets = {}
        self.kickoff_ready = False
        self.kickoff_taken = False

        # goal banner
        self.goal_banner_frames = 0
        self.goal_banner_text = ""
        self.pending_kickoff_team = None

        # deadlock
        self.deadlock_frames = 0

        self.start_kickoff('blue')

    def nearest_opponent_to_point(self, team, x, y):
        dmin = 1e9
        for o in self.robots:
            if o.team == team:
                continue
            dmin = min(dmin, np.hypot(o.x - x, o.y - y))
        return float(dmin)

    # ---------- Global gates for fall/get-up ----------
    def fall_getup_enabled(self):
        if self.restart_mode == 'kickoff':
            return False
        if self.save_team is not None and self.save_frames > 0:
            return False
        return True

    # ---------- Helpers ----------
    def attack_dir(self, team):
        return 1.0 if team == 'blue' else -1.0

    def opponent_goal_x(self, team):
        return (PITCH_LENGTH / 2) * self.attack_dir(team)

    def our_goal_x(self, team):
        return -(PITCH_LENGTH / 2) * self.attack_dir(team)

    def in_own_half(self, r):
        return (r.x <= 0.0 + HALF_EPS) if r.team == 'blue' else (r.x >= 0.0 - HALF_EPS)

    def dist_to_center(self, r):
        return float(np.hypot(r.x, r.y))

    def kicker_idx(self, team):
        return next((i for i, r in enumerate(self.robots) if r.team == team and r.role == 'attacker'), None)

    def goalie_idx(self, team):
        return next((i for i, r in enumerate(self.robots) if r.team == team and r.role == 'goalie'), None)

    def in_goal_area(self, team, x):
        gx = self.our_goal_x(team)
        return (x < gx + GOAL_AREA_X) if team == 'blue' else (x > gx - GOAL_AREA_X)

    def go_to_point_action(self, r, tx, ty, stop_dist=0.15):
        dist = r.get_distance_to({'x': tx, 'y': ty})
        bearing = r.get_bearing_to({'x': tx, 'y': ty})
        if dist <= stop_dist:
            return 'stay'
        if abs(bearing) > 0.2:
            return 'turn_left' if bearing > 0 else 'turn_right'
        return 'walk_forward'

    def down_opponents_near_ball(self, team, radius=1.0):
        for r in self.robots:
            if r.team != team and r.posture != 'upright':
                if np.hypot(r.x - self.ball.x, r.y - self.ball.y) < radius:
                    return True
        return False

    # ---------- Collision handling ----------
    def clamp_robot_in_field(self, r):
        x_min = -PITCH_LENGTH/2 + ROBOT_RADIUS + WALL_MARGIN
        x_max =  PITCH_LENGTH/2 - ROBOT_RADIUS - WALL_MARGIN
        y_min = -PITCH_WIDTH/2  + ROBOT_RADIUS + WALL_MARGIN
        y_max =  PITCH_WIDTH/2  - ROBOT_RADIUS - WALL_MARGIN
        r.x = float(np.clip(r.x, x_min, x_max))
        r.y = float(np.clip(r.y, y_min, y_max))

    def set_fallen(self, r):
        if not self.fall_getup_enabled():
            return

        if self.pos_idx is not None and self.robots[self.pos_idx] is r:
            self.pos_team = None
            self.pos_idx = None
            self.protect_frames = 0
            ang = np.random.uniform(-np.pi, np.pi)
            self.ball.vx = 0.4 * np.cos(ang)
            self.ball.vy = 0.4 * np.sin(ang)

        r.posture = 'fallen'
        r.down_frames = FALL_FRAMES
        r.up_frames = 0
        r.tackle_cd = max(r.tackle_cd, TACKLE_COOLDOWN)

    def maybe_fall_from_overlap(self, a, b, overlap):
        if not self.fall_getup_enabled():
            return
        if (not a.is_upright()) or (not b.is_upright()):
            return
        if overlap < FALL_MIN_OVERLAP:
            return

        p = FALL_P_BASE + FALL_P_SCALE * (overlap / (2 * ROBOT_RADIUS))
        p = float(np.clip(p, 0.0, FALL_P_MAX))
        if np.random.rand() > p:
            return

        weights = []
        for r in (a, b):
            w = 1.0
            if r.role == 'attacker':
                w *= 1.15
            if r.role == 'goalie':
                w *= 0.85
            weights.append(w)
        probs = np.array(weights) / (np.sum(weights) + 1e-9)
        fallen = a if np.random.rand() < probs[0] else b
        self.set_fallen(fallen)

    def resolve_robot_robot_collisions(self, iters=2):
        for _ in range(iters):
            for i in range(len(self.robots)):
                for j in range(i + 1, len(self.robots)):
                    a, b = self.robots[i], self.robots[j]
                    dx = b.x - a.x
                    dy = b.y - a.y
                    dist = float(np.hypot(dx, dy))
                    min_dist = 2 * ROBOT_RADIUS

                    if dist < 1e-9:
                        nx, ny = np.random.uniform(-1, 1), np.random.uniform(-1, 1)
                        norm = float(np.hypot(nx, ny)) + 1e-9
                        nx, ny = nx / norm, ny / norm
                        dist = 0.0
                    else:
                        nx, ny = dx / dist, dy / dist

                    if dist < min_dist:
                        overlap = (min_dist - dist)
                        self.maybe_fall_from_overlap(a, b, overlap)

                        a.x -= nx * overlap * 0.5
                        a.y -= ny * overlap * 0.5
                        b.x += nx * overlap * 0.5
                        b.y += ny * overlap * 0.5

                        self.clamp_robot_in_field(a)
                        self.clamp_robot_in_field(b)

    def resolve_ball_robot_collisions(self):
        if self.pos_idx is not None:
            return
        for r in self.robots:
            dx = self.ball.x - r.x
            dy = self.ball.y - r.y
            dist = float(np.hypot(dx, dy))
            min_dist = ROBOT_RADIUS + BALL_RADIUS

            if dist < 1e-9:
                nx, ny = 1.0, 0.0
            else:
                nx, ny = dx / dist, dy / dist

            if dist < min_dist:
                push = (min_dist - dist) + 1e-3
                self.ball.x += nx * push
                self.ball.y += ny * push
                self.ball.vx += nx * 0.25
                self.ball.vy += ny * 0.25

    # ---------- Posture update ----------
    def update_postures(self):
        if not self.fall_getup_enabled():
            return

        for r in self.robots:
            if r.posture == 'fallen':
                r.down_frames -= 1
                if r.down_frames <= 0:
                    r.posture = 'getting_up'
                    r.up_frames = GETUP_FRAMES
            elif r.posture == 'getting_up':
                r.up_frames -= 1
                if r.up_frames <= 0:
                    r.posture = 'upright'
                    r.stuck_turn_frames = 0

    # ---------- Passing / shooting ----------
    def nearest_opponent_dist(self, r):
        dmin = 1e9
        for o in self.robots:
            if o.team != r.team:
                dmin = min(dmin, np.hypot(o.x - r.x, o.y - r.y))
        return float(dmin)

    def best_pass_target(self, r, allow_back=False):
        d = self.attack_dir(r.team)
        best, best_score = None, -1e9
        for tm in self.robots:
            if tm.team != r.team or tm.role == 'goalie' or tm is r:
                continue
            if not tm.is_upright():
                continue

            progress = (tm.x - r.x) * d
            if (not allow_back) and progress < 0.2:
                continue

            opp_clear = self.nearest_opponent_dist(tm)
            dist_rt = np.hypot(tm.x - r.x, tm.y - r.y)
            score = 1.2 * progress + 0.7 * opp_clear - 0.25 * dist_rt
            if allow_back:
                score += 0.6 * (1.0 / (0.2 + dist_rt))

            if score > best_score:
                best_score, best = score, tm
        return best

    def choose_shot_target_y(self, shooter_team):
        gk_i = self.goalie_idx('red' if shooter_team == 'blue' else 'blue')
        gk_y = self.robots[gk_i].y if gk_i is not None else 0.0
        prefer = -np.sign(gk_y) * (GOAL_WIDTH * 0.30)
        noise = np.random.uniform(-0.25, 0.25)
        y = prefer + noise
        margin = 0.15
        return float(np.clip(y, -GOAL_WIDTH/2 + margin, GOAL_WIDTH/2 - margin))

    # ---------- SAVE / possession ----------
    def trigger_goalie_save(self, defending_team):
        self.save_team = defending_team
        self.save_frames = GOALIE_SAVE_FRAMES

    def update_goalie_save(self):
        if self.save_team is None or self.save_frames <= 0:
            self.save_team = None
            self.save_frames = 0
            return

        gk_i = self.goalie_idx(self.save_team)
        if gk_i is None:
            self.save_team = None
            self.save_frames = 0
            return

        gk = self.robots[gk_i]
        if not gk.is_upright():
            self.save_team = None
            self.save_frames = 0
            return

        gk_target_y = float(np.clip(self.ball.y, -GOAL_WIDTH / 2, GOAL_WIDTH / 2))
        act = self.go_to_point_action(gk, gk.home_x, gk_target_y, stop_dist=0.10)
        self.apply_action(gk, act)

        if np.hypot(self.ball.x - gk.x, self.ball.y - gk.y) < GOALIE_REACH:
            self.ball.vx = 0.0
            self.ball.vy = 0.0
            self.pos_team = gk.team
            self.pos_idx = gk_i
            self.protect_frames = max(self.protect_frames, PROTECT_FRAMES_ON_GAIN)
            self.attach_ball_if_possessed()
            self.save_team = None
            self.save_frames = 0
            return

        self.save_frames -= 1
        if self.save_frames <= 0:
            self.save_team = None

    def attach_ball_if_possessed(self):
        if self.pos_idx is None:
            return
        p = self.robots[self.pos_idx]
        if not p.is_upright():
            self.pos_team = None
            self.pos_idx = None
            self.protect_frames = 0
            return

        if self.save_team is not None and self.save_frames > 0:
            if p.role != 'goalie':
                return

        offset = ROBOT_RADIUS + BALL_RADIUS + 0.02
        self.ball.x = p.x + offset * np.cos(p.heading)
        self.ball.y = p.y + offset * np.sin(p.heading)
        self.ball.vx = 0.0
        self.ball.vy = 0.0

    def try_gain_or_tackle(self):
        if self.save_team is not None and self.save_frames > 0:
            return
        if self.pos_idx is not None and self.protect_frames > 0:
            return

        dists = [np.hypot(r.x - self.ball.x, r.y - self.ball.y) for r in self.robots]
        i = int(np.argmin(dists))
        r = self.robots[i]
        d = float(dists[i])

        if (not r.is_upright()) or d > CONTROL_DIST:
            return

        if self.pos_team == r.team and self.pos_idx is not None and self.pos_idx != i:
            return

        if self.pos_team is not None and self.pos_team != r.team and self.pos_idx is not None:
            if r.tackle_cd > 0:
                return

            opp = self.robots[self.pos_idx]
            if not opp.is_upright():
                self.pos_team = r.team
                self.pos_idx = i
                self.protect_frames = PROTECT_FRAMES_ON_GAIN
                r.tackle_cd = TACKLE_COOLDOWN
                return

            p = BASE_TACKLE_P
            p += 0.08 if not self.in_goal_area(opp.team, opp.x) else -0.05
            p = float(np.clip(p, 0.05, 0.35))
            if np.random.rand() < p:
                self.pos_team = r.team
                self.pos_idx = i
                self.protect_frames = PROTECT_FRAMES_ON_GAIN
                r.tackle_cd = TACKLE_COOLDOWN
            return

        self.pos_team = r.team
        self.pos_idx = i
        self.protect_frames = PROTECT_FRAMES_ON_RECEIVE

    # ---------- Actions ----------
    def apply_action(self, r, action):
        if not r.is_upright() or action is None:
            return

        if action == 'turn_left':
            r.heading += TURN_STEP
        elif action == 'turn_right':
            r.heading -= TURN_STEP
        elif action == 'walk_forward':
            r.x += WALK_STEP * np.cos(r.heading)
            r.y += WALK_STEP * np.sin(r.heading)
        elif action == 'dribble_left':
            r.heading += TURN_STEP
            r.x += DRIBBLE_STEP * np.cos(r.heading)
            r.y += DRIBBLE_STEP * np.sin(r.heading)
        elif action == 'dribble_right':
            r.heading -= TURN_STEP
            r.x += DRIBBLE_STEP * np.cos(r.heading)
            r.y += DRIBBLE_STEP * np.sin(r.heading)
        elif action == 'poke':
            power = 1.2
            self.ball.vx = power * np.cos(r.heading)
            self.ball.vy = power * np.sin(r.heading)
            self.pos_team = None
            self.pos_idx = None
            self.protect_frames = 0
        elif action == 'kick':
            goal_x = self.opponent_goal_x(r.team)
            goal_y = self.choose_shot_target_y(r.team)
            dx = goal_x - self.ball.x
            dy = goal_y - self.ball.y
            dist = float(np.hypot(dx, dy))
            if dist > 1e-6:
                power = 2.1
                self.ball.vx = (dx / dist) * power
                self.ball.vy = (dy / dist) * power
                self.trigger_goalie_save(defending_team=('red' if r.team == 'blue' else 'blue'))
                self.pos_team = None
                self.pos_idx = None
                self.protect_frames = 0
        elif action == 'pass':
            allow_back = (r.role == 'goalie')  # FIX: goalie can pass sideways/back
            tm = self.best_pass_target(r, allow_back=allow_back)
            if tm is None:
                return
            dx = tm.x - self.ball.x
            dy = tm.y - self.ball.y
            dist = float(np.hypot(dx, dy))
            if dist > 1e-6:
                power = 1.6
                self.ball.vx = (dx / dist) * power
                self.ball.vy = (dy / dist) * power
                self.pos_team = None
                self.pos_idx = None
                self.protect_frames = 0

    # ---------- Team coordination ----------
    def support_target(self, r):
        d = self.attack_dir(r.team)
        if r.role == 'attacker':
            y = 1.2 if r.team == 'blue' else -1.2
            return (0.9 * d, y)
        if r.role == 'defender':
            base_x = -2.4 * d
            base_y = -1.2 if r.id == 2 else 1.2
            return (base_x, base_y)
        return (r.home_x, r.home_y)

    def decide_action(self, i, r):
        if not r.is_upright():
            return None

        # Advantage pressing (non-goalies)
        if self.down_opponents_near_ball(r.team, radius=0.9) and r.role != 'goalie':
            dist = r.get_distance_to({'x': self.ball.x, 'y': self.ball.y})
            bearing = r.get_bearing_to({'x': self.ball.x, 'y': self.ball.y})
            if dist <= CONTROL_DIST:
                if abs(bearing) > 0.25:
                    return 'turn_left' if bearing > 0 else 'turn_right'
                return 'walk_forward'
            if abs(bearing) > 0.25:
                return 'turn_left' if bearing > 0 else 'turn_right'
            return 'walk_forward'

        # If teammate possesses: support (including defenders/attacker)
        if self.pos_team == r.team and self.pos_idx is not None and self.pos_idx != i and r.role != 'goalie':
            tx, ty = self.support_target(r)
            return self.go_to_point_action(r, tx, ty, stop_dist=0.25)

        # If I possess the ball (all roles, including goalie)
        if self.pos_idx == i:
            if r.role == 'goalie':
                opp_close = self.nearest_opponent_to_point(r.team, r.x, r.y)
                if opp_close < 0.9:
                    return 'kick'
                tm = self.best_pass_target(r, allow_back=True)
                if tm is not None:
                    tm_opp = self.nearest_opponent_to_point(r.team, tm.x, tm.y)
                    if tm_opp > 0.7:
                        return 'pass'
                return 'kick'

            goal_x = self.opponent_goal_x(r.team)
            dist_to_goal = float(np.hypot(goal_x - r.x, r.y))
            opp_close = self.nearest_opponent_dist(r)

            if dist_to_goal < 3.2 and (opp_close < 0.9 or r.role == 'attacker'):
                return 'kick'

            tm = self.best_pass_target(r, allow_back=False)
            if tm is not None and opp_close < 1.2:
                return 'pass'

            forward_target = {'x': r.x + 1.0 * self.attack_dir(r.team), 'y': r.y}
            bearing = r.get_bearing_to(forward_target)
            if abs(bearing) > 0.25:
                return 'dribble_left' if bearing > 0 else 'dribble_right'
            return 'walk_forward'

        # Not possessing: goalie tracks ball (SAVE handled elsewhere)
        if r.role == 'goalie':
            gy = float(np.clip(self.ball.y, -GOAL_WIDTH / 2, GOAL_WIDTH / 2))
            return self.go_to_point_action(r, r.home_x, gy, stop_dist=0.12)

        # Not possessing: field players chase or hold shape
        dist = r.get_distance_to({'x': self.ball.x, 'y': self.ball.y})
        bearing = r.get_bearing_to({'x': self.ball.x, 'y': self.ball.y})

        if r.role == 'defender':
            in_our_half = (self.ball.x < 0) if r.team == 'blue' else (self.ball.x > 0)
            if (not in_our_half) and dist > 1.0:
                tx, ty = self.support_target(r)
                return self.go_to_point_action(r, tx, ty, stop_dist=0.25)

        if dist <= CONTROL_DIST:
            if abs(bearing) > 0.25:
                r.stuck_turn_frames += 1
                if r.stuck_turn_frames >= TURN_STUCK_FRAMES:
                    r.stuck_turn_frames = 0
                    return 'poke'
                return 'turn_left' if bearing > 0 else 'turn_right'
            r.stuck_turn_frames = 0
            return 'walk_forward'

        if abs(bearing) > 0.25:
            return 'turn_left' if bearing > 0 else 'turn_right'
        return 'walk_forward'

    # ---------- Kickoff / goal pause ----------
    def reset_all_postures(self):
        for r in self.robots:
            r.posture = 'upright'
            r.down_frames = 0
            r.up_frames = 0
            r.stuck_turn_frames = 0

    def start_goal_pause(self, scoring_team, kickoff_team_after):
        self.restart_mode = 'goal_pause'
        self.goal_banner_frames = GOAL_BANNER_FRAMES
        self.goal_banner_text = f"GOAL!  {scoring_team.upper()} SCORES!"
        self.pending_kickoff_team = kickoff_team_after

        self.ball.x, self.ball.y = 0.0, 0.0
        self.ball.vx, self.ball.vy = 0.0, 0.0

        self.pos_team = None
        self.pos_idx = None
        self.protect_frames = 0
        self.save_team = None
        self.save_frames = 0
        self.deadlock_frames = 0

    def start_kickoff(self, team):
        self.restart_mode = 'kickoff'
        self.kickoff_team = team
        self.kickoff_ready = False
        self.kickoff_taken = False
        self.kickoff_targets = {}

        self.ball = Ball(0.0, 0.0)
        self.pos_team = None
        self.pos_idx = None
        self.protect_frames = 0
        self.save_team = None
        self.save_frames = 0
        self.deadlock_frames = 0

        self.reset_all_postures()

        for i, r in enumerate(self.robots):
            if r.team == 'blue':
                if r.role == 'goalie':
                    tx, ty = (-3.6, 0.0)
                elif r.role == 'defender':
                    tx, ty = (-2.8, -1.3 if r.id == 2 else 1.3)
                else:
                    tx, ty = (-0.2, 0.0) if team == 'blue' else (-1.2, 0.0)
                r.heading = 0.0
            else:
                if r.role == 'goalie':
                    tx, ty = (3.6, 0.0)
                elif r.role == 'defender':
                    tx, ty = (2.8, -1.3 if r.id == 2 else 1.3)
                else:
                    tx, ty = (0.2, 0.0) if team == 'red' else (1.2, 0.0)
                r.heading = np.pi

            if r.team == team and r.role == 'attacker':
                r.heading = 0.0 if team == 'blue' else np.pi

            self.kickoff_targets[i] = (tx, ty)

    def kickoff_constraints_ok(self):
        if np.hypot(self.ball.x, self.ball.y) > 1e-6:
            return False
        if self.ball.speed() > 1e-6:
            return False

        kicker_i = self.kicker_idx(self.kickoff_team)
        if kicker_i is None:
            return False
        if self.dist_to_center(self.robots[kicker_i]) > KICKER_MAX_DIST_TO_CENTER:
            return False

        for r in self.robots:
            if not self.in_own_half(r):
                return False
            if r.team != self.kickoff_team:
                if self.dist_to_center(r) < KICKOFF_OPP_MIN_DIST:
                    return False
        return True

    def kickoff_step(self):
        all_arrived = True
        for i, r in enumerate(self.robots):
            tx, ty = self.kickoff_targets[i]
            act = self.go_to_point_action(r, tx, ty, stop_dist=0.12)
            if act != 'stay':
                all_arrived = False
            self.apply_action(r, act)

        for r in self.robots:
            self.clamp_robot_in_field(r)
        self.resolve_robot_robot_collisions(iters=2)

        self.ball.x, self.ball.y = 0.0, 0.0
        self.ball.vx, self.ball.vy = 0.0, 0.0

        if all_arrived and self.kickoff_constraints_ok():
            self.kickoff_ready = True

        if self.kickoff_ready and not self.kickoff_taken:
            kicker_i = self.kicker_idx(self.kickoff_team)
            kicker = self.robots[kicker_i]

            self.pos_team = kicker.team
            self.pos_idx = kicker_i
            self.protect_frames = PROTECT_FRAMES_ON_GAIN
            self.attach_ball_if_possessed()

            tm = self.best_pass_target(kicker, allow_back=True)
            if tm is not None:
                dx = tm.x - self.ball.x
                dy = tm.y - self.ball.y
                dist = float(np.hypot(dx, dy))
                if dist > 1e-6:
                    power = 1.4
                    self.ball.vx = (dx / dist) * power
                    self.ball.vy = (dy / dist) * power
                    self.pos_team = None
                    self.pos_idx = None
                    self.protect_frames = 0
                else:
                    self.apply_action(kicker, 'kick')
            else:
                self.apply_action(kicker, 'kick')

            self.kickoff_taken = True

        if self.kickoff_taken and self.ball.speed() > BALL_MOVED_EPS:
            self.restart_mode = None
            self.kickoff_team = None
            self.kickoff_ready = False
            self.kickoff_taken = False
            self.kickoff_targets = {}

    # ---------- Deadlock breaker ----------
    def break_deadlock_if_needed(self, dists):
        if self.restart_mode is not None:
            self.deadlock_frames = 0
            return
        if self.save_team is not None and self.save_frames > 0:
            self.deadlock_frames = 0
            return

        ball_slow = (self.ball.speed() < DEADLOCK_BALL_SPEED)
        order = np.argsort(dists)
        i1, i2 = int(order[0]), int(order[1])

        if (not self.robots[i1].is_upright()) or (not self.robots[i2].is_upright()):
            self.deadlock_frames = 0
            return

        close_two = (dists[i1] < DEADLOCK_DIST and dists[i2] < DEADLOCK_DIST)
        two_teams = (self.robots[i1].team != self.robots[i2].team)

        if ball_slow and close_two and two_teams:
            self.deadlock_frames += 1
        else:
            self.deadlock_frames = 0

        if self.deadlock_frames >= DEADLOCK_FRAMES:
            r = self.robots[i1]
            goal_x = self.opponent_goal_x(r.team)
            goal_y = float(np.clip(self.ball.y + np.random.uniform(-0.6, 0.6),
                                   -GOAL_WIDTH / 2, GOAL_WIDTH / 2))
            r.heading = float(np.arctan2(goal_y - r.y, goal_x - r.x))

            self.pos_team = r.team
            self.pos_idx = i1
            self.protect_frames = 0
            self.attach_ball_if_possessed()
            self.apply_action(r, 'poke')

            self.deadlock_frames = 0

    # ---------- Main step ----------
    def step(self):
        if self.restart_mode == 'goal_pause':
            self.goal_banner_frames -= 1
            if self.goal_banner_frames <= 0:
                team = self.pending_kickoff_team
                self.goal_banner_text = ""
                self.pending_kickoff_team = None
                self.start_kickoff(team)
            self.time += 1
            return

        self.update_postures()

        for r in self.robots:
            if r.tackle_cd > 0:
                r.tackle_cd -= 1

        if self.restart_mode == 'kickoff':
            self.kickoff_step()
            self.time += 1
            return

        self.update_goalie_save()

        if self.pos_idx is not None:
            self.attach_ball_if_possessed()

        dists = [float(np.hypot(r.x - self.ball.x, r.y - self.ball.y)) for r in self.robots]
        self.break_deadlock_if_needed(dists)

        mover_idx = set()
        for team in ('blue', 'red'):
            press_bonus = self.down_opponents_near_ball(team, radius=1.0)
            k = 3 if press_bonus else 2
            cand = [i for i, r in enumerate(self.robots)
                    if r.team == team and r.role != 'goalie' and r.is_upright()]
            cand_sorted = sorted(cand, key=lambda i: dists[i])
            mover_idx.update(cand_sorted[:k])

        if self.pos_idx is not None and self.robots[self.pos_idx].role != 'goalie' and self.robots[self.pos_idx].is_upright():
            mover_idx.add(self.pos_idx)

        for i, r in enumerate(self.robots):
            if r.role == 'goalie':
                if not (self.save_team == r.team and self.save_frames > 0):
                    act = self.decide_action(i, r)
                    self.apply_action(r, act)
                continue

            if i not in mover_idx:
                continue

            act = self.decide_action(i, r)

            if self.save_team is not None and self.save_frames > 0:
                if r.team != self.save_team and act in ('kick', 'pass'):
                    act = None

            self.apply_action(r, act)

        for r in self.robots:
            self.clamp_robot_in_field(r)
        self.resolve_robot_robot_collisions(iters=2)
        self.resolve_ball_robot_collisions()

        self.try_gain_or_tackle()

        if self.protect_frames > 0:
            self.protect_frames -= 1

        if self.pos_idx is None:
            self.ball.update()

        if self.ball.x > PITCH_LENGTH/2 - 0.2 and abs(self.ball.y) < GOAL_WIDTH/2:
            self.score['blue'] += 1
            self.start_goal_pause(scoring_team='blue', kickoff_team_after='red')
        elif self.ball.x < -PITCH_LENGTH/2 + 0.2 and abs(self.ball.y) < GOAL_WIDTH/2:
            self.score['red'] += 1
            self.start_goal_pause(scoring_team='red', kickoff_team_after='blue')

        self.time += 1


class Visualizer:
    def __init__(self, sim):
        self.sim = sim
        self.fig, self.ax = plt.subplots(figsize=(12, 8))
        self.setup_field()

        xs = [r.x for r in self.sim.robots]
        ys = [r.y for r in self.sim.robots]

        init_fc = [(0.2, 0.4, 1.0, 1.0) if r.team == 'blue' else (1.0, 0.2, 0.2, 1.0)
                   for r in self.sim.robots]

        self.robot_scatter = self.ax.scatter(xs, ys, s=220, c=init_fc,
                                             edgecolors='white', linewidths=2, zorder=5)

        u = [0.3*np.cos(r.heading) for r in self.sim.robots]
        v = [0.3*np.sin(r.heading) for r in self.sim.robots]
        self.heading_quiver = self.ax.quiver(xs, ys, u, v, angles='xy',
                                             scale_units='xy', scale=1,
                                             width=0.003, color='white',
                                             edgecolor='white', zorder=6)

        self.id_texts = []
        for r in self.sim.robots:
            t = self.ax.text(r.x, r.y, "", ha='center', va='center',
                             color='white', fontsize=8, fontweight='bold', zorder=7)
            self.id_texts.append(t)

        self.ball_scatter = self.ax.scatter([self.sim.ball.x], [self.sim.ball.y],
                                            s=120, c='white', edgecolors='black',
                                            linewidths=2, zorder=8)

        self.info_text = self.ax.text(0, PITCH_WIDTH/2 + 0.3, "", ha='center',
                                      fontsize=12, fontweight='bold', color='white', zorder=30)

        self.banner_text = self.ax.text(0, 0, "", ha='center', va='center',
                                        fontsize=26, fontweight='bold', color='yellow',
                                        zorder=40)

    def setup_field(self):
        self.ax.set_xlim(-PITCH_LENGTH/2 - 0.5, PITCH_LENGTH/2 + 0.5)
        self.ax.set_ylim(-PITCH_WIDTH/2 - 0.5, PITCH_WIDTH/2 + 0.5)
        self.ax.set_aspect('equal')

        field = patches.Rectangle((-PITCH_LENGTH/2, -PITCH_WIDTH/2),
                                  PITCH_LENGTH, PITCH_WIDTH,
                                  linewidth=2, edgecolor='white',
                                  facecolor='green', alpha=0.3)
        self.ax.add_patch(field)

        self.ax.plot([0, 0], [-PITCH_WIDTH/2, PITCH_WIDTH/2], 'w-', linewidth=2)

        circle = patches.Circle((0, 0), CENTER_CIRCLE_RADIUS, linewidth=2,
                                edgecolor='white', facecolor='none')
        self.ax.add_patch(circle)

        goal_left = patches.Rectangle((-PITCH_LENGTH/2 - 0.2, -GOAL_WIDTH/2),
                                      0.2, GOAL_WIDTH, linewidth=2,
                                      edgecolor='white', facecolor='none')
        goal_right = patches.Rectangle((PITCH_LENGTH/2, -GOAL_WIDTH/2),
                                       0.2, GOAL_WIDTH, linewidth=2,
                                       edgecolor='white', facecolor='none')
        self.ax.add_patch(goal_left)
        self.ax.add_patch(goal_right)

        self.ax.set_facecolor('darkgreen')
        self.ax.grid(True, alpha=0.3)

    def update(self, frame):
        self.sim.step()

        xs = [r.x for r in self.sim.robots]
        ys = [r.y for r in self.sim.robots]
        self.robot_scatter.set_offsets(np.c_[xs, ys])

        facecolors, edgecolors, sizes = [], [], []
        u, v = [], []

        for r in self.sim.robots:
            team_rgba = (0.2, 0.4, 1.0, 1.0) if r.team == 'blue' else (1.0, 0.2, 0.2, 1.0)

            if r.posture == 'fallen':
                facecolors.append((0.35, 0.35, 0.35, 1.0))
                edgecolors.append((0.15, 0.15, 0.15, 1.0))
                sizes.append(130)
                u.append(0.0); v.append(0.0)
            elif r.posture == 'getting_up':
                facecolors.append((team_rgba[0], team_rgba[1], team_rgba[2], 0.65))
                edgecolors.append((1.0, 1.0, 0.2, 1.0))
                t = 1.0 - (r.up_frames / max(1, GETUP_FRAMES))
                sizes.append(140 + 80 * t)
                u.append(0.12 * np.cos(r.heading))
                v.append(0.12 * np.sin(r.heading))
            else:
                facecolors.append(team_rgba)
                edgecolors.append((1.0, 1.0, 1.0, 1.0))
                sizes.append(220)
                u.append(0.3 * np.cos(r.heading))
                v.append(0.3 * np.sin(r.heading))

        self.robot_scatter.set_facecolors(facecolors)
        self.robot_scatter.set_edgecolors(edgecolors)
        self.robot_scatter.set_sizes(sizes)

        self.heading_quiver.set_offsets(np.c_[xs, ys])
        self.heading_quiver.set_UVC(u, v)

        for t, r in zip(self.id_texts, self.sim.robots):
            suffix = "F" if r.posture == 'fallen' else ("U" if r.posture == 'getting_up' else "")
            tag = ('B' if r.team == 'blue' else 'R') + str(r.id) + ':' + r.role[0]
            if suffix:
                tag += f'[{suffix}]'
            t.set_position((r.x, r.y))
            t.set_text(tag)

        self.ball_scatter.set_offsets([[self.sim.ball.x, self.sim.ball.y]])

        mode = self.sim.restart_mode if self.sim.restart_mode else "play"
        save = f"SAVE:{self.sim.save_team}" if self.sim.save_team else "SAVE:-"
        pos = f"POS:{self.sim.pos_team}" if self.sim.pos_team else "POS:-"
        self.info_text.set_text(
            f"Mode:{mode} | {save} | {pos} | "
            f"Blue {self.sim.score['blue']} - {self.sim.score['red']} Red | "
            f"Ball {self.sim.ball.speed():.2f}"
        )

        self.banner_text.set_text(self.sim.goal_banner_text if self.sim.restart_mode == 'goal_pause' else "")

        return (self.robot_scatter, self.heading_quiver, self.ball_scatter,
                self.info_text, self.banner_text, *self.id_texts)

    def run(self, frames=3000):
        self.anim = FuncAnimation(self.fig, self.update, frames=frames, interval=50, blit=True)
        plt.show()


def main():
    sim = SoccerSimulator()
    viz = Visualizer(sim)
    viz.run(frames=3000)


if __name__ == "__main__":
    main()
