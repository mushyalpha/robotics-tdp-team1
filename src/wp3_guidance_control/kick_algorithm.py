"""
Kick Algorithm for NAO6 Robot

Implements various kicking techniques with power and direction control.

Author: Team 1
Date: October 2025
"""

import numpy as np
from typing import Dict, Tuple
from enum import Enum


class KickType(Enum):
    """Types of kicks available."""
    STRAIGHT = "straight"
    SIDE = "side"
    CHIP = "chip"
    PASS = "pass"
    CLEAR = "clear"


class KickController:
    """
    Controls kicking motions for the NAO6 robot.
    
    Provides different kick types with adjustable power and direction.
    """
    
    def __init__(self):
        """Initialize kick controller."""
        self.max_kick_power = 1.0
        self.min_kick_power = 0.1
        
        # Kick parameters
        self.kick_duration = 0.3  # seconds
        self.backswing_ratio = 0.4  # Ratio of backswing to forward swing
        
    def prepare_kick(self, kick_type: KickType, power: float,
                     direction: float, foot: str = "right") -> Dict:
        """
        Prepare kick motion sequence.
        
        Args:
            kick_type: Type of kick to perform
            power: Kick power (0.0 to 1.0)
            direction: Kick direction in radians
            foot: "left" or "right"
            
        Returns:
            Dictionary with kick sequence phases
        """
        # Validate inputs
        power = np.clip(power, self.min_kick_power, self.max_kick_power)
        foot = foot.lower()
        if foot not in ["left", "right"]:
            raise ValueError(f"Invalid foot: {foot}")
            
        # Generate kick sequence based on type
        if kick_type == KickType.STRAIGHT:
            return self._straight_kick_sequence(power, direction, foot)
        elif kick_type == KickType.SIDE:
            return self._side_kick_sequence(power, direction, foot)
        elif kick_type == KickType.CHIP:
            return self._chip_kick_sequence(power, direction, foot)
        else:
            return self._straight_kick_sequence(power, direction, foot)
    
    def _straight_kick_sequence(self, power: float, direction: float,
                               foot: str) -> Dict:
        """Generate straight kick sequence."""
        sequence = {
            'phases': [],
            'total_duration': self.kick_duration
        }
        
        # Phase 1: Preparation - shift weight to support leg
        prep_phase = {
            'name': 'preparation',
            'duration': 0.2,
            'joints': self._get_weight_shift_joints(foot)
        }
        sequence['phases'].append(prep_phase)
        
        # Phase 2: Backswing
        backswing_angle = -power * 0.5  # More power = larger backswing
        backswing_phase = {
            'name': 'backswing',
            'duration': self.kick_duration * self.backswing_ratio,
            'joints': self._get_kick_joints(foot, backswing_angle, 0)
        }
        sequence['phases'].append(backswing_phase)
        
        # Phase 3: Forward swing (kick)
        kick_angle = power * 0.8
        kick_phase = {
            'name': 'kick',
            'duration': self.kick_duration * (1 - self.backswing_ratio),
            'joints': self._get_kick_joints(foot, kick_angle, direction)
        }
        sequence['phases'].append(kick_phase)
        
        # Phase 4: Recovery
        recovery_phase = {
            'name': 'recovery',
            'duration': 0.2,
            'joints': self._get_standing_joints()
        }
        sequence['phases'].append(recovery_phase)
        
        return sequence
    
    def _side_kick_sequence(self, power: float, direction: float,
                           foot: str) -> Dict:
        """Generate side kick sequence."""
        # TODO: Implement side kick
        return self._straight_kick_sequence(power, direction, foot)
    
    def _chip_kick_sequence(self, power: float, direction: float,
                           foot: str) -> Dict:
        """Generate chip kick sequence for lofted passes."""
        # TODO: Implement chip kick with toe under ball
        return self._straight_kick_sequence(power, direction, foot)
    
    def _get_weight_shift_joints(self, kicking_foot: str) -> Dict:
        """Get joint angles for weight shift to support leg."""
        joints = {}
        
        if kicking_foot == "right":
            # Shift weight to left leg
            joints['LHipRoll'] = 0.1
            joints['RHipRoll'] = -0.05
            joints['LAnkleRoll'] = 0.05
            joints['RAnkleRoll'] = -0.02
        else:
            # Shift weight to right leg
            joints['LHipRoll'] = -0.05
            joints['RHipRoll'] = 0.1
            joints['LAnkleRoll'] = -0.02
            joints['RAnkleRoll'] = 0.05
            
        return joints
    
    def _get_kick_joints(self, foot: str, hip_pitch: float,
                        hip_yaw: float) -> Dict:
        """Get joint angles for kick motion."""
        joints = {}
        
        if foot == "right":
            joints['RHipPitch'] = hip_pitch
            joints['RHipYawPitch'] = hip_yaw * 0.3
            joints['RKneePitch'] = max(0, -hip_pitch * 0.5)
            joints['RAnklePitch'] = -hip_pitch * 0.3
        else:
            joints['LHipPitch'] = hip_pitch
            joints['LHipYawPitch'] = hip_yaw * 0.3
            joints['LKneePitch'] = max(0, -hip_pitch * 0.5)
            joints['LAnklePitch'] = -hip_pitch * 0.3
            
        return joints
    
    def _get_standing_joints(self) -> Dict:
        """Get joint angles for standing position."""
        return {
            'LHipPitch': 0.0,
            'RHipPitch': 0.0,
            'LKneePitch': 0.0,
            'RKneePitch': 0.0,
            'LAnklePitch': 0.0,
            'RAnklePitch': 0.0,
            'LHipRoll': 0.0,
            'RHipRoll': 0.0,
            'LAnkleRoll': 0.0,
            'RAnkleRoll': 0.0
        }
    
    def calculate_kick_power(self, distance_to_target: float) -> float:
        """
        Calculate required kick power for distance.
        
        Args:
            distance_to_target: Distance to target in meters
            
        Returns:
            Kick power (0.0 to 1.0)
        """
        # Simple linear model - should be calibrated
        MAX_KICK_DISTANCE = 5.0  # meters
        
        power = distance_to_target / MAX_KICK_DISTANCE
        return np.clip(power, self.min_kick_power, self.max_kick_power)
    
    def calculate_kick_direction(self, target_position: Tuple[float, float],
                                robot_position: Tuple[float, float],
                                robot_orientation: float) -> float:
        """
        Calculate kick direction to reach target.
        
        Args:
            target_position: (x, y) target position
            robot_position: (x, y) robot position
            robot_orientation: Robot orientation in radians
            
        Returns:
            Kick direction relative to robot orientation
        """
        # Vector to target
        dx = target_position[0] - robot_position[0]
        dy = target_position[1] - robot_position[1]
        
        # Angle to target (global frame)
        target_angle = np.arctan2(dy, dx)
        
        # Relative angle (robot frame)
        relative_angle = target_angle - robot_orientation
        
        # Normalize to [-pi, pi]
        while relative_angle > np.pi:
            relative_angle -= 2 * np.pi
        while relative_angle < -np.pi:
            relative_angle += 2 * np.pi
            
        return relative_angle
