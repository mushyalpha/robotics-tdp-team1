from controller import Robot
import math
from scipy.interpolate import make_interp_spline
import pandas as pd

class WalkingMin:
    """
    Simple walking controller using gait template to set motor positions
    
    Template is used to create continous repeating pattern for forward step motion.
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
            # Cap motor speed to avoid aggressive jumps (90% of maximum)
            m.setVelocity(m.getMaxVelocity()*0.9)
            self.motors[n] = m

        # Neutral posture (radians): slight knee bend and slight forward lean for stability
        self.neutral = dict(HipYawPitch=0.0, HipRoll=0.0, HipPitch=-0.5,
                            KneePitch=1.0, AnklePitch=-0.5, AnkleRoll=0.0)
        self.set_neutral()

        # ---- Gait parameters (constant for this minimal controller) ----
        self.f0 = 0.7        # fixed step frequency [Hz]; start within 0.8–1.2 for stability
        self.phase = 0.0            # global gait phase [0, 2π)
        
        # load the forward gait file
        gait_df = pd.read_csv("../../motions/forward_walk_gait.csv")
        
        # convert from discete path to continous repeating path 
        self.gait_models = {}
        
        for col in gait_df:
            name = col
            gait = gait_df[col].to_numpy()
            step = gait_df["step"].to_numpy()
            # ignore the step column
            if name == "step":
                pass
            else:
                # spline interpolation to create repeating model
                model = make_interp_spline(step, gait, k=5, bc_type="periodic")
                self.gait_models[col] = model
                

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
        
        # load the gait file and create models

        while self.robot.step(int(self.dt*1000)) != -1:
            
            # adjust the fraction of step to get correct step frequency
            dstep = self.dt * self.f0
            # increment the step
            self.phase += dstep
            
            # move motors to desired position
            # Left
            l_hip_yaw = self.gait_models["LHipYawPitch"](self.phase)
            l_hip_pitch = self.gait_models["LHipPitch"](self.phase)
            l_knee      = self.gait_models["LKneePitch"](self.phase)
            l_ankle_p   = self.gait_models["LAnklePitch"](self.phase) 
            l_ankle_r   = self.gait_models["LAnkleRoll"](self.phase)
            l_hip_roll  = self.gait_models["LHipRoll"](self.phase)       

            # Right
            r_hip_yaw = self.gait_models["RHipYawPitch"](self.phase)
            r_hip_pitch = self.gait_models["RHipPitch"](self.phase)
            r_knee      = self.gait_models["RKneePitch"](self.phase)
            r_ankle_p   = self.gait_models["RAnklePitch"](self.phase)
            r_hip_roll  = self.gait_models["RHipRoll"](self.phase)
            r_ankle_r   = self.gait_models["RAnkleRoll"](self.phase)
            
            # implement the motor movements to each leg
            self.set_leg_pose("L", l_hip_yaw, l_hip_roll, l_hip_pitch, l_knee, l_ankle_p, l_ankle_r)
            self.set_leg_pose("R", r_hip_yaw, r_hip_roll, r_hip_pitch, r_knee, r_ankle_p, r_ankle_r)
            

if __name__ == "__main__":
    WalkingMin().run()