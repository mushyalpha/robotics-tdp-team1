"""
4v4 Robot Soccer Simulation -- Mode Selection Edition
=====================================================

Teams:   Blue (attacks right, +x) vs Red (attacks left, -x)
Roster:  1 GK + 1 DEF + 2 ATK per team (4 players each)
Kickoff: Blue kicks off first; loser kicks off after each goal

Formation modes (applied to BOTH teams):
  1. always_attack  -- All players use attack formation at all times.
                       DEF (pid=1) stays near own goal as permanent
                       last-line guardian regardless of ball position.
  2. always_defend  -- All players use defend formation at all times.
                       No formation switch triggered by ball position.
  3. dynamic        -- Formation switches based on ball position.
                       Ball in own half  -> defend formation.
                       Ball in enemy half -> attack formation.
                       Both teams switch independently using this rule.

Permanent rule across ALL modes:
  DEF (pid=1) always keeps a goal-side anchor position.
  In attack formation: DEF holds at own penalty-box edge (~x = own_goal+2.0).
  In defend formation: DEF presses as DF1 but never advances past midfield.

Output metrics printed after all matches:
  - Win rate
  - Shots taken
  - Shots conceded
  - Formation switches (dynamic mode only, counted per team)
"""

import numpy as np
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.animation import FuncAnimation

# =============================================================================
# CONSTANTS
# =============================================================================

PITCH_LENGTH   = 9.0          # x: -4.5 to +4.5
PITCH_WIDTH    = 6.0           # y: -3.0 to +3.0
GOAL_WIDTH     = 2.6
GOAL_DEPTH     = 0.5
PLAYER_R       = 0.13          # physics collision radius
BALL_R_VISUAL  = 0.10          # visual ball radius

SPEED_GK_ATTACK  = 0.14
SPEED_GK_DEFEND  = 0.11
SPEED_DEF        = 0.12
SPEED_ATK_ATTACK = 0.16
SPEED_ATK_DEFEND = 0.12
BALL_FRICTION    = 0.6
BALL_MAX_SPEED   = 2.2

TOUCH_RADIUS     = 0.32        # distance to interact with ball
MIN_PLAYER_DIST  = PLAYER_R * 2.2
PLAYER_DISPLAY_R = 0.15        # visual circle radius

# =============================================================================
# INITIAL POSITIONS
# =============================================================================

BLUE_INIT = [
    dict(x=-0.3, y= 0.0, role='gk'),
    dict(x=-2.5, y= 0.0, role='def'),
    dict(x=-1.0, y=-1.2, role='atk'),
    dict(x=-1.0, y= 1.2, role='atk'),
]

RED_INIT = [
    dict(x= 0.3, y= 0.0, role='gk'),
    dict(x= 2.5, y= 0.0, role='def'),
    dict(x= 1.0, y=-1.2, role='atk'),
    dict(x= 1.0, y= 1.2, role='atk'),
]

ROLE_LABEL = {'gk': 'GK', 'def': 'DEF', 'atk': 'ATK'}

MODE_NAMES = {
    'always_attack': 'ALWAYS ATTACK',
    'always_defend': 'ALWAYS DEFEND',
    'dynamic':       'DYNAMIC',
}

MODE_COLORS = {
    'always_attack': '#f43f5e',
    'always_defend': '#60a5fa',
    'dynamic':       '#4ade80',
}

# =============================================================================
# FORMATION TARGET FUNCTIONS
# =============================================================================

# Penalty box dimensions (matches the drawn rectangle: depth=1.8, half-width=1.5)
PENALTY_BOX_DEPTH  = 1.8
PENALTY_BOX_HALF_W = 1.5


def _box_clamp(x, y, own_goal_x, attack_dir):
    """Clamp position to inside the penalty box."""
    inner = own_goal_x + PENALTY_BOX_DEPTH * attack_dir
    x_lo  = min(own_goal_x, inner) + 0.15
    x_hi  = max(own_goal_x, inner) - 0.15
    return np.clip(x, x_lo, x_hi), np.clip(y, -PENALTY_BOX_HALF_W + 0.15, PENALTY_BOX_HALF_W - 0.15)


def get_defend_target(pid, ball_x, ball_y, attack_dir, df1_x=None, df1_y=None):
    """
    Defend formation positional targets.

    pid=0  GK  : goal cut-angle, hugs own goal line
    pid=1  DEF : LOCKED inside penalty box, tracks ball y only within box bounds
    pid=2  DF2 : support layer -- goal-side of DF1's ideal intercept, opposite lateral lane
    pid=3  ATK : counter-attack pivot near centre line

    df1_x / df1_y: DF1 current position, used by DF2 for support slot calculation.
    """
    own_goal_x = -(PITCH_LENGTH / 2) * attack_dir

    if pid == 0:
        # GK: cut-angle position, stays just off goal line, tracks ball laterally
        gx = own_goal_x + 0.35 * attack_dir
        gy = np.clip(ball_y * 0.5, -GOAL_WIDTH / 2 + 0.2, GOAL_WIDTH / 2 - 0.2)
        return gx, gy

    elif pid == 1:
        # DEF: permanently locked inside the penalty box.
        # x sits at ~60% depth of the box (between goal line and front edge).
        # y tracks ball laterally but is clamped to box half-width.
        # This player NEVER leaves the penalty area.
        box_x = own_goal_x + PENALTY_BOX_DEPTH * 0.6 * attack_dir
        box_y = np.clip(ball_y * 0.6, -PENALTY_BOX_HALF_W + 0.2, PENALTY_BOX_HALF_W - 0.2)
        return box_x, box_y

    elif pid == 2:
        # DF2: support defender.
        # x -- one step goal-side of DF1's current position
        # y -- opposite lateral lane to DF1, forming X-shape coverage
        if df1_x is not None:
            df2_x = df1_x - 0.8 * attack_dir
            df2_x = np.clip(df2_x, min(own_goal_x, df1_x), max(own_goal_x, df1_x))
        else:
            df2_x = own_goal_x + 1.0 * attack_dir

        if df1_y is not None:
            lateral = -0.7 * np.sign(df1_y - ball_y) if df1_y != ball_y else 0.7
        else:
            lateral = -0.7 * np.sign(ball_y) if ball_y != 0 else 0.7

        df2_y = np.clip(ball_y * 0.3 + lateral, -PITCH_WIDTH / 2 + 0.3, PITCH_WIDTH / 2 - 0.3)
        return df2_x, df2_y

    else:
        # pid=3 ATK: counter-attack pivot, holds near centre line
        return 0.0, np.clip(ball_y * 0.3, -1.5, 1.5)


def get_attack_target(pid, ball_x, ball_y, attack_dir):
    """
    Attack formation positional targets.

    pid=0  GK  : pushes past centre line to support attack
    pid=1  DEF : LOCKED inside penalty box as permanent last-line guardian
    pid=2  ATK : primary striker, chases ball directly
    pid=3  ATK : wide support, creates passing triangle on flank
    """
    own_goal_x = -(PITCH_LENGTH / 2) * attack_dir

    if pid == 0:
        # GK pushes forward roughly 1/4 into enemy half
        gx = 1.5 * attack_dir
        gy = np.clip(ball_y * 0.3, -1.5, 1.5)
        return gx, gy

    elif pid == 1:
        # DEF: locked inside penalty box (same constraint as defend formation).
        # Tracks ball y slightly but never leaves the box.
        box_x = own_goal_x + PENALTY_BOX_DEPTH * 0.6 * attack_dir
        box_y = np.clip(ball_y * 0.6, -PENALTY_BOX_HALF_W + 0.2, PENALTY_BOX_HALF_W - 0.2)
        return box_x, box_y

    elif pid == 2:
        # ATK primary: chase the ball
        return ball_x, ball_y

    else:
        # pid=3 ATK support: wide flank offset from primary striker
        gx = np.clip(ball_x - 1.0 * attack_dir,
                     -PITCH_LENGTH / 2 + 0.3, PITCH_LENGTH / 2 - 0.3)
        side = 1.0 if ball_y <= 0 else -1.0
        gy   = np.clip(ball_y + side * 1.2, -PITCH_WIDTH / 2 + 0.3, PITCH_WIDTH / 2 - 0.3)
        return gx, gy


# =============================================================================
# PLAYER
# =============================================================================

class Player:
    def __init__(self, x, y, role, team, pid):
        self.x         = float(x)
        self.y         = float(y)
        self.home_x    = float(x)
        self.home_y    = float(y)
        self.heading   = 0.0 if team == 'blue' else np.pi
        self.role      = role
        self.team      = team
        self.pid       = pid
        self.state     = 'idle'
        self.is_kicker = False

    def dist_to(self, other):
        if hasattr(other, 'x'):
            return np.hypot(self.x - other.x, self.y - other.y)
        return np.hypot(self.x - other[0], self.y - other[1])

    def move_toward(self, tx, ty, speed):
        dx, dy = tx - self.x, ty - self.y
        d = np.hypot(dx, dy)
        if d < 0.02:
            return
        s = min(speed, d)
        self.x += (dx / d) * s
        self.y += (dy / d) * s
        self.heading = np.arctan2(dy, dx)
        self.x = np.clip(self.x, -PITCH_LENGTH / 2 + 0.15, PITCH_LENGTH / 2 - 0.15)
        self.y = np.clip(self.y, -PITCH_WIDTH  / 2 + 0.15, PITCH_WIDTH  / 2 - 0.15)


# =============================================================================
# BALL
# =============================================================================

class Ball:
    def __init__(self):
        self.reset()

    def reset(self, x=0.0, y=0.0):
        self.x          = x
        self.y          = y
        self.vx         = 0.0
        self.vy         = 0.0
        self.last_touch = None

    def update(self):
        self.x  += self.vx
        self.y  += self.vy
        self.vx *= BALL_FRICTION
        self.vy *= BALL_FRICTION

        spd = np.hypot(self.vx, self.vy)
        if spd > BALL_MAX_SPEED:
            self.vx = self.vx / spd * BALL_MAX_SPEED
            self.vy = self.vy / spd * BALL_MAX_SPEED
        if spd < 0.03:
            self.vx = self.vy = 0.0

        if self.y < -PITCH_WIDTH / 2:
            self.y  = -PITCH_WIDTH / 2
            self.vy =  abs(self.vy) * 0.35
            self.vx *= 0.75
        if self.y >  PITCH_WIDTH / 2:
            self.y  =  PITCH_WIDTH / 2
            self.vy = -abs(self.vy) * 0.35
            self.vx *= 0.75

    def kick(self, shooter, target_x, target_y, power, accuracy):
        angle  = np.arctan2(target_y - self.y, target_x - self.x)
        angle += np.random.uniform(-accuracy, accuracy)
        self.vx = np.cos(angle) * power
        self.vy = np.sin(angle) * power
        spd = np.hypot(self.vx, self.vy)
        if spd > BALL_MAX_SPEED:
            self.vx = self.vx / spd * BALL_MAX_SPEED
            self.vy = self.vy / spd * BALL_MAX_SPEED
        self.last_touch = shooter


# =============================================================================
# STATISTICS
# =============================================================================

class Stats:
    def __init__(self):
        self.wins               = 0
        self.losses             = 0
        self.draws              = 0
        self.shots              = 0
        self.shots_conceded     = 0
        self.goals_scored       = 0
        self.goals_conceded     = 0
        self.formation_switches = 0

    def win_rate(self, total):
        return (self.wins / total * 100) if total > 0 else 0.0


# =============================================================================
# SIMULATOR
# =============================================================================

class Soccer4v4:
    """
    mode: formation mode applied to BOTH teams.
      'always_attack' -- Both teams always use attack formation.
      'always_defend' -- Both teams always use defend formation.
      'dynamic'       -- Both teams switch based on ball position independently.

    In all modes, DEF (pid=1) always anchors near own goal as last-line guardian.
    """

    def __init__(self, mode: str = 'dynamic'):
        self.mode = mode
        self.ball = Ball()
        self.blue = [Player(**BLUE_INIT[i], team='blue', pid=i) for i in range(4)]
        self.red  = [Player(**RED_INIT[i],  team='red',  pid=i) for i in range(4)]
        self.all_players = self.blue + self.red

        self.blue_goals = 0
        self.red_goals  = 0
        self.step_count = 0
        self.log        = []

        self.blue_stats = Stats()
        self.red_stats  = Stats()

        # Track last formation for each team (dynamic mode switch counting)
        self._blue_last_formation = None
        self._red_last_formation  = None

        # Kickoff state
        self.phase        = 'kickoff_setup'
        self.kickoff_team = 'blue'
        self.kickoff_wait = 0
        self.match_over   = False
        self._next_kickoff = 'blue'
        self._assign_kicker()

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------
    def _assign_kicker(self):
        for p in self.all_players:
            p.is_kicker = False
        team = self.blue if self.kickoff_team == 'blue' else self.red
        for p in team:
            if p.role == 'gk':
                p.is_kicker = True
                break

    def _add_log(self, msg):
        self.log.append(msg)
        if len(self.log) > 6:
            self.log.pop(0)

    def _separate_players(self):
        for i in range(len(self.all_players)):
            for j in range(i + 1, len(self.all_players)):
                a, b = self.all_players[i], self.all_players[j]
                dx, dy = a.x - b.x, a.y - b.y
                d = np.hypot(dx, dy)
                if 0.001 < d < MIN_PLAYER_DIST:
                    push = (MIN_PLAYER_DIST - d) * 0.55
                    nx, ny = dx / d, dy / d
                    a.x = np.clip(a.x + nx * push, -PITCH_LENGTH/2+0.15, PITCH_LENGTH/2-0.15)
                    a.y = np.clip(a.y + ny * push, -PITCH_WIDTH /2+0.15, PITCH_WIDTH /2-0.15)
                    b.x = np.clip(b.x - nx * push, -PITCH_LENGTH/2+0.15, PITCH_LENGTH/2-0.15)
                    b.y = np.clip(b.y - ny * push, -PITCH_WIDTH /2+0.15, PITCH_WIDTH /2-0.15)

    def _reset_positions(self):
        for p in self.all_players:
            p.is_kicker = False
            p.state     = 'idle'
            init        = BLUE_INIT[p.pid] if p.team == 'blue' else RED_INIT[p.pid]
            p.x, p.y   = init['x'], init['y']
            p.home_x, p.home_y = init['x'], init['y']

    def reset_after_goal(self, next_kickoff_team: str):
        """Called when a goal is scored. Only records who kicks off next
        and sets match_over=True. Does NOT reset positions here -- the
        Visualiser will call new_game() after recording the result."""
        self.match_over   = True
        self._next_kickoff = next_kickoff_team   # remember for after new_game

    def new_game(self):
        """Start a new match while preserving cumulative statistics."""
        self.blue_goals           = 0
        self.red_goals            = 0
        self.step_count           = 0
        self.log                  = []
        self.match_over           = False
        self._blue_last_formation = None
        self._red_last_formation  = None
        self.kickoff_team         = getattr(self, '_next_kickoff', 'blue')
        self._next_kickoff        = 'blue'
        self.phase                = 'kickoff_setup'
        self.kickoff_wait         = 0
        self.ball.reset()
        self._reset_positions()
        self._assign_kicker()

    def record_match_result(self):
        """Write win/loss/draw and goals to cumulative stats."""
        if self.blue_goals > self.red_goals:
            self.blue_stats.wins  += 1
            self.red_stats.losses += 1
        elif self.red_goals > self.blue_goals:
            self.red_stats.wins    += 1
            self.blue_stats.losses += 1
        else:
            self.blue_stats.draws += 1
            self.red_stats.draws  += 1
        self.blue_stats.goals_scored   += self.blue_goals
        self.blue_stats.goals_conceded += self.red_goals
        self.red_stats.goals_scored    += self.red_goals
        self.red_stats.goals_conceded  += self.blue_goals

    def formation_label(self, team: str) -> str:
        """
        Return a formation string like '1-1-2' based on current player positions.

        Lines are defined by x-position relative to attack direction:
          Layer 0 (deepest / goalkeeper zone)  : x in own goal area
          Layer 1 (defensive mid / own half)    : x between goal area and midline
          Layer 2 (attacking / enemy half)      : x past midline

        Counts players per layer and joins with '-', e.g. '1-1-2'.
        """
        players    = self.blue if team == 'blue' else self.red
        attack_dir = 1 if team == 'blue' else -1
        own_goal_x = -(PITCH_LENGTH / 2) * attack_dir

        layers = [0, 0, 0]
        for p in players:
            # signed distance from own goal line toward enemy goal
            depth = (p.x - own_goal_x) * attack_dir
            if depth < PENALTY_BOX_DEPTH + 0.3:
                layers[0] += 1
            elif depth < PITCH_LENGTH / 2:
                layers[1] += 1
            else:
                layers[2] += 1

        # Drop empty leading/trailing layers but always keep at least 2 parts
        parts = [str(c) for c in layers if c > 0]
        if len(parts) < 2:
            parts = [str(c) for c in layers]
        return '-'.join(parts)

    # -------------------------------------------------------------------------
    # Formation decision
    # -------------------------------------------------------------------------
    def _get_formation(self, team: str) -> str:
        """
        Return 'attack' or 'defend' for the given team based on the mode.

        always_attack: always 'attack'
        always_defend: always 'defend'
        dynamic:       blue defends when ball.x < 0 (own half for blue)
                       red defends  when ball.x > 0 (own half for red)
        """
        if self.mode == 'always_attack':
            return 'attack'
        elif self.mode == 'always_defend':
            return 'defend'
        else:
            # dynamic
            if team == 'blue':
                formation = 'defend' if self.ball.x < 0 else 'attack'
                if (self._blue_last_formation is not None and
                        formation != self._blue_last_formation):
                    self.blue_stats.formation_switches += 1
                self._blue_last_formation = formation
            else:
                formation = 'defend' if self.ball.x > 0 else 'attack'
                if (self._red_last_formation is not None and
                        formation != self._red_last_formation):
                    self.red_stats.formation_switches += 1
                self._red_last_formation = formation
            return formation

    # -------------------------------------------------------------------------
    # Per-player action
    # -------------------------------------------------------------------------
    def _act(self, p: Player, own_team: list, attack_dir: int, formation: str):
        b      = self.ball
        d_ball = p.dist_to(b)
        df1    = own_team[1]   # DEF player, always box-locked
        own_goal_x = -(PITCH_LENGTH / 2) * attack_dir

        # Update formation home marker for display
        if formation == 'defend':
            if p.pid == 2:
                tx, ty = get_defend_target(2, b.x, b.y, attack_dir,
                                           df1_x=df1.x, df1_y=df1.y)
            else:
                tx, ty = get_defend_target(p.pid, b.x, b.y, attack_dir)
        else:
            tx, ty = get_attack_target(p.pid, b.x, b.y, attack_dir)
        p.home_x, p.home_y = tx, ty

        # If touching the ball, decide kick action.
        # Exception: pid=1 (DEF) NEVER picks up the ball -- they only guard.
        if d_ball <= TOUCH_RADIUS and p.pid != 1:
            self._act_with_ball(p, own_team, attack_dir)
            return

        # ------------------------------------------------------------------
        # ALWAYS DEFEND: roles are SWAPPED vs normal defend.
        #   GK (pid=0) goes out to press / chase the ball.
        #   DEF (pid=1) stays locked in the penalty box as the goal guardian.
        # ------------------------------------------------------------------
        if self.mode == 'always_defend' and formation == 'defend':

            if p.pid == 0:
                # GK acts like a field player: presses ball aggressively
                if d_ball <= TOUCH_RADIUS:
                    self._act_with_ball(p, own_team, attack_dir)
                elif d_ball < 2.5:
                    p.move_toward(b.x, b.y, SPEED_GK_ATTACK * 1.1)
                    p.state = 'gk_rush'
                else:
                    # When far from ball, move to intercept position between
                    # ball and own goal (acts as an outfield defender)
                    ix = (own_goal_x + b.x) / 2.0
                    ix = np.clip(ix, own_goal_x, 0.0 * attack_dir)
                    iy = np.clip(b.y * 0.5, -PITCH_WIDTH / 2 + 0.3, PITCH_WIDTH / 2 - 0.3)
                    p.move_toward(ix, iy, SPEED_GK_ATTACK)
                    p.state = 'gk_guard'

            elif p.pid == 1:
                # DEF: goal guardian locked in penalty box, never chases ball.
                # Tracks ball y within box, stays at box mid-depth.
                bx, by = get_defend_target(1, b.x, b.y, attack_dir)
                bx, by = _box_clamp(bx, by, own_goal_x, attack_dir)
                p.move_toward(bx, by, SPEED_DEF)
                p.state = 'def_anchor'

            elif p.pid == 2:
                # DEFENSIVE SUPPORT in always_defend.
                # Base position: orbit near pid=1 (DEF), slightly in front
                # and laterally offset to cover the other shot lane.
                # Highest priority: retreat if in enemy half while ball in own half.
                p2_in_enemy_half = (p.x * attack_dir) > 0
                ball_in_own_half = (b.x * attack_dir) < 0
                if p2_in_enemy_half and ball_in_own_half:
                    retreat_x = -0.5 * attack_dir
                    retreat_y = np.clip(b.y * 0.3, -PITCH_WIDTH / 2 + 0.3, PITCH_WIDTH / 2 - 0.3)
                    p.move_toward(retreat_x, retreat_y, SPEED_ATK_ATTACK)
                    p.state = 'df2_retreat'
                else:
                    enemies = self.red if p.team == 'blue' else self.blue
                    enemy_breached = any(
                        (e.x * attack_dir) > (df1.x * attack_dir) and e.dist_to(b) < 2.0
                        for e in enemies
                    )
                    if enemy_breached:
                        # Emergency: step toward ball, stay on own half
                        tx = np.clip(b.x, -PITCH_LENGTH / 2, 0.0) if attack_dir == 1 \
                             else np.clip(b.x, 0.0, PITCH_LENGTH / 2)
                        p.move_toward(tx, b.y, SPEED_ATK_DEFEND * 1.2)
                        p.state = 'df2_cover'
                    else:
                        # Normal: orbit near DEF (pid=1).
                        # x: just in front of DEF (one step toward midfield)
                        support_x = df1.x + PENALTY_BOX_DEPTH * 0.5 * attack_dir
                        support_x = np.clip(support_x, min(own_goal_x, 0.0), max(own_goal_x, 0.0))
                        # y: offset opposite to DEF relative to ball to cover wider lane
                        lateral = -0.7 * np.sign(df1.y - b.y) if abs(df1.y - b.y) > 0.1 else 0.7
                        support_y = np.clip(df1.y + lateral,
                                            -PITCH_WIDTH / 2 + 0.3, PITCH_WIDTH / 2 - 0.3)
                        p.move_toward(support_x, support_y, SPEED_ATK_DEFEND)
                        p.state = 'df2_hold'

            else:
                # pid=3: sole attacker in always_defend, stays near midline
                # ready to receive a counter-attack pass
                atk_x = np.clip(b.x * 0.3, -1.5 * attack_dir, 0.5 * attack_dir)
                atk_y = np.clip(b.y * 0.3, -1.5, 1.5)
                p.move_toward(atk_x, atk_y, SPEED_ATK_DEFEND)
                p.state = 'atk_wait'

            return   # done with always_defend branch

        # ------------------------------------------------------------------
        # DEFEND formation behaviour (dynamic / always_attack defend phase)
        # ------------------------------------------------------------------
        if formation == 'defend':

            if p.pid == 0:
                # GK: cut-angle position, rush out if ball very close
                gx, gy = get_defend_target(0, b.x, b.y, attack_dir)
                if d_ball < 1.2:
                    p.move_toward(b.x, b.y, SPEED_GK_DEFEND * 1.2)
                    p.state = 'gk_rush'
                else:
                    p.move_toward(gx, gy, SPEED_GK_DEFEND)
                    p.state = 'gk_guard'

            elif p.pid == 1:
                # DEF: LOCKED in penalty box, tracks ball y only.
                # Never presses, never leaves box.
                bx, by = get_defend_target(1, b.x, b.y, attack_dir)
                bx, by = _box_clamp(bx, by, own_goal_x, attack_dir)
                p.move_toward(bx, by, SPEED_DEF)
                p.state = 'def_anchor'

            elif p.pid == 2:
                # DF2: support defender, orbits near DEF (pid=1).
                # Priority 0: retreat if in enemy half while ball in own half.
                p2_in_enemy_half = (p.x * attack_dir) > 0
                ball_in_own_half = (b.x * attack_dir) < 0
                if p2_in_enemy_half and ball_in_own_half:
                    retreat_x = -0.5 * attack_dir
                    retreat_y = np.clip(b.y * 0.3, -PITCH_WIDTH / 2 + 0.3, PITCH_WIDTH / 2 - 0.3)
                    p.move_toward(retreat_x, retreat_y, SPEED_ATK_ATTACK)
                    p.state = 'df2_retreat'
                else:
                    enemies = self.red if p.team == 'blue' else self.blue
                    df1_breached = any(
                        (e.x * attack_dir) > (df1.x * attack_dir) and e.dist_to(b) < 2.0
                        for e in enemies
                    )
                    if df1_breached:
                        # Emergency: press toward ball
                        p.move_toward(b.x, b.y, SPEED_ATK_DEFEND * 1.2)
                        p.state = 'df2_cover'
                    else:
                        # Normal: orbit near DEF (pid=1), one step in front and
                        # laterally offset to cover the opposite shot lane.
                        support_x = df1.x + PENALTY_BOX_DEPTH * 0.5 * attack_dir
                        support_x = np.clip(support_x, min(own_goal_x, 0.0), max(own_goal_x, 0.0))
                        lateral = -0.7 * np.sign(df1.y - b.y) if abs(df1.y - b.y) > 0.1 else 0.7
                        support_y = np.clip(df1.y + lateral,
                                            -PITCH_WIDTH / 2 + 0.3, PITCH_WIDTH / 2 - 0.3)
                        p.move_toward(support_x, support_y, SPEED_ATK_DEFEND)
                        p.state = 'df2_hold'

            else:
                # pid=3: counter-attack pivot
                gx, gy = get_defend_target(3, b.x, b.y, attack_dir)
                if b.last_touch and b.last_touch.team == p.team:
                    enemy_goal_x = (PITCH_LENGTH / 2) * attack_dir
                    p.move_toward(enemy_goal_x - 1.5 * attack_dir, b.y, SPEED_ATK_ATTACK)
                    p.state = 'atk_counter'
                else:
                    p.move_toward(gx, gy, SPEED_ATK_DEFEND)
                    p.state = 'atk_wait'

        # ------------------------------------------------------------------
        # ATTACK formation behaviour
        # ------------------------------------------------------------------
        else:

            if p.pid == 0:
                # GK pushes forward past centre line
                gx, gy = get_attack_target(0, b.x, b.y, attack_dir)
                p.move_toward(gx, gy, SPEED_GK_ATTACK)
                p.state = 'gk_attack'

            elif p.pid == 1:
                # DEF: locked in penalty box even during attack formation.
                # Only steps toward ball if enemy is inside the box.
                bx, by = get_attack_target(1, b.x, b.y, attack_dir)
                bx, by = _box_clamp(bx, by, own_goal_x, attack_dir)
                enemies = self.red if p.team == 'blue' else self.blue
                threat_in_box = any(
                    abs(e.x - own_goal_x) < PENALTY_BOX_DEPTH
                    and abs(e.y) < PENALTY_BOX_HALF_W
                    and e.dist_to(b) < 1.5
                    for e in enemies
                )
                if threat_in_box:
                    # Press within box only
                    tx2 = np.clip(b.x, min(own_goal_x, own_goal_x + PENALTY_BOX_DEPTH * attack_dir),
                                  max(own_goal_x, own_goal_x + PENALTY_BOX_DEPTH * attack_dir))
                    ty2 = np.clip(b.y, -PENALTY_BOX_HALF_W, PENALTY_BOX_HALF_W)
                    p.move_toward(tx2, ty2, SPEED_DEF * 1.1)
                    p.state = 'def_press'
                else:
                    p.move_toward(bx, by, SPEED_DEF)
                    p.state = 'def_anchor'

            elif p.pid == 2:
                # ATK primary: chase ball aggressively
                p.move_toward(b.x, b.y, SPEED_ATK_ATTACK)
                p.state = 'atk_chase'

            else:
                # pid=3 ATK support: wide flank
                gx, gy = get_attack_target(3, b.x, b.y, attack_dir)
                p.move_toward(gx, gy, SPEED_ATK_ATTACK * 0.9)
                p.state = 'atk_support'

    def _act_with_ball(self, p: Player, own_team: list, attack_dir: int):
        """Decide whether to shoot or pass when a player has the ball."""
        b            = self.ball
        enemy_goal_x = (PITCH_LENGTH / 2) * attack_dir
        d_goal       = p.dist_to((enemy_goal_x, 0.0))

        if d_goal < PITCH_LENGTH * 0.55:
            # Shoot on goal
            if p.team == 'blue':
                self.blue_stats.shots         += 1
                self.red_stats.shots_conceded  += 1
            else:
                self.red_stats.shots          += 1
                self.blue_stats.shots_conceded += 1
            b.kick(p, enemy_goal_x, 0.0,
                   power=0.5 + np.random.uniform(-0.2, 0.2),
                   accuracy=0.13)
            p.state = 'shoot'
        else:
            # Pass to best-positioned teammate
            best   = None
            bscore = -1e9
            for tm in own_team:
                if tm.pid == p.pid:
                    continue
                tm_d_goal = tm.dist_to((enemy_goal_x, 0.0))
                fwd   = (tm.x - p.x) * attack_dir
                score = -tm_d_goal + fwd * 0.8 + np.random.uniform(-0.2, 0.2)
                if score > bscore:
                    bscore = score
                    best   = tm
            if best is not None:
                b.kick(p, best.x, best.y,
                       power=0.5 + p.dist_to(best) * 0.14,
                       accuracy=0.09)
                p.state = 'pass'
            else:
                b.kick(p, enemy_goal_x, b.y, power=0.5, accuracy=0.15)
                p.state = 'kick_fwd'

    # -------------------------------------------------------------------------
    # Kickoff phases
    # -------------------------------------------------------------------------
    def _kickoff_setup_step(self):
        non_kick_team = 'red' if self.kickoff_team == 'blue' else 'blue'
        nk_attack_dir = 1 if non_kick_team == 'blue' else -1
        nk_gk_x      = -1.8 * nk_attack_dir

        all_in = True
        for p in self.all_players:
            if p.team == non_kick_team and p.role == 'gk':
                tx, ty = nk_gk_x, 0.0
            else:
                init   = BLUE_INIT[p.pid] if p.team == 'blue' else RED_INIT[p.pid]
                tx, ty = init['x'], init['y']

            if p.dist_to((tx, ty)) > 0.2:
                all_in = False
                p.move_toward(tx, ty, 0.16)

            p.heading = np.arctan2(0.0 - p.y, 0.0 - p.x)
            p.state   = 'setup'

        self._separate_players()
        if all_in:
            self.phase        = 'kickoff_wait'
            self.kickoff_wait = 0

    def _kickoff_wait_step(self):
        self.kickoff_wait += 1
        if self.kickoff_wait >= 30:
            for p in self.all_players:
                if p.is_kicker:
                    attack_dir   = 1 if p.team == 'blue' else -1
                    enemy_goal_x = (PITCH_LENGTH / 2) * attack_dir
                    self.ball.kick(p, enemy_goal_x, 0.0, power=1.6, accuracy=0.10)
                    self._add_log(f"Kickoff: {'Blue' if p.team == 'blue' else 'Red'} team")
                    p.is_kicker = False
                    self.phase  = 'play'
                    break

    # -------------------------------------------------------------------------
    # Goal detection
    # -------------------------------------------------------------------------
    def _check_goals(self):
        b = self.ball
        if b.x >= PITCH_LENGTH / 2 and abs(b.y) < GOAL_WIDTH / 2:
            self.blue_goals += 1
            self._add_log(f"GOAL! Blue scores! ({self.blue_goals} - {self.red_goals})")
            self.reset_after_goal('red')    # loser (Red) kicks off next match
            return True
        if b.x <= -PITCH_LENGTH / 2 and abs(b.y) < GOAL_WIDTH / 2:
            self.red_goals += 1
            self._add_log(f"GOAL! Red scores! ({self.blue_goals} - {self.red_goals})")
            self.reset_after_goal('blue')   # loser (Blue) kicks off next match
            return True
        # Ball out on right endline (no goal)
        if b.x >= PITCH_LENGTH / 2:
            b.x  =  PITCH_LENGTH / 2 - 0.3
            b.y  = np.clip(b.y, -PITCH_WIDTH / 2 + 0.3, PITCH_WIDTH / 2 - 0.3)
            b.vx = -abs(b.vx) * 0.3
            b.vy *= 0.3
            self._add_log("Ball out (right) -- goal kick")
        # Ball out on left endline (no goal)
        if b.x <= -PITCH_LENGTH / 2:
            b.x  = -PITCH_LENGTH / 2 + 0.3
            b.y  = np.clip(b.y, -PITCH_WIDTH / 2 + 0.3, PITCH_WIDTH / 2 - 0.3)
            b.vx =  abs(b.vx) * 0.3
            b.vy *= 0.3
            self._add_log("Ball out (left) -- goal kick")
        return False

    # -------------------------------------------------------------------------
    # Main simulation step
    # -------------------------------------------------------------------------
    def step(self):
        self.step_count += 1

        if self.phase == 'kickoff_setup':
            self._kickoff_setup_step()
            return
        if self.phase == 'kickoff_wait':
            self._kickoff_wait_step()
            return

        blue_formation = self._get_formation('blue')
        red_formation  = self._get_formation('red')

        for p in self.blue:
            self._act(p, self.blue, attack_dir=1,  formation=blue_formation)
        for p in self.red:
            self._act(p, self.red,  attack_dir=-1, formation=red_formation)

        self._separate_players()
        self.ball.update()
        self._check_goals()


# =============================================================================
# VISUALISER
# =============================================================================

STATE_COLOR = {
    # GK states
    'gk_guard':      '#a78bfa',
    'gk_rush':       '#f97316',
    'gk_attack':     '#4ade80',
    # DF1 states
    'def_press':     '#f97316',
    'def_intercept': '#facc15',
    # DF2 states
    'df2_hold':      '#60a5fa',
    'df2_shadow':    '#38bdf8',
    'df2_cover':     '#f97316',
    'df2_retreat':   '#e879f9',
    # DEF anchor (attack formation)
    'def_anchor':    '#38bdf8',
    # ATK states
    'atk_chase':     '#4ade80',
    'atk_support':   '#a3e635',
    'atk_wait':      '#94a3b8',
    'atk_counter':   '#f43f5e',
    # Ball actions
    'shoot':         '#f43f5e',
    'pass':          '#fb923c',
    'kick_fwd':      '#fb923c',
    # Misc
    'setup':         '#94a3b8',
    'idle':          '#94a3b8',
}

STATE_LABEL = {
    # GK states
    'gk_guard':      'GK-GUARD',
    'gk_rush':       'GK-RUSH',
    'gk_attack':     'GK-ATK',
    # DF1 states
    'def_press':     'DF1-PRESS',
    'def_intercept': 'DF1-INTER',
    # DF2 states
    'df2_hold':      'DF2-HOLD',
    'df2_shadow':    'DF2-SHADOW',
    'df2_cover':     'DF2-COVER',
    'df2_retreat':   'DF2-RETREAT',
    # DEF anchor (attack formation)
    'def_anchor':    'DEF-ANCHOR',
    # ATK states
    'atk_chase':     'ATK-CHASE',
    'atk_support':   'ATK-SUPP',
    'atk_wait':      'ATK-WAIT',
    'atk_counter':   'COUNTER!',
    # Ball actions
    'shoot':         'SHOOT!',
    'pass':          'PASS',
    'kick_fwd':      'KICK',
    # Misc
    'setup':         'SETUP',
    'idle':          'IDLE',
}


class Visualiser:
    def __init__(self, sim: Soccer4v4, total_matches: int, steps_per_match: int):
        self.sim             = sim
        self.total_matches   = total_matches
        self.steps_per_match = steps_per_match
        self.current_match   = 1

        self.fig, self.ax = plt.subplots(figsize=(14, 9.5))
        self.fig.patch.set_facecolor('#060d1a')
        self.ax.set_facecolor('#155e2b')
        self.ax.set_xlim(-PITCH_LENGTH / 2 - 1.0, PITCH_LENGTH / 2 + 1.0)
        self.ax.set_ylim(-PITCH_WIDTH  / 2 - 1.6, PITCH_WIDTH  / 2 + 1.2)
        self.ax.set_aspect('equal')
        self.ax.axis('off')

    # -------------------------------------------------------------------------
    def _draw_field(self):
        ax = self.ax
        ax.cla()
        ax.set_facecolor('#155e2b')
        ax.set_xlim(-PITCH_LENGTH / 2 - 1.0, PITCH_LENGTH / 2 + 1.0)
        ax.set_ylim(-PITCH_WIDTH  / 2 - 1.6, PITCH_WIDTH  / 2 + 1.2)
        ax.set_aspect('equal')
        ax.axis('off')

        # Grass stripes
        stripe_w = PITCH_LENGTH / 8
        for i in range(8):
            col = '#166534' if i % 2 == 0 else '#155e2b'
            ax.add_patch(patches.Rectangle(
                (-PITCH_LENGTH / 2 + i * stripe_w, -PITCH_WIDTH / 2),
                stripe_w, PITCH_WIDTH, fc=col, ec='none', zorder=0))

        # Pitch border
        ax.add_patch(patches.Rectangle(
            (-PITCH_LENGTH / 2, -PITCH_WIDTH / 2), PITCH_LENGTH, PITCH_WIDTH,
            lw=2, ec='white', fc='none', alpha=0.6, zorder=1))

        # Centre line and circle
        ax.plot([0, 0], [-PITCH_WIDTH / 2, PITCH_WIDTH / 2],
                'w-', lw=1.5, alpha=0.5, zorder=1)
        ax.add_patch(patches.Circle((0, 0), 0.75,
                                    lw=1.5, ec='white', fc='none', alpha=0.5, zorder=1))
        ax.plot(0, 0, 'wo', ms=4, alpha=0.7, zorder=1)

        # Penalty boxes
        for sign in (-1, 1):
            bx = sign * PITCH_LENGTH / 2
            ax.add_patch(patches.Rectangle(
                (bx - sign * 1.8, -1.5), sign * 1.8, 3.0,
                lw=1, ec='white', fc='none', alpha=0.25, zorder=1))

        # Goals
        ax.add_patch(patches.Rectangle(
            (-PITCH_LENGTH / 2 - GOAL_DEPTH, -GOAL_WIDTH / 2), GOAL_DEPTH, GOAL_WIDTH,
            lw=2, ec='#ef4444', fc='#ef444420', zorder=1))
        ax.add_patch(patches.Rectangle(
            ( PITCH_LENGTH / 2,              -GOAL_WIDTH / 2), GOAL_DEPTH, GOAL_WIDTH,
            lw=2, ec='#3b82f6', fc='#3b82f620', zorder=1))

        # Penalty box guardian zone highlight (matches penalty box dimensions)
        ax.add_patch(patches.Rectangle(
            (-PITCH_LENGTH / 2, -PENALTY_BOX_HALF_W),
            PENALTY_BOX_DEPTH, PENALTY_BOX_HALF_W * 2,
            fc='#3b82f610', ec='#3b82f640', lw=1, linestyle=':', zorder=0))
        ax.add_patch(patches.Rectangle(
            ( PITCH_LENGTH / 2 - PENALTY_BOX_DEPTH, -PENALTY_BOX_HALF_W),
            PENALTY_BOX_DEPTH, PENALTY_BOX_HALF_W * 2,
            fc='#ef444410', ec='#ef444440', lw=1, linestyle=':', zorder=0))

        # Ball-side half highlight
        b   = self.sim.ball
        hx  = -PITCH_LENGTH / 2 if b.x < 0 else 0
        col = '#ef444406' if b.x < 0 else '#3b82f606'
        ax.add_patch(patches.Rectangle(
            (hx, -PITCH_WIDTH / 2), PITCH_LENGTH / 2, PITCH_WIDTH,
            fc=col, ec='none', zorder=0))

    # -------------------------------------------------------------------------
    def _draw_player(self, p: Player):
        ax   = self.ax
        col  = '#1e40af' if p.team == 'blue' else '#991b1b'
        ecol = STATE_COLOR.get(p.state, 'white')

        # Shadow
        ax.add_patch(patches.Circle(
            (p.x + 0.05, p.y - 0.05), PLAYER_DISPLAY_R,
            fc='black', ec='none', alpha=0.25, zorder=3))
        # Body
        ax.add_patch(patches.Circle(
            (p.x, p.y), PLAYER_DISPLAY_R,
            fc=col, ec=ecol, lw=2.2, zorder=4))

        # Heading arrow
        hx = p.x + np.cos(p.heading) * (PLAYER_DISPLAY_R * 1.6)
        hy = p.y + np.sin(p.heading) * (PLAYER_DISPLAY_R * 1.6)
        ax.annotate('', xy=(hx, hy), xytext=(p.x, p.y),
                    arrowprops=dict(arrowstyle='->', color='white',
                                   lw=1.3, mutation_scale=9), zorder=5)

        # Role label inside circle
        ax.text(p.x, p.y, ROLE_LABEL[p.role],
                ha='center', va='center', fontsize=6, fontweight='bold',
                color='white', zorder=6)

        # State label below circle
        slbl = STATE_LABEL.get(p.state, p.state[:10].upper())
        ax.text(p.x, p.y - PLAYER_DISPLAY_R - 0.16, slbl,
                ha='center', va='top', fontsize=4.5,
                color=ecol, alpha=0.85, zorder=6)

        # Formation home marker (dashed circle)
        mc = '#60a5fa44' if p.team == 'blue' else '#f8717144'
        ax.add_patch(patches.Circle(
            (p.home_x, p.home_y), 0.20,
            lw=0.8, ec=mc, fc='none', linestyle='--', zorder=2))

        # Kicker crown
        if p.is_kicker:
            ax.text(p.x, p.y + PLAYER_DISPLAY_R + 0.12, 'K',
                    ha='center', va='bottom', fontsize=8,
                    color='#facc15', fontweight='bold', zorder=6)

    # -------------------------------------------------------------------------
    def _draw_stats_bar(self):
        ax   = self.ax
        sim  = self.sim
        bs   = sim.blue_stats
        rs   = sim.red_stats
        done = self.current_match - 1

        blue_wr = bs.win_rate(done) if done > 0 else 0.0
        red_wr  = rs.win_rate(done) if done > 0 else 0.0

        # Formation switch count only shown in dynamic mode
        if sim.mode == 'dynamic':
            sw_txt = f"  | Switches B:{bs.formation_switches} R:{rs.formation_switches}"
        else:
            sw_txt = ""

        line1 = (f"Blue [{MODE_NAMES[sim.mode]}]  "
                 f"W:{bs.wins} L:{bs.losses} D:{bs.draws}  "
                 f"WR:{blue_wr:.1f}%  "
                 f"Shots:{bs.shots}  Conceded:{bs.shots_conceded}"
                 f"{sw_txt}")
        line2 = (f"Red  [{MODE_NAMES[sim.mode]}]  "
                 f"W:{rs.wins} L:{rs.losses} D:{rs.draws}  "
                 f"WR:{red_wr:.1f}%  "
                 f"Shots:{rs.shots}  Conceded:{rs.shots_conceded}")

        ax.text(0, -PITCH_WIDTH / 2 - 0.55, line1,
                ha='center', va='top', fontsize=6.5, color='#93c5fd',
                fontfamily='monospace', zorder=10)
        ax.text(0, -PITCH_WIDTH / 2 - 0.88, line2,
                ha='center', va='top', fontsize=6.5, color='#fca5a5',
                fontfamily='monospace', zorder=10)

    # -------------------------------------------------------------------------
    def update(self, frame):
        sim = self.sim

        # ── End-of-match detection ────────────────────────────────────────
        # A match ends when either:
        #   (a) a goal was scored  → sim.match_over == True
        #   (b) the step limit is reached  (time-out, result is a draw)
        if sim.match_over or sim.step_count >= self.steps_per_match:
            sim.record_match_result()
            end_reason = 'GOAL' if sim.match_over else 'TIME'
            print(f"[Match {self.current_match}/{self.total_matches}]  "
                  f"Blue {sim.blue_goals} - {sim.red_goals} Red  [{end_reason}]")

            self.current_match += 1
            if self.current_match > self.total_matches:
                plt.close(self.fig)   # triggers on_close → prints final stats
                return []
            sim.new_game()            # resets everything for the next match

        # ── Advance simulation one step ───────────────────────────────────
        sim.step()

        # ── Draw everything ───────────────────────────────────────────────
        self._draw_field()
        ax = self.ax
        b  = sim.ball

        for p in sim.all_players:
            self._draw_player(p)

        # Ball shadow and body
        ax.add_patch(patches.Circle(
            (b.x + 0.05, b.y - 0.05), BALL_R_VISUAL,
            fc='black', ec='none', alpha=0.30, zorder=7))
        ax.add_patch(patches.Circle(
            (b.x, b.y), BALL_R_VISUAL,
            fc='white', ec='#fbbf24', lw=2.0, zorder=8))
        # Ball velocity arrow
        spd = np.hypot(b.vx, b.vy)
        if spd > 0.15:
            ax.annotate('', xy=(b.x + b.vx * 0.5, b.y + b.vy * 0.5),
                        xytext=(b.x, b.y),
                        arrowprops=dict(arrowstyle='->', color='#fbbf24',
                                        lw=2.0, mutation_scale=11), zorder=9)

        # HUD bar
        mode_name  = MODE_NAMES.get(sim.mode, sim.mode.upper())
        mode_color = MODE_COLORS.get(sim.mode, 'white')
        phase_txt  = {'kickoff_setup': 'KICKOFF SETUP',
                      'kickoff_wait':  'KICKOFF WAIT',
                      'play':          'PLAY'}.get(sim.phase, sim.phase.upper())

        hud = (f"  Blue {sim.blue_goals}  :  {sim.red_goals} Red  |  "
               f"Match {self.current_match}/{self.total_matches}  |  "
               f"Step {sim.step_count}/{self.steps_per_match}  |  {phase_txt}  ")
        ax.text(0, PITCH_WIDTH / 2 + 0.85, hud,
                ha='center', va='center', fontsize=8.5, color='white',
                fontfamily='monospace',
                bbox=dict(boxstyle='round,pad=0.5', fc='#0d1829', ec='#1e3a5f', lw=1.2),
                zorder=10)

        # Mode label (top-left)
        ax.text(-PITCH_LENGTH / 2 - 0.9, PITCH_WIDTH / 2 + 0.85,
                f"Mode: {mode_name}",
                ha='left', va='center', fontsize=7.5,
                color=mode_color, fontfamily='monospace', fontweight='bold', zorder=10)

        # Formation labels (dynamic mode only) -- shown above each team's half
        if sim.mode == 'dynamic' and sim.phase == 'play':
            blue_form = sim.formation_label('blue')
            red_form  = sim.formation_label('red')
            ax.text(-PITCH_LENGTH / 4, PITCH_WIDTH / 2 + 0.45,
                    f"Blue: {blue_form}",
                    ha='center', va='center', fontsize=8, color='#93c5fd',
                    fontfamily='monospace', fontweight='bold', zorder=10)
            ax.text( PITCH_LENGTH / 4, PITCH_WIDTH / 2 + 0.45,
                    f"Red: {red_form}",
                    ha='center', va='center', fontsize=8, color='#fca5a5',
                    fontfamily='monospace', fontweight='bold', zorder=10)

        # Legend: anchor zone label
        ax.text(-PITCH_LENGTH / 2 + 0.05, PITCH_WIDTH / 2 - 0.05,
                "DEF anchor zone",
                ha='left', va='top', fontsize=5.5, color='#93c5fd',
                fontfamily='monospace', alpha=0.8, zorder=10)
        ax.text( PITCH_LENGTH / 2 - 0.05, PITCH_WIDTH / 2 - 0.05,
                "DEF anchor zone",
                ha='right', va='top', fontsize=5.5, color='#fca5a5',
                fontfamily='monospace', alpha=0.8, zorder=10)

        # Kickoff banner
        if sim.phase in ('kickoff_setup', 'kickoff_wait'):
            ko_txt = f"{'Blue' if sim.kickoff_team == 'blue' else 'Red'} team kicks off"
            ax.text(0, 0, ko_txt, ha='center', va='center',
                    fontsize=13, fontweight='bold', color='#facc15',
                    bbox=dict(boxstyle='round,pad=0.4', fc='#000000aa', ec='#facc15'),
                    zorder=11)

        # Stats bar
        self._draw_stats_bar()

        # Event log
        for i, msg in enumerate(reversed(sim.log[-4:])):
            ax.text(-PITCH_LENGTH / 2 + 0.1,
                    -PITCH_WIDTH / 2 - 1.10 - i * 0.18,
                    msg, ha='left', va='top', fontsize=6.5,
                    color='#94a3b8', fontfamily='monospace', zorder=10)

        return []

    def run(self):
        self._stats_printed = False

        def on_close(event):
            if self._stats_printed:
                return
            self._stats_printed = True
            matches_done = self.current_match - 1
            if matches_done > 0:
                print_final_stats(self.sim, matches_done)
            else:
                print("\n  No matches completed -- no stats to report.\n")

        self.fig.canvas.mpl_connect('close_event', on_close)

        # Use a very large frame count -- the animation stops when
        # plt.close() is called inside update() after all matches finish.
        anim = FuncAnimation(self.fig, self.update, frames=10_000_000,
                             interval=50, blit=False)
        plt.tight_layout()
        plt.show()


# =============================================================================
# FINAL STATISTICS PRINT
# =============================================================================

def print_final_stats(sim: Soccer4v4, matches_done: int):
    bs  = sim.blue_stats
    rs  = sim.red_stats
    sep = "=" * 62

    print()
    print(sep)
    print(f"  FINAL STATISTICS  ({matches_done} matches played)")
    print(f"  Mode (both teams): {MODE_NAMES.get(sim.mode, sim.mode)}")
    print(sep)
    print(f"  {'Metric':<32} {'Blue':>12} {'Red':>12}")
    print(f"  {'-'*32} {'-'*12} {'-'*12}")
    print(f"  {'Wins':<32} {bs.wins:>12} {rs.wins:>12}")
    print(f"  {'Losses':<32} {bs.losses:>12} {rs.losses:>12}")
    print(f"  {'Draws':<32} {bs.draws:>12} {rs.draws:>12}")
    print(f"  {'Win rate (%)':<32} "
          f"{bs.win_rate(matches_done):>11.1f}% "
          f"{rs.win_rate(matches_done):>11.1f}%")
    print(f"  {'Goals scored':<32} {bs.goals_scored:>12} {rs.goals_scored:>12}")
    print(f"  {'Goals conceded':<32} {bs.goals_conceded:>12} {rs.goals_conceded:>12}")
    print(f"  {'Shots taken':<32} {bs.shots:>12} {rs.shots:>12}")
    print(f"  {'Shots conceded':<32} {bs.shots_conceded:>12} {rs.shots_conceded:>12}")
    if matches_done > 0:
        print(f"  {'Shot accuracy (%)':<32} "
              f"{bs.goals_scored/bs.shots*100 if bs.shots else 0:>11.1f}% "
              f"{rs.goals_scored/rs.shots*100 if rs.shots else 0:>11.1f}%")
    if sim.mode == 'dynamic':
        print(f"  {'Formation switches':<32} "
              f"{bs.formation_switches:>12} {rs.formation_switches:>12}")
    print(sep)
    print()


# =============================================================================
# PRE-GAME MENU
# =============================================================================

def select_mode() -> tuple:
    print()
    print("=" * 62)
    print("  4v4 Robot Soccer -- Formation Mode Selection")
    print("=" * 62)
    print()
    print("  Both teams will use the same selected mode.")
    print()
    print("  [1]  Always Attack  -- Both teams always use attack formation.")
    print("                         DEF (pid=1) stays anchored near own goal")
    print("                         as permanent last-line guardian.")
    print()
    print("  [2]  Always Defend  -- Both teams always use defend formation.")
    print("                         No formation switch on ball position.")
    print()
    print("  [3]  Dynamic        -- Formation switches on ball position.")
    print("                         Each team defends when ball is in their")
    print("                         own half; attacks when ball is in enemy")
    print("                         half. (default)")
    print()

    mode_map = {'1': 'always_attack', '2': 'always_defend', '3': 'dynamic'}
    while True:
        choice = input("  Enter option [1/2/3] (Enter = default 3): ").strip()
        if choice == '':
            choice = '3'
        if choice in mode_map:
            mode = mode_map[choice]
            break
        print("  Invalid input. Please enter 1, 2, or 3.")

    print()
    while True:
        raw = input("  Enter number of matches (Enter = default 30): ").strip()
        if raw == '':
            total_matches = 30
            break
        try:
            total_matches = int(raw)
            if total_matches > 0:
                break
            print("  Please enter a positive integer.")
        except ValueError:
            print("  Please enter a valid number.")

    steps_per_match = 2000   # ~100 seconds per match at 50 ms/step

    print()
    print(f"  Mode selected  : {MODE_NAMES[mode]}")
    print(f"  Matches        : {total_matches}")
    print(f"  Steps / match  : {steps_per_match}  "
          f"(~{steps_per_match * 50 // 1000}s per match)")
    print()
    print("  Permanent rule: DEF (pid=1) always anchors near own goal")
    print("  in all modes to ensure at least one field defender is present.")
    print()
    print("  Close the window to quit early.")
    print("=" * 62)
    print()

    return mode, total_matches, steps_per_match


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == '__main__':
    mode, total_matches, steps_per_match = select_mode()
    sim = Soccer4v4(mode=mode)
    viz = Visualiser(sim, total_matches=total_matches, steps_per_match=steps_per_match)
    viz.run()