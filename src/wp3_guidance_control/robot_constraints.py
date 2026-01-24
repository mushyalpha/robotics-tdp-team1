"""
NAO6 Robot Physical Constraints and Limitations

This module documents all physical constraints of the NAO6 robot based on:
- Official NAO6 specifications (NAO6 Datasheet.md)
- Webots NaoV6.proto file
- Physics calculations

All values extracted from proto file on: November 3, 2025
Proto file version: NaoV6.proto (current version)

IMPORTANT: Some joints have asymmetric limits (left vs right), particularly
in leg joints (knee, ankle). This reflects the actual NAO6 hardware design.

Author: WP3
Date: October 2025 (Updated: November 2025)
"""

class NAO6Constraints:
    """Physical constraints for NAO6 humanoid robot.
    
    All angles in radians, velocities in rad/s, distances in meters.
    Values extracted directly from webots_simulation/protos/NaoV6.proto
    """
    
    # JOINT ANGLE LIMITS
    # (min,max) of angle in radians

    # LEFT LEG JOINTS
    L_HIP_YAW_PITCH_RANGE = (-1.145303, 0.740810)  # Hip yaw-pitch coupled joint (-65.6° to 42.4°)
    L_HIP_ROLL_RANGE = (-0.379472, 0.790477)       # Side leg swing (-21.7° to 45.3°)
    L_HIP_PITCH_RANGE = (-1.535889, 0.484090)      # Forward/back leg swing (-88° to 27.7°)
    L_KNEE_PITCH_RANGE = (-0.092346, 2.112528)     # Knee bend (-5.3° to 121°)
    L_ANKLE_PITCH_RANGE = (-1.189516, 0.922747)    # Ankle pitch (-68.2° to 52.9°)
    4L_ANKLE_ROLL_RANGE = (-0.397880, 0.769001)     # Ankle roll (-22.8° to 44.1°)
    
    # RIGHT LEG JOINTS - NOTE: Asymmetric to left leg
    R_HIP_YAW_PITCH_RANGE = (-1.145303, 0.740810)  # Same as left
    R_HIP_ROLL_RANGE = (-0.790477, 0.379472)       # Mirrored from left
    R_HIP_PITCH_RANGE = (-1.535889, 0.484090)      # Same as left
    R_KNEE_PITCH_RANGE = (-0.103083, 2.120198)     # DIFFERENT from left!
    R_ANKLE_PITCH_RANGE = (-1.186448, 0.932056)    # DIFFERENT from left!
    R_ANKLE_ROLL_RANGE = (-0.768992, 0.397935)     # Mirrored from left
    
    # HEAD JOINTS
    HEAD_YAW_RANGE = (-2.0857, 2.0857)             # Left/right head turn (~119.5°)
    HEAD_PITCH_RANGE = (-0.6720, 0.5149)           # Up/down head tilt (-38.5° to 29.5°)
    
    # LEFT ARM JOINTS
    L_SHOULDER_PITCH_RANGE = (-2.0857, 2.0857)     # Forward/back arm swing (~±119.5°)
    L_SHOULDER_ROLL_RANGE = (-0.3142, 1.3265)      # Arm raise to side (-18° to 76°)
    L_ELBOW_YAW_RANGE = (-2.0857, 2.0857)          # Arm rotation (~±119.5°)
    L_ELBOW_ROLL_RANGE = (-1.5446, -0.0349)        # Elbow bend (-88.5° to -2°)  [maxPosition commented in proto]
    L_WRIST_YAW_RANGE = (-1.82387, 1.82387)        # Wrist rotation (~±104.5°)
    L_HAND_RANGE = (0.0, 1.0)                      # Hand open/close (per phalanx)
    
    # RIGHT ARM JOINTS
    R_SHOULDER_PITCH_RANGE = (-2.0857, 2.0857)     # Forward/back arm swing (~±119.5°)
    R_SHOULDER_ROLL_RANGE = (-1.3265, 0.3142)      # Arm raise to side (mirrored)
    R_ELBOW_YAW_RANGE = (-2.0857, 2.0857)          # Arm rotation (~±119.5°)
    R_ELBOW_ROLL_RANGE = (0.0349, 1.5446)          # Elbow bend (2° to 88.5°)  [minPosition commented in proto]
    R_WRIST_YAW_RANGE = (-1.82387, 1.82387)        # Wrist rotation (~±104.5°)
    R_HAND_RANGE = (0.0, 1.0)                      # Hand open/close (per phalanx)
    
    # JOINT VELOCITY LIMITS
    # RotationalMotor maxVelocity in NaoV6.proto (rad/s)
    
    # HEAD
    HEAD_YAW_MAX_VELOCITY = 8.26797                # rad/s
    HEAD_PITCH_MAX_VELOCITY = 7.19407              # rad/s (~412°/s)
    
    # ARMS
    SHOULDER_PITCH_MAX_VELOCITY = 8.26797          # rad/s
    SHOULDER_ROLL_MAX_VELOCITY = 7.19407           # rad/s
    ELBOW_YAW_MAX_VELOCITY = 8.26797               # rad/s
    ELBOW_ROLL_MAX_VELOCITY = 7.19407              # rad/s
    WRIST_YAW_MAX_VELOCITY = 24.6229               # rad/s 
    
    # LEGS
    HIP_YAW_PITCH_MAX_VELOCITY = 4.16174           # rad/s (~238°/s)
    HIP_ROLL_MAX_VELOCITY = 4.16174                # rad/s
    HIP_PITCH_MAX_VELOCITY = 6.40239               # rad/s (~367°/s)
    KNEE_PITCH_MAX_VELOCITY = 6.40239              # rad/s
    ANKLE_PITCH_MAX_VELOCITY = 6.40239             # rad/s
    ANKLE_ROLL_MAX_VELOCITY = 4.16174              # rad/s
    
    # JOINT TORQUE LIMITS
    # RotationalMotor maxTorque in NaoV6.proto (Nm)
    
    # HEAD
    HEAD_YAW_MAX_TORQUE = 4.0                      # Nm 
    HEAD_PITCH_MAX_TORQUE = 5.0                    # Nm
    
    # ARMS
    SHOULDER_PITCH_MAX_TORQUE = 4.0                # Nm
    SHOULDER_ROLL_MAX_TORQUE = 5.0                 # Nm 
    ELBOW_YAW_MAX_TORQUE = 4.0                     # Nm 
    ELBOW_ROLL_MAX_TORQUE = 5.0                    # Nm 
    WRIST_YAW_MAX_TORQUE = 1.5                     # Nm 
    HAND_MAX_TORQUE = 10.0                         # Nm
    
    # LEGS (higher torque for weight bearing)
    HIP_YAW_PITCH_MAX_TORQUE = 14.8                # Nm 
    HIP_ROLL_MAX_TORQUE = 14.8                     # Nm 
    HIP_PITCH_MAX_TORQUE = 9.8                     # Nm
    KNEE_PITCH_MAX_TORQUE = 9.8                    # Nm 
    ANKLE_PITCH_MAX_TORQUE = 9.8                   # Nm
    ANKLE_ROLL_MAX_TORQUE = 14.8                   # Nm
    
    # PHYSICAL PROPERTIES
    # NAO6 Datasheet.md
    
    TOTAL_MASS = 5.48                              # kg
    HEIGHT = 0.574                                 # m
    WIDTH = 0.311                                  # m
    DEPTH = 0.275                                  # m
    
    # Centre of Mass
    COM_HEIGHT_STANDING = 0.31                     # m
    COM_OFFSET_X = 0.0                             # m
    COM_OFFSET_Y = 0.0                             # m
    
    # Link Masses
    HEAD_MASS = 0.559730                           # kg
    TORSO_MASS = 1.049560                          # kg
    L_UPPER_ARM_MASS = 0.150570                    # kg
    L_FOREARM_MASS = 0.156570                      # kg
    L_HAND_MASS = 0.187960                         # kg
    L_THIGH_MASS = 0.399730                        # kg
    L_TIBIA_MASS = 0.301960                        # kg
    L_FOOT_MASS = 0.170960                         # kg
    
    # FOOT GEOMETRY
    
    FOOT_LENGTH = 0.160                            # m 
    FOOT_WIDTH = 0.120                             # m 
    FOOT_HEIGHT = 0.025                            # m
    
    # BALANCE CONSTRAINTS
    
    # Zero Moment Poin Constraints
    ZMP_MARGIN = 0.02                              # meters from foot edge
    STABLE_ZMP_REGION_X = (-FOOT_LENGTH/2 + ZMP_MARGIN, FOOT_LENGTH/2 - ZMP_MARGIN)
    STABLE_ZMP_REGION_Y = (-FOOT_WIDTH/2 + ZMP_MARGIN, FOOT_WIDTH/2 - ZMP_MARGIN)
    
    # Body Lean Limits 
    MAX_FORWARD_LEAN = 0.15                        # rad
    MAX_BACKWARD_LEAN = 0.20                       # rad
    MAX_LATERAL_LEAN = 0.12                        # rad
    
    # MOTION CONSTRAINTS

    # Walking Capabilities 
    MAX_WALKING_SPEED_FORWARD = 0.15 # m/s
    MAX_WALKING_SPEED_BACKWARD = 0.08 # m/s
    MAX_WALKING_SPEED_SIDEWAYS = 0.1 # m/s 
    MAX_TURNING_RATE = 1.25 # rad/s
    
    # Step Parameters
    MAX_STEP_LENGTH = 0.17 # m                 
    MAX_STEP_HEIGHT = 0.31 # m         
    MAX_STEP_FREQUENCY = 0.895 # Hz
    MAX_STEP_ANGLE = 0.54 # rad ..from literature
    
    # Acceleration Limits
    max_friction_force = 32.3 # N
    MAX_LINEAR_ACCELERATION = 5.9 # m/s^2
    MAX_ANGULAR_ACCELERATION = 240 # rad/s^2
    
    # KICK CONSTRAINTS
    
    MAX_KICK_FORCE = None
    MAX_KICK_DISTANCE = None
    KICK_CONTACT_TIME = None

    
    # SENSOR SPECIFICATIONS
    # Source: NAO6 Datasheet.md
    
    # Camera (OV5640 sensor)
    CAMERA_RESOLUTION = (640, 480)                 # pixels (VGA @ 30 fps)
    CAMERA_FOV_HORIZONTAL = 56.3                   # degrees (HFOV)
    CAMERA_FOV_VERTICAL = 43.7                     # degrees (VFOV)
    CAMERA_FOV_DIAGONAL = 67.4                     # degrees (DFOV)
    CAMERA_FPS = 30                                # fps
    CAMERA_MAX_RANGE = 2.5                         # m (recognition range)
    CAMERA_FOCUS_RANGE = (0.10, float('inf'))      # m (10 cm to infinity)
    
    # Inertial Measurement Unit (IMU)
    GYRO_RANGE = 500                               # degrees/second
    ACCELEROMETER_RANGE = 2                        # g (gravity units)
    IMU_SAMPLE_RATE = 100                          # Hz
    
    # ENVIRONMENTAL CONSTRAINTS
    
    MAX_FLOOR_SLOPE = 5.0                          # degrees
    COEFFICIENT_FRICTION = 0.6                     # rubber on artificial grass
    
    # RoboCup Field Constraints in metres (KidSize Humanoid League)
    FIELD_LENGTH = 9.0                             
    FIELD_WIDTH = 6.0                              
    GOAL_WIDTH = 2.6                               
    GOAL_HEIGHT = 1.8                             
    PENALTY_AREA_LENGTH = 1.0                     
    PENALTY_AREA_WIDTH = 5.0               
    BALL_DIAMETER = 0.133                         
    
    # DEVICE NAME
    # For use in robot.getDevice() calls in controllers
    
    # Motors
    MOTOR_NAMES = {
        'head': ['HeadYaw', 'HeadPitch'],
        'left_arm': ['LShoulderPitch', 'LShoulderRoll', 'LElbowYaw', 'LElbowRoll', 'LWristYaw', 'LHand'],
        'right_arm': ['RShoulderPitch', 'RShoulderRoll', 'RElbowYaw', 'RElbowRoll', 'RWristYaw', 'RHand'],
        'left_leg': ['LHipYawPitch', 'LHipRoll', 'LHipPitch', 'LKneePitch', 'LAnklePitch', 'LAnkleRoll'],
        'right_leg': ['RHipYawPitch', 'RHipRoll', 'RHipPitch', 'RKneePitch', 'RAnklePitch', 'RAnkleRoll'],
    }
    
    # Sensors (append '_sensor' to motor name for position sensors)
    SENSOR_NAMES = {
        'cameras': ['CameraTop', 'CameraBottom'],
        'imu': ['IMU inertial', 'IMU gyro', 'IMU accelerometer'],
        'touch': ['ChestBoard/Button', 'Head/Touch/Front', 'Head/Touch/Middle', 'Head/Touch/Rear',
                 'LHand/Touch/Back', 'LHand/Touch/Left', 'LHand/Touch/Right',
                 'RHand/Touch/Back', 'RHand/Touch/Left', 'RHand/Touch/Right',
                 'LFoot/Bumper/Left', 'LFoot/Bumper/Right', 
                 'RFoot/Bumper/Left', 'RFoot/Bumper/Right'],
        'audio': ['MicroFrontLeft', 'MicroFrontRight', 'MicroRearLeft', 'MicroRearRight',
                 'SpeakerLeft', 'SpeakerRight'],
    }
    
    # HELPER METHODS
    
    @classmethod
    def get_safe_joint_limit(cls, joint_name, limit_type='position'):
        """
        Get safe joint limits with safety margin applied.
        
        Args:
            joint_name: Name of joint (e.g., 'L_HIP_PITCH')
            limit_type: 'position', 'velocity', or 'torque'
        
        Returns:
            tuple: (min_safe, max_safe) with safety margin applied
        """
        attr_name = f"{joint_name}_RANGE" if limit_type == 'position' else f"{joint_name}_MAX_{limit_type.upper()}"
        
        if not hasattr(cls, attr_name):
            raise ValueError(f"Unknown joint or limit type: {joint_name}, {limit_type}")
        
        value = getattr(cls, attr_name)
        
        if limit_type == 'position' and isinstance(value, tuple):
            min_val, max_val = value
            margin = cls.JOINT_ANGLE_SAFETY_MARGIN
            range_size = max_val - min_val
            reduction = range_size * (1 - margin) / 2
            return (min_val + reduction, max_val - reduction)
        elif limit_type == 'velocity':
            return value * cls.JOINT_VELOCITY_SAFETY_MARGIN
        elif limit_type == 'torque':
            return value * cls.JOINT_TORQUE_SAFETY_MARGIN
        else:
            return value
    
    @classmethod
    def is_within_limits(cls, joint_name, angle):
        """
        Check if angle is within safe joint limits.
        
        Args:
            joint_name: Name of joint (e.g., 'L_HIP_PITCH')
            angle: Angle in radians
        
        Returns:
            bool: True if within safe limits
        """
        min_safe, max_safe = cls.get_safe_joint_limit(joint_name, 'position')
        return min_safe <= angle <= max_safe


# MODULE-LEVEL CONSTANTS

#common constraints
JOINT_LIMITS = {
    'head_yaw': NAO6Constraints.HEAD_YAW_RANGE,
    'head_pitch': NAO6Constraints.HEAD_PITCH_RANGE,
    'l_hip_pitch': NAO6Constraints.L_HIP_PITCH_RANGE,
    'l_knee_pitch': NAO6Constraints.L_KNEE_PITCH_RANGE,
    'l_ankle_pitch': NAO6Constraints.L_ANKLE_PITCH_RANGE,
    'r_hip_pitch': NAO6Constraints.R_HIP_PITCH_RANGE,
    'r_knee_pitch': NAO6Constraints.R_KNEE_PITCH_RANGE,
    'r_ankle_pitch': NAO6Constraints.R_ANKLE_PITCH_RANGE,
}

# Example usage
if __name__ == "__main__":
    # Print all joint limits
    print("NAO6 Joint Angle Limits (radians):")
    print("=" * 60)
    print(f"Head Yaw:        {NAO6Constraints.HEAD_YAW_RANGE}")
    print(f"Head Pitch:      {NAO6Constraints.HEAD_PITCH_RANGE}")
    print(f"L Hip Pitch:     {NAO6Constraints.L_HIP_PITCH_RANGE}")
    print(f"L Knee Pitch:    {NAO6Constraints.L_KNEE_PITCH_RANGE}")
    print(f"L Ankle Pitch:   {NAO6Constraints.L_ANKLE_PITCH_RANGE}")
    print()
    print("Max Velocities (rad/s):")
    print("=" * 60)
    print(f"Hip:             {NAO6Constraints.HIP_PITCH_MAX_VELOCITY}")
    print(f"Knee:            {NAO6Constraints.KNEE_PITCH_MAX_VELOCITY}")
    print(f"Ankle:           {NAO6Constraints.ANKLE_PITCH_MAX_VELOCITY}")
    print()
    print("Physical Properties:")
    print("=" * 60)
    print(f"Total Mass:      {NAO6Constraints.TOTAL_MASS} kg")
    print(f"Height:          {NAO6Constraints.HEIGHT} m")
    print(f"Foot Size:       {NAO6Constraints.FOOT_LENGTH} × {NAO6Constraints.FOOT_WIDTH} m")

