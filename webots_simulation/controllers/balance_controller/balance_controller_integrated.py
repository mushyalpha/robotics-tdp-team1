from controller import Robot, Motion
import os

class BalanceParameters:
    """Parameters for balance control and fall detection."""
    
    def __init__(self):
        # Safe zone ,no control needed
        self.safe_roll = 0.10      
        self.safe_pitch = 0.10     
        
        # Balance zone. PID control active
        self.balance_roll = 0.25  
        self.balance_pitch = 0.30  
        
        # Fall zone. need recovery
        self.fall_roll = 0.6       # ~34.4°
        self.fall_pitch = 0.6   
        self.fall_angular_velocity = 3.7 
    
    def get_stability_state(self, roll, pitch, roll_rate, pitch_rate):
 
        if self.is_falling(roll, pitch, roll_rate, pitch_rate):
            return 'falling'

        if abs(roll) < self.safe_roll and abs(pitch) < self.safe_pitch:
            return 'stable'
    
        return 'balancing'
    
    def is_falling(self, roll, pitch, roll_rate, pitch_rate):
        """Detect if robot is falling."""
        angle_large = (
            abs(roll) > self.fall_roll or
            abs(pitch) > self.fall_pitch
        )
        rate_large = (
            abs(roll_rate) > self.fall_angular_velocity or
            abs(pitch_rate) > self.fall_angular_velocity
        )
        return angle_large or rate_large


class PIDController:

    def __init__(self, kp, ki, kd, output_limit=0.3, slew_limit=0.05, i_max=0.3):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.output_limit = output_limit
        self.slew_limit = slew_limit
        self.i_max = i_max
        
        # State variables
        self.integral = 0.0
        self.prev_error = 0.0
        self.prev_output = 0.0
        
        # Integral leak parameters
        self.leak_tau = 8.0  # s
        self.eps = 0.02      # Dead zone for integral
    
    def update(self, error, dt):
        """
        Calculate PID output with safety limits.
        
        Args:
            error: Current error (target - actual)
            dt: Time step
        
        Returns:
            Control output
        """
        # Proportional term
        p_term = self.kp * error
        
        # Integral term
        # Only accumulate if error is small and output not saturated
        if abs(error) < self.eps and abs(self.prev_output) < self.output_limit * 0.95:
            self.integral += error * dt
        
        # Integral leak
        self.integral *= (1.0 - dt / self.leak_tau)
        
        # Clamp integral
        self.integral = max(min(self.integral, self.i_max), -self.i_max)
        i_term = self.ki * self.integral
        
        # Derivative term
        derivative = (error - self.prev_error) / dt if dt > 0 else 0.0
        d_term = self.kd * derivative
        
        # Total output
        output = p_term + i_term + d_term
        
        # Output limiting
        output = max(min(output, self.output_limit), -self.output_limit)
        
        # Slew rate limiting
        delta = output - self.prev_output
        if delta > self.slew_limit:
            output = self.prev_output + self.slew_limit
        elif delta < -self.slew_limit:
            output = self.prev_output - self.slew_limit
        
        # Update state
        self.prev_error = error
        self.prev_output = output
        
        return output
    
    def reset(self):
        """Reset controller state."""
        self.integral = 0.0
        self.prev_error = 0.0
        self.prev_output = 0.0


class BalanceController:
    def __init__(self, robot):
        self.robot = robot
        self.timestep = int(robot.getBasicTimeStep())
        self.dt = self.timestep / 1000.0
        
        # parameters
        self.params = BalanceParameters()
        
        # Initialise PID controllers
        # Pitch control
        self.pid_pitch = PIDController(
            kp=2.0,
            ki=0.1,
            kd=0.3,
            output_limit=0.3,
            slew_limit=0.05,
            i_max=0.3
        )
        
        # Roll control
        self.pid_roll = PIDController(
            kp=1.5,  # lower than pitch
            ki=0.08,
            kd=0.25,
            output_limit=0.3,
            slew_limit=0.05,
            i_max=0.3
        )
        
        # Initialise sensors
        self.imu = robot.getDevice("InertialUnit")
        self.imu.enable(self.timestep)
        self.gyro = robot.getDevice("Gyro")
        self.gyro.enable(self.timestep)
        
        # Initialise motors
        self.motors = {
            'LHipPitch': robot.getDevice('LHipPitch'),
            'RHipPitch': robot.getDevice('RHipPitch'),
            'LKneePitch': robot.getDevice('LKneePitch'),
            'RKneePitch': robot.getDevice('RKneePitch'),
            'LAnklePitch': robot.getDevice('LAnklePitch'),
            'RAnklePitch': robot.getDevice('RAnklePitch'),
            'LHipRoll': robot.getDevice('LHipRoll'),
            'RHipRoll': robot.getDevice('RHipRoll'),
            'LAnkleRoll': robot.getDevice('LAnkleRoll'),
            'RAnkleRoll': robot.getDevice('RAnkleRoll'),
        }
        
        # Load fall recovery motion
        motion_path = os.path.join("..", "..", "motions", "StandUpFromFront.motion")
        if os.path.exists(motion_path):
            self.recovery_motion = Motion(motion_path)
        else:
            self.recovery_motion = None
        
        # State tracking
        self.is_recovering = False
        self.recovery_start_time = 0
        
        # Standing pose
        self.standing_pose = {
            'LHipPitch': 0.0,
            'RHipPitch': 0.0,
            'LKneePitch': 0.0,
            'RKneePitch': 0.0,
            'LAnklePitch': 0.01,
            'RAnklePitch': 0.01,
            'LHipRoll': 0.0,
            'RHipRoll': 0.0,
            'LAnkleRoll': 0.0,
            'RAnkleRoll': 0.0,
        }
        
        print("Balance Controller initialized!")
        print(f"PID Gains - Pitch: Kp={self.pid_pitch.kp}, Ki={self.pid_pitch.ki}, Kd={self.pid_pitch.kd}")
        print(f"PID Gains - Roll:  Kp={self.pid_roll.kp}, Ki={self.pid_roll.ki}, Kd={self.pid_roll.kd}")
        print()
    
    def set_standing_pose(self):
        """Set robot to neutral standing position."""
        for joint_name, angle in self.standing_pose.items():
            if joint_name in self.motors:
                self.motors[joint_name].setPosition(angle)
    
    def apply_balance_adjustments(self, roll, pitch):
        """ apply PID corrections for balance"""
        # Calculate errors 
        roll_error = 0.0 - roll
        pitch_error = 0.0 - pitch
        
        # PID corrections
        roll_correction = self.pid_roll.update(roll_error, self.dt)
        pitch_correction = self.pid_pitch.update(pitch_error, self.dt)
        
        # Apply pitch correction to hip pitch (primary)
        # Negative sign because positive pitch = forward lean, need backward correction
        hip_pitch_adjustment = -pitch_correction
        
        # Apply roll correction to hip/ankle roll
        ankle_roll_adjustment = roll_correction
        hip_roll_adjustment = 0.5 * roll_correction  # Hip has less effect
        
        # Set joint positions (base pose + adjustments)
        self.motors['LHipPitch'].setPosition(self.standing_pose['LHipPitch'] + hip_pitch_adjustment)
        self.motors['RHipPitch'].setPosition(self.standing_pose['RHipPitch'] + hip_pitch_adjustment)
        
        self.motors['LAnkleRoll'].setPosition(self.standing_pose['LAnkleRoll'] + ankle_roll_adjustment)
        self.motors['RAnkleRoll'].setPosition(self.standing_pose['RAnkleRoll'] - ankle_roll_adjustment)  # Opposite
        
        self.motors['LHipRoll'].setPosition(self.standing_pose['LHipRoll'] + hip_roll_adjustment)
        self.motors['RHipRoll'].setPosition(self.standing_pose['RHipRoll'] - hip_roll_adjustment)  # Opposite
    
    def prepare_for_recovery(self):
        """Position arms for fall recovery."""
        # Get arm motors if available
        arm_motors = {
            "LShoulderPitch": 1.2,
            "RShoulderPitch": 1.2,
            "LShoulderRoll": 0.3,
            "RShoulderRoll": -0.3,
            "LElbowRoll": -0.5,
            "RElbowRoll": 0.5,
        }
        
        for name, angle in arm_motors.items():
            motor = self.robot.getDevice(name)
            if motor:
                motor.setPosition(angle)
        
        # Wait for positioning
        for _ in range(10):
            self.robot.step(self.timestep)
    
    def update(self):
        """ Main update loop 
        
        Returns:
            Current stability state
        """
        # Read sensors
        roll, pitch, yaw = self.imu.getRollPitchYaw()
        gx, gy, gz = self.gyro.getValues()
        roll_rate = gx
        pitch_rate = gy
        
        # Check if recovering from fall
        if self.is_recovering:
            if self.recovery_motion and self.recovery_motion.isOver():
                recovery_time = self.robot.getTime() - self.recovery_start_time
                print(f"\n=== RECOVERY COMPLETE ({recovery_time:.1f}s) ===\n")
                self.is_recovering = False
                self.pid_pitch.reset()
                self.pid_roll.reset()
            return 'recovering'
        
        # Get stability state
        state = self.params.get_stability_state(roll, pitch, roll_rate, pitch_rate)
        
        # Handle different states
        if state == 'falling':
            print(f"\n=== FALL DETECTED ===")
            print(f"Roll: {roll:.2f} rad, Pitch: {pitch:.2f} rad")
            
            if self.recovery_motion:
                print("Starting recovery motion...\n")
                self.prepare_for_recovery()
                self.recovery_motion.play()
                self.is_recovering = True
                self.recovery_start_time = self.robot.getTime()
            else:
                print("No recovery motion available - resetting to standing pose\n")
                self.set_standing_pose()
                self.pid_pitch.reset()
                self.pid_roll.reset()
        
        elif state == 'balancing':
            # Apply PID corrections
            self.apply_balance_adjustments(roll, pitch)
        
        else:  # stable
            # Maintain standing pose
            self.set_standing_pose()
        
        return state

def main():
    robot = Robot()
    
    # Create balance controller
    controller = BalanceController(robot)
    
    # Main loop
    print("Starting balance control loop...\n")
    
    step_count = 0
    while robot.step(controller.timestep) != -1:
        # Update balance controller
        state = controller.update()
        
        # status every 2 seconds
        if step_count % 200 == 0:
            roll, pitch, _ = controller.imu.getRollPitchYaw()
            print(f"State: {state:12s} | Roll: {roll:6.3f} | Pitch: {pitch:6.3f}")
        
        step_count += 1


if __name__ == "__main__":
    main()

