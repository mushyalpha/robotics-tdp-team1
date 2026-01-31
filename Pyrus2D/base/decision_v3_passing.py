"""
Version 3: Add Simple Passing
- Can pass to teammates
- Still shoots randomly
- Has positioning
"""
from base.strategy_formation import StrategyFormation
from base.generator_pass import BhvPassGen
from lib.action.intercept import Intercept
from lib.action.smart_kick import SmartKick
from lib.action.go_to_point import GoToPoint
from lib.action.scan_field import ScanField
from lib.action.neck_turn_to_ball import NeckTurnToBall
from pyrusgeom.vector_2d import Vector2D
import random

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from lib.player.player_agent import PlayerAgent


def get_decision(agent: 'PlayerAgent'):
    """Add passing capability"""
    wm = agent.world()
    st = StrategyFormation().i()
    st.update(wm)
    
    # Goalie: stay near goal
    if wm.self().goalie():
        goal_pos = Vector2D(-50, 0)
        if wm.self().pos().dist(goal_pos) > 3:
            GoToPoint(goal_pos, 1.0, 100).execute(agent)
        agent.set_neck_action(NeckTurnToBall())
        return True
    
    if wm.self().is_kickable():
        # Try to find a pass
        pass_candidates = BhvPassGen().generator(wm)
        
        if pass_candidates and len(pass_candidates) > 0:
            best_pass = max(pass_candidates)
            target = best_pass.target_ball_pos
            SmartKick(target, best_pass.start_ball_speed, best_pass.start_ball_speed - 1, 3).execute(agent)
            agent.set_neck_action(NeckTurnToBall())
            return True
        
        # No good pass, kick towards goal harder
        target_x = 52.5
        target_y = random.uniform(-7, 7)
        target = Vector2D(target_x, target_y)
        SmartKick(target, 3.0, 2.5, 3).execute(agent)
        agent.set_neck_action(NeckTurnToBall())
        return True
    
    # Intercept logic
    self_min = wm.intercept_table().self_reach_cycle()
    tm_min = wm.intercept_table().teammate_reach_cycle()
    
    if self_min <= tm_min and self_min <= 10:
        if Intercept().execute(agent):
            agent.set_neck_action(NeckTurnToBall())
            return True
    
    # Go to position
    home_pos = st.get_position(wm.self().unum())
    if home_pos and wm.self().pos().dist(home_pos) > 1.0:
        GoToPoint(home_pos, 0.5, 100).execute(agent)
        agent.set_neck_action(NeckTurnToBall())
        return True
    
    return ScanField().execute(agent)
