# %% [markdown]

# # Task 3: Balance & Posture Controller for NAO6 Robot

#

# **Assignee:** Bonolo  

# **Duration:** 5 days  

# **Objective:** Implement a balance controller that uses IMU feedback to maintain stability, recover from disturbances, and handle falls.

#

# ## Learning Objectives

# - Understand bipedal balance and stability

# - Implement IMU-based feedback control

# - Create PID controllers for joint adjustments

# - Implement Zero Moment Point (ZMP) calculations

# - Develop fall detection and recovery sequences

#

# ## Key Concepts

# 1. **Center of Mass (CoM):** The average position of mass in the robot

# 2. **Zero Moment Point (ZMP):** Point where net moment is zero - must stay within support polygon

# 3. **Support Polygon:** Area defined by contact points with ground

# 4. **IMU Feedback:** Using gyroscope and accelerometer data for balance

# 5. **PID Control:** Proportional-Integral-Derivative control for smooth corrections

  

# %% [markdown]

# ---

# ## Setup and Imports

  

# %%

# Import necessary libraries

import numpy as np

import matplotlib.pyplot as plt

from typing import Dict, Tuple, List

import sys

import os

  

# Add project root to path

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

  

# Import robot constraints

from src.wp3_guidance_control.robot_constraints import NAO6Constraints

  

# For Webots integration (optional during development)

try:

    from controller import Robot, Motor, InertialUnit, Gyro, Accelerometer

    WEBOTS_AVAILABLE = True

except ImportError:

    WEBOTS_AVAILABLE = False

    print("Webots not available - using simulation mode")

  

# %% [markdown]

# ---

# ## Task 3.1: Understanding Balance Parameters

#

# Define the key parameters that control balance behaviour.

  

# %%

class BalanceParameters:

    """Parameters for balance control."""

    def __init__(self):

        # Stability thresholds

        self.max_roll_angle = ...  # TODO: Maximum safe roll (rad) - try 0.3 rad (~17°)

        self.max_pitch_angle = ...  # TODO: Maximum safe pitch (rad) - try 0.4 rad (~23°)

        self.max_angular_velocity = ...  # TODO: Maximum safe angular velocity (rad/s) - try 2.0

        # PID gains for ankle control (roll)

        self.ankle_roll_kp = ...  # TODO: Proportional gain - try 0.5

        self.ankle_roll_ki = ...  # TODO: Integral gain - try 0.01

        self.ankle_roll_kd = ...  # TODO: Derivative gain - try 0.1

        # PID gains for ankle control (pitch)

        self.ankle_pitch_kp = ...  # TODO: Proportional gain - try 0.4

        self.ankle_pitch_ki = ...  # TODO: Integral gain - try 0.01

        self.ankle_pitch_kd = ...  # TODO: Derivative gain - try 0.08

        # PID gains for hip control

        self.hip_roll_kp = ...  # TODO: Proportional gain - try 0.3

        self.hip_pitch_kp = ...  # TODO: Proportional gain - try 0.3

        # Center of mass parameters

        self.nominal_com_height = ...  # TODO: Target CoM height (m) - try 0.25m

        self.com_shift_limit = ...  # TODO: Maximum CoM shift (m) - try 0.05m

        # Fall detection thresholds

        self.fall_roll_threshold = ...  # TODO: Roll angle indicating fall (rad) - try 0.7 rad

        self.fall_pitch_threshold = ...  # TODO: Pitch angle indicating fall (rad) - try 0.8 rad

    def is_stable(self, roll: float, pitch: float) -> bool:

        """

        Check if robot is in stable configuration.

        Args:

            roll: Current roll angle (rad)

            pitch: Current pitch angle (rad)

        Returns:

            True if stable, False otherwise

        """

        return ...  # TODO: Check if abs(roll) < max_roll and abs(pitch) < max_pitch

    def is_falling(self, roll: float, pitch: float) -> bool:

        """

        Check if robot is falling.

        Args:

            roll: Current roll angle (rad)

            pitch: Current pitch angle (rad)

        Returns:

            True if falling, False otherwise

        """

        return ...  # TODO: Check if abs(roll) > fall_threshold or abs(pitch) > fall_threshold

  

# Test your implementation

params = BalanceParameters()

print(f"Stable at roll=0.2, pitch=0.3: {params.is_stable(0.2, 0.3)}")

print(f"Falling at roll=0.8, pitch=0.2: {params.is_falling(0.8, 0.2)}")

  

# %% [markdown]

# ---

# ## Task 3.2: PID Controller Implementation

#

# Implement a PID controller for smooth balance corrections.

  

# %%

class PIDController:

    """

    PID controller for balance adjustments.

    """

    def __init__(self, kp: float, ki: float, kd: float):

        """

        Initialise PID controller.

        Args:

            kp: Proportional gain

            ki: Integral gain

            kd: Derivative gain

        """

        self.kp = kp

        self.ki = ki

        self.kd = kd

        # State variables

        self.integral = 0.0

        self.previous_error = 0.0

    def reset(self):

        """Reset controller state."""

        self.integral = 0.0

        self.previous_error = 0.0

    def update(self, error: float, dt: float) -> float:

        """

        Calculate control output based on error.

        Args:

            error: Current error (target - actual)

            dt: Time step (seconds)

        Returns:

            Control output

        """

        # Proportional term

        p_term = ...  # TODO: Calculate proportional term (kp * error)

        # Integral term (with anti-windup)

        self.integral += ...  # TODO: Add error * dt to integral

        self.integral = ...  # TODO: Clamp integral between -1.0 and 1.0 (anti-windup)

        i_term = ...  # TODO: Calculate integral term (ki * integral)

        # Derivative term

        derivative = ...  # TODO: Calculate derivative ((error - previous_error) / dt)

        d_term = ...  # TODO: Calculate derivative term (kd * derivative)

        # Update previous error

        self.previous_error = error

        # Total output

        output = ...  # TODO: Sum all terms (p_term + i_term + d_term)

        return output

  

# Test PID controller

pid = PIDController(kp=0.5, ki=0.1, kd=0.05)

  

# Simulate step response

time_points = np.linspace(0, 5, 500)

dt = time_points[1] - time_points[0]

errors = []

outputs = []

  

# Simulate error that decreases over time

for t in time_points:

    error = 0.5 * np.exp(-t)  # Exponentially decreasing error

    output = pid.update(error, dt)

    errors.append(error)

    outputs.append(output)

  

plt.figure(figsize=(10, 4))

plt.subplot(1, 2, 1)

plt.plot(time_points, errors, 'r-', linewidth=2, label='Error')

plt.xlabel('Time (s)')

plt.ylabel('Error')

plt.title('Error Over Time')

plt.legend()

plt.grid(True)

  

plt.subplot(1, 2, 2)

plt.plot(time_points, outputs, 'b-', linewidth=2, label='PID Output')

plt.xlabel('Time (s)')

plt.ylabel('Control Output')

plt.title('PID Controller Response')

plt.legend()

plt.grid(True)

  

plt.tight_layout()

plt.show()

  

# %% [markdown]

# ---

# ## Task 3.3: IMU Data Processing

#

# Process IMU data to extract useful information for balance control.

  

# %%

class IMUProcessor:

    """

    Process IMU data for balance control.

    """

    def __init__(self):

        """Initialise IMU processor."""

        # Filtering parameters

        self.alpha = ...  # TODO: Low-pass filter coefficient - try 0.8

        # Filtered values

        self.filtered_roll = 0.0

        self.filtered_pitch = 0.0

        self.filtered_gyro_x = 0.0

        self.filtered_gyro_y = 0.0

        self.filtered_gyro_z = 0.0

    def process_imu_data(self, roll: float, pitch: float, yaw: float,

                        gyro_x: float, gyro_y: float, gyro_z: float) -> Dict[str, float]:

        """

        Process and filter IMU data.

        Args:

            roll: Roll angle from IMU (rad)

            pitch: Pitch angle from IMU (rad)

            yaw: Yaw angle from IMU (rad)

            gyro_x: Angular velocity around X axis (rad/s)

            gyro_y: Angular velocity around Y axis (rad/s)

            gyro_z: Angular velocity around Z axis (rad/s)

        Returns:

            Dictionary of processed IMU data

        """

        # Apply low-pass filter to reduce noise

        # filtered = alpha * previous + (1 - alpha) * current

        self.filtered_roll = ...  # TODO: Apply low-pass filter to roll

        self.filtered_pitch = ...  # TODO: Apply low-pass filter to pitch

        self.filtered_gyro_x = ...  # TODO: Apply low-pass filter to gyro_x

        self.filtered_gyro_y = ...  # TODO: Apply low-pass filter to gyro_y

        self.filtered_gyro_z = ...  # TODO: Apply low-pass filter to gyro_z

        return {

            'roll': self.filtered_roll,

            'pitch': self.filtered_pitch,

            'yaw': yaw,

            'gyro_x': self.filtered_gyro_x,

            'gyro_y': self.filtered_gyro_y,

            'gyro_z': self.filtered_gyro_z,

        }

    def detect_disturbance(self, gyro_magnitude: float, threshold: float = 1.5) -> bool:

        """

        Detect sudden disturbances based on gyro data.

        Args:

            gyro_magnitude: Magnitude of angular velocity

            threshold: Threshold for disturbance detection (rad/s)

        Returns:

            True if disturbance detected

        """

        return ...  # TODO: Check if gyro_magnitude > threshold

  

# Test IMU processor with simulated noisy data

imu_processor = IMUProcessor()

  

# Simulate noisy IMU data

time_points = np.linspace(0, 2, 200)

true_roll = 0.1 * np.sin(2 * np.pi * time_points)  # Oscillating roll

noisy_roll = true_roll + np.random.normal(0, 0.02, len(time_points))  # Add noise

  

filtered_rolls = []

for roll in noisy_roll:

    processed = imu_processor.process_imu_data(roll, 0.0, 0.0, 0.0, 0.0, 0.0)

    filtered_rolls.append(processed['roll'])

  

plt.figure(figsize=(10, 5))

plt.plot(time_points, true_roll, 'g-', linewidth=2, label='True Roll', alpha=0.7)

plt.plot(time_points, noisy_roll, 'r.', markersize=2, label='Noisy Roll', alpha=0.5)

plt.plot(time_points, filtered_rolls, 'b-', linewidth=2, label='Filtered Roll')

plt.xlabel('Time (s)')

plt.ylabel('Roll Angle (rad)')

plt.title('IMU Data Filtering')

plt.legend()

plt.grid(True)

plt.show()

  

# %% [markdown]

# ---

# ## Task 3.4: Zero Moment Point (ZMP) Calculation

#

# Calculate ZMP to ensure robot stability.

  

# %%

def calculate_zmp(com_position: Tuple[float, float, float],

                 com_velocity: Tuple[float, float, float],

                 com_acceleration: Tuple[float, float, float],

                 robot_mass: float = 5.4) -> Tuple[float, float]:

    """

    Calculate Zero Moment Point position.

    The ZMP must stay within the support polygon for stability.

    Args:

        com_position: Center of mass position (x, y, z) in meters

        com_velocity: Center of mass velocity (vx, vy, vz) in m/s

        com_acceleration: Center of mass acceleration (ax, ay, az) in m/s²

        robot_mass: Total robot mass in kg

    Returns:

        (zmp_x, zmp_y): ZMP position in ground plane

    """

    g = 9.81  # Gravity (m/s²)

    x_com, y_com, z_com = com_position

    ax, ay, az = com_acceleration

    # ZMP equations (simplified)

    # zmp_x = x_com - (z_com / (az + g)) * ax

    # zmp_y = y_com - (z_com / (az + g)) * ay

    zmp_x = ...  # TODO: Calculate ZMP x position

    zmp_y = ...  # TODO: Calculate ZMP y position

    return zmp_x, zmp_y

  

def is_zmp_stable(zmp_x: float, zmp_y: float, foot_positions: List[Tuple[float, float]]) -> bool:

    """

    Check if ZMP is within support polygon.

    Args:

        zmp_x: ZMP x position

        zmp_y: ZMP y position

        foot_positions: List of (x, y) positions of feet in contact with ground

    Returns:

        True if ZMP is within support polygon

    """

    # Simplified check: ZMP should be close to center of foot positions

    if len(foot_positions) == 0:

        return False

    # Calculate center of support polygon

    center_x = ...  # TODO: Calculate mean x position of feet

    center_y = ...  # TODO: Calculate mean y position of feet

    # Check distance from center

    distance = ...  # TODO: Calculate distance from ZMP to center

    # ZMP should be within reasonable distance (e.g., 0.1m)

    return ...  # TODO: Check if distance < 0.1

  

# Test ZMP calculation

com_pos = (0.0, 0.0, 0.25)  # CoM at 25cm height

com_vel = (0.1, 0.0, 0.0)   # Moving forward at 0.1 m/s

com_acc = (0.0, 0.0, 0.0)   # No acceleration

  

zmp_x, zmp_y = calculate_zmp(com_pos, com_vel, com_acc)

print(f"ZMP position: ({zmp_x:.3f}, {zmp_y:.3f})")

  

# Check stability with two feet

foot_positions = [(-0.05, 0.05), (-0.05, -0.05)]  # Left and right foot

stable = is_zmp_stable(zmp_x, zmp_y, foot_positions)

print(f"ZMP stable: {stable}")

  

# %% [markdown]

# ---

# ## Task 3.5: Balance Adjustment Calculation

#

# Calculate joint adjustments needed to maintain balance.

  

# %%

def calculate_balance_adjustments(imu_data: Dict[str, float],

                                 pid_roll: PIDController,

                                 pid_pitch: PIDController,

                                 dt: float) -> Dict[str, float]:

    """

    Calculate joint adjustments to maintain balance.

    Args:

        imu_data: Processed IMU data

        pid_roll: PID controller for roll

        pid_pitch: PID controller for pitch

        dt: Time step (seconds)

    Returns:

        Dictionary of joint adjustments

    """

    roll = imu_data['roll']

    pitch = imu_data['pitch']

    # Target is zero roll and pitch (upright)

    roll_error = ...  # TODO: Calculate roll error (0.0 - roll)

    pitch_error = ...  # TODO: Calculate pitch error (0.0 - pitch)

    # Calculate corrections using PID

    roll_correction = ...  # TODO: Call pid_roll.update(roll_error, dt)

    pitch_correction = ...  # TODO: Call pid_pitch.update(pitch_error, dt)

    # Apply corrections to joints

    # Roll correction affects ankle roll and hip roll

    # Pitch correction affects ankle pitch and hip pitch

    adjustments = {

        'LAnkleRoll': ...,  # TODO: Apply roll_correction

        'RAnkleRoll': ...,  # TODO: Apply -roll_correction (opposite)

        'LAnklePitch': ...,  # TODO: Apply pitch_correction

        'RAnklePitch': ...,  # TODO: Apply pitch_correction

        'LHipRoll': ...,  # TODO: Apply roll_correction * 0.5 (less aggressive)

        'RHipRoll': ...,  # TODO: Apply -roll_correction * 0.5

        'LHipPitch': ...,  # TODO: Apply pitch_correction * 0.3

        'RHipPitch': ...,  # TODO: Apply pitch_correction * 0.3

    }

    # Clamp adjustments to safe limits

    for joint_name in adjustments:

        adjustments[joint_name] = ...  # TODO: Clamp between -0.2 and 0.2 rad

    return adjustments

  

# Test balance adjustment calculation

params = BalanceParameters()

pid_roll = PIDController(params.ankle_roll_kp, params.ankle_roll_ki, params.ankle_roll_kd)

pid_pitch = PIDController(params.ankle_pitch_kp, params.ankle_pitch_ki, params.ankle_pitch_kd)

  

# Simulate tilted robot

imu_data = {'roll': 0.1, 'pitch': -0.05, 'yaw': 0.0,

            'gyro_x': 0.0, 'gyro_y': 0.0, 'gyro_z': 0.0}

  

adjustments = calculate_balance_adjustments(imu_data, pid_roll, pid_pitch, 0.01)

print("Balance adjustments:")

for joint, adjustment in adjustments.items():

    print(f"  {joint}: {np.degrees(adjustment):.2f}°")

  

# %% [markdown]

# ---

# ## Task 3.6: Fall Recovery Sequences

#

# Implement sequences to get up after falling.

  

# %%

class FallRecovery:

    """

    Fall detection and recovery sequences.

    """

    def __init__(self):

        """Initialise fall recovery."""

        self.recovery_phase = 0

        self.phase_time = 0.0

    def detect_fall_direction(self, roll: float, pitch: float) -> str:

        """

        Detect which direction robot has fallen.

        Args:

            roll: Roll angle (rad)

            pitch: Pitch angle (rad)

        Returns:

            Fall direction: 'front', 'back', 'left', 'right', or 'none'

        """

        # Check pitch first (front/back)

        if pitch > 0.8:

            return 'front'

        elif pitch < -0.8:

            return 'back'

        # Check roll (left/right)

        if roll > 0.7:

            return 'left'

        elif roll < -0.7:

            return 'right'

        return 'none'

    def get_recovery_sequence_front(self, phase: int) -> Dict[str, float]:

        """

        Get joint positions for recovering from front fall.

        Args:

            phase: Current recovery phase (0-4)

        Returns:

            Dictionary of joint positions

        """

        if phase == 0:

            # Tuck legs

            return {

                'LHipPitch': ...,  # TODO: Bend hips forward (e.g., 1.5 rad)

                'RHipPitch': ...,

                'LKneePitch': ...,  # TODO: Bend knees (e.g., -2.0 rad)

                'RKneePitch': ...,

                'LAnklePitch': 0.0,

                'RAnklePitch': 0.0,

            }

        elif phase == 1:

            # Push up with arms (simplified - just transition)

            return {

                'LHipPitch': 1.0,

                'RHipPitch': 1.0,

                'LKneePitch': -1.5,

                'RKneePitch': -1.5,

                'LAnklePitch': -0.5,

                'RAnklePitch': -0.5,

            }

        elif phase == 2:

            # Bring feet under body

            return {

                'LHipPitch': 0.0,

                'RHipPitch': 0.0,

                'LKneePitch': -1.0,

                'RKneePitch': -1.0,

                'LAnklePitch': -0.3,

                'RAnklePitch': -0.3,

            }

        elif phase == 3:

            # Stand up

            return {

                'LHipPitch': -0.3,

                'RHipPitch': -0.3,

                'LKneePitch': 0.6,

                'RKneePitch': 0.6,

                'LAnklePitch': -0.3,

                'RAnklePitch': -0.3,

            }

        else:

            # Standing position

            return {

                'LHipPitch': -0.3,

                'RHipPitch': -0.3,

                'LKneePitch': 0.6,

                'RKneePitch': 0.6,

                'LAnklePitch': -0.3,

                'RAnklePitch': -0.3,

            }

    def get_recovery_sequence_back(self, phase: int) -> Dict[str, float]:

        """

        Get joint positions for recovering from back fall.

        Args:

            phase: Current recovery phase (0-4)

        Returns:

            Dictionary of joint positions

        """

        # TODO: Implement back fall recovery sequence

        # Similar structure to front recovery but different joint angles

        pass

    def update_recovery(self, dt: float, fall_direction: str) -> Tuple[Dict[str, float], bool]:

        """

        Update recovery sequence.

        Args:

            dt: Time step (seconds)

            fall_direction: Direction of fall

        Returns:

            (joint_positions, recovery_complete)

        """

        self.phase_time += dt

        # Each phase lasts 1 second

        if self.phase_time >= 1.0:

            self.recovery_phase += 1

            self.phase_time = 0.0

        # Get joint positions for current phase

        if fall_direction == 'front':

            joints = self.get_recovery_sequence_front(self.recovery_phase)

        elif fall_direction == 'back':

            joints = self.get_recovery_sequence_back(self.recovery_phase)

        else:

            joints = {}

        # Check if recovery complete

        recovery_complete = ...  # TODO: Check if recovery_phase >= 4

        return joints, recovery_complete

  

# Test fall recovery

recovery = FallRecovery()

  

# Simulate fall detection

fall_dir = recovery.detect_fall_direction(roll=0.0, pitch=1.0)

print(f"Fall direction: {fall_dir}")

  

# Get first recovery phase

joints, complete = recovery.update_recovery(0.5, fall_dir)

print(f"Recovery phase {recovery.recovery_phase}:")

for joint, angle in joints.items():

    print(f"  {joint}: {np.degrees(angle):.2f}°")

  

# %% [markdown]

# ---

# ## Task 3.7: Complete Balance Controller Class

#

# Integrate all balance components into the final `BalanceController` class.

  

# %%

class BalanceController:

    """

    Complete balance controller for NAO6 robot.

    Provides continuous balance maintenance, disturbance recovery,

    and fall detection/recovery.

    """

    def __init__(self, robot=None):

        """

        Initialise balance controller.

        Args:

            robot: Webots Robot instance (optional)

        """

        self.robot = robot

        self.params = BalanceParameters()

        # PID controllers

        self.pid_roll = PIDController(

            self.params.ankle_roll_kp,

            self.params.ankle_roll_ki,

            self.params.ankle_roll_kd

        )

        self.pid_pitch = PIDController(

            self.params.ankle_pitch_kp,

            self.params.ankle_pitch_ki,

            self.params.ankle_pitch_kd

        )

        # IMU processor

        self.imu_processor = IMUProcessor()

        # Fall recovery

        self.fall_recovery = FallRecovery()

        # State

        self.is_falling = False

        self.is_recovering = False

        # Sensors

        self.imu = None

        self.gyro = None

        self.accelerometer = None

        # Motors

        self.motors = {}

        if robot:

            self._initialise_devices()

    def _initialise_devices(self):

        """Initialise sensors and motors."""

        # Get IMU

        self.imu = ...  # TODO: Get IMU from robot

        if self.imu:

            timestep = int(self.robot.getBasicTimeStep())

            self.imu.enable(timestep)

        # Get gyro

        self.gyro = ...  # TODO: Get gyro from robot

        if self.gyro:

            self.gyro.enable(timestep)

        # Get motors

        joint_names = [

            'LHipPitch', 'LKneePitch', 'LAnklePitch', 'LHipRoll', 'LAnkleRoll',

            'RHipPitch', 'RKneePitch', 'RAnklePitch', 'RHipRoll', 'RAnkleRoll'

        ]

        for joint_name in joint_names:

            motor = self.robot.getDevice(joint_name)

            if motor:

                self.motors[joint_name] = motor

    def maintain_balance(self, imu_data: dict) -> Dict[str, float]:

        """

        Continuous balance adjustments based on IMU.

        Args:

            imu_data: Dictionary with IMU readings

        Returns:

            Dictionary of joint adjustments

        """

        # Process IMU data

        processed_imu = self.imu_processor.process_imu_data(

            imu_data.get('roll', 0.0),

            imu_data.get('pitch', 0.0),

            imu_data.get('yaw', 0.0),

            imu_data.get('gyro_x', 0.0),

            imu_data.get('gyro_y', 0.0),

            imu_data.get('gyro_z', 0.0)

        )

        # Calculate balance adjustments

        adjustments = calculate_balance_adjustments(

            processed_imu, self.pid_roll, self.pid_pitch, 0.01

        )

        return adjustments

    def recover_balance(self, disturbance: dict) -> Dict[str, float]:

        """

        Emergency recovery from push/collision.

        Args:

            disturbance: Dictionary describing disturbance

        Returns:

            Dictionary of joint positions for recovery

        """

        # TODO: Implement emergency recovery

        # For now, return aggressive balance adjustments

        return self.maintain_balance(disturbance)

    def adjust_posture(self, target_com: Tuple[float, float]) -> Dict[str, float]:

        """

        Shift center of mass for stability.

        Args:

            target_com: Target (x, y) position for center of mass

        Returns:

            Dictionary of joint adjustments

        """

        # TODO: Implement CoM shifting

        # This would calculate joint angles to move CoM to target position

        return {}

    def get_up_from_fall(self, fall_direction: str) -> Dict[str, float]:

        """

        Recovery sequence after falling.

        Args:

            fall_direction: Direction of fall ('front', 'back', 'left', 'right')

        Returns:

            Dictionary of joint positions for current recovery phase

        """

        joints, complete = self.fall_recovery.update_recovery(0.01, fall_direction)

        if complete:

            self.is_recovering = False

            self.is_falling = False

        return joints

    def update(self, dt: float) -> Dict[str, float]:

        """

        Update balance controller.

        Args:

            dt: Time step (seconds)

        Returns:

            Dictionary of joint positions/adjustments

        """

        # Read IMU data

        if self.imu:

            roll, pitch, yaw = self.imu.getRollPitchYaw()

        else:

            roll, pitch, yaw = 0.0, 0.0, 0.0

        if self.gyro:

            gyro_values = self.gyro.getValues()

            gyro_x, gyro_y, gyro_z = gyro_values

        else:

            gyro_x, gyro_y, gyro_z = 0.0, 0.0, 0.0

        imu_data = {

            'roll': roll, 'pitch': pitch, 'yaw': yaw,

            'gyro_x': gyro_x, 'gyro_y': gyro_y, 'gyro_z': gyro_z

        }

        # Check for falls

        if self.params.is_falling(roll, pitch) and not self.is_recovering:

            self.is_falling = True

            self.is_recovering = True

            fall_direction = self.fall_recovery.detect_fall_direction(roll, pitch)

            return self.get_up_from_fall(fall_direction)

        # If recovering, continue recovery sequence

        if self.is_recovering:

            fall_direction = self.fall_recovery.detect_fall_direction(roll, pitch)

            return self.get_up_from_fall(fall_direction)

        # Normal balance maintenance

        return self.maintain_balance(imu_data)

  

# Test the complete controller

controller = BalanceController()

print("Balance Controller initialised successfully!")

  

# Test balance maintenance

imu_data = {'roll': 0.1, 'pitch': -0.05, 'yaw': 0.0,

            'gyro_x': 0.0, 'gyro_y': 0.0, 'gyro_z': 0.0}

adjustments = controller.maintain_balance(imu_data)

print("\nBalance adjustments:")

for joint, adjustment in adjustments.items():

    print(f"  {joint}: {np.degrees(adjustment):.2f}°")

  

# %% [markdown]

# ---

# ## Deliverables Checklist

#

# Before submitting, ensure you have completed:

#

# - [ ] **Task 3.1:** Balance parameters defined and tested

# - [ ] **Task 3.2:** PID controller implemented and tested

# - [ ] **Task 3.3:** IMU data processing working

# - [ ] **Task 3.4:** ZMP calculation implemented

# - [ ] **Task 3.5:** Balance adjustment calculation working

# - [ ] **Task 3.6:** Fall recovery sequences defined

# - [ ] **Task 3.7:** Complete `BalanceController` class implemented

# - [ ] **Code Quality:** All functions documented with docstrings

# - [ ] **Testing:** Controller tested with various IMU inputs

# - [ ] **Constraints:** All joint angles respect `NAO6Constraints` limits

# - [ ] **Webots Test:** Robot maintains balance during disturbances

#

# ## Next Steps

#

# After completing this task:

# 1. Save the `BalanceController` class to `src/wp3_guidance_control/balance_controller.py`

# 2. Test in Webots simulation with disturbances

# 3. Integrate with `WalkingController` and `TurningController`

# 4. Tune PID gains for optimal performance

# 5. Update development log with progress