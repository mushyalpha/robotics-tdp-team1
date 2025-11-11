from controller import Robot, Motor, InertialUnit, Gyro, Accelerometer, Keyboard, GPS
import math, csv, os

class WalkingControllerTuner:
    def __init__(self):
        self.robot = Robot()
        self.timestep = int(self.robot.getBasicTimeStep())
        
        # Devices
        self.imu = self.robot.getDevice("inertial unit"); self.imu.enable(self.timestep)
        self.gyro = self.robot.getDevice("gyro"); self.gyro.enable(self.timestep)
        self.acc = self.robot.getDevice("accelerometer"); self.acc.enable(self.timestep)
        try:
            self.gps = self.robot.getDevice("gps"); self.gps.enable(self.timestep)
        except:
            self.gps = None
        
        # Keyboard
        self.kb = Keyboard(); self.kb.enable(self.timestep)
        
        # Motors
        names_L = ["LHipYawPitch","LHipRoll","LHipPitch","LKneePitch","LAnklePitch","LAnkleRoll"]
        names_R = ["RHipYawPitch","RHipRoll","RHipPitch","RKneePitch","RAnklePitch","RAnkleRoll"]
        self.motors = {}
        for n in names_L + names_R:
            m = self.robot.getDevice(n)
            m.setPosition(0.0); m.setVelocity(m.getMaxVelocity()*0.6)
            self.motors[n] = m
        
        # Neutral
        self.neutral = {"HipYawPitch":0.0,"HipRoll":0.0,"HipPitch":-0.2,"KneePitch":0.4,"AnklePitch":-0.2,"AnkleRoll":0.0}
        
        # Gait params and gains
        self.freq_min, self.freq_max = 0.6, 2.0
        self.step_len_min, self.step_len_max = 0.05, 0.14
        self.A_hip_pitch_base = 0.2
        self.A_knee_base = 0.35
        self.A_ankle_pitch_base = 0.15
        self.A_hip_roll = 0.05
        self.A_ankle_roll = 0.05
        
        self.kp_pitch, self.kd_pitch = 0.9, 0.02
        self.kp_roll, self.kd_roll = 0.9, 0.02
        
        # Speed command
        self.target_speed = 0.0; self.cmd_speed = 0.0; self.speed_increment = 0.02
        
        # Envelope
        self.amp, self.amp_target = 0.0, 0.0
        self.amp_rise_rate, self.amp_fall_rate = 3.0, 3.0
        
        # Phases
        self.phase = 0.0; self.left_phase = 0.0; self.right_phase = math.pi
        
        # States
        self.state = "IDLE"
        
        # Speed estimate
        self.last_pos = None; self.last_time = self.robot.getTime(); self.filtered_speed = 0.0
        
        # Tuning
        self.tuning_mode = False
        self.grid_mode = False
        self.v_min, self.v_max, self.v_step = 0.06, 0.40, 0.02
        self.dwell_time = 4.0  # seconds per step
        self.current_step_start = None
        self.fall_pitch_thr, self.fall_roll_thr = 0.6, 0.6  # radians
        self.fall_count_required = 6  # consecutive steps over threshold
        self.fall_counter = 0
        
        # Grid params
        self.grid_freqs = [0.8,1.0,1.2,1.4,1.6]
        self.grid_steps = [0.06,0.08,0.10,0.12,0.14]
        self.grid_i, self.grid_j = 0, 0
        
        # Logging
        self.log_path = os.path.join(os.getcwd(), "nao6_tuning_log.csv")
        self._init_log()
        
        print("[tuner] Controls: ↑/W speed+, ↓/S speed-, Space start/stop, R reset")
        print("[tuner] T: toggle speed sweep, G: toggle (freq,step) grid search")
        print(f"[tuner] Logging to {self.log_path}")
    
    def _init_log(self):
        write_header = not os.path.exists(self.log_path)
        self.log_file = open(self.log_path, "a", newline="")
        self.csv = csv.writer(self.log_file)
        if write_header:
            self.csv.writerow(["time","mode","v_cmd","v_meas","freq","step_len",
                               "A_hip_pitch","A_knee","A_ankle_pitch",
                               "pitch","roll","gyro_x","gyro_y",
                               "amp","state","fall"])
    
    def clamp(self,val,lo,hi): return max(lo,min(hi,val))
    
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
    
    def set_neutral(self):
        for s in ("L","R"):
            self.set_leg_pose(s,0.0,self.neutral["HipRoll"],self.neutral["HipPitch"],
                              self.neutral["KneePitch"],self.neutral["AnklePitch"],self.neutral["AnkleRoll"])
    
    def handle_keyboard(self):
        key = self.kb.getKey()
        while key != -1:
            if key in (Keyboard.UP, ord('W')): self.target_speed += self.speed_increment
            elif key in (Keyboard.DOWN, ord('S')): self.target_speed -= self.speed_increment
            elif key == Keyboard.SPACE:
                if self.state in ("IDLE","STOPPING"):
                    self.state="STARTING"; self.amp_target=1.0
                elif self.state in ("STARTING","WALKING"):
                    self.state="STOPPING"; self.amp_target=0.0
            elif key == ord('R'):
                self.state="IDLE"; self.amp_target=0.0; self.target_speed=0.0; self.cmd_speed=0.0
                self.tuning_mode=False; self.grid_mode=False; self.set_neutral()
            elif key == ord('T'):
                self.tuning_mode = not self.tuning_mode
                self.grid_mode = False
                if self.tuning_mode:
                    self.state="STARTING"; self.amp_target=1.0; self.target_speed=self.v_min; self.current_step_start=None
                    print("[tuner] Speed sweep ON")
                else:
                    print("[tuner] Speed sweep OFF")
            elif key == ord('G'):
                self.grid_mode = not self.grid_mode
                self.tuning_mode = False
                if self.grid_mode:
                    self.state="STARTING"; self.amp_target=1.0; self.grid_i=0; self.grid_j=0; self.current_step_start=None
                    print("[tuner] Grid search ON")
                else:
                    print("[tuner] Grid search OFF")
            key = self.kb.getKey()
        
        self.target_speed = self.clamp(self.target_speed, 0.0, 0.5)
        dt = self.timestep/1000.0; tau=0.3; alpha = dt/(tau+dt)
        self.cmd_speed += alpha*(self.target_speed - self.cmd_speed)
    
    def stabilize_ankles(self):
        rpy = self.imu.getRollPitchYaw()
        roll, pitch = rpy[0], rpy[1]
        gx, gy, _ = self.gyro.getValues()
        d_pitch, d_roll = gx, -gy
        pitch_corr = self.clamp(-self.kp_pitch*pitch - self.kd_pitch*d_pitch, -0.15, 0.15)
        roll_corr = self.clamp(-self.kp_roll*roll - self.kd_roll*d_roll, -0.15, 0.15)
        return pitch, roll, gx, gy, pitch_corr, roll_corr
    
    def estimate_speed(self):
        t = self.robot.getTime()
        v = self.cmd_speed
        if self.gps:
            pos = self.gps.getValues()
            if self.last_pos is not None:
                dt = max(1e-3, t - self.last_time)
                dx = pos[0]-self.last_pos[0]; dy = pos[2]-self.last_pos[2]
                inst = math.hypot(dx,dy)/dt
                self.filtered_speed = 0.8*self.filtered_speed + 0.2*inst
                v = self.filtered_speed
            self.last_pos = pos; self.last_time = t
        return v
    
    def compute_freq_step(self):
        v = self.cmd_speed
        s = self.clamp(v/self.freq_min if v>0 else self.step_len_min, self.step_len_min, self.step_len_max)
        f = v/max(s,1e-6) if v>0 else self.freq_min
        if f>self.freq_max: f=self.freq_max; s=self.clamp(v/f, self.step_len_min,self.step_len_max)
        if f<self.freq_min and v>0: f=self.freq_min; s=self.clamp(v/f, self.step_len_min,self.step_len_max)
        return f, s
    
    def update_amp(self, dt):
        rate = self.amp_rise_rate if self.amp_target>self.amp else self.amp_fall_rate
        self.amp += self.clamp(self.amp_target - self.amp, -rate*dt, rate*dt)
    
    def fall_detector(self, pitch, roll):
        over = (abs(pitch)>self.fall_pitch_thr) or (abs(roll)>self.fall_roll_thr)
        if over: self.fall_counter += 1
        else: self.fall_counter = max(0, self.fall_counter-1)
        return self.fall_counter >= self.fall_count_required
    
    def log_row(self, mode, v_cmd, v_meas, freq, step_len, A_hp, A_k, A_ap, pitch, roll, gx, gy, amp, state, fall):
        self.csv.writerow([f"{self.robot.getTime():.3f}", mode, f"{v_cmd:.3f}", f"{v_meas:.3f}", f"{freq:.3f}", f"{step_len:.3f}",
                           f"{A_hp:.3f}", f"{A_k:.3f}", f"{A_ap:.3f}", f"{pitch:.3f}", f"{roll:.3f}", f"{gx:.3f}", f"{gy:.3f}",
                           f"{amp:.3f}", state, int(fall)])
        self.log_file.flush()
    
    def set_targets(self, L, R):
        self.set_leg_pose("L", *L); self.set_leg_pose("R", *R)
    
    def run(self):
        self.set_neutral()
        while self.robot.step(self.timestep) != -1:
            dt = self.timestep/1000.0
            self.handle_keyboard()
            self.update_amp(dt)
            
            if self.state == "STARTING" and self.amp >= 0.99: self.state="WALKING"
            if self.state == "STOPPING" and self.amp <= 0.01:
                self.state="IDLE"; self.set_neutral()
            
            # Determine freq/step
            if self.grid_mode:
                f = self.grid_freqs[self.grid_i]; s = self.grid_steps[self.grid_j]
                self.cmd_speed = f*s; mode = "GRID"
            else:
                f, s = self.compute_freq_step(); mode = "SWEEP" if self.tuning_mode else "MANUAL"
            
            dphi = 2.0*math.pi*f*dt
            self.phase = (self.phase + dphi)%(2.0*math.pi)
            lp = self.phase; rp = (self.phase + math.pi)%(2.0*math.pi)
            
            pitch, roll, gx, gy, pitch_corr, roll_corr = self.stabilize_ankles()
            
            # Amplitude scaling with step length
            step_scale = (s - self.step_len_min) / max(self.step_len_max - self.step_len_min, 1e-6)
            A_hp = self.A_hip_pitch_base + 0.2*step_scale
            A_k  = self.A_knee_base      + 0.25*step_scale
            A_ap = self.A_ankle_pitch_base+0.10*step_scale
            
            if self.state in ("STARTING","WALKING","STOPPING"):
                l_hip_pitch = self.neutral["HipPitch"] + self.amp*A_hp*math.sin(lp)
                l_knee      = self.neutral["KneePitch"]+ self.amp*A_k*math.sin(lp + 0.5*math.pi)
                l_ankle_p   = self.neutral["AnklePitch"]- self.amp*A_ap*math.sin(lp + 0.3*math.pi) + pitch_corr
                l_hip_roll  = self.neutral["HipRoll"] + self.amp*self.A_hip_roll*math.sin(lp + math.pi)
                l_ankle_r   = self.neutral["AnkleRoll"]- self.amp*self.A_ankle_roll*math.sin(lp + math.pi) + roll_corr
                
                r_hip_pitch = self.neutral["HipPitch"] + self.amp*A_hp*math.sin(rp)
                r_knee      = self.neutral["KneePitch"]+ self.amp*A_k*math.sin(rp + 0.5*math.pi)
                r_ankle_p   = self.neutral["AnklePitch"]- self.amp*A_ap*math.sin(rp + 0.3*math.pi) + pitch_corr
                r_hip_roll  = self.neutral["HipRoll"] + self.amp*self.A_hip_roll*math.sin(rp + math.pi)
                r_ankle_r   = self.neutral["AnkleRoll"]- self.amp*self.A_ankle_roll*math.sin(rp + math.pi) + roll_corr
                
                l_yaw = 0.02; r_yaw = -0.02
                
                clamp = lambda x, lo, hi: self.clamp(x,lo,hi)
                L = (clamp(l_yaw,-0.5,0.5), clamp(l_hip_roll,-0.45,0.45), clamp(l_hip_pitch,-1.2,0.6),
                     clamp(l_knee,-0.1,2.6), clamp(l_ankle_p,-1.0,0.9), clamp(l_ankle_r,-0.5,0.5))
                R = (clamp(r_yaw,-0.5,0.5), clamp(r_hip_roll,-0.45,0.45), clamp(r_hip_pitch,-1.2,0.6),
                     clamp(r_knee,-0.1,2.6), clamp(r_ankle_p,-1.0,0.9), clamp(r_ankle_r,-0.5,0.5))
                self.set_targets(L,R)
            else:
                self.set_neutral()
            
            v_meas = self.estimate_speed()
            fall = self.fall_detector(pitch, roll)
            self.log_row(mode, self.cmd_speed, v_meas, f, s, A_hp, A_k, A_ap, pitch, roll, gx, gy, self.amp, self.state, fall)
            
            # Tuning automation
            t = self.robot.getTime()
            if self.tuning_mode and self.state=="WALKING":
                if self.current_step_start is None:
                    self.current_step_start = t; self.fall_counter = 0
                dwell = t - self.current_step_start
                if fall:
                    print(f"[tuner] FALL at v_cmd={self.cmd_speed:.2f}. Stopping sweep.")
                    self.state="STOPPING"; self.amp_target=0.0; self.tuning_mode=False
                elif dwell >= self.dwell_time:
                    self.target_speed = min(self.v_max, self.target_speed + self.v_step)
                    if self.target_speed >= self.v_max:
                        print("[tuner] Sweep complete."); self.tuning_mode=False
                    self.current_step_start = t; self.fall_counter = 0
            
            if self.grid_mode and self.state=="WALKING":
                if self.current_step_start is None:
                    self.current_step_start = t; self.fall_counter = 0
                dwell = t - self.current_step_start
                if fall:
                    print(f"[grid] FALL at f={f:.2f}, s={s:.2f}. Marking unstable.")
                    # Advance grid
                    self.grid_j += 1
                    if self.grid_j >= len(self.grid_steps):
                        self.grid_j = 0; self.grid_i += 1
                    if self.grid_i >= len(self.grid_freqs):
                        print("[grid] Grid search complete."); self.grid_mode=False
                    self.current_step_start = None; self.fall_counter = 0
                elif dwell >= self.dwell_time:
                    # Stable at this point; advance
                    self.grid_j += 1
                    if self.grid_j >= len(self.grid_steps):
                        self.grid_j = 0; self.grid_i += 1
                    if self.grid_i >= len(self.grid_freqs):
                        print("[grid] Grid search complete."); self.grid_mode=False
                    self.current_step_start = None; self.fall_counter = 0

if __name__ == "__main__":
    c = WalkingControllerTuner()
    c.run()
