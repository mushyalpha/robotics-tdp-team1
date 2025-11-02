"""
NAO6 Robot Physical Constraints and Limitations

This module documents all physical constraints of the NAO6 robot based on:
- Official NAO6 specifications (NAO6 Datasheet.md)
- Webots NAO.proto file (webots_simulation/protos/NAO.proto)
- Physics calculations
- Safety margins

All values extracted from proto file on: October 28, 2025
Proto file version: R2022b

Author: WP3 Team (Guidance & Control)
Date: October 2025
"""


class NAO6Constraints:
    """Physical constraints for NAO6 humanoid robot.
    
    All angles in radians, velocities in rad/s, distances in meters.
    Values extracted directly from webots_simulation/protos/NAO.proto
    """
    
    # ==================== JOINT ANGLE LIMITS ====================
    # Source: RotationalMotor minPosition/maxPosition in NAO.proto
    # Format: (min_angle, max_angle) in radians
    
    # HEAD JOINTS
    HEAD_YAW_RANGE = (-2.08567, 2.08567)           # Left/right head turn (~119.5°)
    HEAD_PITCH_RANGE = (-0.671952, 0.514872)       # Up/down head tilt (-38.5° to 29.5°)
    
    # LEFT ARM JOINTS
    L_SHOULDER_PITCH_RANGE = (-2.08567, 2.08567)   # Forward/back arm swing (~±119.5°)
    L_SHOULDER_ROLL_RANGE = (-0.314159, 1.32645)   # Arm raise to side (-18° to 76°)
    L_ELBOW_YAW_RANGE = (-2.08567, 2.08567)        # Arm rotation (~±119.5°)
    L_ELBOW_ROLL_RANGE = (-1.54462, -0.0349066)    # Elbow bend (-88.5° to -2°)
    L_WRIST_YAW_RANGE = (-1.82387, 1.82387)        # Wrist rotation (~±104.5°)
    L_HAND_RANGE = (0.0, 1.0)                      # Hand open/close
    
    # RIGHT ARM JOINTS
    R_SHOULDER_PITCH_RANGE = (-2.08567, 2.08567)
    R_SHOULDER_ROLL_RANGE = (-1.32645, 0.314159)   # 
    R_ELBOW_YAW_RANGE = (-2.08567, 2.08567)
    R_ELBOW_ROLL_RANGE = (0.0349066, 1.54462)      #
    R_WRIST_YAW_RANGE = (-1.82387, 1.82387)
    R_HAND_RANGE = (0.0, 1.0)
    
    # LEFT LEG JOINTS
    L_HIP_YAW_PITCH_RANGE = (-1.14529, 0.740718)   # Hip yaw-pitch coupled joint (-65.6° to 42.4°)
    L_HIP_ROLL_RANGE = (-0.379435, 0.79046)        # Side leg swing (-21.7° to 45.3°)
    L_HIP_PITCH_RANGE = (-1.53589, 0.48398)        # Forward/back leg swing (-88° to 27.7°)
    L_KNEE_PITCH_RANGE = (-0.0923279, 2.11255)     # Knee bend (-5.3° to 121°)
    L_ANKLE_PITCH_RANGE = (-1.18944, 0.922581)     # Ankle pitch (-68.2° to 52.9°)
    L_ANKLE_ROLL_RANGE = (-0.397761, 0.768992)     # Ankle roll (-22.8° to 44.1°)
    
    # RIGHT LEG JOINTS (symmetric to left)
    R_HIP_YAW_PITCH_RANGE = (-1.14529, 0.740718)
    R_HIP_ROLL_RANGE = (-0.79046, 0.379435)        # 
    R_HIP_PITCH_RANGE = (-1.53589, 0.48398)
    R_KNEE_PITCH_RANGE = (-0.0923279, 2.11255)
    R_ANKLE_PITCH_RANGE = (-1.18944, 0.922581)
    R_ANKLE_ROLL_RANGE = (-0.768992, 0.397761)     # Note: reversed from left
    
    # ==================== JOINT VELOCITY LIMITS ====================
    # RotationalMotor maxVelocity in NAO.proto (rad/s)
    
    # HEAD
    HEAD_YAW_MAX_VELOCITY = 8.26797                # rad/s
    HEAD_PITCH_MAX_VELOCITY = 7.19407              # rad/s (~412°/s)
    
    # ARMS
    SHOULDER_PITCH_MAX_VELOCITY = 8.26797          # rad/s
    SHOULDER_ROLL_MAX_VELOCITY = 7.19407           # rad/s
    ELBOW_YAW_MAX_VELOCITY = 8.26797               # rad/s
    ELBOW_ROLL_MAX_VELOCITY = 7.19407              # rad/s
    WRIST_YAW_MAX_VELOCITY = 24.6229               # rad/s 
    HAND_MAX_VELOCITY = 8.33                        # rad/s
    
    # LEGS
    HIP_YAW_PITCH_MAX_VELOCITY = 4.16174           # rad/s (~238°/s)
    HIP_ROLL_MAX_VELOCITY = 4.16174                # rad/s
    HIP_PITCH_MAX_VELOCITY = 6.40239               # rad/s (~367°/s)
    KNEE_PITCH_MAX_VELOCITY = 6.40239              # rad/s
    ANKLE_PITCH_MAX_VELOCITY = 6.40239             # rad/s
    ANKLE_ROLL_MAX_VELOCITY = 4.16174              # rad/s
    
    # JOINT TORQUE LIMITS
    # RotationalMotor maxTorque in NAO.proto (Nm)
    
    # HEAD
    HEAD_YAW_MAX_TORQUE = 2.148861                 # Nm
    HEAD_PITCH_MAX_TORQUE = 2.477046               # Nm
    
    # ARMS
    SHOULDER_PITCH_MAX_TORQUE = 3.366048           # Nm
    SHOULDER_ROLL_MAX_TORQUE = 2.477046            # Nm
    ELBOW_YAW_MAX_TORQUE = 2.148861                # Nm
    ELBOW_ROLL_MAX_TORQUE = 2.477046               # Nm
    WRIST_YAW_MAX_TORQUE = 0.475734                # Nm
    HAND_MAX_TORQUE = 0.340656                     # Nm
    
    # LEGS (higher torque for weight bearing)
    HIP_YAW_PITCH_MAX_TORQUE = 13.0845             # Nm
    HIP_ROLL_MAX_TORQUE = 13.0845                  # Nm
    HIP_PITCH_MAX_TORQUE = 8.50525                 # Nm
    KNEE_PITCH_MAX_TORQUE = 8.50525                # Nm
    ANKLE_PITCH_MAX_TORQUE = 8.50525               # Nm
    ANKLE_ROLL_MAX_TORQUE = 13.0845                # Nm
    
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
    
    FOOT_LENGTH = 0.160                            # meters (16 cm)
    FOOT_WIDTH = 0.120                             # meters (12 cm)
    FOOT_HEIGHT = 0.025                            # meters (2.5 cm)
    
    # BALANCE CONSTRAINTS
    
    # Zero Moment Poin Constraints
    ZMP_MARGIN = 0.02                              # meters from foot edge
    STABLE_ZMP_REGION_X = (-FOOT_LENGTH/2 + ZMP_MARGIN, FOOT_LENGTH/2 - ZMP_MARGIN)
    STABLE_ZMP_REGION_Y = (-FOOT_WIDTH/2 + ZMP_MARGIN, FOOT_WIDTH/2 - ZMP_MARGIN)
    
    # Body Lean Limits 
    MAX_FORWARD_LEAN = 0.15                        # radians (~8.6°)
    MAX_BACKWARD_LEAN = 0.20                       # radians (~11.5°)
    MAX_LATERAL_LEAN = 0.12                        # radians (~6.9°)
    
    # MOTION CONSTRAINTS

    # Walking Capabilities 
    MAX_WALKING_SPEED_FORWARD = 0.15               # m/s
    MAX_WALKING_SPEED_BACKWARD = 0.08              # m/s 
    MAX_WALKING_SPEED_SIDEWAYS = 0.10              # m/s
    MAX_TURNING_RATE = 0.40                        # rad/s
    
    # Step Parameters
    MAX_STEP_LENGTH = 0.08                         # m
    MAX_STEP_HEIGHT = 0.020                        # m
    MIN_STEP_DURATION = 0.4                        # s
    SAFE_STEP_FREQUENCY = 1.5                      # Hz
    
    # Acceleration Limits
    MAX_LINEAR_ACCELERATION = 0.5                  # m/s²
    MAX_ANGULAR_ACCELERATION = 1.0                 # rad/s²
    
    # KICK CONSTRAINTS
    
    MAX_KICK_FORCE = 25.0                          # N
    MAX_KICK_DISTANCE = 3.0                        # m
    KICK_CONTACT_TIME = 0.10                       # s
    
    # Kick Geometry (to be validated)
    KICK_APPROACH_ANGLES = (-45, 45)               # degrees
    MIN_BALL_DISTANCE = 0.08                       # meters
    MAX_BALL_DISTANCE = 0.25                       # meters
    KICK_FOOT_CLEARANCE = 0.05                     # meters above ground - ESTIMATE
    
    # SENSOR SPECIFICATIONS
    # Source: NAO6 Datasheet.md
    
    # Camera (OV5640 sensor)
    CAMERA_RESOLUTION = (640, 480)                 # pixels (VGA @ 30 fps)
    CAMERA_FOV_HORIZONTAL = 56.3                   # degrees (HFOV)
    CAMERA_FOV_VERTICAL = 43.7                     # degrees (VFOV)
    CAMERA_FOV_DIAGONAL = 67.4                     # degrees (DFOV)
    CAMERA_FPS = 30                                # frames per second
    CAMERA_MAX_RANGE = 2.5                         # meters (recognition range)
    CAMERA_FOCUS_RANGE = (0.10, float('inf'))      # meters (10 cm to infinity)
    
    # Inertial Measurement Unit (IMU)
    GYRO_RANGE = 500                               # degrees/second
    ACCELEROMETER_RANGE = 2                        # g (gravity units)
    IMU_SAMPLE_RATE = 100                          # Hz
    
    # ==================== ENVIRONMENTAL CONSTRAINTS ====================
    
    MAX_FLOOR_SLOPE = 5.0                          # degrees (maximum safe slope)
    COEFFICIENT_FRICTION = 0.6                     # rubber on artificial grass
    
    # RoboCup Field Constraints (KidSize Humanoid League)
    FIELD_LENGTH = 9.0                             # meters
    FIELD_WIDTH = 6.0                              # meters
    GOAL_WIDTH = 2.6                               # meters
    GOAL_HEIGHT = 1.8                              # meters
    PENALTY_AREA_LENGTH = 1.0                      # meters
    PENALTY_AREA_WIDTH = 5.0                       # meters
    BALL_DIAMETER = 0.133                          # meters (133 mm)
    
    # ==================== DEVICE NAMES ====================
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
    
    # ==================== HELPER METHODS ====================
    
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


# ==================== MODULE-LEVEL CONSTANTS ====================

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

