from controller import Robot, Motor, InertialUnit, Gyro, Accelerometer, Keyboard, GPS
import math

class WalkingController:
    def __init__(self):
        self.robot = Robot()
        self.timestep = int(self.robot.getBasicTimeStep())
        
        # Devices
        self.imu = self.robot.getDevice("inertial unit")
        if self.imu:
            self.imu.enable(self.timestep)
        self.gyro = self.robot.getDevice("gyro")
        if self.gyro:
            self.gyro.enable(self.timestep)
        self.acc = self.robot.getDevice("accelerometer")
        if self.acc:
            self.acc.enable(self.timestep)
        try:
            self.gps = self.robot.getDevice("gps")
            if self.gps:
                self.gps.enable(self.timestep)
        except:
            self.gps = None
        
        
        # Keyboard input
        self.kb = Keyboard()
        self.kb.enable(self.timestep)
        
        
        # Joints
        self.joint_names_L = [
            "LHipYawPitch", "LHipRoll", "LHipPitch", "LKneePitch", "LAnklePitch", "LAnkleRoll"
        ]
        self.joint_names_R = [
            "RHipYawPitch", "RHipRoll", "RHipPitch", "RKneePitch", "RAnklePitch", "RAnkleRoll"
        ]
        self.motors = {}
        for name in self.joint_names_L + self.joint_names_R:
            m = self.robot.getDevice(name)
            if m is None:
                raise RuntimeError(f"Motor '{name}' not found. Check your NAO6 PROTO joint names.")
            m.setPosition(0.0)
            m.setVelocity(m.getMaxVelocity() * 0.5)
            self.motors[name] = m
        
        
        # Neutral pose
        self.neutral_pose = {
            "HipYawPitch": 0.0,
            "HipRoll": 0.0,
            "HipPitch": -0.2,
            "KneePitch": 0.4,
            "AnklePitch": -0.2,
            "AnkleRoll": 0.0
        }
        
        
        # Gait params
        self.step_height = 0.10
        self.step_length_min = 0.05
        self.step_length_max = 0.12
        self.freq_min = 0.6
        self.freq_max = 2.0
        
        self.cmd_speed = 0.0
        self.target_speed = 0.0
        self.speed_increment = 0.02
        
        self.amp = 0.0
        self.amp_target = 0.0
        self.amp_rise_rate = 3.0
        self.amp_fall_rate = 3.0
        
        self.kp_pitch = 0.9
        self.kd_pitch = 0.02
        self.kp_roll = 0.9
        self.kd_roll = 0.02
        
        self.phase = 0.0
        self.left_phase = 0.0
        self.right_phase = math.pi
        
        self.state = "IDLE"
        self.last_pos = None
        self.last_time = self.robot.getTime()
        self.filtered_speed = 0.0
        
        print("[walking_controller] Ready. Controls:")
        print("  ↑ / W : increase speed")
        print("  ↓ / S : decrease speed")
        print("  Space : start/stop walking")
        print("  R     : reset to neutral")
    
    def clamp(self, val, lo, hi):
        return max(lo, min(hi, val))
    
    def handle_keyboard(self):
        key = self.kb.getKey()
        while key != -1:
            if key in (Keyboard.UP, ord('W')):
                self.target_speed += self.speed_increment
            elif key in (Keyboard.DOWN, ord('S')):
                self.target_speed -= self.speed_increment
            elif key == Keyboard.SPACE:
                if self.state in ("IDLE", "STOPPING"):
                    self.state = "STARTING"
                    self.amp_target = 1.0
                elif self.state in ("STARTING", "WALKING"):
                    self.state = "STOPPING"
                    self.amp_target = 0.0
            elif key == ord('R'):
                self.state = "IDLE"
                self.amp_target = 0.0
                self.target_speed = 0.0
                self.cmd_speed = 0.0
                self.set_neutral_pose()
            key = self.kb.getKey()
        
        self.target_speed = self.clamp(self.target_speed, 0.0, 0.4)
        dt = self.timestep / 1000.0
        tau = 0.3
        alpha = dt / (tau + dt)
        self.cmd_speed += alpha * (self.target_speed - self.cmd_speed)
    
    def set_neutral_pose(self):
        for side in ("L", "R"):
            self.set_leg_pose(side,
                              self.neutral_pose["HipYawPitch"],
                              self.neutral_pose["HipRoll"],
                              self.neutral_pose["HipPitch"],
                              self.neutral_pose["KneePitch"],
                              self.neutral_pose["AnklePitch"],
                              self.neutral_pose["AnkleRoll"])
    
    def set_leg_pose(self, side, hip_yaw_pitch, hip_roll, hip_pitch, knee_pitch, ankle_pitch, ankle_roll):
        names = {
            "HipYawPitch": f"{side}HipYawPitch",
            "HipRoll": f"{side}HipRoll",
            "HipPitch": f"{side}HipPitch",
            "KneePitch": f"{side}KneePitch",
            "AnklePitch": f"{side}AnklePitch",
            "AnkleRoll": f"{side}AnkleRoll",
        }
        self.motors[names["HipYawPitch"]].setPosition(hip_yaw_pitch)
        self.motors[names["HipRoll"]].setPosition(hip_roll)
        self.motors[names["HipPitch"]].setPosition(hip_pitch)
        self.motors[names["KneePitch"]].setPosition(knee_pitch)
        self.motors[names["AnklePitch"]].setPosition(ankle_pitch)
        self.motors[names["AnkleRoll"]].setPosition(ankle_roll)
    
    def compute_gait_params(self):
        v = self.cmd_speed
        s = self.clamp(v / self.freq_min if v > 0 else self.step_length_min,
                       self.step_length_min, self.step_length_max)
        f = v / max(s, 1e-6) if v > 0 else self.freq_min
        if f > self.freq_max:
            f = self.freq_max
            s = self.clamp(v / f, self.step_length_min, self.step_length_max)
        if f < self.freq_min and v > 0:
            f = self.freq_min
            s = self.clamp(v / f, self.step_length_min, self.step_length_max)
        return f, s
    
    def update_amp(self, dt):
        rate = self.amp_rise_rate if self.amp_target > self.amp else self.amp_fall_rate
        delta = self.amp_target - self.amp
        step = self.clamp(delta, -rate * dt, rate * dt)
        self.amp += step
    
    def stabilize_ankles(self):
        pitch = 0.0
        roll = 0.0
        d_pitch = 0.0
        d_roll = 0.0
        if self.imu:
            rpy = self.imu.getRollPitchYaw()
            roll = rpy[0]
            pitch = rpy[1]
        if self.gyro:
            g = self.gyro.getValues()
            d_pitch = g[0]
            d_roll = -g[1]
        pitch_corr = (-self.kp_pitch * pitch) + (-self.kd_pitch * d_pitch)
        roll_corr = (-self.kp_roll * roll) + (-self.kd_roll * d_roll)
        pitch_corr = self.clamp(pitch_corr, -0.15, 0.15)
        roll_corr = self.clamp(roll_corr, -0.15, 0.15)
        return pitch_corr, roll_corr
    
    def estimate_speed(self):
        t = self.robot.getTime()
        v = self.cmd_speed
        if hasattr(self, "gps") and self.gps:
            pos = self.gps.getValues()
            if self.last_pos is not None:
                dt = t - self.last_time if t > self.last_time else 1e-3
                dx = pos[0] - self.last_pos[0]
                dy = pos[2] - self.last_pos[2]
                inst = math.hypot(dx, dy) / dt
                alpha = 0.2
                self.filtered_speed = (1 - alpha) * self.filtered_speed + alpha * inst
                v = self.filtered_speed
            self.last_pos = pos
            self.last_time = t
        return v
    
    def run(self):
        self.set_neutral_pose()
        while self.robot.step(self.timestep) != -1:
            dt = self.timestep / 1000.0
            self.handle_keyboard()
            self.update_amp(dt)
            
            if self.state == "STARTING" and self.amp >= 0.99:
                self.state = "WALKING"
            if self.state == "STOPPING" and self.amp <= 0.01:
                self.state = "IDLE"
                self.set_neutral_pose()
            
            freq, step_len = self.compute_gait_params()
            dphi = 2.0 * math.pi * freq * dt
            self.phase = (self.phase + dphi) % (2.0 * math.pi)
            self.left_phase = self.phase
            self.right_phase = (self.phase + math.pi) % (2.0 * math.pi)
            
            pitch_corr, roll_corr = self.stabilize_ankles()
            
            if self.state in ("STARTING", "WALKING", "STOPPING"):
                step_scale = (step_len - self.step_length_min) / max(self.step_length_max - self.step_length_min, 1e-6)
                A_hip_pitch = 0.2 + 0.2 * step_scale
                A_knee = 0.35 + 0.25 * step_scale
                A_ankle_pitch = 0.15 + 0.10 * step_scale
                A_hip_roll = 0.05
                A_ankle_roll = 0.05
                
                lp = self.left_phase
                l_hip_pitch = self.neutral_pose["HipPitch"] + self.amp * A_hip_pitch * math.sin(lp)
                l_knee = self.neutral_pose["KneePitch"] + self.amp * A_knee * math.sin(lp + 0.5*math.pi)
                l_ankle_pitch = self.neutral_pose["AnklePitch"] - self.amp * A_ankle_pitch * math.sin(lp + 0.3*math.pi) + pitch_corr
                l_hip_roll = self.neutral_pose["HipRoll"] + self.amp * A_hip_roll * math.sin(lp + math.pi)
                l_ankle_roll = self.neutral_pose["AnkleRoll"] - self.amp * A_ankle_roll * math.sin(lp + math.pi) + roll_corr
                
                rp = self.right_phase
                r_hip_pitch = self.neutral_pose["HipPitch"] + self.amp * A_hip_pitch * math.sin(rp)
                r_knee = self.neutral_pose["KneePitch"] + self.amp * A_knee * math.sin(rp + 0.5*math.pi)
                r_ankle_pitch = self.neutral_pose["AnklePitch"] - self.amp * A_ankle_pitch * math.sin(rp + 0.3*math.pi) + pitch_corr
                r_hip_roll = self.neutral_pose["HipRoll"] + self.amp * A_hip_roll * math.sin(rp + math.pi)
                r_ankle_roll = self.neutral_pose["AnkleRoll"] - self.amp * A_ankle_roll * math.sin(rp + math.pi) + roll_corr
                
                l_hip_yaw_pitch = 0.02
                r_hip_yaw_pitch = -0.02
                
                def clamp_joint(x, lo, hi): 
                    return self.clamp(x, lo, hi)
                
                l_targets = (
                    clamp_joint(l_hip_yaw_pitch, -0.5, 0.5),
                    clamp_joint(l_hip_roll, -0.45, 0.45),
                    clamp_joint(l_hip_pitch, -1.2, 0.6),
                    clamp_joint(l_knee, -0.1, 2.6),
                    clamp_joint(l_ankle_pitch, -1.0, 0.9),
                    clamp_joint(l_ankle_roll, -0.5, 0.5),
                )
                r_targets = (
                    clamp_joint(r_hip_yaw_pitch, -0.5, 0.5),
                    clamp_joint(r_hip_roll, -0.45, 0.45),
                    clamp_joint(r_hip_pitch, -1.2, 0.6),
                    clamp_joint(r_knee, -0.1, 2.6),
                    clamp_joint(r_ankle_pitch, -1.0, 0.9),
                    clamp_joint(r_ankle_roll, -0.5, 0.5),
                )
                
                self.set_leg_pose("L", *l_targets)
                self.set_leg_pose("R", *r_targets)
            else:
                l_targets = (
                    0.0,
                    self.neutral_pose["HipRoll"],
                    self.neutral_pose["HipPitch"],
                    self.neutral_pose["KneePitch"],
                    self.neutral_pose["AnklePitch"] + pitch_corr,
                    self.neutral_pose["AnkleRoll"] + roll_corr,
                )
                r_targets = (
                    0.0,
                    self.neutral_pose["HipRoll"],
                    self.neutral_pose["HipPitch"],
                    self.neutral_pose["KneePitch"],
                    self.neutral_pose["AnklePitch"] + pitch_corr,
                    self.neutral_pose["AnkleRoll"] + roll_corr,
                )
                self.set_leg_pose("L", *l_targets)
                self.set_leg_pose("R", *r_targets)
            
            v_meas = self.estimate_speed()
            print(f"[{self.state}] v_cmd={self.cmd_speed:.2f} m/s  v_meas={v_meas:.2f} m/s  freq≈{self.compute_gait_params()[0]:.2f} Hz  amp={self.amp:.2f}")


if __name__ == "__main__":
    controller = WalkingController()
    controller.run()
