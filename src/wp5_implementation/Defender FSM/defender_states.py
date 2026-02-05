# defender_states.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Tuple
import math


# ---------- Shared Action definition (minimal) ----------
@dataclass
class Action:
    """
    Minimal action command produced by states/FSM and consumed by the player.
    type: "IDLE" | "WALK_TO" | "TURN_TO" | "KICK" | "STOP"
    """
    type: str
    target_xy: Optional[Tuple[float, float]] = None
    target_theta: Optional[float] = None
    speed: float = 0.5
    kick_dir: Optional[Tuple[float, float]] = None
    kick_power: float = 1.0


# ---------- Helper utilities ----------
def _dist(x1: float, y1: float, x2: float, y2: float) -> float:
    dx, dy = x2 - x1, y2 - y1
    return math.hypot(dx, dy)

def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


# ---------- State base ----------
class DefenderState:
    name: str = "Base"

    def on_enter(self, world) -> None:
        pass

    def on_exit(self, world) -> None:
        pass

    def check_transition(self, world) -> Optional[str]:
        """Return next state's name, or None to stay."""
        return None

    def execute(self, world) -> Action:
        """Return an Action for this timestep."""
        return Action(type="IDLE")


# ---------- Concrete states ----------
class HoldZone(DefenderState):
    name = "HoldZone"

    # Tunable thresholds (MVP)
    THREAT_DIST_TO_GOAL = 2.0     # if ball is within this distance to our goal -> threat
    GO_INTERCEPT_DIST = 2.5       # if ball is close enough to defender -> intercept
    HOLD_X_OFFSET = 1.2           # stand this far in front of our goal (towards field center)
    HOLD_Y_GAIN = 0.4             # follow ball y slightly

    def check_transition(self, world) -> Optional[str]:
        if world.game.phase != "PLAYING":
            return None

        bx, by = world.ball.pos
        gx, gy = world.field.our_goal
        rx, ry, _ = world.robot.pose

        dist_ball_goal = _dist(bx, by, gx, gy)
        dist_robot_ball = _dist(rx, ry, bx, by)

        # Threat near our goal OR ball is close to us -> try intercept
        if dist_ball_goal < self.THREAT_DIST_TO_GOAL or dist_robot_ball < self.GO_INTERCEPT_DIST:
            return "InterceptBall"
        return None

    def execute(self, world) -> Action:
        # Hold a simple defensive position: in front of our goal, y follows ball a bit
        gx, gy = world.field.our_goal
        bx, by = world.ball.pos

        target_x = gx + self.HOLD_X_OFFSET
        target_y = gy + _clamp((by - gy) * self.HOLD_Y_GAIN, -0.6, 0.6)

        # Face the ball
        rx, ry, _ = world.robot.pose
        target_theta = math.atan2(by - ry, bx - rx)

        return Action(type="WALK_TO", target_xy=(target_x, target_y), target_theta=target_theta, speed=0.5)


class InterceptBall(DefenderState):
    name = "InterceptBall"

    CLOSE_TO_BALL = 0.35
    PREDICT_T = 0.5               # seconds, rough prediction horizon
    LOST_THREAT_DIST = 2.6        # hysteresis: leave intercept when ball is far from goal

    def check_transition(self, world) -> Optional[str]:
        if world.game.phase != "PLAYING":
            return "HoldZone"

        rx, ry, _ = world.robot.pose
        bx, by = world.ball.pos
        gx, gy = world.field.our_goal

        dist_robot_ball = _dist(rx, ry, bx, by)
        dist_ball_goal = _dist(bx, by, gx, gy)

        if dist_robot_ball < self.CLOSE_TO_BALL:
            return "ClearBall"

        if dist_ball_goal > self.LOST_THREAT_DIST:
            return "HoldZone"

        return None

    def execute(self, world) -> Action:
        # Go to predicted ball point (very simple)
        bx, by = world.ball.pos
        vx, vy = world.ball.vel

        px = bx + vx * self.PREDICT_T
        py = by + vy * self.PREDICT_T

        rx, ry, _ = world.robot.pose
        target_theta = math.atan2(by - ry, bx - rx)

        return Action(type="WALK_TO", target_xy=(px, py), target_theta=target_theta, speed=0.7)


class ClearBall(DefenderState):
    name = "ClearBall"

    TOO_FAR_FROM_BALL = 0.55

    def check_transition(self, world) -> Optional[str]:
        if world.game.phase != "PLAYING":
            return "HoldZone"

        rx, ry, _ = world.robot.pose
        bx, by = world.ball.pos
        dist_robot_ball = _dist(rx, ry, bx, by)

        if dist_robot_ball > self.TOO_FAR_FROM_BALL:
            return "InterceptBall"
        return None

    def execute(self, world) -> Action:
        # Clear away from our goal: kick direction from goal -> ball (push ball outward)
        bx, by = world.ball.pos
        gx, gy = world.field.our_goal

        dx = bx - gx
        dy = by - gy
        norm = math.hypot(dx, dy) + 1e-9
        kick_dir = (dx / norm, dy / norm)

        return Action(type="KICK", kick_dir=kick_dir, kick_power=1.0)
