# sidestepping_controller.py
# lateral movement for the NAO6 robot.
# includes foot trajectory generation, weight shifting, body lean control for stable sideways motion.

import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, Tuple, List
import sys
import os

# project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))


from controller import Robot, Motor, InertialUnit

try:
    from src.wp3_guidance_control.robot_constraints import NAO6Constraints
    # hip width estimate
    HIP_WIDTH = NAO6Constraints.WIDTH / 3.0  
except (ImportError, AttributeError):
    # Use default value if constraints not available
    HIP_WIDTH = 0.10  # meters
    print(f"Using default NAO6 hip width: {HIP_WIDTH:.3f}m")

# PARAMETER CLASS


class SidestepParameters:
    """
    Parameters that define sidestepping behaviour.
    These have been tuned for stable NAO6 sidestepping.
    """
    
    def __init__(self):
        # Basic Step Parameters
        self.step_distance = 0.04      # Lateral distance per step (m)
        self.step_height = 0.03        # How high to lift foot (m)
        self.step_frequency = 0.6       # Steps per second (Hz)
        
        # Body Lean Parameters
        self.hip_roll_lean = 0.08      # Hip roll angle during step (rad)
        self.ankle_roll_compensation = 0.05  # Ankle roll to keep foot flat (rad)
        
        # Phase Timing (fractions of cycle)
        self.weight_shift_ratio = 0.3  # 30% of cycle for weight shift
        self.swing_ratio = 0.4          # 40% of cycle for swing
        # Landing takes the remaining 30%
        
        # Safety Limits
        self.max_speed = self.step_distance * self.step_frequency  # 0.024 m/s
        self.max_lean_angle = 0.15     # Maximum safe lean (rad)
    
    def calculate_cycle_time(self) -> float:
        """Calculate time for one complete sidestep cycle."""
        return 1.0 / self.step_frequency
    
    def get_phase_times(self) -> Dict[str, Tuple[float, float]]:
        """
        Calculate start and end times for each phase.
        
        Returns:
            Dictionary with phase names and (start_time, end_time) tuples
        """
        cycle_time = self.calculate_cycle_time()
        
        weight_shift_end = self.weight_shift_ratio * cycle_time
        swing_end = weight_shift_end + self.swing_ratio * cycle_time
        
        phases = {
            'weight_shift': (0.0, weight_shift_end),
            'swing': (weight_shift_end, swing_end),
            'landing': (swing_end, cycle_time),
        }
        
        return phases
    
    def validate_parameters(self) -> bool:
        """Check if parameters are within safe ranges."""
        issues = []
        
        if self.step_distance > 0.06:
            issues.append("Step distance too large (>0.06m)")
        if self.step_distance < 0.02:
            issues.append("Step distance too small (<0.02m)")
        if self.step_height > 0.05:
            issues.append("Step height too large (>0.05m)")
        if self.step_frequency > 1.0:
            issues.append("Step frequency too fast (>1.0 Hz)")
        if self.hip_roll_lean > self.max_lean_angle:
            issues.append("Hip roll lean exceeds max lean angle")
        if self.weight_shift_ratio + self.swing_ratio > 0.9:
            issues.append("Not enough time for landing phase")
        
        if issues:
            print("Parameter validation issues:")
            for issue in issues:
                print(f"  - {issue}")
            return False
        
        return True


# TRAJECTORY GENERATION


def generate_sidestep_trajectory(t: float, params: SidestepParameters, 
                                direction: float) -> Tuple[float, float, float]:
    """
    Generate foot trajectory for sidestepping.
    
    Args:
        t: Current time in cycle (0 to cycle_time)
        params: Sidestepping parameters
        direction: +1.0 for left, -1.0 for right
    
    Returns:
        (x, y, z): Foot position in meters relative to starting point
    """
    cycle_time = params.calculate_cycle_time()
    phases = params.get_phase_times()
    
    # Normalize time to phase (0.0 to 1.0)
    phase = t / cycle_time
    
    # Clamp phase to [0, 1] to handle edge cases
    phase = max(0.0, min(1.0, phase))
    
    # X Trajectory (no forward/back motion for pure sidestepping)
    x = 0.0
    
    # Get phase boundaries
    weight_shift_end = phases['weight_shift'][1] / cycle_time
    swing_end = phases['swing'][1] / cycle_time
    
    # Y Trajectory (Lateral)
    if phase < weight_shift_end:
        # Weight shift phase - foot hasn't moved yet
        y = 0.0
    elif phase < swing_end:
        # Swing phase - foot is moving
        swing_phase = (phase - weight_shift_end) / (swing_end - weight_shift_end)
        # Smooth sinusoidal trajectory
        y = params.step_distance * (1 - np.cos(np.pi * swing_phase)) / 2 * direction
    else:
        # Landing phase - foot is at final position
        y = params.step_distance * direction
    
    # Z Trajectory (Vertical)
    if phase < weight_shift_end:
        # Weight shift - foot on ground
        z = 0.0
    elif phase < swing_end:
        # Swing phase - parabolic lift
        swing_phase = (phase - weight_shift_end) / (swing_end - weight_shift_end)
        z = 4 * params.step_height * swing_phase * (1 - swing_phase)
    else:
        # Landing phase - descending to ground
        landing_phase = (phase - swing_end) / (1.0 - swing_end)
        # Smooth descent using cosine
        z = params.step_height * (1 + np.cos(np.pi * landing_phase)) / 2
    
    return x, y, z

# BODY LEAN CALCULATION

def calculate_body_lean(t: float, params: SidestepParameters, 
                       direction: float, support_foot: str) -> Dict[str, float]:
    """
    Calculate hip and ankle roll angles for balance during sidestep.
    
    Args:
        t: Current time in cycle
        params: Sidestepping parameters
        direction: +1.0 for left, -1.0 for right
        support_foot: 'left' or 'right' - which foot is on ground
    
    Returns:
        Dictionary with 'hip_roll' and 'ankle_roll' angles (rad)
    """
    cycle_time = params.calculate_cycle_time()
    phases = params.get_phase_times()
    phase = t / cycle_time
    phase = max(0.0, min(1.0, phase))  # Clamp to [0, 1]
    
    weight_shift_end = phases['weight_shift'][1] / cycle_time
    swing_end = phases['swing'][1] / cycle_time
    
    # Hip Roll Angle
    if phase < weight_shift_end:
        # Weight shift - gradually increase lean
        shift_phase = phase / weight_shift_end
        # Use smooth transition (sin curve)
        lean_amount = np.sin(shift_phase * np.pi / 2)  # 0 to 1 smoothly
        hip_roll = params.hip_roll_lean * lean_amount * (-direction)
    elif phase < swing_end:
        # Swing phase - maintain maximum lean
        hip_roll = -params.hip_roll_lean * direction
    else:
        # Landing phase - reduce lean back to neutral
        landing_phase = (phase - swing_end) / (1.0 - swing_end)
        # Smooth return using cosine
        lean_amount = (1 + np.cos(np.pi * landing_phase)) / 2  # 1 to 0 smoothly
        hip_roll = -params.hip_roll_lean * direction * lean_amount
    
    # Ankle Roll Compensation (opposite to hip roll to keep foot flat)
    ankle_roll = -hip_roll * (params.ankle_roll_compensation / params.hip_roll_lean)
    
    return {
        'hip_roll': hip_roll,
        'ankle_roll': ankle_roll
    }

# MAIN CONTROLLER CLASS


class SidesteppingController:
    """
    Complete sidestepping controller for NAO6 robot.
    
    This controller handles lateral movement by:
    1. Generating foot trajectories
    2. Calculating body lean for balance
    3. Converting to joint angles
    4. Coordinating left/right steps
    """
    
    def __init__(self, robot=None):
        """
        Initialise sidestepping controller.
        
        Args:
            robot: Webots Robot instance (optional)
        """
        self.robot = robot
        self.params = SidestepParameters()
        
        # Validate parameters on initialization
        if not self.params.validate_parameters():
            print("Warning: Parameters may not be safe!")
        
        # Motor references (will be populated if robot is provided)
        self.motors = {}
        
        # State variables
        self.is_active = False
        self.phase_time = 0.0
        self.step_count = 0
        self.current_direction = 0.0  # +1 = left, -1 = right
        self.support_foot = 'left'    # Which foot is currently supporting
        
        if robot:
            self._initialize_motors()
    
    def _initialize_motors(self):
        """Get motor references from Webots robot."""
        leg_joints = [
            'LHipPitch', 'RHipPitch',
            'LKneePitch', 'RKneePitch',
            'LAnklePitch', 'RAnklePitch',
            'LHipRoll', 'RHipRoll',
            'LAnkleRoll', 'RAnkleRoll',
        ]
        
        for joint_name in leg_joints:
            motor = self.robot.getDevice(joint_name)
            if motor:
                self.motors[joint_name] = motor
            else:
                print(f"Warning: Could not find motor {joint_name}")
    
    def start(self, direction: float):
        """
        Start sidestepping in specified direction.
        
        Args:
            direction: +1.0 for left, -1.0 for right
        """
        self.current_direction = 1.0 if direction > 0 else -1.0
        self.is_active = True
        self.phase_time = 0.0
        self.step_count = 0
        self.support_foot = 'left'  # Always start with left foot as support
        
        print(f"Starting sidestep {'left' if self.current_direction > 0 else 'right'}")
    
    def stop(self):
        """Stop sidestepping and return to neutral stance."""
        self.is_active = False
        self.phase_time = 0.0
        print("Stopping sidestep")
    
    def get_standing_pose(self) -> Dict[str, float]:
        """
        Get neutral standing pose joint angles.
        
        Returns:
            Dictionary of joint names and angles
        """
        return {
            'LHipPitch': -0.3,     # Slight forward lean
            'RHipPitch': -0.3,
            'LKneePitch': 0.6,     # Knees slightly bent
            'RKneePitch': 0.6,
            'LAnklePitch': -0.3,   # Balance knee bend
            'RAnklePitch': -0.3,
            'LHipRoll': 0.0,       # Neutral
            'RHipRoll': 0.0,
            'LAnkleRoll': 0.0,
            'RAnkleRoll': 0.0,
        }
    
    def get_joint_positions(self) -> Dict[str, float]:
        """
        Calculate current joint positions based on phase.
        
        Returns:
            Dictionary of joint names and target angles
        """
        # Determine which foot is moving (opposite of support foot)
        moving_foot = 'right' if self.support_foot == 'left' else 'left'
        
        # Get foot trajectory for moving foot
        x, y, z = generate_sidestep_trajectory(
            self.phase_time, self.params, self.current_direction
        )
        
        # Get body lean angles
        lean = calculate_body_lean(
            self.phase_time, self.params, 
            self.current_direction, self.support_foot
        )
        
        # Start with standing pose
        joints = self.get_standing_pose()
        
        # Apply hip roll for weight shift
        if self.support_foot == 'left':
            # Weight on left, lean right for left sidestep
            joints['LHipRoll'] = lean['hip_roll']
            joints['RHipRoll'] = -lean['hip_roll'] * 0.5  # Less lean on moving foot
        else:
            # Weight on right, lean left for right sidestep
            joints['LHipRoll'] = -lean['hip_roll'] * 0.5
            joints['RHipRoll'] = lean['hip_roll']
        
        # Apply ankle roll compensation
        joints['LAnkleRoll'] = lean['ankle_roll'] if self.support_foot == 'left' else lean['ankle_roll'] * 0.3
        joints['RAnkleRoll'] = lean['ankle_roll'] if self.support_foot == 'right' else lean['ankle_roll'] * 0.3
        
        # Adjust hip/knee/ankle pitch for foot height (simplified IK)
        if z > 0.001:  # Foot is lifting
            if moving_foot == 'right':
                # Right foot is lifting
                joints['RHipPitch'] = -0.3 + z * 2.0   # Lift hip
                joints['RKneePitch'] = 0.6 + z * 3.0   # Bend knee more
                joints['RAnklePitch'] = -0.3 - z * 1.0  # Point toe down slightly
            else:
                # Left foot is lifting
                joints['LHipPitch'] = -0.3 + z * 2.0
                joints['LKneePitch'] = 0.6 + z * 3.0
                joints['LAnklePitch'] = -0.3 - z * 1.0
        
        return joints
    
    def update(self, dt: float) -> Dict[str, float]:
        """
        Main update function - call this every timestep.
        
        Args:
            dt: Time step in seconds (typically 0.032s for Webots)
        
        Returns:
            Dictionary of joint positions to apply
        """
        if not self.is_active:
            return self.get_standing_pose()
        
        # Update phase time
        self.phase_time += dt
        
        cycle_time = self.params.calculate_cycle_time()
        
        # Check if we've completed a cycle
        if self.phase_time >= cycle_time:
            # Reset phase time for next cycle
            self.phase_time = self.phase_time - cycle_time  # Keep remainder for smooth transition
            
            # Increment step count
            self.step_count += 1
            
            # Alternate support foot
            if self.support_foot == 'left':
                self.support_foot = 'right'
            else:
                self.support_foot = 'left'
            
            print(f"Step {self.step_count} complete, support: {self.support_foot}")
        
        # Generate joint positions
        joints = self.get_joint_positions()
        
        # Apply to robot if available
        if self.robot:
            self._apply_joint_positions(joints)
        
        return joints
    
    def _apply_joint_positions(self, joints: Dict[str, float]):
        """Apply joint positions to robot motors."""
        for joint_name, position in joints.items():
            if joint_name in self.motors:
                self.motors[joint_name].setPosition(position)
    
    def get_state_info(self) -> Dict:
        """
        Get current controller state for debugging/visualization.
        
        Returns:
            Dictionary with state information
        """
        cycle_time = self.params.calculate_cycle_time()
        cycle_progress = (self.phase_time / cycle_time * 100) if cycle_time > 0 else 0
        
        return {
            'is_active': self.is_active,
            'phase_time': self.phase_time,
            'step_count': self.step_count,
            'support_foot': self.support_foot,
            'direction': 'left' if self.current_direction > 0 else 'right',
            'cycle_progress': cycle_progress
        }

# VISUALISATION AND ANALYSIS


def analyze_sidestep_performance(params: SidestepParameters = None, 
                                num_steps: int = 3,
                                direction: float = 1.0):
    """
    Simulate and visualize complete sidestepping sequence.
    
    Args:
        params: Sidestepping parameters (uses default if None)
        num_steps: Number of steps to simulate
        direction: +1.0 for left, -1.0 for right
    """
    if params is None:
        params = SidestepParameters()
    
    controller = SidesteppingController()
    controller.params = params
    controller.start(direction)
    
    dt = 0.032  # 32ms timestep
    total_time = params.calculate_cycle_time() * num_steps
    num_samples = int(total_time / dt)
    
    # Data collection
    times = []
    support_foot_history = []
    joint_angles = {
        'LHipRoll': [], 'RHipRoll': [],
        'LKneePitch': [], 'RKneePitch': []
    }
    
    # Simulate and collect data
    for i in range(num_samples):
        current_time = i * dt
        times.append(current_time)
        
        # Update controller
        joints = controller.update(dt)
        state = controller.get_state_info()
        
        # Collect joint angle data
        for joint_name in joint_angles.keys():
            if joint_name in joints:
                joint_angles[joint_name].append(joints[joint_name])
        
        support_foot_history.append(controller.support_foot)
    
    # Create visualization plots
    fig = plt.figure(figsize=(16, 10))
    
    # Plot 1: Joint Angles Over Time
    ax1 = plt.subplot(2, 3, 1)
    ax1.plot(times, np.degrees(joint_angles['LHipRoll']), 
             'b-', linewidth=2, label='Left Hip Roll')
    ax1.plot(times, np.degrees(joint_angles['RHipRoll']), 
             'r-', linewidth=2, label='Right Hip Roll')
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Angle (degrees)')
    ax1.set_title('Hip Roll Angles (Weight Shift)')
    ax1.legend()
    ax1.grid(True)
    
    # Plot 2: Knee Angles Over Time
    ax2 = plt.subplot(2, 3, 2)
    ax2.plot(times, np.degrees(joint_angles['LKneePitch']), 
             'b-', linewidth=2, label='Left Knee')
    ax2.plot(times, np.degrees(joint_angles['RKneePitch']), 
             'r-', linewidth=2, label='Right Knee')
    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('Angle (degrees)')
    ax2.set_title('Knee Angles (Swing/Stance)')
    ax2.legend()
    ax2.grid(True)
    
    # Plot 3: Support Foot Timeline
    ax3 = plt.subplot(2, 3, 3)
    support_binary = [1 if s == 'left' else 0 for s in support_foot_history]
    ax3.fill_between(times, 0, support_binary, alpha=0.3, color='blue', label='Left Support')
    ax3.fill_between(times, support_binary, 1, alpha=0.3, color='red', label='Right Support')
    ax3.set_xlabel('Time (s)')
    ax3.set_ylabel('Support Foot')
    ax3.set_yticks([0, 1])
    ax3.set_yticklabels(['Right', 'Left'])
    ax3.set_title('Support Foot Timeline')
    ax3.grid(True, axis='x')
    
    # Plot 4: Single Step Detail
    ax4 = plt.subplot(2, 3, 4)
    cycle_time = params.calculate_cycle_time()
    time_detail = np.linspace(0, cycle_time, 100)
    
    traj_detail = [generate_sidestep_trajectory(t, params, direction) 
                   for t in time_detail]
    y_detail = [pos[1] for pos in traj_detail]
    z_detail = [pos[2] for pos in traj_detail]
    
    ax4.plot(y_detail, z_detail, 'g-', linewidth=3)
    ax4.set_xlabel('Lateral Position (m)')
    ax4.set_ylabel('Height (m)')
    ax4.set_title('Single Step Foot Path')
    ax4.grid(True)
    ax4.axis('equal')
    ax4.axhline(y=0, color='k', linestyle='--', alpha=0.3)
    
    # Plot 5: Phase Analysis
    ax5 = plt.subplot(2, 3, 5)
    phases = params.get_phase_times()
    phase_names = list(phases.keys())
    phase_durations = [(end - start) for start, end in phases.values()]
    
    ax5.bar(phase_names, phase_durations, color=['blue', 'green', 'red'])
    ax5.set_ylabel('Duration (s)')
    ax5.set_title('Phase Duration Breakdown')
    ax5.grid(True, axis='y')
    
    # Plot 6: Performance Metrics
    ax6 = plt.subplot(2, 3, 6)
    ax6.axis('off')
    
    metrics_text = f"""
    PERFORMANCE METRICS
    ═══════════════════
    
    Step Parameters:
    • Distance: {params.step_distance:.3f} m
    • Height: {params.step_height:.3f} m
    • Frequency: {params.step_frequency:.2f} Hz
    
    Timing:
    • Cycle Time: {cycle_time:.3f} s
    • Weight Shift: {phase_durations[0]:.3f} s ({phase_durations[0]/cycle_time*100:.1f}%)
    • Swing: {phase_durations[1]:.3f} s ({phase_durations[1]/cycle_time*100:.1f}%)
    • Landing: {phase_durations[2]:.3f} s ({phase_durations[2]/cycle_time*100:.1f}%)
    
    Performance:
    • Lateral Speed: {params.max_speed:.4f} m/s
    • Steps Simulated: {num_steps}
    • Total Distance: {params.step_distance * num_steps:.3f} m
    • Total Time: {total_time:.2f} s
    
    Safety:
    • Max Hip Roll: {np.degrees(params.hip_roll_lean):.2f}°
    • Max Lean Angle: {np.degrees(params.max_lean_angle):.2f}°
    """
    
    ax6.text(0.1, 0.95, metrics_text, transform=ax6.transAxes,
             fontsize=10, verticalalignment='top', fontfamily='monospace',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    plt.show()
    
    return {
        'times': times,
        'joint_angles': joint_angles,
        'support_history': support_foot_history,
    }


def compare_parameters():
    """Compare different parameter sets to find optimal configuration."""
    param_sets = {
        'conservative': {
            'step_distance': 0.03,
            'step_height': 0.025,
            'step_frequency': 0.5,
        },
        'moderate': {
            'step_distance': 0.04,
            'step_height': 0.03,
            'step_frequency': 0.6,
        },
        'aggressive': {
            'step_distance': 0.05,
            'step_height': 0.035,
            'step_frequency': 0.8,
        },
    }
    
    results = {}
    
    plt.figure(figsize=(15, 5))
    
    for i, (name, param_dict) in enumerate(param_sets.items()):
        params = SidestepParameters()
        
        # Apply parameters from param_dict
        params.step_distance = param_dict['step_distance']
        params.step_height = param_dict['step_height']
        params.step_frequency = param_dict['step_frequency']
        params.max_speed = params.step_distance * params.step_frequency
        
        # Generate trajectory
        cycle_time = params.calculate_cycle_time()
        time_points = np.linspace(0, cycle_time, 100)
        
        trajectories = [generate_sidestep_trajectory(t, params, 1.0) 
                       for t in time_points]
        
        y_traj = [pos[1] for pos in trajectories]
        z_traj = [pos[2] for pos in trajectories]
        
        # Plot
        plt.subplot(1, 3, i + 1)
        plt.plot(y_traj, z_traj, linewidth=3)
        plt.xlabel('Lateral (m)')
        plt.ylabel('Height (m)')
        plt.title(f'{name.capitalize()}\n'
                 f'{param_dict["step_distance"]*1000:.0f}mm @ '
                 f'{param_dict["step_frequency"]:.1f}Hz')
        plt.grid(True)
        plt.axis('equal')
        plt.axhline(y=0, color='k', linestyle='--', alpha=0.3)
        
        # Calculate metrics
        results[name] = {
            'speed': param_dict['step_distance'] * param_dict['step_frequency'],
            'cycle_time': cycle_time,
            'max_height': max(z_traj),
        }
    
    plt.tight_layout()
    plt.show()
    
    # Print comparison
    print("\n=== Parameter Comparison ===")
    print(f"{'Strategy':<15} {'Speed (m/s)':<12} {'Cycle Time (s)':<15} {'Max Height (m)':<15}")
    print("=" * 60)
    for name, metrics in results.items():
        print(f"{name.capitalize():<15} "
              f"{metrics['speed']:<12.4f} "
              f"{metrics['cycle_time']:<15.3f} "
              f"{metrics['max_height']:<15.4f}")
    
    return results

# MAIN EXECUTION AND TESTING

if __name__ == "__main__":
    print("=" * 70)
    print("SIDESTEPPING CONTROLLER - Complete Implementation")
    print("=" * 70)
    
    # Test parameters
    print("\n=== Testing Parameters ===")
    params = SidestepParameters()
    print(f"Step distance: {params.step_distance:.3f} m")
    print(f"Step height: {params.step_height:.3f} m")
    print(f"Step frequency: {params.step_frequency:.2f} Hz")
    print(f"Cycle time: {params.calculate_cycle_time():.3f} s")
    print(f"Max speed: {params.max_speed:.3f} m/s")
    
    phases = params.get_phase_times()
    print(f"\nPhase timing:")
    for phase_name, (start, end) in phases.items():
        print(f"  {phase_name}: {start:.3f}s - {end:.3f}s ({(end-start):.3f}s duration)")
    
    if params.validate_parameters():
        print("\n✓ Parameters validated successfully")
    
    # Test controller
    print("\n=== Testing Controller ===")
    controller = SidesteppingController()
    controller.start(direction=1.0)
    
    print("\nSimulating 3 steps:")
    dt = 0.032  # 32ms timestep
    total_time = controller.params.calculate_cycle_time() * 3
    
    for step_num in range(int(total_time / dt)):
        joints = controller.update(dt)
        state = controller.get_state_info()
        
        # Print every 0.5 seconds
        if step_num % 15 == 0:
            print(f"Time: {step_num * dt:.2f}s | "
                  f"Step: {state['step_count']} | "
                  f"Support: {state['support_foot']} | "
                  f"Progress: {state['cycle_progress']:.1f}%")
    
    controller.stop()
    
    # Visualize trajectories
    print("\n=== Generating Trajectory Visualizations ===")
    
    # Single step trajectory
    plt.figure(figsize=(15, 4))
    cycle_time = params.calculate_cycle_time()
    time_points = np.linspace(0, cycle_time, 100)
    direction = 1.0  # Step to the left
    
    trajectories = [generate_sidestep_trajectory(t, params, direction) 
                    for t in time_points]
    
    x_traj = [pos[0] for pos in trajectories]
    y_traj = [pos[1] for pos in trajectories]
    z_traj = [pos[2] for pos in trajectories]
    
    plt.subplot(1, 3, 1)
    plt.plot(time_points, y_traj, 'g-', linewidth=2)
    plt.xlabel('Time (s)')
    plt.ylabel('Lateral Position (m)')
    plt.title('Y Trajectory (Sideways Motion)')
    plt.grid(True)
    plt.axhline(y=0, color='k', linestyle='--', alpha=0.3)
    
    plt.subplot(1, 3, 2)
    plt.plot(time_points, z_traj, 'b-', linewidth=2)
    plt.xlabel('Time (s)')
    plt.ylabel('Height (m)')
    plt.title('Z Trajectory (Vertical Motion)')
    plt.grid(True)
    plt.axhline(y=0, color='k', linestyle='--', alpha=0.3)
    
    plt.subplot(1, 3, 3)
    plt.plot(y_traj, z_traj, 'r-', linewidth=2)
    plt.xlabel('Lateral Position (m)')
    plt.ylabel('Height (m)')
    plt.title('Foot Path (Side View)')
    plt.grid(True)
    plt.axhline(y=0, color='k', linestyle='--', alpha=0.3)
    plt.axis('equal')
    
    plt.tight_layout()
    plt.show()
    
    print(f"Max lateral position: {max(y_traj):.4f} m")
    print(f"Max height: {max(z_traj):.4f} m")
    
    # Body lean visualization
    print("\n=== Body Lean Analysis ===")
    lean_data = [calculate_body_lean(t, params, direction, 'left') 
                 for t in time_points]
    
    hip_rolls = [data['hip_roll'] for data in lean_data]
    ankle_rolls = [data['ankle_roll'] for data in lean_data]
    
    plt.figure(figsize=(12, 5))
    
    plt.subplot(1, 2, 1)
    plt.plot(time_points, np.degrees(hip_rolls), 'b-', linewidth=2, label='Hip Roll')
    plt.plot(time_points, np.degrees(ankle_rolls), 'r-', linewidth=2, label='Ankle Roll')
    plt.xlabel('Time (s)')
    plt.ylabel('Angle (degrees)')
    plt.title('Body Lean Angles During Sidestep')
    plt.legend()
    plt.grid(True)
    plt.axhline(y=0, color='k', linestyle='--', alpha=0.3)
    
    plt.subplot(1, 2, 2)
    plt.plot(time_points, y_traj, 'g-', linewidth=2, label='Foot Position')
    plt.xlabel('Time (s)')
    plt.ylabel('Lateral Position (m)')
    plt.title('Foot Position vs Time')
    plt.legend()
    plt.grid(True)
    plt.axhline(y=0, color='k', linestyle='--', alpha=0.3)
    
    plt.tight_layout()
    plt.show()
    
    # Full performance analysis
    print("\n=== Running Full Performance Analysis ===")
    results = analyze_sidestep_performance(params, num_steps=3, direction=1.0)
    
    # Parameter comparison
    print("\n=== Comparing Different Parameter Sets ===")
    comparison_results = compare_parameters()
    
    print("\n" + "=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)
