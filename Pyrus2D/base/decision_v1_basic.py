"""
Version 1: Basic Decision Tree
- Simple chase ball behavior
- Random kick direction
- No passing, no shooting strategy
- No formation
"""
from lib.action.intercept import Intercept
from lib.action.smart_kick import SmartKick
from lib.action.scan_field import ScanField
from lib.action.neck_turn_to_ball import NeckTurnToBall
from pyrusgeom.vector_2d import Vector2D
import random

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from lib.player.player_agent import PlayerAgent


def get_decision(agent: 'PlayerAgent'):
    """Basic decision: intercept ball, kick towards goal randomly"""
    wm = agent.world()
    
    # Goalie: just stay near goal
    if wm.self().goalie():
        from lib.action.go_to_point import GoToPoint
        goal_pos = Vector2D(-50, 0)
        if wm.self().pos().dist(goal_pos) > 3:
            GoToPoint(goal_pos, 1.0, 100).execute(agent)
        agent.set_neck_action(NeckTurnToBall())
        return True
    
    # If we can kick the ball
    if wm.self().is_kickable():
        # Kick towards opponent goal with random angle
        target_x = 52.5  # opponent goal
        target_y = random.uniform(-7, 7)  # random height within goal
        target = Vector2D(target_x, target_y)
        
        # Kick harder
        SmartKick(target, 3.0, 2.5, 3).execute(agent)
        agent.set_neck_action(NeckTurnToBall())
        return True
    
    # Otherwise, chase the ball
    if Intercept().execute(agent):
        agent.set_neck_action(NeckTurnToBall())
        return True
    
    # Default: scan field
    return ScanField().execute(agent)
