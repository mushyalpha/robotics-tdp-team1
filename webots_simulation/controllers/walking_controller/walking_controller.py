from controller import Robot
import math
from scipy.interpolate import make_interp_spline
import pandas as pd
import os
from typing import Dict, Any
import json  # ★ NEW


# Joint names for convenience / clarity
JOINT_NAMES_L = [
    "LHipYawPitch", "LHipRoll", "LHipPitch",
    "LKneePitch", "LAnklePitch", "LAnkleRoll"
]
JOINT_NAMES_R = [
    "RHipYawPitch", "RHipRoll", "RHipPitch",
    "RKneePitch", "RAnklePitch", "RAnkleRoll"
]

EPS = 1e-6


class WalkingMin:
    """
    Walking controller using three gait templates:
      - start: rest -> start walking (one-shot)
      - walk : continuous walking (loopable)
      - stop : walking -> rest (one-shot)

    Gaits are defined in CSVs with columns:
      frac_step, LHipYawPitch, LHipRoll, ..., RAnkleRoll
    """

    def __init__(
        self,
        start_csv: str = "rest_to_start.csv",
        walk_csv: str = "forward_walk_gait.csv",
        stop_csv: str = "walk_to_rest.csv",
        target_steps: int = 4,            # fallback if no distance / no GPS
        target_distance: float | None = None,  # [m] total distance from start
        stop_distance_offset: float = 0.2      # [m] expected distance during stop
    ) -> None:
        self.robot = Robot()
        # Convert Webots basicTimeStep (ms) to seconds
        self.dt: float = int(self.robot.getBasicTimeStep()) / 1000.0

        # ★ NEW: access own node and track last customData payload
        self._last_custom_data: str = ""

        # Motor devices setup
        self.motors: Dict[str, Any] = {}
        for name in JOINT_NAMES_L + JOINT_NAMES_R:
            m = self.robot.getDevice(name)
            # limit velocity to 90% of max for smoother motion
            m.setVelocity(m.getMaxVelocity() * 0.9)
            self.motors[name] = m

        # Start at neutral posture
        self.neutral = dict(
            HipYawPitch=0.0,
            HipRoll=0.0,
            HipPitch=-0.5,
            KneePitch=1.0,
            AnklePitch=-0.5,
            AnkleRoll=0.0,
        )
        self.set_neutral()

        # Gait parameters for continuous walking state
        self.f0: float = 1.0      # "step frequency" [Hz] through frac_step
        self.target_steps: int = target_steps

        # Paths to gait templates
        controller_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(controller_dir, "..", ".."))
        gait_dir = os.path.join(project_root, "gait_templates")

        self.start_gait = self._load_gait_csv(os.path.join(gait_dir, start_csv))
        self.walk_gait = self._load_gait_csv(os.path.join(gait_dir, walk_csv))
        self.stop_gait = self._load_gait_csv(os.path.join(gait_dir, stop_csv))

        # Length of one walking cycle (in frac_step units)
        self.walk_cycle_len: float = (
            self.walk_gait["step_max"] - self.walk_gait["step_min"]
        )

        # State machine initialization
        self.state: str = "start"   # 'start' -> 'walk' -> 'stop' -> 'done'

        # Phase variables in frac_step units
        self.start_phase: float = self.start_gait["step_min"]
        self.walk_phase: float = 0.0          # unbounded, used for cycles
        self.stop_phase: float = self.stop_gait["step_min"]

        # Step counting during walking (full gait cycles)
        self.step_counter: int = 0
        self.prev_cycle_index: int = 0

        # Distance-related parameters/state
        self.target_distance: float | None = target_distance   # meters
        self.stop_distance_offset: float = stop_distance_offset

        # GPS for measuring travelled distance
        # Make sure "gps" matches your NAO/world device name.
        try:
            self.gps = self.robot.getDevice("gps")
            self.gps.enable(int(self.robot.getBasicTimeStep()))
        except Exception:
            self.gps = None
            print("[WalkingMin] WARNING: GPS device 'gps' not found, "
                  "distance-based stopping will be disabled.")

        self.initial_pos: list[float] | None = None  # position at motion start
        self.current_distance: float = 0.0           # meters from initial_pos


    # CSV loading helper
    def _load_gait_csv(self, filepath: str) -> Dict[str, Any]:
        """
        Load a gait CSV file and build cubic spline models for each joint.

        CSV must contain:
          frac_step, LHipYawPitch, LHipRoll, ... , RAnkleRoll
        """
        df = pd.read_csv(filepath)
        if "frac_step" not in df.columns:
            raise ValueError(f"CSV {filepath} must contain a 'frac_step' column.")

        frac = df["frac_step"].to_numpy()
        step_min = float(frac[0])
        step_max = float(frac[-1])

        models: Dict[str, Any] = {}
        for col in df.columns:
            if col == "frac_step":
                continue
            y = df[col].to_numpy()
            # cubic spline interpolation
            models[col] = make_interp_spline(frac, y, k=3)

        return {
            "models": models,
            "step_min": step_min,
            "step_max": step_max,
        }


    # Distance update
    def _update_distance(self) -> None:
        """Update self.current_distance (meters) using GPS, if available."""
        if self.gps is None:
            return

        pos = self.gps.getValues()  # [x, y, z]
        if self.initial_pos is None:
            # First call – define origin at motion start
            self.initial_pos = list(pos)
            self.current_distance = 0.0
            return

        dx = pos[0] - self.initial_pos[0]
        dz = pos[2] - self.initial_pos[2]  # assuming Y is vertical
        self.current_distance = math.hypot(dx, dz)

    # read parameters from Supervisor via customData
    def _update_from_custom_data(self) -> None:
        """
        Reads:
          {"step_frequency": 1.2, "target_distance": 3.0}
        from Robot's customData string set by Supervisor.
        """
        data = self.robot.getCustomData()
        if not data or data == self._last_custom_data:
            return  # nothing new
    
        self._last_custom_data = data
    
        try:
            cfg = json.loads(data)
        except json.JSONDecodeError:
            print(f"[WalkingMin] WARN: invalid customData JSON: {data}")
            return
    
        if "step_frequency" in cfg:
            try:
                self.f0 = float(cfg["step_frequency"])
                print(f"[WalkingMin] step_frequency (f0) updated to {self.f0} Hz")
            except (TypeError, ValueError):
                print(f"[WalkingMin] WARN: bad step_frequency in customData: "
                      f"{cfg['step_frequency']}")
    
        if "target_distance" in cfg:
            try:
                self.target_distance = float(cfg["target_distance"])
                print(f"[WalkingMin] target_distance updated to {self.target_distance} m")
            except (TypeError, ValueError):
                print(f"[WalkingMin] WARN: bad target_distance in customData: "
                      f"{cfg['target_distance']}")



    # Motor helpers
    def set_leg_pose(
        self,
        side: str,
        hip_yaw_pitch: float,
        hip_roll: float,
        hip_pitch: float,
        knee_pitch: float,
        ankle_pitch: float,
        ankle_roll: float,
    ) -> None:
        """Send a leg target joint configuration to the motors (side = 'L' or 'R')."""
        m = self.motors
        m[f"{side}HipYawPitch"].setPosition(hip_yaw_pitch)
        m[f"{side}HipRoll"].setPosition(hip_roll)
        m[f"{side}HipPitch"].setPosition(hip_pitch)
        m[f"{side}KneePitch"].setPosition(knee_pitch)
        m[f"{side}AnklePitch"].setPosition(ankle_pitch)
        m[f"{side}AnkleRoll"].setPosition(ankle_roll)


    def set_neutral(self) -> None:
        """Set both legs to the neutral (standing) posture."""
        for side in ("L", "R"):
            self.set_leg_pose(
                side,
                self.neutral["HipYawPitch"],
                self.neutral["HipRoll"],
                self.neutral["HipPitch"],
                self.neutral["KneePitch"],
                self.neutral["AnklePitch"],
                self.neutral["AnkleRoll"],
            )


    # Apply gait at given phase
    def _apply_gait_models(self, models: Dict[str, Any], phase: float) -> None:
        """Evaluate joint splines at the given phase and send targets to the motors."""
        # Left
        l_hip_yaw = models["LHipYawPitch"](phase)
        l_hip_roll = models["LHipRoll"](phase)
        l_hip_pitch = models["LHipPitch"](phase)
        l_knee = models["LKneePitch"](phase)
        l_ankle_p = models["LAnklePitch"](phase)
        l_ankle_r = models["LAnkleRoll"](phase)

        # Right
        r_hip_yaw = models["RHipYawPitch"](phase)
        r_hip_roll = models["RHipRoll"](phase)
        r_hip_pitch = models["RHipPitch"](phase)
        r_knee = models["RKneePitch"](phase)
        r_ankle_p = models["RAnklePitch"](phase)
        r_ankle_r = models["RAnkleRoll"](phase)

        self.set_leg_pose("L", l_hip_yaw, l_hip_roll, l_hip_pitch,
                          l_knee, l_ankle_p, l_ankle_r)
        self.set_leg_pose("R", r_hip_yaw, r_hip_roll, r_hip_pitch,
                          r_knee, r_ankle_p, r_ankle_r)


    # Main loop
    def run(self) -> None:
        """Main control loop: start -> walk (by distance or steps) -> stop -> done."""
        timestep_ms = int(self.dt * 1000)

        while self.robot.step(timestep_ms) != -1:
            # allow Supervisor to update f0 / target_distance
            self._update_from_custom_data()

            # Update travelled distance from the very beginning
            self._update_distance()

            # START PHASE (one-shot)
            if self.state == "start":
                dstep = self.dt * self.f0
                self.start_phase += dstep

                # Clamp to end of start gait
                if self.start_phase > self.start_gait["step_max"]:
                    self.start_phase = self.start_gait["step_max"]

                self._apply_gait_models(self.start_gait["models"],
                                        self.start_phase)

                # When start motion is finished, transition to walking
                if self.start_phase >= self.start_gait["step_max"] - EPS:
                    self.state = "walk"
                    self.walk_phase = 0.0
                    self.prev_cycle_index = 0
                    self.step_counter = 0


            # WALK PHASE (loop, distance-based)
            elif self.state == "walk":
                dstep = self.dt * self.f0
                self.walk_phase += dstep     # unbounded "cycle phase"

                # Map to [step_min, step_max] via modulo to loop
                cycle_len = self.walk_cycle_len
                step_min = self.walk_gait["step_min"]
                local_phase = step_min + (self.walk_phase % cycle_len)

                self._apply_gait_models(self.walk_gait["models"],
                                        local_phase)

                # Count how many full cycles have passed (debug / fallback)
                cycles = self.walk_phase / cycle_len
                cycle_index = math.floor(cycles)

                if cycle_index > self.prev_cycle_index:
                    self.step_counter += (cycle_index - self.prev_cycle_index)
                    self.prev_cycle_index = cycle_index

                # Decide when to stop walking
                use_distance = (
                    self.target_distance is not None and self.gps is not None
                )

                stop_now = False

                if use_distance:
                    # Distance at which we enter the stop phase
                    effective_target = self.target_distance - self.stop_distance_offset
                    if effective_target < 0.0:
                        effective_target = 0.0

                    if self.current_distance >= effective_target:
                        stop_now = True
                else:
                    # Fallback: use step-based stopping
                    if self.step_counter >= self.target_steps:
                        stop_now = True

                if stop_now:
                    self.state = "stop"
                    self.stop_phase = self.stop_gait["step_min"]

            # STOP PHASE (one-shot)
            elif self.state == "stop":
                dstep = self.dt * self.f0
                self.stop_phase += dstep

                if self.stop_phase > self.stop_gait["step_max"]:
                    self.stop_phase = self.stop_gait["step_max"]

                self._apply_gait_models(self.stop_gait["models"],
                                        self.stop_phase)

                if self.stop_phase >= self.stop_gait["step_max"] - EPS:
                    self.state = "done"
                    # Optionally: self.set_neutral()

            # DONE / IDLE
            elif self.state == "done":
                # return to neutral posture
                self.set_neutral()
                pass



if __name__ == "__main__":
    WalkingMin(
        start_csv="motor_patterns_smooth_start.csv",
        walk_csv="motor_patterns_continous_gait.csv",
        stop_csv="motor_patterns_smooth_stop.csv",
        target_distance=10.0,     # desired total distance [m]
        stop_distance_offset=0.05   # expected distance during stopping phase [m]
    ).run()