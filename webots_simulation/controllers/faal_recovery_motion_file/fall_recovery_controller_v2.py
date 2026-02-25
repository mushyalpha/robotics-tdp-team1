"""
Practical Fall Recovery Controller for NAO6 Robot

Uses Webots' built-in motion files for reliable fall recovery.
This is the industry-standard approach used by professional teams.

Author: Bonolo
Date: Nov 18, 2025
"""

from controller import Robot, Motion
import os

# Initialize robot
robot = Robot()
timestep = int(robot.getBasicTimeStep())

# Initialize sensors
imu = robot.getDevice("InertialUnit")
imu.enable(timestep)
gyro = robot.getDevice("Gyro")
gyro.enable(timestep)

# Load motion file for front fall recovery
motion_path = os.path.join("..", "..", "motions", "StandUpFromFront.motion")
stand_up_front = Motion(motion_path)

# Fall detection parameters
FALL_PITCH_THRESHOLD = 0.6  # rad (~34 degrees)
FALL_ROLL_THRESHOLD = 0.6   # rad (~34 degrees)
FALL_ANGULAR_VELOCITY = 3.7 # rad/s

# State tracking
is_recovering = False
recovery_start_time = 0

print("Fall Recovery Controller initialized!")
print("Using Webots motion files for reliable recovery")
print()

def detect_fall_direction(roll, pitch):
    """
    Detect which direction the robot has fallen.
    
    Args:
        roll: Roll angle (rad)
        pitch: Pitch angle (rad)
    
    Returns:
        'front', 'back', 'left', 'right', or 'none'
    """
    # Prioritize pitch (front/back) over roll (left/right)
    if abs(pitch) > abs(roll):
        if pitch > FALL_PITCH_THRESHOLD:
            return 'front'
        elif pitch < -FALL_PITCH_THRESHOLD:
            return 'back'
    else:
        if roll > FALL_ROLL_THRESHOLD:
            return 'right'
        elif roll < -FALL_ROLL_THRESHOLD:
            return 'left'
    
    return 'none'

def is_falling(roll, pitch, roll_rate, pitch_rate):
    """Check if robot is falling based on angles and angular velocities."""
    angle_large = (
        abs(roll) > FALL_ROLL_THRESHOLD or
        abs(pitch) > FALL_PITCH_THRESHOLD
    )
    rate_large = (
        abs(roll_rate) > FALL_ANGULAR_VELOCITY or
        abs(pitch_rate) > FALL_ANGULAR_VELOCITY
    )
    return angle_large or rate_large

def prepare_for_recovery():
    """Position arms and legs for recovery."""
    print("Preparing for recovery...")
    
    # Get arm motors
    motors = {
        "LShoulderPitch": 1.2,
        "RShoulderPitch": 1.2,
        "LShoulderRoll": 0.3,
        "RShoulderRoll": -0.3,
        "LElbowRoll": -0.5,
        "RElbowRoll": 0.5,
    }
    
    for name, angle in motors.items():
        motor = robot.getDevice(name)
        motor.setPosition(angle)
    
    # Wait for positioning
    for _ in range(10):
        robot.step(timestep)

# Main control loop
while robot.step(timestep) != -1:
    # Read sensors
    roll, pitch, yaw = imu.getRollPitchYaw()
    gx, gy, gz = gyro.getValues()
    roll_rate = gx
    pitch_rate = gy
    
    # Check if currently recovering
    if is_recovering:
        if stand_up_front.isOver():
            print("=== RECOVERY COMPLETE ===")
            recovery_time = (robot.getTime() - recovery_start_time)
            print(f"Recovery took {recovery_time:.1f} seconds")
            print()
            is_recovering = False
        else:
            # Still recovering
            print(f"Recovering... | Roll: {roll:6.2f} | Pitch: {pitch:6.2f}")
        continue
    
    # Check for fall
    if is_falling(roll, pitch, roll_rate, pitch_rate):
        fall_direction = detect_fall_direction(roll, pitch)
        
        if fall_direction != 'none':
            print(f"=== FALL DETECTED: {fall_direction} ===")
            print(f"Roll: {roll:.2f} rad, Pitch: {pitch:.2f} rad")
            print()
            
            if fall_direction == 'front':
                # Use motion file for front fall
                prepare_for_recovery()
                stand_up_front.play()
                is_recovering = True
                recovery_start_time = robot.getTime()
            else:
                # For other directions, provide feedback
                print(f"Note: Only front fall recovery is implemented with motion files.")
                print(f"Back/side fall recovery requires additional motion files.")
                print(f"Attempting front recovery sequence...")
                print()
                prepare_for_recovery()
                stand_up_front.play()
                is_recovering = True
                recovery_start_time = robot.getTime()
    else:
        # Robot is stable
        state = "stable"
        print(f"State: {state:9s} | Roll: {roll:6.2f} | Pitch: {pitch:6.2f}")

