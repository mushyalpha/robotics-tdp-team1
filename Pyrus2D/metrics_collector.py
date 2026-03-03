"""
Metrics Collector — Per-step data logging for behavior analysis
================================================================

Wraps a SoccerSimulator and logs per-step state for later analysis.
Exports match results as JSON for batch processing.
"""

import json
import os
import numpy as np

PITCH_LENGTH = 9.0
GOAL_WIDTH = 2.6
SHOT_QUALITY_DISTANCE_LAMBDA = 2.0
SHOT_QUALITY_ANGLE_REF_RAD = 0.7
SHOT_QUALITY_W_DISTANCE = 0.5
SHOT_QUALITY_W_ANGLE = 0.5


def _cross(o, a, b):
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def _convex_hull(points):
    """Monotonic chain convex hull. Returns hull vertices in CCW order."""
    pts = sorted(set(points))
    if len(pts) <= 1:
        return pts

    lower = []
    for p in pts:
        while len(lower) >= 2 and _cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)

    upper = []
    for p in reversed(pts):
        while len(upper) >= 2 and _cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)

    return lower[:-1] + upper[:-1]


def _polygon_area(poly):
    """Shoelace area for polygon points in order."""
    if len(poly) < 3:
        return 0.0
    area = 0.0
    for i in range(len(poly)):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % len(poly)]
        area += x1 * y2 - x2 * y1
    return abs(area) * 0.5


class MetricsCollector:
    """Collects per-step and match-level metrics from a simulation."""

    def __init__(self, sim):
        """
        Args:
            sim: SoccerSimulator (v3) instance
        """
        self.sim = sim
        self.step_data = []
        self.events = []  # Goals, set pieces, etc.

        # Falls
        self.falls_per_game = 0
        self._prev_robot_fallen = {
            (r.team, r.id): (r.state.value == 'FALLEN') for r in self.sim.robots
        }

        # Aggregate counters
        self.blue_possession_steps = 0
        self.red_possession_steps = 0
        self.blue_shot_quality_sum = 0.0
        self.red_shot_quality_sum = 0.0
        self.blue_shots_counted = 0
        self.red_shots_counted = 0
        self.blue_danger_zone_steps = 0   # Ball in opponent third
        self.red_danger_zone_steps = 0
        self.blue_danger_entries = 0
        self.red_danger_entries = 0

        # Possession + continuity (defined by last touch)
        self.turnover_count = 0
        self._prev_touch_team = None

        # Net territory gain per possession
        self._current_possession_team = None
        self._current_possession_start_x = None
        self.blue_possession_progress = []
        self.red_possession_progress = []

        # Danger zone entry tracking
        self._prev_danger_owner = None

        # Spacing during possession (convex hull area + centroid)
        self.blue_spacing_samples = 0
        self.red_spacing_samples = 0
        self.blue_hull_area_sum = 0.0
        self.red_hull_area_sum = 0.0
        self.blue_centroid_x_sum = 0.0
        self.blue_centroid_y_sum = 0.0
        self.red_centroid_x_sum = 0.0
        self.red_centroid_y_sum = 0.0

    def _close_possession(self, end_ball_x):
        """Finalize currently tracked possession and store forward progression."""
        if self._current_possession_team not in ('blue', 'red'):
            return
        if self._current_possession_start_x is None:
            return

        attack_direction = 1 if self._current_possession_team == 'blue' else -1
        progress = (end_ball_x - self._current_possession_start_x) * attack_direction
        if self._current_possession_team == 'blue':
            self.blue_possession_progress.append(progress)
        else:
            self.red_possession_progress.append(progress)

        self._current_possession_team = None
        self._current_possession_start_x = None

    def _record_spacing_sample(self, team):
        if team == 'blue':
            robots = self.sim.blue_robots
        else:
            robots = self.sim.red_robots

        points = [(float(r.x), float(r.y)) for r in robots if not r.is_incapacitated()]
        if not points:
            return

        centroid_x = float(np.mean([p[0] for p in points]))
        centroid_y = float(np.mean([p[1] for p in points]))
        hull_area = _polygon_area(_convex_hull(points))

        if team == 'blue':
            self.blue_spacing_samples += 1
            self.blue_hull_area_sum += hull_area
            self.blue_centroid_x_sum += centroid_x
            self.blue_centroid_y_sum += centroid_y
        else:
            self.red_spacing_samples += 1
            self.red_hull_area_sum += hull_area
            self.red_centroid_x_sum += centroid_x
            self.red_centroid_y_sum += centroid_y

    def _compute_shot_quality(self, robot):
        """Shot quality from distance + visible goal angle (no blocker model)."""
        attack_direction = 1 if robot.team == 'blue' else -1
        goal_x = (PITCH_LENGTH / 2) * attack_direction
        goal_top_y = GOAL_WIDTH / 2
        goal_bot_y = -GOAL_WIDTH / 2

        dx = goal_x - robot.x
        dy = 0.0 - robot.y
        dist_to_goal = float(np.sqrt(dx**2 + dy**2))

        angle_top = np.arctan2(goal_top_y - robot.y, goal_x - robot.x)
        angle_bot = np.arctan2(goal_bot_y - robot.y, goal_x - robot.x)
        visible_angle = abs((angle_top - angle_bot + np.pi) % (2 * np.pi) - np.pi)

        distance_term = float(np.exp(-dist_to_goal / SHOT_QUALITY_DISTANCE_LAMBDA))
        angle_term = float(min(1.0, visible_angle / SHOT_QUALITY_ANGLE_REF_RAD))

        sq = SHOT_QUALITY_W_DISTANCE * distance_term + SHOT_QUALITY_W_ANGLE * angle_term
        return float(np.clip(sq, 0.0, 1.0))

    def record_step(self):
        """Record metrics for the current simulation step."""
        sim = self.sim

        # Falls per game (count transitions into FALLEN)
        for robot in sim.robots:
            key = (robot.team, robot.id)
            is_fallen = (robot.state.value == 'FALLEN')
            was_fallen = self._prev_robot_fallen.get(key, False)
            if is_fallen and not was_fallen:
                self.falls_per_game += 1
            self._prev_robot_fallen[key] = is_fallen

        # Possession (defined by last touch team)
        possession = sim.last_touch_team if sim.last_touch_team in ('blue', 'red') else None
        if possession == 'blue':
            self.blue_possession_steps += 1
            self._record_spacing_sample('blue')
        elif possession == 'red':
            self.red_possession_steps += 1
            self._record_spacing_sample('red')

        # Turnovers + possession segment tracking
        if possession in ('blue', 'red'):
            if self._prev_touch_team in ('blue', 'red') and possession != self._prev_touch_team:
                self.turnover_count += 1
                self._close_possession(sim.ball.x)

            if self._current_possession_team is None:
                self._current_possession_team = possession
                self._current_possession_start_x = sim.ball.x
            elif self._current_possession_team != possession:
                self._close_possession(sim.ball.x)
                self._current_possession_team = possession
                self._current_possession_start_x = sim.ball.x

            self._prev_touch_team = possession

        # Danger zone (opponent's third)
        pitch_third = 9.0 / 3.0
        danger_owner = None
        if sim.ball.x > pitch_third / 2:
            self.blue_danger_zone_steps += 1  # Blue attacking red's third
            danger_owner = 'blue'
        elif sim.ball.x < -pitch_third / 2:
            self.red_danger_zone_steps += 1   # Red attacking blue's third
            danger_owner = 'red'

        if danger_owner in ('blue', 'red') and danger_owner != self._prev_danger_owner:
            if danger_owner == 'blue':
                self.blue_danger_entries += 1
            else:
                self.red_danger_entries += 1
        self._prev_danger_owner = danger_owner

        # Shot quality tracking (on shot start)
        for robot in sim.robots:
            if robot.state.value == "KICKING" and robot.state_duration == 0:
                sq = self._compute_shot_quality(robot)
                if robot.team == 'blue':
                    self.blue_shot_quality_sum += sq
                    self.blue_shots_counted += 1
                else:
                    self.red_shot_quality_sum += sq
                    self.red_shots_counted += 1

    def record_event(self, event_type, details=None):
        """Record a discrete event (goal, set piece, etc.)."""
        self.events.append({
            'step': self.sim.time,
            'type': event_type,
            'details': details or {}
        })

    def get_summary(self):
        """Generate match-level summary statistics."""
        sim = self.sim
        self._close_possession(sim.ball.x)

        total_steps = max(1, sim.time)
        elapsed_seconds = sim.time * 0.05
        elapsed_minutes = max(1e-9, elapsed_seconds / 60.0)

        blue_net_territory_gain = float(np.mean(self.blue_possession_progress)) if self.blue_possession_progress else 0.0
        red_net_territory_gain = float(np.mean(self.red_possession_progress)) if self.red_possession_progress else 0.0

        blue_avg_hull_area = self.blue_hull_area_sum / max(1, self.blue_spacing_samples)
        red_avg_hull_area = self.red_hull_area_sum / max(1, self.red_spacing_samples)
        blue_avg_centroid_x = self.blue_centroid_x_sum / max(1, self.blue_spacing_samples)
        blue_avg_centroid_y = self.blue_centroid_y_sum / max(1, self.blue_spacing_samples)
        red_avg_centroid_x = self.red_centroid_x_sum / max(1, self.red_spacing_samples)
        red_avg_centroid_y = self.red_centroid_y_sum / max(1, self.red_spacing_samples)
        spacing_centroid_progress_balance = blue_avg_centroid_x - (-red_avg_centroid_x)
        blue_avg_shot_quality = self.blue_shot_quality_sum / max(1, self.blue_shots_counted)
        red_avg_shot_quality = self.red_shot_quality_sum / max(1, self.red_shots_counted)

        summary = {
            # Match info
            'behavior_mode': getattr(sim, 'behavior_mode', 'adaptive'),
            'blue_personality': getattr(sim, 'blue_personality', 'unknown'),
            'red_personality': getattr(sim, 'red_personality', 'unknown'),
            'blue_goals': sim.blue_goals,
            'red_goals': sim.red_goals,
            'winner': 'blue' if sim.blue_goals > sim.red_goals
                      else 'red' if sim.red_goals > sim.blue_goals
                      else 'draw',
            'total_steps': sim.time,
            'elapsed_seconds': elapsed_seconds,
            'falls_per_game': self.falls_per_game,

            # Possession
            'blue_possession_pct': round(100 * self.blue_possession_steps / total_steps, 1),
            'red_possession_pct': round(100 * self.red_possession_steps / total_steps, 1),
            'turnovers_per_min': round(self.turnover_count / elapsed_minutes, 2),

            # Territory progression
            'blue_net_territory_gain': round(blue_net_territory_gain, 3),
            'red_net_territory_gain': round(red_net_territory_gain, 3),
            'net_territory_gain_balance': round(blue_net_territory_gain - red_net_territory_gain, 3),

            # Danger zone
            'blue_danger_zone_pct': round(100 * self.blue_danger_zone_steps / max(1, sim.time), 1),
            'red_danger_zone_pct': round(100 * self.red_danger_zone_steps / max(1, sim.time), 1),
            'blue_danger_entries': self.blue_danger_entries,
            'red_danger_entries': self.red_danger_entries,
            'danger_entry_balance': self.blue_danger_entries - self.red_danger_entries,
            'danger_zone_balance': round(
                (100 * self.blue_danger_zone_steps / max(1, sim.time))
                - (100 * self.red_danger_zone_steps / max(1, sim.time)),
                1,
            ),

            # Shot quality (distance + angle only)
            'blue_shot_quality_sum': round(self.blue_shot_quality_sum, 3),
            'red_shot_quality_sum': round(self.red_shot_quality_sum, 3),
            'blue_avg_shot_quality': round(blue_avg_shot_quality, 3),
            'red_avg_shot_quality': round(red_avg_shot_quality, 3),
            'shot_quality_balance': round(self.blue_shot_quality_sum - self.red_shot_quality_sum, 3),

            # Spacing / coordination during own possession
            'blue_avg_hull_area': round(blue_avg_hull_area, 3),
            'red_avg_hull_area': round(red_avg_hull_area, 3),
            'spacing_area_balance': round(blue_avg_hull_area - red_avg_hull_area, 3),
            'blue_avg_centroid_x': round(blue_avg_centroid_x, 3),
            'blue_avg_centroid_y': round(blue_avg_centroid_y, 3),
            'red_avg_centroid_x': round(red_avg_centroid_x, 3),
            'red_avg_centroid_y': round(red_avg_centroid_y, 3),
            'spacing_centroid_progress_balance': round(spacing_centroid_progress_balance, 3),
        }

        return summary

    def save_to_json(self, filepath):
        """Save match summary to a JSON file."""
        summary = self.get_summary()
        os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(summary, f, indent=2)
        return filepath
