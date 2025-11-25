"""
Fall Recovery Controller for NAO6 Robot
Implements multi-phase fall recovery sequences based on fall direction
Author: Bonolo
Date: Nov 17, 2025
"""

from controller import Robot
import sys
import os

# Add project root to path to import robot constraints
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
        self.phase_duration = 1.5  # seconds per phase
    
    def detect_fall_direction(self, roll, pitch):
        """
        Detect which direction robot has fallen.
        
        Args:
            roll: Roll angle (rad)
            pitch: Pitch angle (rad)
        
        Returns:
            Fall direction: 'front', 'back', 'left', 'right', or 'none'
        """
        # Check pitch first (front/back falls are more common)
        if pitch > 0.6:
            return 'front'
        elif pitch < -0.6:
            return 'back'
        
        # Check roll (left/right)
        if roll > 0.6:
            return 'right'
        elif roll < -0.6:
            return 'left'
        
        return 'none'
    
    def get_recovery_sequence_front(self, phase):
        """
        Get joint positions for recovering from front fall.
        
        Phase 0: Tuck legs and prepare
        Phase 1: Push with arms, transition
        Phase 2: Bring feet under body
        Phase 3: Stand up
        Phase 4+: Final standing position
        """
        if phase == 0:
            # Tuck legs
            return {
                'LHipPitch': 1.5,
                'RHipPitch': 1.5,
                'LKneePitch': -2.0,
                'RKneePitch': -2.0,
                'LAnklePitch': 0.0,
                'RAnklePitch': 0.0,
                'LShoulderPitch': 1.2,
                'RShoulderPitch': 1.2,
                'LElbowRoll': -0.5,
                'RElbowRoll': 0.5,
            }
        elif phase == 1:
            # Push up transition
            return {
                'LHipPitch': 1.0,
                'RHipPitch': 1.0,
                'LKneePitch': -1.5,
                'RKneePitch': -1.5,
                'LAnklePitch': -0.5,
                'RAnklePitch': -0.5,
                'LShoulderPitch': 1.0,
                'RShoulderPitch': 1.0,
            }
        elif phase == 2:
            # Bring feet under body
            return {
                'LHipPitch': 0.5,
                'RHipPitch': 0.5,
                'LKneePitch': -1.2,
                'RKneePitch': -1.2,
                'LAnklePitch': -0.4,
                'RAnklePitch': -0.4,
                'LShoulderPitch': 0.5,
                'RShoulderPitch': 0.5,
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
        """Get joint positions for recovering from back fall."""
        if phase == 0:
            # Roll to side first
            return {
                'LHipPitch': -1.2,
                'RHipPitch': -1.2,
                'LKneePitch': 2.0,
                'RKneePitch': 2.0,
                'LAnklePitch': 0.5,
                'RAnklePitch': 0.5,
                'LHipRoll': 0.3,
                'RHipRoll': 0.3,
            }
        elif phase == 1:
            # Transition to front-like position
            return {
                'LHipPitch': 0.5,
                'RHipPitch': 0.5,
                'LKneePitch': -1.5,
                'RKneePitch': -1.5,
                'LAnklePitch': -0.3,
                'RAnklePitch': -0.3,
            }
        elif phase == 2:
            # Get on knees
            return {
                'LHipPitch': 0.3,
                'RHipPitch': 0.3,
                'LKneePitch': -1.0,
                'RKneePitch': -1.0,
                'LAnklePitch': -0.4,
                'RAnklePitch': -0.4,
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
    
    def update_recovery(self, dt, fall_direction):
        """
        Update recovery sequence.
        
        Args:
            dt: Time step (seconds)
            fall_direction: Direction of fall
        
        Returns:
            (joint_positions, recovery_complete)
        """
        self.phase_time += dt
        
        # Move to next phase after duration
        if self.phase_time >= self.phase_duration:
            self.recovery_phase += 1
            self.phase_time = 0.0
            print(f"Recovery phase {self.recovery_phase}")
        
        # Get joint positions for current phase
        if fall_direction == 'front':
            joints = self.get_recovery_sequence_front(self.recovery_phase)
        elif fall_direction == 'back':
            joints = self.get_recovery_sequence_back(self.recovery_phase)
        else:
            # For left/right, treat as front for now
            joints = self.get_recovery_sequence_front(self.recovery_phase)
        
        # Check if recovery complete
        recovery_complete = self.recovery_phase >= 4
        
        return joints, recovery_complete
    
    def reset(self):
        """Reset recovery state."""
        self.recovery_phase = 0
        self.phase_time = 0.0


# Initialize robot
robot = Robot()
timestep = int(robot.getBasicTimeStep())
dt = timestep / 1000.0  # Convert to seconds

# Initialize sensors
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

# Initialize controllers
params = BalanceParameters()
recovery = FallRecovery()

# State variables
is_recovering = False
fall_direction = 'none'
recovery_start_time = 0

print("Fall Recovery Controller initialized!")
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

