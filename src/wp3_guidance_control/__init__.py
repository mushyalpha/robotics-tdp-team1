"""
Work Package 3: Guidance and Control

This module provides low-level control algorithms for NAO6 robot motion,
including walking, kicking, balancing, and trajectory planning.

Lead: Bonolo Masima
Team: Zefu Wang, Chengjie Hao
"""

from .motion_controller import MotionController
from .balance_controller import BalanceController
from .kick_algorithm import KickController
from .trajectory_planner import TrajectoryPlanner

__all__ = [
    'MotionController',
    'BalanceController', 
    'KickController',
    'TrajectoryPlanner'
]
