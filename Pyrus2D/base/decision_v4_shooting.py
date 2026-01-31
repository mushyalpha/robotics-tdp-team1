"""
Version 4: Add Smart Shooting
- Analyzes goal angles
- Considers goalkeeper position
- Has passing and positioning
"""
from base.strategy_formation import StrategyFormation
from base.generator_pass import BhvPassGen
from base.generator_shoot import BhvShhotGen
from lib.action.intercept import Intercept
from lib.action.smart_kick import SmartKick
from lib.action.go_to_point import GoToPoint
from lib.action.scan_field import ScanField
from lib.action.neck_turn_to_ball import NeckTurnToBall
from lib.action.neck_scan_players import NeckScanPlayers

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from lib.player.player_agent import PlayerAgent


def get_decision(agent: 'PlayerAgent'):
    """Add intelligent shooting"""
    wm = agent.world()
    st = StrategyFormation().i()
    st.update(wm)
    
    # Goalie: stay near goal
    if wm.self().goalie():
        from pyrusgeom.vector_2d import Vector2D
        from lib.action.go_to_point import GoToPoint
        goal_pos = Vector2D(-50, 0)
        if wm.self().pos().dist(goal_pos) > 3:
            GoToPoint(goal_pos, 1.0, 100).execute(agent)
        agent.set_neck_action(NeckTurnToBall())
        return True
    
    if wm.self().is_kickable():
        # First try shooting
        shoot_candidate = BhvShhotGen().generator(wm)
        if shoot_candidate:
            SmartKick(shoot_candidate.target_point, shoot_candidate.first_ball_speed,
                     shoot_candidate.first_ball_speed - 1, 3).execute(agent)
            agent.set_neck_action(NeckScanPlayers())
            return True
        
        # Then try passing
        pass_candidates = BhvPassGen().generator(wm)
        if pass_candidates and len(pass_candidates) > 0:
            best_pass = max(pass_candidates)
            target = best_pass.target_ball_pos
            SmartKick(target, best_pass.start_ball_speed, best_pass.start_ball_speed - 1, 3).execute(agent)
            agent.set_neck_action(NeckTurnToBall())
            return True
        
        # Fallback: kick forward harder
        from pyrusgeom.vector_2d import Vector2D
        target = Vector2D(52.5, 0)
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
    
    # Positioning
    home_pos = st.get_position(wm.self().unum())
    if home_pos and wm.self().pos().dist(home_pos) > 1.0:
        GoToPoint(home_pos, 0.5, 100).execute(agent)
        agent.set_neck_action(NeckTurnToBall())
        return True
    
    return ScanField().execute(agent)
