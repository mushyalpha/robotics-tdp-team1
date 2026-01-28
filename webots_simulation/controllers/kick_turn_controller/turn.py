# nao_turn_and_pid_reset.py
# Functions:
# 1) Input a target turn angle (deg=90 / deg=-40 / rad=1.57);
# 2) Closed-loop IMU yaw: choose a combination of TurnLeft40/60/180 or TurnRight40/60 based on the error;
# 3) Stop when |error| < 40deg;
# 4) Enter PID reset (works even without Stand.motion; improves stability / reduces foot collisions).

import math
import os
import sys
from controller import Robot, Motion


# -------------------- Configuration you may adjust for your project --------------------
MOTION_PATHS = {
    "L40":  "../../motions/TurnLeft40.motion",
    "L60":  "../../motions/TurnLeft60.motion",
    "L180": "../../motions/TurnLeft180.motion",
    "R40":  "../../motions/TurnRight40.motion",
    "R60":  "../../motions/TurnRight60.motion",
}

# Stop threshold: stop turning when the error is smaller than 10 degrees
STOP_THRESHOLD_DEG = 10.0

#Turning angle
DELTA=90

# Max number of turn actions (prevents infinite loops)
MAX_TURN_STEPS = 30

# PID reset duration
RESET_DURATION_S = 0.8

# PID reset target pose (wide stance: larger foot separation to reduce foot collisions)
RESET_POSE = {
    "LHipRoll":  +0.07,
    "RHipRoll":  -0.07,
    "LKneePitch": 0.18,
    "RKneePitch": 0.18,
    "LAnkleRoll": -0.035,
    "RAnkleRoll": +0.035,
    "LAnklePitch": -0.10,
    "RAnklePitch": -0.10,
    "LHipPitch":  0.00,
    "RHipPitch":  0.00,
}

RESET_JOINTS = list(RESET_POSE.keys())

# Outer-loop PID parameters (recommended to start with PD: Ki=0)
PID_KP = 0.60
PID_KI = 0.00
PID_KD = 0.10

# Maximum change allowed for the "progressive target" per timestep
# (smaller = more stable, larger = faster)
PID_MAX_STEP_RAD = 0.05

# -----------------------------------------------------------------


def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def wrap_to_pi(a: float) -> float:
    """Normalize to [-pi, pi]."""
    while a > math.pi:
        a -= 2 * math.pi
    while a < -math.pi:
        a += 2 * math.pi
    return a


class JointPIDReset:
    """
    Outer-loop PID: read joint angles each step, compute PID output, update a "progressive target",
    then apply setPosition().
    Note: Webots setPosition() already uses an internal position servo; this class is used to smooth
    the reset between motions and improve steady-state convergence.
    """
    def __init__(self, robot: Robot, timestep_ms: int, motor_names):
        self.robot = robot
        self.timestep_ms = timestep_ms
        self.dt = timestep_ms / 1000.0

        self.motors = {}
        self.sensors = {}
        self.limits = {}

        # Allow missing joints (more robust), but print warnings
        self.available = []
        for name in motor_names:
            m = robot.getDevice(name)
            if not m:
                print(f"[RESET] WARNING: motor not found: {name} (skipped)")
                continue

            ps = m.getPositionSensor()
            if not ps:
                print(f"[RESET] WARNING: PositionSensor not found for: {name} (skipped)")
                continue

            ps.enable(timestep_ms)
            self.motors[name] = m
            self.sensors[name] = ps
            self.available.append(name)

            try:
                self.limits[name] = (m.getMinPosition(), m.getMaxPosition())
            except Exception:
                self.limits[name] = (-float("inf"), float("inf"))

        if not self.available:
            raise RuntimeError("[RESET] No joints available for PID reset. Check joint names.")

        self.i_term = {n: 0.0 for n in self.available}
        self.prev_err = {n: 0.0 for n in self.available}

        self.Kp = PID_KP
        self.Ki = PID_KI
        self.Kd = PID_KD
        self.max_step = PID_MAX_STEP_RAD
        self.i_limit = 0.4

    def set_gains(self, kp, ki, kd):
        self.Kp, self.Ki, self.Kd = kp, ki, kd

    def reset_integrators(self):
        for k in self.available:
            self.i_term[k] = 0.0
            self.prev_err[k] = 0.0

    def pid_reset_pose(self, pose_targets: dict, duration_s=0.8, tol_rad=0.04):
        steps = int(duration_s / self.dt)
        # Progressive targets start from the current joint angles to avoid sudden jumps
        cur_target = {}
        for j in self.available:
            if j in pose_targets:
                cur_target[j] = self.sensors[j].getValue()

        for _ in range(steps):
            if self.robot.step(self.timestep_ms) == -1:
                break

            all_ok = True
            for j in self.available:
                if j not in pose_targets:
                    continue

                tgt = pose_targets[j]
                cur = self.sensors[j].getValue()
                err = tgt - cur

                if abs(err) > tol_rad:
                    all_ok = False

                derr = (err - self.prev_err[j]) / self.dt
                self.prev_err[j] = err

                self.i_term[j] += err * self.dt
                self.i_term[j] = clamp(self.i_term[j], -self.i_limit, self.i_limit)

                u = self.Kp * err + self.Ki * self.i_term[j] + self.Kd * derr
                delta = clamp(u, -self.max_step, self.max_step)
                cur_target[j] += delta

                mn, mx = self.limits[j]
                cur_target[j] = clamp(cur_target[j], mn, mx)
                self.motors[j].setPosition(cur_target[j])

            if all_ok:
                break


class NAOTurnAndResetController:
    def __init__(self):
        self.robot = Robot()
        self.timestep = int(self.robot.getBasicTimeStep())

        self.imu = self._get_imu()
        self.imu.enable(self.timestep)

        self.motions = {k: self._load_motion(p, k) for k, p in MOTION_PATHS.items()}

        # PID reset helper
        self.pid_reset = JointPIDReset(self.robot, self.timestep, RESET_JOINTS)
        self.pid_reset.set_gains(PID_KP, PID_KI, PID_KD)

        # Nominal motion angles (used for "combination selection")
        # Note: these are nominal values and may not match actual yaw change; closed-loop error corrects it.
        self.step_nominal = {
            "L40":  math.radians(40),
            "L60":  math.radians(60),
            "L180": math.radians(180),
            "R40":  math.radians(40),
            "R60":  math.radians(60),
        }

        self.stop_threshold_rad = math.radians(STOP_THRESHOLD_DEG)

    def _get_imu(self):
        for name in ["inertial unit", "InertialUnit", "imu", "IMU"]:
            try:
                dev = self.robot.getDevice(name)
            except Exception:
                dev = None
            if dev:
                print(f"[IMU] Using device: {name}")
                return dev
        raise RuntimeError("IMU/InertialUnit not found. Please check the device name in the Scene Tree and update the candidate list.")

    def _load_motion(self, path: str, key: str) -> Motion:
        if not os.path.exists(path):
            raise FileNotFoundError(f"[MOTION] Missing {key}: {path} (please check the path/file name)")
        print(f"[MOTION] Loaded {key}: {path}")
        return Motion(path)

    def yaw(self) -> float:
        return self.imu.getRollPitchYaw()[2]

    def step(self, n=1) -> bool:
        for _ in range(n):
            if self.robot.step(self.timestep) == -1:
                return False
        return True

    def play_motion_blocking(self, motion: Motion):
        motion.play()
        while not motion.isOver():
            if not self.step(1):
                break
        self.step(2)  # stabilize a bit

    def choose_motion_key(self, err_rad: float) -> str:
        """
        Choose a motion based on error magnitude (combination strategy):
          - Left: prefer 180 (very large error), else 60, else 40
          - Right: only 60/40
        Stop logic is handled outside: stop when |err| < 40deg and do not call any motion.
        """
        left = err_rad > 0
        mag = abs(err_rad)

        if left:
            # Very large error: use 180 to converge faster (only available for left)
            if mag >= math.radians(140):
                return "L180"
            # Medium error: use 60
            if mag >= math.radians(70):
                return "L60"
            # Near the stop threshold but still >= 40: use 40
            return "L40"
        else:
            # Right has no 180: large error -> 60, small error -> 40
            if mag >= math.radians(70):
                return "R60"
            return "R40"

    def turn_then_reset(self, delta_yaw_rad: float):
        """
        Main flow:
          1) Compute target yaw (relative turn)
          2) Loop: read yaw -> compute error -> if |error|<40deg stop -> else play a motion
          3) After stopping, perform PID reset (stability)
        """
        start = self.yaw()
        target = wrap_to_pi(start + delta_yaw_rad)
        print(f"[TURN] start={start:+.3f} target={target:+.3f} delta={delta_yaw_rad:+.3f}")
        print(f"[TURN] stop when |err| < {STOP_THRESHOLD_DEG:.1f} deg")

        for i in range(MAX_TURN_STEPS):
            cur = self.yaw()
            err = wrap_to_pi(target - cur)

            print(f"[TURN] step={i:02d} cur={cur:+.3f} err={err:+.3f} ({math.degrees(err):+.1f} deg)")

            if abs(err) < self.stop_threshold_rad:
                print("[TURN] ✓ Stop threshold reached. Enter PID reset.")
                break

            key = self.choose_motion_key(err)

            # Safety: if error is close to threshold but key chooses 60/180,
            # it may overshoot and cause foot collisions.
            # Since your stop threshold is 40deg, apply a conservative protection:
            # disable 180 when |err| < 120deg.
            if key == "L180" and abs(err) < math.radians(120):
                key = "L60"

            self.play_motion_blocking(self.motions[key])

        # PID reset: return legs to a wide stance to reduce foot collisions accumulated across motions
        self.pid_reset.reset_integrators()
        self.pid_reset.pid_reset_pose(RESET_POSE, duration_s=RESET_DURATION_S, tol_rad=0.05)
        print("[RESET] ✓ PID reset done.")

    def run(self):
        delta = math.radians(DELTA)
        self.turn_then_reset(delta)

        # Keep running
        while self.step(1):
            pass


def main():
    ctrl = NAOTurnAndResetController()
    ctrl.run()


if __name__ == "__main__":
    main()
