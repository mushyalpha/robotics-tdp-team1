from controller import Robot
import sys
import os

# project root t path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.wp3_guidance_control.robot_constraints import NAO6Constraints


class BalanceParameters:
    """Parameters for balance control and fall detection."""
    
    def __init__(self):
        # Safe zone - no control needed
        self.safe_roll = 0.10
        self.safe_pitch_forward = 0.10
        self.safe_pitch_backward = 0.12
        
        # Balance zone - PID control active
        self.max_roll_angle = 0.25
        self.max_pitch_angle = 0.30
        
        # Fall zone - recovery sequence needed
        self.roll_fall_angle = 0.6
        self.pitch_fall_angle = 0.6
        
        # Angular velocity threshold for early fall detection
        self.max_angular_velocity = 3.7
    
    def is_stable(self, roll, pitch):
        """Check if robot is in safe zone."""
        return (
            abs(roll) < self.safe_roll and 
            -self.safe_pitch_backward < pitch < self.safe_pitch_forward
        )
    
    def is_falling(self, roll, pitch, roll_rate, pitch_rate):
        """Detect if robot is falling (angle OR velocity too large)."""
        angle_large = (
            abs(roll) > self.roll_fall_angle or 
            abs(pitch) > self.pitch_fall_angle
        )
        rate_large = (
            abs(roll_rate) > self.max_angular_velocity or
            abs(pitch_rate) > self.max_angular_velocity
        )
        return angle_large or rate_large
    
    def get_stability_state(self, roll, pitch, roll_rate, pitch_rate):
        """Get current stability state."""
        if self.is_falling(roll, pitch, roll_rate, pitch_rate):
            return 'falling'
        elif not self.is_stable(roll, pitch):
            return 'balancing'
        else:
            return 'stable'


class FallRecovery:
    """Fall detection and recovery sequences."""
    
    def __init__(self):
        self.recovery_phase = 0
        self.phase_time = 0.0
        self.phase_duration = 2.0  # secs/phase
    
    def detect_fall_direction(self, roll, pitch):
        """  Fall direction: 'front', 'back', 'left', 'right', or 'none' """
        
        abs_roll = abs(roll)
        abs_pitch = abs(pitch)
        
        #is piutch or roll dominant?
        if abs_pitch > abs_roll:
            # Front/back fall
            if pitch > 0.6:
                return 'front'
            elif pitch < -0.6:
                return 'back'
        else:
            # Side fall
            if roll > 0.6:
                return 'right'
            elif roll < -0.6:
                return 'left'
        
        return 'none'
    
    def get_recovery_sequence_front(self, phase):

        if phase == 0:
            # Tuck legs, bend knees forward hop back
            return {
                'LHipPitch': -1.3,   
                'RHipPitch': -1.3,
                'LKneePitch': 2.0,  #bend knees forward
                'RKneePitch': 2.0,
                'LAnklePitch': 0.5,
                'RAnklePitch': 0.5,
                'LShoulderPitch': 1.5,  
                'RShoulderPitch': 1.5,
                'LElbowRoll': -0.8,
                'RElbowRoll': 0.8,
            }
        elif phase == 1:
            # kneeling posiontion
            return {
                'LHipPitch': -0.8,
                'RHipPitch': -0.8,
                'LKneePitch': 1.8,
                'RKneePitch': 1.8,
                'LAnklePitch': 0.3,
                'RAnklePitch': 0.3,
                'LShoulderPitch': 1.2,
                'RShoulderPitch': 1.2,
            }
        elif phase == 2:
            # prepare to stand
            return {
                'LHipPitch': -0.5,
                'RHipPitch': -0.5,
                'LKneePitch': 1.5,
                'RKneePitch': 1.5,
                'LAnklePitch': 0.0,
                'RAnklePitch': 0.0,
                'LShoulderPitch': 0.8,
                'RShoulderPitch': 0.8,
            }
        elif phase == 3:
            # Stand up
            return {
                'LHipPitch': -0.2,
                'RHipPitch': -0.2,
                'LKneePitch': 0.5,
                'RKneePitch': 0.5,
                'LAnklePitch': -0.3,
                'RAnklePitch': -0.3,
                'LShoulderPitch': 1.5,
                'RShoulderPitch': 1.5,
            }
        else:
            # Final standing position
            return {
                'LHipPitch': -0.3,
                'RHipPitch': -0.3,
                'LKneePitch': 0.6,
                'RKneePitch': 0.6,
                'LAnklePitch': -0.3,
                'RAnklePitch': -0.3,
                'LShoulderPitch': 1.5,
                'RShoulderPitch': 1.5,
            }
    
    def get_recovery_sequence_back(self, phase):
        """
        Get joint positions for recovering from back fall.
        Strategy: Roll to side, then use front recovery sequence.
        """
        if phase == 0:
            # Tuck and roll to side
            return {
                'LHipPitch': -1.2,
                'RHipPitch': -1.2,
                'LKneePitch': 2.0,     
                'RKneePitch': 2.0,
                'LAnklePitch': 0.5,
                'RAnklePitch': 0.5,
                'LHipRoll': 0.5,      
                'RHipRoll': -0.3,
            }
        elif phase == 1:
            # kneeling
            return {
                'LHipPitch': -0.8,
                'RHipPitch': -0.8,
                'LKneePitch': 1.8,
                'RKneePitch': 1.8,
                'LAnklePitch': 0.3,
                'RAnklePitch': 0.3,
                'LHipRoll': 0.0,
                'RHipRoll': 0.0,
            }
        elif phase == 2:
            # Prepare to stand
            return {
                'LHipPitch': -0.5,
                'RHipPitch': -0.5,
                'LKneePitch': 1.5,
                'RKneePitch': 1.5,
                'LAnklePitch': 0.0,
                'RAnklePitch': 0.0,
            }
        elif phase == 3:
            # Stand up
            return {
                'LHipPitch': -0.2,
                'RHipPitch': -0.2,
                'LKneePitch': 0.5,
                'RKneePitch': 0.5,
                'LAnklePitch': -0.3,
                'RAnklePitch': -0.3,
            }
        else:
            # Final standing
            return {
                'LHipPitch': -0.3,
                'RHipPitch': -0.3,
                'LKneePitch': 0.6,
                'RKneePitch': 0.6,
                'LAnklePitch': -0.3,
                'RAnklePitch': -0.3,
            }
    
    def get_recovery_sequence_left(self, phase):

        if phase == 0:
            # Extend right leg, tuck left leg to initiate roll
            return {
                'LHipPitch': -1.3,      # Left leg tucked back
                'RHipPitch': 0.3,       # Right leg forward
                'LKneePitch': 2.0,      # Left knee bent
                'RKneePitch': 0.5,      # Right knee straighter
                'LAnklePitch': 0.8,
                'RAnklePitch': -0.5,
                'LHipRoll': 0.7,        # Strong roll right
                'RHipRoll': -0.6,       # Strong roll right
                'LShoulderPitch': 2.0,  # Arms up and forward
                'RShoulderPitch': 2.0,
                'LShoulderRoll': 0.3,
                'RShoulderRoll': -0.3,
            }
        elif phase == 1:
            # rolling motion with momentum
            return {
                'LHipPitch': -1.4,
                'RHipPitch': 0.2,
                'LKneePitch': 2.0,
                'RKneePitch': 1.0,
                'LAnklePitch': 0.7,
                'RAnklePitch': -0.3,
                'LHipRoll': 0.5,
                'RHipRoll': -0.5,
                'LShoulderPitch': 1.8,
                'RShoulderPitch': 1.8,
                'LElbowRoll': -1.0,
                'RElbowRoll': 1.0,
            }
        elif phase == 2:
            # Should be on stomach now, get into push-up position
            return {
                'LHipPitch': -1.2,
                'RHipPitch': -1.2,
                'LKneePitch': 2.0,
                'RKneePitch': 2.0,
                'LAnklePitch': 0.5,
                'RAnklePitch': 0.5,
                'LHipRoll': 0.0,
                'RHipRoll': 0.0,
                'LShoulderPitch': 1.5,
                'RShoulderPitch': 1.5,
                'LElbowRoll': -0.8,
                'RElbowRoll': 0.8,
            }
        elif phase == 3:
            # Push up to kneeling
            return {
                'LHipPitch': -0.8,
                'RHipPitch': -0.8,
                'LKneePitch': 1.8,
                'RKneePitch': 1.8,
                'LAnklePitch': 0.3,
                'RAnklePitch': 0.3,
                'LHipRoll': 0.0,
                'RHipRoll': 0.0,
                'LShoulderPitch': 1.2,
                'RShoulderPitch': 1.2,
            }
        elif phase == 4:
            # Bring feet under body
            return {
                'LHipPitch': -0.5,
                'RHipPitch': -0.5,
                'LKneePitch': 1.5,
                'RKneePitch': 1.5,
                'LAnklePitch': 0.0,
                'RAnklePitch': 0.0,
                'LShoulderPitch': 0.8,
                'RShoulderPitch': 0.8,
            }
        elif phase == 5:
            # Stand up
            return {
                'LHipPitch': -0.2,
                'RHipPitch': -0.2,
                'LKneePitch': 0.5,
                'RKneePitch': 0.5,
                'LAnklePitch': -0.3,
                'RAnklePitch': -0.3,
                'LShoulderPitch': 1.5,
                'RShoulderPitch': 1.5,
            }
        else:
            # Final standing
            return {
                'LHipPitch': -0.3,
                'RHipPitch': -0.3,
                'LKneePitch': 0.6,
                'RKneePitch': 0.6,
                'LAnklePitch': -0.3,
                'RAnklePitch': -0.3,
                'LShoulderPitch': 1.5,
                'RShoulderPitch': 1.5,
            }
    
    def get_recovery_sequence_right(self, phase):
        """
        Get joint positions for recovering from right side fall.
        Strategy: Use asymmetric leg positioning to roll onto stomach.
        Right side = robot's right is on ground, need to roll LEFT.
        """
        if phase == 0:
            #
            return {
                'LHipPitch': 0.3,       # Left leg forward
                'RHipPitch': -1.3,      # Right leg tucked back
                'LKneePitch': 0.5,      # Left knee straighter
                'RKneePitch': 2.0,      # Right knee bent
                'LAnklePitch': -0.5,
                'RAnklePitch': 0.8,
                'LHipRoll': -0.6,       # Strong roll left
                'RHipRoll': 0.7,        # Strong roll left
                'LShoulderPitch': 2.0,  # Arms up and forward
                'RShoulderPitch': 2.0,
                'LShoulderRoll': 0.3,
                'RShoulderRoll': -0.3,
            }
        elif phase == 1:
            # rolling motion with momentum
            return {
                'LHipPitch': 0.2,
                'RHipPitch': -1.4,
                'LKneePitch': 1.0,
                'RKneePitch': 2.0,
                'LAnklePitch': -0.3,
                'RAnklePitch': 0.7,
                'LHipRoll': -0.5,
                'RHipRoll': 0.5,
                'LShoulderPitch': 1.8,
                'RShoulderPitch': 1.8,
                'LElbowRoll': -1.0,
                'RElbowRoll': 1.0,
            }
        elif phase == 2:
            # get into push-up position
            return {
                'LHipPitch': -1.2,
                'RHipPitch': -1.2,
                'LKneePitch': 2.0,
                'RKneePitch': 2.0,
                'LAnklePitch': 0.5,
                'RAnklePitch': 0.5,
                'LHipRoll': 0.0,
                'RHipRoll': 0.0,
                'LShoulderPitch': 1.5,
                'RShoulderPitch': 1.5,
                'LElbowRoll': -0.8,
                'RElbowRoll': 0.8,
            }
        elif phase == 3:
            # Push up to kneeling
            return {
                'LHipPitch': -0.8,
                'RHipPitch': -0.8,
                'LKneePitch': 1.8,
                'RKneePitch': 1.8,
                'LAnklePitch': 0.3,
                'RAnklePitch': 0.3,
                'LHipRoll': 0.0,
                'RHipRoll': 0.0,
                'LShoulderPitch': 1.2,
                'RShoulderPitch': 1.2,
            }
        elif phase == 4:
            # Bring feet under body
            return {
                'LHipPitch': -0.5,
                'RHipPitch': -0.5,
                'LKneePitch': 1.5,
                'RKneePitch': 1.5,
                'LAnklePitch': 0.0,
                'RAnklePitch': 0.0,
                'LShoulderPitch': 0.8,
                'RShoulderPitch': 0.8,
            }
        elif phase == 5:
            # Stand up
            return {
                'LHipPitch': -0.2,
                'RHipPitch': -0.2,
                'LKneePitch': 0.5,
                'RKneePitch': 0.5,
                'LAnklePitch': -0.3,
                'RAnklePitch': -0.3,
                'LShoulderPitch': 1.5,
                'RShoulderPitch': 1.5,
            }
        else:
            # Final standing
            return {
                'LHipPitch': -0.3,
                'RHipPitch': -0.3,
                'LKneePitch': 0.6,
                'RKneePitch': 0.6,
                'LAnklePitch': -0.3,
                'RAnklePitch': -0.3,
                'LShoulderPitch': 1.5,
                'RShoulderPitch': 1.5,
            }
    
    def update_recovery(self, dt, fall_direction):
        """ Update recovery sequence.
    
        returns (joint_positions, recovery_complete)
        """
        self.phase_time += dt
        
        # Move to next phase after duration
        if self.phase_time >= self.phase_duration:
            self.recovery_phase += 1
            self.phase_time = 0.0
            print(f"Recovery phase {self.recovery_phase}")
        
        # joint positions on current phase
        if fall_direction == 'front':
            joints = self.get_recovery_sequence_front(self.recovery_phase)
            max_phases = 4
        elif fall_direction == 'back':
            joints = self.get_recovery_sequence_back(self.recovery_phase)
            max_phases = 4
        elif fall_direction == 'left':
            joints = self.get_recovery_sequence_left(self.recovery_phase)
            max_phases = 6  # more phase for side falls
        elif fall_direction == 'right':
            joints = self.get_recovery_sequence_right(self.recovery_phase)
            max_phases = 6  
        else:
            joints = {}
            max_phases = 4
        
        # is recovery compleet
        recovery_complete = self.recovery_phase >= max_phases
        
        return joints, recovery_complete
    
    def reset(self):
        """Reset recovery state."""
        self.recovery_phase = 0
        self.phase_time = 0.0


robot = Robot()
timestep = int(robot.getBasicTimeStep())
dt = timestep / 1000.0  # Convert to seconds

# sensors
imu = robot.getDevice("InertialUnit")
imu.enable(timestep)
gyro = robot.getDevice("Gyro")
gyro.enable(timestep)

# Get all motors we might need
motor_names = [
    'LHipPitch', 'RHipPitch', 'LKneePitch', 'RKneePitch',
    'LAnklePitch', 'RAnklePitch', 'LHipRoll', 'RHipRoll',
    'LAnkleRoll', 'RAnkleRoll', 'LShoulderPitch', 'RShoulderPitch',
    'LElbowRoll', 'RElbowRoll', 'LShoulderRoll', 'RShoulderRoll'
]

motors = {}
for name in motor_names:
    motor = robot.getDevice(name)
    if motor:
        motors[name] = motor
    else:
        print(f"Warning: Could not find motor {name}")

# controllers
params = BalanceParameters()
recovery = FallRecovery()

# State variables
is_recovering = False
fall_direction = 'none'
recovery_start_time = 0

print("Fall Recovery Controller initialised!")
print("Waiting for robot to fall...")

# Main control loop
while robot.step(timestep) != -1:
    # Read IMU data
    roll, pitch, yaw = imu.getRollPitchYaw()
    gx, gy, gz = gyro.getValues()
    roll_rate = gx
    pitch_rate = gy
    
    # Get stability state
    state = params.get_stability_state(roll, pitch, roll_rate, pitch_rate)
    
    # Check if we should start recovery
    if state == 'falling' and not is_recovering:
        fall_direction = recovery.detect_fall_direction(roll, pitch)
        if fall_direction != 'none':
            print(f"\n=== FALL DETECTED: {fall_direction} ===")
            print(f"Roll: {roll:.2f} rad, Pitch: {pitch:.2f} rad")
            is_recovering = True
            recovery.reset()
            recovery_start_time = robot.getTime()
    
    # Execute recovery sequence
    if is_recovering:
        joint_positions, complete = recovery.update_recovery(dt, fall_direction)
        
        # Apply joint positions
        for joint_name, position in joint_positions.items():
            if joint_name in motors:
                motors[joint_name].setPosition(position)
        
        # Check if recovery is complete
        if complete:
            recovery_time = robot.getTime() - recovery_start_time
            print(f"\n=== RECOVERY COMPLETE ===")
            print(f"Recovery took {recovery_time:.1f} seconds")
            is_recovering = False
            fall_direction = 'none'
    else:
        # Normal operation - maintain standing pose
        if state == 'stable':
            # Robot is stable, maintain neutral position
            pass
        else:
            # Could add balance control here
            pass
    
    # Debug output every 2 seconds
    if int(robot.getTime() * 10) % 20 == 0:
        print(f"State: {state:10s} | Roll: {roll:6.2f} | Pitch: {pitch:6.2f} | Recovering: {is_recovering}")

