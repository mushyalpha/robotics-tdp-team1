from controller import Robot, Motor
import math

class WalkingMin:
    """
    Minimal NAO6 walking controller:
    - Fixed-frequency sinusoidal gait (no sensors, no feedback)
    - Anti-phase legs (right leg = left leg + π)
    - Small toe-out (HipYawPitch) for stability
    - Safety: joint limits (clamps) and a neutral (slightly bent) posture
    """
    def __init__(self):
        self.robot = Robot()
        # Convert Webots basicTimeStep (ms) to seconds for frequency-accurate phase updates
        self.dt = int(self.robot.getBasicTimeStep()) / 1000.0

        # Acquire motors by device name (must match NAO6 PROTO)
        names_L = ["LHipYawPitch","LHipRoll","LHipPitch","LKneePitch","LAnklePitch","LAnkleRoll"]
        names_R = ["RHipYawPitch","RHipRoll","RHipPitch","RKneePitch","RAnklePitch","RAnkleRoll"]
        self.motors = {}
        for n in names_L + names_R:
            m = self.robot.getDevice(n)
            # Position control mode: set desired angle targets each step
            m.setPosition(0.0)
            # Cap motor speed to avoid aggressive jumps (60% of maximum)
            m.setVelocity(m.getMaxVelocity()*0.6)
            self.motors[n] = m

        # Neutral posture (radians): slight knee bend and slight forward lean for stability
        self.neutral = dict(HipYawPitch=0.0, HipRoll=0.0, HipPitch=-0.2,
                            KneePitch=0.4, AnklePitch=-0.2, AnkleRoll=0.0)
        self.set_neutral()

        # ---- Gait parameters (constant for this minimal controller) ----
        self.f0 = 0.8               # fixed step frequency [Hz]; start within 0.8–1.2 for stability
        self.phase = 0.0            # global gait phase [0, 2π)

        # Sinusoidal amplitudes (radians) — tune conservatively, increase gradually
        self.A_hip_pitch   = 0.20   # Hip forward/back swing (main driver)
        self.A_knee        = 0.40   # Knee flexion for foot clearance
        self.A_ankle_pitch = 0.20   # Ankle pitch: toe up/down
        self.A_hip_roll    = 0.04   # Hip roll: lateral balance helper
        self.A_ankle_roll  = 0.04   # Ankle roll: lateral balance helper

        # Small toe-out for more stable foot landing (left +, right -)
        self.yaw_out = 0.03

    @staticmethod
    def clamp(x, lo, hi):
        """Limit x to [lo, hi] to respect joint mechanical bounds."""
        return max(lo, min(hi, x))

    def set_leg_pose(self, side, hip_yaw_pitch, hip_roll, hip_pitch, knee_pitch, ankle_pitch, ankle_roll):
        """Send one leg's target joint angles to motors (side = 'L' or 'R')."""
        m = self.motors
        m[f"{side}HipYawPitch"].setPosition(hip_yaw_pitch)
        m[f"{side}HipRoll"].setPosition(hip_roll)
        m[f"{side}HipPitch"].setPosition(hip_pitch)
        m[f"{side}KneePitch"].setPosition(knee_pitch)
        m[f"{side}AnklePitch"].setPosition(ankle_pitch)
        m[f"{side}AnkleRoll"].setPosition(ankle_roll)

    def set_neutral(self):
        """Set both legs to the neutral (standing) posture."""
        for s in ("L","R"):
            self.set_leg_pose(s,
                self.neutral["HipYawPitch"], self.neutral["HipRoll"],
                self.neutral["HipPitch"],    self.neutral["KneePitch"],
                self.neutral["AnklePitch"],  self.neutral["AnkleRoll"]
            )

    def run(self):
        """Main control loop: advance phase, synthesize joint targets, clamp, send to motors."""
        while self.robot.step(int(self.dt*1000)) != -1:
            # ---- Phase update ----
            # Advance global phase based on fixed frequency f0:
            # Δphase = 2π f0 Δt
            self.phase = (self.phase + 2.0*math.pi*self.f0*self.dt) % (2.0*math.pi)

            # Left leg phase (lp) and right leg anti-phase (rp = lp + π)
            lp = self.phase
            rp = (self.phase + math.pi) % (2.0*math.pi)

            # ---- Left leg joint targets (sinusoidal) ----
            # Pitch chain: orchestrates forward progression and foot clearance via phase offsets
            l_hip_pitch = self.neutral["HipPitch"]   + self.A_hip_pitch   * math.sin(lp)
            l_knee      = self.neutral["KneePitch"]  + self.A_knee        * math.sin(lp + 0.5*math.pi)  # +90°
            l_ankle_p   = self.neutral["AnklePitch"] - self.A_ankle_pitch * math.sin(lp + 0.3*math.pi)  # +54° (toe-up during swing)

            # Roll chain: lateral balance — use opposite phase to provide counter-lean during stance
            l_hip_roll  = self.neutral["HipRoll"]    + self.A_hip_roll    * math.sin(lp + math.pi)       # +180°
            l_ankle_r   = self.neutral["AnkleRoll"]  - self.A_ankle_roll  * math.sin(lp + math.pi)       # +180°
            l_yaw       = +self.yaw_out  # slight toe-out

            # ---- Right leg joint targets (anti-phase) ----
            r_hip_pitch = self.neutral["HipPitch"]   + self.A_hip_pitch   * math.sin(rp)
            r_knee      = self.neutral["KneePitch"]  + self.A_knee        * math.sin(rp + 0.5*math.pi)
            r_ankle_p   = self.neutral["AnklePitch"] - self.A_ankle_pitch * math.sin(rp + 0.3*math.pi)
            r_hip_roll  = self.neutral["HipRoll"]    + self.A_hip_roll    * math.sin(rp + math.pi)
            r_ankle_r   = self.neutral["AnkleRoll"]  - self.A_ankle_roll  * math.sin(rp + math.pi)
            r_yaw       = -self.yaw_out  # slight toe-out (opposite sign)

            # ---- Safety clamps: keep all joints within plausible NAO ranges (radians) ----
            def c(x, lo, hi): return self.clamp(x, lo, hi)
            L = (c(l_yaw,-0.5,0.5), c(l_hip_roll,-0.45,0.45), c(l_hip_pitch,-1.2,0.6),
                 c(l_knee,-0.1,2.6), c(l_ankle_p,-1.0,0.9),   c(l_ankle_r,-0.5,0.5))
            R = (c(r_yaw,-0.5,0.5), c(r_hip_roll,-0.45,0.45), c(r_hip_pitch,-1.2,0.6),
                 c(r_knee,-0.1,2.6), c(r_ankle_p,-1.0,0.9),   c(r_ankle_r,-0.5,0.5))

            # ---- Send targets to motors ----
            self.set_leg_pose("L", *L)
            self.set_leg_pose("R", *R)

if __name__ == "__main__":
    WalkingMin().run()
