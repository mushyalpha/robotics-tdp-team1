
from controller import Robot, Motor
import math

class WalkingMin:
    """
    Minimal NAO6 walking controller Version:0.2:
    - Fixed-frequency sinusoidal gait (no sensors, no feedback)
    - Anti-phase legs (right leg = left leg + π)
    - Small toe-out (HipYawPitch) for stability
    - Safety: joint limits (clamps) and a neutral posture
    - What's New: COM shift
    """
    def __init__(self):
        self.robot = Robot()
        # Convert Webots basicTimeStep (ms) to seconds for frequency-accurate phase updates
        self.dt = int(self.robot.getBasicTimeStep()) / 1000.0  # seconds

        # Acquire motors by device name
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

        self.neutral = dict(HipYawPitch=0.0, HipRoll=0.0, HipPitch=-0.23,
                            KneePitch=0.45, AnklePitch=-0.20, AnkleRoll=0.0)
        self.set_neutral()

        # Gait parameters
        self.f0 = 0.8
        self.phase = 0.0

        self.A_hip_pitch   = 0.18
        self.A_knee        = 0.35
        self.A_ankle_pitch = 0.18
        self.A_hip_roll    = 0.03
        self.A_ankle_roll  = 0.03

        self.yaw_out       = 0.03

        # New：Center of Mass shift amplitude
        self.com_roll_amp  = 0.05

    def clamp(self, x, lo, hi):
        return max(lo, min(hi, x))

    def set_leg_pose(self, side, hip_yaw_pitch, hip_roll, hip_pitch, knee_pitch, ankle_pitch, ankle_roll):
        m = self.motors
        m[f"{side}HipYawPitch"].setPosition(hip_yaw_pitch)
        m[f"{side}HipRoll"].setPosition(hip_roll)
        m[f"{side}HipPitch"].setPosition(hip_pitch)
        m[f"{side}KneePitch"].setPosition(knee_pitch)
        m[f"{side}AnklePitch"].setPosition(ankle_pitch)
        m[f"{side}AnkleRoll"].setPosition(ankle_roll)

    def set_neutral(self):
        for s in ("L","R"):
            self.set_leg_pose(s,
                self.neutral["HipYawPitch"], self.neutral["HipRoll"],
                self.neutral["HipPitch"],    self.neutral["KneePitch"],
                self.neutral["AnklePitch"],  self.neutral["AnkleRoll"]
            )

    def run(self):
        while self.robot.step(int(self.dt*1000)) != -1:
            # ---- Phase update ----
            # Advance global phase based on fixed frequency f0:
            # Δphase = 2π f0 Δt
            # Left leg phase (lp) and right leg anti-phase (rp = lp + π)
            self.phase = (self.phase + 2.0*math.pi*self.f0*self.dt) % (2.0*math.pi)
            lp = self.phase
            rp = (self.phase + math.pi) % (2.0*math.pi)

            # Estimate the support leg based on the phase and apply a COM shift
            # If sin(lp) > 0: The left leg is more forward (acting more like the swing leg), so shift the CoM to the right.
            # Otherwise (if sin(lp) <= 0): Shift the CoM to the left.
            hip_phase = math.sin(lp)
            com_bias = -self.com_roll_amp * hip_phase

            # left leg pitch chain
            l_hip_pitch = self.neutral["HipPitch"]   + self.A_hip_pitch   * math.sin(lp)
            l_knee      = self.neutral["KneePitch"]  + self.A_knee        * math.sin(lp + 0.5*math.pi)
            l_ankle_p   = self.neutral["AnklePitch"] - self.A_ankle_pitch * math.sin(lp + 0.3*math.pi)

            # left leg roll chain + COM shifting
            base_l_hip_roll = self.A_hip_roll   * math.sin(lp + math.pi)
            base_l_ankle_r  = -self.A_ankle_roll* math.sin(lp + math.pi)
            l_hip_roll      = self.neutral["HipRoll"]   + base_l_hip_roll + com_bias
            l_ankle_r       = self.neutral["AnkleRoll"] + base_l_ankle_r  + com_bias

            l_yaw = +self.yaw_out

            # right lrg pitch chain
            r_hip_pitch = self.neutral["HipPitch"]   + self.A_hip_pitch   * math.sin(rp)
            r_knee      = self.neutral["KneePitch"]  + self.A_knee        * math.sin(rp + 0.5*math.pi)
            r_ankle_p   = self.neutral["AnklePitch"] - self.A_ankle_pitch * math.sin(rp + 0.3*math.pi)

            # right leg roll chain + COM shifting(reverse)
            base_r_hip_roll = self.A_hip_roll   * math.sin(rp + math.pi)
            base_r_ankle_r  = -self.A_ankle_roll* math.sin(rp + math.pi)
            r_hip_roll      = self.neutral["HipRoll"]   + base_r_hip_roll - com_bias
            r_ankle_r       = self.neutral["AnkleRoll"] + base_r_ankle_r  - com_bias

            r_yaw = -self.yaw_out

            # Safety clamps
            def c(x, lo, hi): return self.clamp(x, lo, hi)
            L = (c(l_yaw,-0.5,0.5), c(l_hip_roll,-0.45,0.45), c(l_hip_pitch,-1.2,0.6),
                 c(l_knee,-0.1,2.6), c(l_ankle_p,-1.0,0.9),   c(l_ankle_r,-0.5,0.5))
            R = (c(r_yaw,-0.5,0.5), c(r_hip_roll,-0.45,0.45), c(r_hip_pitch,-1.2,0.6),
                 c(r_knee,-0.1,2.6), c(r_ankle_p,-1.0,0.9),   c(r_ankle_r,-0.5,0.5))

            # Send targets to motors
            self.set_leg_pose("L", *L)
            self.set_leg_pose("R", *R)

if __name__ == "__main__":
    WalkingMin().run()
