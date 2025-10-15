"""
Balance Controller for NAO6 Robot

Implements balance control using IMU feedback and center of mass management.

Author: Team 1
Date: October 2025
"""

import numpy as np
from typing import Tuple, Dict


class BalanceController:
    """
    Controls robot balance during standing and walking.
    
    Uses PID control with IMU feedback to maintain stability
    by adjusting ankle and hip joints.
    """
    
    def __init__(self):
        """Initialize balance controller."""
        # PID gains for pitch control
        self.kp_pitch = 0.5
        self.ki_pitch = 0.1
        self.kd_pitch = 0.05
        
        # PID gains for roll control
        self.kp_roll = 0.5
        self.ki_roll = 0.1
        self.kd_roll = 0.05
        
        # Error accumulators
        self.pitch_error_sum = 0.0
        self.roll_error_sum = 0.0
        self.last_pitch_error = 0.0
        self.last_roll_error = 0.0
        
        # Control limits
        self.max_ankle_correction = 0.2  # radians
        self.max_hip_correction = 0.1  # radians
        
    def compute_corrections(self, imu_data: Dict, dt: float) -> Dict:
        """
        Compute joint corrections for balance.
        
        Args:
            imu_data: IMU sensor data {'pitch': float, 'roll': float}
            dt: Time step in seconds
            
        Returns:
            Dictionary of joint corrections
        """
        pitch = imu_data.get('pitch', 0.0)
        roll = imu_data.get('roll', 0.0)
        
        # Compute PID for pitch
        pitch_correction = self._compute_pid(
            pitch, 0.0,  # Target is 0 (upright)
            self.kp_pitch, self.ki_pitch, self.kd_pitch,
            'pitch', dt
        )
        
        # Compute PID for roll
        roll_correction = self._compute_pid(
            roll, 0.0,  # Target is 0 (upright)
            self.kp_roll, self.ki_roll, self.kd_roll,
            'roll', dt
        )
        
        # Apply corrections to joints
        corrections = {
            'LAnklePitch': -pitch_correction * 0.5,
            'RAnklePitch': -pitch_correction * 0.5,
            'LAnkleRoll': -roll_correction * 0.5,
            'RAnkleRoll': roll_correction * 0.5,
            'LHipPitch': pitch_correction * 0.3,
            'RHipPitch': pitch_correction * 0.3,
            'LHipRoll': roll_correction * 0.3,
            'RHipRoll': -roll_correction * 0.3
        }
        
        # Apply limits
        for joint, value in corrections.items():
            if 'Ankle' in joint:
                corrections[joint] = np.clip(value, -self.max_ankle_correction, 
                                            self.max_ankle_correction)
            elif 'Hip' in joint:
                corrections[joint] = np.clip(value, -self.max_hip_correction,
                                            self.max_hip_correction)
                
        return corrections
    
    def _compute_pid(self, current: float, target: float,
                     kp: float, ki: float, kd: float,
                     axis: str, dt: float) -> float:
        """
        Compute PID control output.
        
        Args:
            current: Current value
            target: Target value
            kp, ki, kd: PID gains
            axis: 'pitch' or 'roll' for tracking
            dt: Time step
            
        Returns:
            Control output
        """
        error = target - current
        
        # Update error tracking based on axis
        if axis == 'pitch':
            self.pitch_error_sum += error * dt
            error_rate = (error - self.last_pitch_error) / dt if dt > 0 else 0
            self.last_pitch_error = error
            
            # Anti-windup
            self.pitch_error_sum = np.clip(self.pitch_error_sum, -1.0, 1.0)
            
            error_sum = self.pitch_error_sum
            
        else:  # roll
            self.roll_error_sum += error * dt
            error_rate = (error - self.last_roll_error) / dt if dt > 0 else 0
            self.last_roll_error = error
            
            # Anti-windup
            self.roll_error_sum = np.clip(self.roll_error_sum, -1.0, 1.0)
            
            error_sum = self.roll_error_sum
        
        # PID calculation
        output = kp * error + ki * error_sum + kd * error_rate
        
        return output
    
    def reset(self):
        """Reset controller state."""
        self.pitch_error_sum = 0.0
        self.roll_error_sum = 0.0
        self.last_pitch_error = 0.0
        self.last_roll_error = 0.0
