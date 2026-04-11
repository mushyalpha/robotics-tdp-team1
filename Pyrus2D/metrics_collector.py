"""
Metrics Collector — Per-step data logging for behavior analysis
================================================================

Wraps a SoccerSimulator and logs per-step state for later analysis.
Exports match results as JSON for batch processing.
"""

import json
import os
import numpy as np
from datetime import datetime


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

        # Aggregate counters
        self.blue_possession_steps = 0
        self.red_possession_steps = 0
        self.blue_shots = 0
        self.red_shots = 0
        self.blue_shots_on_target = 0   # Shot where ball travels toward opponent goal
        self.red_shots_on_target = 0
        self.blue_danger_zone_steps = 0   # Ball in opponent third
        self.red_danger_zone_steps = 0
        self.blue_falls = 0
        self.red_falls = 0
        self.blue_distance = {i: 0.0 for i in range(1, 5)}  # Per-player distance
        self.red_distance = {i: 0.0 for i in range(5, 9)}
        self.prev_positions = {}  # For distance tracking

        # Team centroid X (average outfield player X position)
        self.blue_centroid_x_sum = 0.0
        self.red_centroid_x_sum = 0.0
        self.centroid_steps = 0

    def record_step(self):
        """Record metrics for the current simulation step."""
        sim = self.sim

        # Possession (which team is closer to ball)
        blue_dists = [r.get_distance_to({'x': sim.ball.x, 'y': sim.ball.y})
                      for r in sim.blue_robots]
        red_dists = [r.get_distance_to({'x': sim.ball.x, 'y': sim.ball.y})
                     for r in sim.red_robots]
        min_blue = min(blue_dists)
        min_red = min(red_dists)

        if min_blue < min_red:
            self.blue_possession_steps += 1
            possession = 'blue'
        else:
            self.red_possession_steps += 1
            possession = 'red'

        # Danger zone (opponent's third)
        pitch_third = 9.0 / 3.0
        if sim.ball.x > pitch_third / 2:
            self.blue_danger_zone_steps += 1  # Blue attacking red's third
        elif sim.ball.x < -pitch_third / 2:
            self.red_danger_zone_steps += 1   # Red attacking blue's third

        # Distance covered
        for robot in sim.robots:
            rid = robot.id
            if rid in self.prev_positions:
                px, py = self.prev_positions[rid]
                dist = np.sqrt((robot.x - px)**2 + (robot.y - py)**2)
                if robot.team == 'blue':
                    self.blue_distance[rid] = self.blue_distance.get(rid, 0) + dist
                else:
                    self.red_distance[rid] = self.red_distance.get(rid, 0) + dist
            self.prev_positions[rid] = (robot.x, robot.y)

        # Falls tracking
        for robot in sim.robots:
            if robot.state.value == "FALLEN" and robot.state_duration == 0:
                if robot.team == 'blue':
                    self.blue_falls += 1
                else:
                    self.red_falls += 1

        # Shots tracking (kick actions toward goal)
        # Shots on target: ball velocity points toward opponent's goal at moment of kick
        for robot in sim.robots:
            if robot.state.value == "KICKING" and robot.state_duration == 0:
                if robot.team == 'blue':
                    self.blue_shots += 1
                    if sim.ball.vx > 0:   # Ball heading toward red goal (+X)
                        self.blue_shots_on_target += 1
                else:
                    self.red_shots += 1
                    if sim.ball.vx < 0:   # Ball heading toward blue goal (-X)
                        self.red_shots_on_target += 1

        # Team centroid X (outfield players only)
        blue_outfield = [r for r in sim.blue_robots
                         if r.role.name != 'GOALKEEPER']
        red_outfield = [r for r in sim.red_robots
                        if r.role.name != 'GOALKEEPER']
        if blue_outfield:
            self.blue_centroid_x_sum += np.mean([r.x for r in blue_outfield])
        if red_outfield:
            self.red_centroid_x_sum += np.mean([r.x for r in red_outfield])
        self.centroid_steps += 1

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
        total_steps = max(1, self.blue_possession_steps + self.red_possession_steps)

        summary = {
            # Match info
            'blue_profile': sim.blue_profile.name,
            'red_profile': sim.red_profile.name,
            'blue_goals': sim.blue_goals,
            'red_goals': sim.red_goals,
            'winner': 'blue' if sim.blue_goals > sim.red_goals
                      else 'red' if sim.red_goals > sim.blue_goals
                      else 'draw',
            'total_steps': sim.time,
            'elapsed_seconds': sim.time * 0.05,

            # Possession
            'blue_possession_pct': round(100 * self.blue_possession_steps / total_steps, 1),
            'red_possession_pct': round(100 * self.red_possession_steps / total_steps, 1),

            # Offense
            'blue_shots': self.blue_shots,
            'red_shots': self.red_shots,
            'blue_shots_on_target': self.blue_shots_on_target,
            'red_shots_on_target': self.red_shots_on_target,
            'blue_passes': sim.total_passes_blue,
            'red_passes': sim.total_passes_red,

            # Danger zone
            'blue_danger_zone_pct': round(100 * self.blue_danger_zone_steps / max(1, sim.time), 1),
            'red_danger_zone_pct': round(100 * self.red_danger_zone_steps / max(1, sim.time), 1),

            # Physical
            'blue_falls': self.blue_falls,
            'red_falls': self.red_falls,
            'blue_total_distance': round(sum(self.blue_distance.values()), 1),
            'red_total_distance': round(sum(self.red_distance.values()), 1),

            # Per-player distances
            'blue_distance_per_player': {str(k): round(v, 1) for k, v in self.blue_distance.items()},
            'red_distance_per_player': {str(k): round(v, 1) for k, v in self.red_distance.items()},

            # Team centroid X (average outfield player X over the match)
            'blue_avg_centroid_x': round(self.blue_centroid_x_sum / max(1, self.centroid_steps), 3),
            'red_avg_centroid_x': round(self.red_centroid_x_sum / max(1, self.centroid_steps), 3),
        }

        return summary

    def save_to_json(self, filepath):
        """Save match summary to a JSON file."""
        summary = self.get_summary()
        os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(summary, f, indent=2)
        return filepath
