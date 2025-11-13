# ## Learning Objectives

# - Understand rotational motion for bipedal robots

# - Implement in-place turning and curved walking

# - Create lateral movement (sidestepping)

# - Maintain balance during turning manoeuvres

#

# ## Key Concepts

# 1. **In-Place Turning:** Rotating without forward motion

# 2. **Arc Walking:** Combining forward motion with rotation

# 3. **Sidestepping:** Lateral movement perpendicular to forward direction

# 4. **Turn Radius:** Relationship between forward speed and angular velocity

  

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

    from controller import Robot, Motor, InertialUnit

    WEBOTS_AVAILABLE = True

except ImportError:

    WEBOTS_AVAILABLE = False

    print("Webots not available - using simulation mode")

  

# %% [markdown]

# ---

# ## Task 2.1: Understanding Turning Parameters

#

# Define the key parameters that control turning behaviour.

  

# %%

class TurningParameters:

    """Parameters that define turning behaviour."""

    def __init__(self):

        # Rotation parameters

        self.max_angular_velocity = ...  # TODO: Maximum turn rate (rad/s) - try 0.5 rad/s

        self.min_turn_radius = ...  # TODO: Minimum radius for arc walking (m) - try 0.3m

        # Step parameters for turning

        self.turn_step_length = ...  # TODO: Step length during turning (m) - try 0.03m

        self.turn_step_height = ...  # TODO: Foot lift height during turning (m) - try 0.02m

        self.turn_step_frequency = ...  # TODO: Steps per second during turning - try 0.8 Hz

        # Sidestep parameters

        self.sidestep_distance = ...  # TODO: Lateral step distance (m) - try 0.04m

        self.sidestep_height = ...  # TODO: Foot lift height for sidestep (m) - try 0.03m

        self.sidestep_frequency = ...  # TODO: Sidesteps per second - try 0.6 Hz

        # Body parameters during turning

        self.hip_roll_lean = ...  # TODO: Lateral lean during turning (rad) - try 0.05 rad

        self.yaw_offset = ...  # TODO: Body yaw during turning (rad) - try 0.0 initially

    def calculate_turn_cycle_time(self):

        """Calculate time for one complete turn cycle."""

        return ...  # TODO: Calculate from turn_step_frequency

    def calculate_arc_radius(self, forward_speed: float, angular_velocity: float) -> float:

        """

        Calculate radius of arc for given forward speed and angular velocity.

        Args:

            forward_speed: Forward velocity (m/s)

            angular_velocity: Rotation rate (rad/s)

        Returns:

            Turn radius (m)

        """

        if angular_velocity == 0:

            return float('inf')  # Straight line

        return ...  # TODO: Calculate radius = forward_speed / angular_velocity

  

# Test your implementation

params = TurningParameters()

print(f"Turn cycle time: {params.calculate_turn_cycle_time():.3f} seconds")

print(f"Arc radius at 0.1 m/s, 0.2 rad/s: {params.calculate_arc_radius(0.1, 0.2):.3f} m")

  

# %% [markdown]

# ---

# ## Task 2.2: In-Place Turning Trajectory

#

# Generate foot trajectories for rotating in place without forward motion.

  

# %%

def generate_turn_in_place_trajectory(t: float, cycle_time: float, angular_step: float,

                                      step_height: float, is_left_foot: bool) -> Tuple[float, float, float, float]:

    """

    Generate foot trajectory for in-place turning.

    Args:

        t: Current time in cycle (0 to cycle_time)

        cycle_time: Total time for one turn cycle

        angular_step: Rotation angle per step (radians)

        step_height: Maximum height foot lifts

        is_left_foot: True for left foot, False for right foot

    Returns:

        (x, y, z, yaw): Foot position and orientation relative to starting point

    """

    # Normalise time to 0-1 range

    phase = ...  # TODO: Calculate phase = t / cycle_time

    # For in-place turning, feet stay roughly in same position

    # But we rotate the body by shifting weight and pivoting

    # X and Y stay near zero (no forward/lateral motion)

    x = 0.0

    y = 0.0

    # Z trajectory (vertical) - lift foot during turn

    z = ...  # TODO: Calculate height using parabolic function

    # Hint: z = 4 * step_height * phase * (1 - phase)

    # Yaw (rotation) - accumulate rotation during stance phase

    if phase < 0.5:

        # Foot on ground, rotate body

        yaw = ...  # TODO: Calculate rotation (angular_step * phase * 2)

    else:

        # Foot in air, maintain rotation

        yaw = angular_step

    # Adjust sign based on which foot

    if not is_left_foot:

        yaw = -yaw  # Right foot rotates opposite direction

    return x, y, z, yaw

  

# Visualise the turning trajectory

params = TurningParameters()

cycle_time = params.calculate_turn_cycle_time()

angular_step = 0.2  # 0.2 radians per step (~11 degrees)

time_points = np.linspace(0, cycle_time, 100)

  

trajectories = [generate_turn_in_place_trajectory(t, cycle_time, angular_step,

                                                   params.turn_step_height, True)

                for t in time_points]

  

z_traj = [pos[2] for pos in trajectories]

yaw_traj = [pos[3] for pos in trajectories]

  

plt.figure(figsize=(10, 4))

plt.subplot(1, 2, 1)

plt.plot(time_points, z_traj, 'b-', linewidth=2)

plt.xlabel('Time (s)')

plt.ylabel('Height (m)')

plt.title('Vertical Trajectory During Turn')

plt.grid(True)

  

plt.subplot(1, 2, 2)

plt.plot(time_points, np.degrees(yaw_traj), 'r-', linewidth=2)

plt.xlabel('Time (s)')

plt.ylabel('Rotation (degrees)')

plt.title('Body Rotation During Turn')

plt.grid(True)

  

plt.tight_layout()

plt.show()

  

# %% [markdown]

# ---

# ## Task 2.3: Arc Walking Trajectory

#

# Generate trajectories for walking in a curved path (combining forward motion and rotation).

  

# %%

def generate_arc_walking_trajectory(t: float, cycle_time: float, forward_speed: float,

                                   turn_radius: float, step_height: float,

                                   is_left_foot: bool) -> Tuple[float, float, float]:

    """

    Generate foot trajectory for walking in an arc.

    Args:

        t: Current time in cycle

        cycle_time: Total time for one cycle

        forward_speed: Forward velocity (m/s)

        turn_radius: Radius of turn (m)

        step_height: Maximum height foot lifts

        is_left_foot: True for left foot, False for right foot

    Returns:

        (x, y, z): Foot position relative to starting point

    """

    # Normalise time

    phase = ...  # TODO: Calculate phase = t / cycle_time

    # Calculate arc parameters

    arc_length = ...  # TODO: Distance travelled in one step (forward_speed * cycle_time)

    angular_displacement = ...  # TODO: Angle turned in one step (arc_length / turn_radius)

    # For arc walking, inside foot has shorter path, outside foot has longer path

    # Left foot is inside when turning left (positive angular velocity)

    if is_left_foot:

        # Inside foot - shorter radius

        foot_radius = turn_radius - 0.05  # 5cm inside

    else:

        # Outside foot - longer radius

        foot_radius = turn_radius + 0.05  # 5cm outside

    # Calculate position along arc

    angle = ...  # TODO: Calculate angle = angular_displacement * phase

    # X and Y follow circular arc

    x = ...  # TODO: Calculate x = foot_radius * np.sin(angle)

    y = ...  # TODO: Calculate y = foot_radius * (1 - np.cos(angle))

    # Z trajectory (vertical) - lift foot during swing

    z = ...  # TODO: Calculate height using parabolic function

    return x, y, z

  

# Visualise arc walking trajectory

forward_speed = 0.1  # m/s

turn_radius = 0.5  # m

time_points = np.linspace(0, cycle_time, 100)

  

left_trajectories = [generate_arc_walking_trajectory(t, cycle_time, forward_speed,

                                                     turn_radius, params.turn_step_height, True)

                     for t in time_points]

right_trajectories = [generate_arc_walking_trajectory(t, cycle_time, forward_speed,

                                                      turn_radius, params.turn_step_height, False)

                      for t in time_points]

  

left_x = [pos[0] for pos in left_trajectories]

left_y = [pos[1] for pos in left_trajectories]

right_x = [pos[0] for pos in right_trajectories]

right_y = [pos[1] for pos in right_trajectories]

  

plt.figure(figsize=(8, 8))

plt.plot(left_y, left_x, 'b-', linewidth=2, label='Left Foot (Inside)')

plt.plot(right_y, right_x, 'r-', linewidth=2, label='Right Foot (Outside)')

plt.xlabel('Lateral Position (m)')

plt.ylabel('Forward Position (m)')

plt.title('Arc Walking Trajectories')

plt.legend()

plt.grid(True)

plt.axis('equal')

plt.show()

  

# %% [markdown]

# ---

# ## Task 2.4: Sidestep Trajectory

#

# Generate trajectories for lateral movement (sidestepping).

  

# %%

def generate_sidestep_trajectory(t: float, cycle_time: float, sidestep_distance: float,

                                step_height: float, direction: float) -> Tuple[float, float, float]:

    """

    Generate foot trajectory for sidestepping.

    Args:

        t: Current time in cycle

        cycle_time: Total time for one cycle

        sidestep_distance: Lateral distance to move (m)

        step_height: Maximum height foot lifts

        direction: +1.0 for left, -1.0 for right

    Returns:

        (x, y, z): Foot position relative to starting point

    """

    # Normalise time

    phase = ...  # TODO: Calculate phase = t / cycle_time

    # X trajectory (forward) - stay in place

    x = 0.0

    # Y trajectory (lateral) - move sideways

    y = ...  # TODO: Calculate lateral position (sidestep_distance * phase * direction)

    # Z trajectory (vertical) - lift foot

    z = ...  # TODO: Calculate height using parabolic function

    return x, y, z

  

# Visualise sidestep trajectory

sidestep_distance = 0.04  # m

direction = 1.0  # Left

time_points = np.linspace(0, cycle_time, 100)

  

trajectories = [generate_sidestep_trajectory(t, cycle_time, sidestep_distance,

                                            params.sidestep_height, direction)

                for t in time_points]

  

y_traj = [pos[1] for pos in trajectories]

z_traj = [pos[2] for pos in trajectories]

  

plt.figure(figsize=(10, 4))

plt.subplot(1, 2, 1)

plt.plot(time_points, y_traj, 'g-', linewidth=2)

plt.xlabel('Time (s)')

plt.ylabel('Lateral Position (m)')

plt.title('Lateral Movement')

plt.grid(True)

  

plt.subplot(1, 2, 2)

plt.plot(time_points, z_traj, 'b-', linewidth=2)

plt.xlabel('Time (s)')

plt.ylabel('Height (m)')

plt.title('Vertical Movement')

plt.grid(True)

  

plt.tight_layout()

plt.show()

  

# %% [markdown]

# ---

# ## Task 2.5: Complete Turning Controller Class

#

# Integrate all turning components into the final `TurningController` class.

  

# %%

from enum import Enum

  

class TurnMode(Enum):

    """Different turning modes."""

    IN_PLACE = 0      # Rotate without forward motion

    ARC_WALK = 1      # Walk in curved path

    SIDESTEP = 2      # Lateral movement

    STOPPED = 3       # Not turning

  

class TurningController:

    """

    Complete turning controller for NAO6 robot.

    Provides high-level turning commands that generate appropriate

    joint trajectories for rotational and lateral motion.

    """

    def __init__(self, robot=None):

        """

        Initialise turning controller.

        Args:

            robot: Webots Robot instance (optional)

        """

        self.robot = robot

        self.params = TurningParameters()

        # Motor references

        self.motors = {}

        # Current state

        self.turn_mode = TurnMode.STOPPED

        self.target_angular_velocity = 0.0

        self.target_forward_speed = 0.0

        self.sidestep_direction = 0.0

        # Timing

        self.phase_time = 0.0

        self.cycle_count = 0

        if robot:

            self._initialise_motors()

    def _initialise_motors(self):

        """Get motor references from robot."""

        leg_joints = [

            'LHipPitch', 'LKneePitch', 'LAnklePitch', 'LHipRoll', 'LHipYawPitch',

            'RHipPitch', 'RKneePitch', 'RAnklePitch', 'RHipRoll'

        ]

        for joint_name in leg_joints:

            motor = ...  # TODO: Get motor from robot using self.robot.getDevice(joint_name)

            if motor:

                self.motors[joint_name] = motor

    def turn_in_place(self, angular_velocity: float) -> Dict[str, float]:

        """

        Rotate in place without forward motion.

        Args:

            angular_velocity: Rotation rate in rad/s (positive = left, negative = right)

        Returns:

            Dictionary of joint names and target positions

        """

        # Clamp angular velocity to safe range

        max_vel = self.params.max_angular_velocity

        angular_velocity = ...  # TODO: Clamp between -max_vel and +max_vel

        # Update state

        self.turn_mode = TurnMode.IN_PLACE

        self.target_angular_velocity = angular_velocity

        self.target_forward_speed = 0.0

        # Generate joint positions

        return self._generate_turn_joint_positions()

    def arc_walk(self, forward_speed: float, turn_radius: float) -> Dict[str, float]:

        """

        Walk in an arc (combine forward motion with turning).

        Args:

            forward_speed: Forward velocity in m/s (0.0 to 0.2)

            turn_radius: Radius of turn in m (positive = left, negative = right)

        Returns:

            Dictionary of joint names and target positions

        """

        # Clamp forward speed

        forward_speed = ...  # TODO: Clamp between 0.0 and 0.2

        # Clamp turn radius

        min_radius = self.params.min_turn_radius

        if abs(turn_radius) < min_radius:

            turn_radius = min_radius if turn_radius > 0 else -min_radius

        # Calculate angular velocity from radius and speed

        angular_velocity = ...  # TODO: Calculate angular_velocity = forward_speed / turn_radius

        # Update state

        self.turn_mode = TurnMode.ARC_WALK

        self.target_forward_speed = forward_speed

        self.target_angular_velocity = angular_velocity

        # Generate joint positions

        return self._generate_arc_joint_positions()

    def side_step(self, speed: float, direction: float) -> Dict[str, float]:

        """

        Lateral movement (crab walk).

        Args:

            speed: Lateral velocity in m/s (0.0 to 0.1)

            direction: +1.0 for left, -1.0 for right

        Returns:

            Dictionary of joint names and target positions

        """

        # Clamp speed

        speed = ...  # TODO: Clamp between 0.0 and 0.1

        # Normalise direction

        direction = ...  # TODO: Set to +1.0 if direction > 0 else -1.0

        # Update state

        self.turn_mode = TurnMode.SIDESTEP

        self.sidestep_direction = direction

        self.target_forward_speed = speed

        # Generate joint positions

        return self._generate_sidestep_joint_positions()

    def stop(self) -> Dict[str, float]:

        """

        Stop turning and return to standing position.

        Returns:

            Dictionary of joint names and target positions for standing

        """

        self.turn_mode = TurnMode.STOPPED

        self.target_angular_velocity = 0.0

        self.target_forward_speed = 0.0

        # Return standing pose

        standing_pose = {

            'LHipPitch': -0.3,

            'LKneePitch': 0.6,

            'LAnklePitch': -0.3,

            'LHipRoll': 0.0,

            'RHipPitch': -0.3,

            'RKneePitch': 0.6,

            'RAnklePitch': -0.3,

            'RHipRoll': 0.0,

        }

        return standing_pose

    def _generate_turn_joint_positions(self) -> Dict[str, float]:

        """

        Generate joint positions for in-place turning.

        Returns:

            Dictionary of joint names and target positions

        """

        # Calculate angular step based on target velocity

        cycle_time = self.params.calculate_turn_cycle_time()

        angular_step = ...  # TODO: Calculate angular_step = target_angular_velocity * cycle_time

        # Get current phase

        phase = ...  # TODO: Calculate phase = phase_time / cycle_time

        # Generate trajectories for both feet

        left_x, left_y, left_z, left_yaw = generate_turn_in_place_trajectory(

            self.phase_time, cycle_time, angular_step, self.params.turn_step_height, True)

        right_x, right_y, right_z, right_yaw = generate_turn_in_place_trajectory(

            self.phase_time, cycle_time, angular_step, self.params.turn_step_height, False)

        # Convert to joint angles (simplified - use IK from Task 1)

        # For now, return basic turning pose

        joints = {

            'LHipPitch': -0.3,

            'LKneePitch': 0.6,

            'LAnklePitch': -0.3,

            'LHipRoll': ...  # TODO: Add lateral lean based on turn direction

            'RHipPitch': -0.3,

            'RKneePitch': 0.6,

            'RAnklePitch': -0.3,

            'RHipRoll': ...  # TODO: Add lateral lean (opposite of left)

        }

        return joints

    def _generate_arc_joint_positions(self) -> Dict[str, float]:

        """

        Generate joint positions for arc walking.

        Returns:

            Dictionary of joint names and target positions

        """

        # Calculate turn radius from angular velocity and forward speed

        if self.target_angular_velocity != 0:

            turn_radius = ...  # TODO: Calculate radius = forward_speed / angular_velocity

        else:

            turn_radius = float('inf')

        # Generate trajectories

        cycle_time = self.params.calculate_turn_cycle_time()

        left_x, left_y, left_z = generate_arc_walking_trajectory(

            self.phase_time, cycle_time, self.target_forward_speed,

            turn_radius, self.params.turn_step_height, True)

        right_x, right_y, right_z = generate_arc_walking_trajectory(

            self.phase_time, cycle_time, self.target_forward_speed,

            turn_radius, self.params.turn_step_height, False)

        # Convert to joint angles using IK

        # TODO: Implement full IK conversion

        # For now, return basic pose

        joints = {

            'LHipPitch': -0.3,

            'LKneePitch': 0.6,

            'LAnklePitch': -0.3,

            'LHipRoll': 0.0,

            'RHipPitch': -0.3,

            'RKneePitch': 0.6,

            'RAnklePitch': -0.3,

            'RHipRoll': 0.0,

        }

        return joints

    def _generate_sidestep_joint_positions(self) -> Dict[str, float]:

        """

        Generate joint positions for sidestepping.

        Returns:

            Dictionary of joint names and target positions

        """

        cycle_time = self.params.calculate_turn_cycle_time()

        sidestep_distance = self.params.sidestep_distance

        # Generate trajectory

        x, y, z = generate_sidestep_trajectory(

            self.phase_time, cycle_time, sidestep_distance,

            self.params.sidestep_height, self.sidestep_direction)

        # Convert to joint angles

        # TODO: Implement full IK conversion

        # For now, return basic pose with hip roll for lateral movement

        joints = {

            'LHipPitch': -0.3,

            'LKneePitch': 0.6,

            'LAnklePitch': -0.3,

            'LHipRoll': ...  # TODO: Add roll based on sidestep direction

            'RHipPitch': -0.3,

            'RKneePitch': 0.6,

            'RAnklePitch': -0.3,

            'RHipRoll': ...  # TODO: Add roll (opposite of left)

        }

        return joints

    def update(self, dt: float) -> Dict[str, float]:

        """

        Update controller state and generate new joint positions.

        Args:

            dt: Time step (seconds)

        Returns:

            Dictionary of joint names and target positions

        """

        if self.turn_mode == TurnMode.STOPPED:

            return self.stop()

        # Update phase time

        self.phase_time += dt

        # Check if cycle complete

        cycle_time = self.params.calculate_turn_cycle_time()

        if self.phase_time >= cycle_time:

            self.phase_time = 0.0

            self.cycle_count += 1

        # Generate positions based on mode

        if self.turn_mode == TurnMode.IN_PLACE:

            return self._generate_turn_joint_positions()

        elif self.turn_mode == TurnMode.ARC_WALK:

            return self._generate_arc_joint_positions()

        elif self.turn_mode == TurnMode.SIDESTEP:

            return self._generate_sidestep_joint_positions()

        else:

            return self.stop()

  

# Test the complete controller

controller = TurningController()

print("Turning Controller initialised successfully!")

  

# Test in-place turning

joints = controller.turn_in_place(0.3)

print("\nJoint positions for in-place turning at 0.3 rad/s:")

for joint, angle in joints.items():

    print(f"  {joint}: {angle:.3f}")

  

# %% [markdown]

# ---

# ## Task 2.6: Performance Analysis

#

# Analyse the turning controller's performance across different parameters.

  

# %%

# Test different turning speeds

test_angular_velocities = [0.1, 0.2, 0.3, 0.4, 0.5]  # rad/s

results = []

  

for ang_vel in test_angular_velocities:

    controller = TurningController()

    controller.turn_in_place(ang_vel)

    cycle_time = controller.params.calculate_turn_cycle_time()

    angular_step = ang_vel * cycle_time

    # Estimate time to turn 90 degrees

    time_for_90_deg = ...  # TODO: Calculate (π/2) / ang_vel

    result = {

        'angular_velocity': ang_vel,

        'angular_step': angular_step,

        'time_for_90deg': time_for_90_deg,

    }

    results.append(result)

  

# Plot results

ang_vels = [r['angular_velocity'] for r in results]

times_90 = [r['time_for_90deg'] for r in results]

  

plt.figure(figsize=(8, 5))

plt.plot(np.degrees(ang_vels), times_90, 'bo-', linewidth=2, markersize=8)

plt.xlabel('Angular Velocity (deg/s)')

plt.ylabel('Time to Turn 90° (s)')

plt.title('Turning Performance')

plt.grid(True)

plt.show()

  

print("\nTurning Performance Summary:")

for r in results:

    print(f"Angular Velocity: {np.degrees(r['angular_velocity']):.1f}°/s | "

          f"Time for 90°: {r['time_for_90deg']:.2f}s")

  

# %% [markdown]

# ---

# ## Deliverables Checklist

#

# Before submitting, ensure you have completed:

#

# - [ ] **Task 2.1:** Turning parameters defined and tested

# - [ ] **Task 2.2:** In-place turning trajectory working

# - [ ] **Task 2.3:** Arc walking trajectory implemented

# - [ ] **Task 2.4:** Sidestep trajectory implemented

# - [ ] **Task 2.5:** Complete `TurningController` class implemented

# - [ ] **Task 2.6:** Performance analysis completed

# - [ ] **Code Quality:** All functions documented with docstrings

# - [ ] **Testing:** Controller tested at multiple angular velocities

# - [ ] **Constraints:** All joint angles respect `NAO6Constraints` limits

# - [ ] **Webots Test:** Robot turns smoothly without falling

#

# ## Next Steps

#

# After completing this task:

# 1. Save the `TurningController` class to `src/wp3_guidance_control/turning_controller.py`

# 2. Test in Webots simulation

# 3. Integrate with `WalkingController` for combined motion

# 4. Update development log with progress