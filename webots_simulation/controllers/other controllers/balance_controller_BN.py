# Import Required Libraries
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, Tuple, List 
import sys
import os

# Add project root to path (notebook is in src/wp3_guidance_control/)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__ if '__file__' in globals() else ''), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
                                             
#robot constraints
from src.wp3_guidance_control.robot_constraints import NAO6Constraints

try:
    from controller import Robot, Motor, InertialUnit, Gyro, Accelerometer
except ImportError:
    print("Webots controller modules not found. Running in notebook mode.")


# defining parameters
class BalanceParameters:

    def __init__(self):
        # Safe operating limits (from robot constraints)
        # the robot is within good balance zone and no need for control
        self.safe_roll_limit = NAO6Constraints.MAX_LATERAL_LEAN      # 0.12 rad
        self.safe_pitch_forward = NAO6Constraints.MAX_FORWARD_LEAN   # 0.15 rad
        self.safe_pitch_backward = NAO6Constraints.MAX_BACKWARD_LEAN # 0.20 rad

        # balance zone - we need PID to recover the robot
        # I need to justify these values
        self.max_roll_angle = 0.3
        self.max_pitch_angle = 0.4

        # fall zone: need recovery sequence for these - points of no return
        self.roll_fall_angle = 0.7
        self.pitch_fall_angle = 0.8

        # angular velocity to help detect falls earlier
        self.max_angular_velocity = 3.7

    def is_stable(self, roll, pitch):
        """
        are we inside the safe zone?
        """

        if np.abs(roll) < self.safe_roll_limit and - self.safe_pitch_backward < pitch < self.safe_pitch_forward:
            return True
        else:
            return False
            # I need to justify the minus sign in front of safe_pitch backward ## ahh found out its a Webots thing: positive pitch is rbot leaning forward and negative pitch is robot leaning backward
        
    def is_falling(self, roll, pitch):
        """Detect if the robot is falling based on roll n pitch angles"""
       
        if np.abs(roll) > self.roll_fall_angle or np.abs(pitch) > self.pitch_fall_angle:
            return False


    def get_stability_state(self, roll, pitch):
        if self.is_falling(roll, pitch):
            return 'falling'
        elif not self.is_stable(roll, pitch):
            return 'balancing'
        else:
            return 'stable'

params = BalanceParameters()
#example
print(f"check stability at roll = 0.2 and pitch = 0.3: {params.is_stable(0.2, 0.3)}")
print(f"check fall at roll = 0.8, pitch = 0.2 {params.is_falling(0.8, 0.2)}")
print(params.get_stability_state(0.2,0.3))


# JIE's PID Controller: