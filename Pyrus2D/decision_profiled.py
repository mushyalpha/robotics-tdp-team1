"""
Profile-Driven Decision Algorithm
==================================

A single decision function that reads from a BehaviorProfile to produce
aggressive, conservative, or baseline behavior — no separate code paths.

Works for BOTH teams: the 'attack_direction' parameter determines which
goal the team attacks (+1 = right goal, -1 = left goal).
"""

import numpy as np
from behavior_profile import BehaviorProfile

# Field constants (must match simple_soccer_sim2.py)
PITCH_LENGTH = 9.0
PITCH_WIDTH = 6.0
GOAL_WIDTH = 2.6
MIN_PASS_SCORE = 1.4


def decide_action_profiled(sim, robot, profile: BehaviorProfile, attack_direction: int):
    """
    Profile-driven decision for a single robot.
    
    Args:
        sim: SoccerSimulator instance (has .ball, .robots, .blue_robots, .red_robots, etc.)
        robot: The Robot making the decision
        profile: BehaviorProfile controlling behavior thresholds
        attack_direction: +1 if attacking right goal, -1 if attacking left goal
    
    Returns:
        str: action name ('kick', 'pass', 'walk_forward', 'turn_left', 'turn_right', 'stay', 'tackle')
    """
    # Skip if incapacitated (fallen/recovering)
    if hasattr(robot, 'is_incapacitated') and robot.is_incapacitated():
        return 'incapacitated'
    
    ball = sim.ball
    ball_pos = {'x': ball.x, 'y': ball.y}
    distance_to_ball = robot.get_distance_to(ball_pos)
    
    # --- GOALKEEPER BEHAVIOR ---
    if hasattr(robot, 'role') and robot.role.name == 'GOALKEEPER':
        return _decide_goalkeeper(sim, robot, profile, attack_direction)
    
    # --- FIELD PLAYER BEHAVIOR ---
    
    # Get all teammates (same team as this robot)
    teammates = _get_teammates(sim, robot)
    opponents = _get_opponents(sim, robot)
    
    # Determine if this robot should chase the ball
    should_chase = _should_chase_ball(sim, robot, teammates, profile)
    
    if distance_to_ball <= 0.3:
        # === ROBOT HAS POSSESSION ===
        return _decide_with_ball(sim, robot, profile, attack_direction, teammates)
    
    elif should_chase and distance_to_ball <= profile.chase_radius:
        # === CHASE THE BALL ===
        bearing = robot.get_bearing_to(ball_pos)
        if abs(bearing) > 0.2:
            return 'turn_left' if bearing > 0 else 'turn_right'
        else:
            return 'walk_forward'
    
    else:
        # === HOLD POSITION ===
        return _move_to_position(sim, robot, profile, attack_direction)


def _decide_with_ball(sim, robot, profile, attack_direction, teammates):
    """Decision when robot has the ball (within 0.3m)."""
    
    # Goal position (centre of the goal we're attacking)
    goal_x = (PITCH_LENGTH / 2) * attack_direction
    goal_y = 0.0
    
    dist_to_goal = np.sqrt((goal_x - robot.x)**2 + (goal_y - robot.y)**2)
    
    # --- Check shooting conditions ---
    in_shooting_range = dist_to_goal <= profile.shoot_distance_max
    
    # Calculate open goal angle (simplified)
    goal_angle = _estimate_goal_angle(robot, goal_x, attack_direction)
    good_angle = goal_angle >= profile.shoot_angle_min
    
    # Pass count check
    pass_count = getattr(sim, 'pass_count', 0)
    met_min_passes = pass_count >= profile.min_passes_before_shot
    
    # Shoot-first policy: if shot conditions are met, shoot immediately.
    if in_shooting_range and good_angle and met_min_passes:
        # SHOOT!
        if hasattr(robot, 'set_state'):
            from simple_soccer_sim3 import RobotState
            robot.set_state(RobotState.KICKING)
        sim.pass_count = 0
        sim.last_passer_id = None
        return 'kick'
    
    # --- Find best pass target ---
    best_pass_target, best_pass_score = _find_best_pass(
        sim, robot, teammates, profile, attack_direction
    )
    
    if best_pass_target is not None and best_pass_score > MIN_PASS_SCORE:
        # PASS
        if hasattr(robot, 'set_state'):
            from simple_soccer_sim3 import RobotState
            robot.set_state(RobotState.PASSING)
        sim.last_passer_id = robot.id
        sim.pass_count = getattr(sim, 'pass_count', 0) + 1
        sim.total_passes = getattr(sim, 'total_passes', 0) + 1
        sim.pass_target = best_pass_target
        return 'pass'
    
    # --- No good pass, shoot if possible or dribble forward ---
    if in_shooting_range:
        if hasattr(robot, 'set_state'):
            from simple_soccer_sim3 import RobotState
            robot.set_state(RobotState.KICKING)
        sim.pass_count = 0
        sim.last_passer_id = None
        return 'kick'
    
    # Dribble: walk forward toward goal
    goal_bearing = robot.get_bearing_to({'x': goal_x, 'y': goal_y})
    if abs(goal_bearing) > 0.2:
        return 'turn_left' if goal_bearing > 0 else 'turn_right'
    return 'walk_forward'


def _decide_goalkeeper(sim, robot, profile, attack_direction):
    """Goalkeeper decision: track ball, sweep if close enough."""
    ball = sim.ball
    ball_pos = {'x': ball.x, 'y': ball.y}
    distance_to_ball = robot.get_distance_to(ball_pos)
    
    # Goalkeeper home position (on the goal line)
    gk_home_x = -(PITCH_LENGTH / 2 - 0.3) * attack_direction  # Slightly in front of own goal
    gk_home_y = 0.0
    
    # If ball is within sweep radius, go get it
    if distance_to_ball <= profile.gk_sweep_radius:
        if distance_to_ball <= 0.3:
            # Has ball — kick it away (clearance)
            if hasattr(robot, 'set_state'):
                from simple_soccer_sim3 import RobotState
                robot.set_state(RobotState.KICKING)
            return 'kick'
        
        # Chase ball
        bearing = robot.get_bearing_to(ball_pos)
        if hasattr(robot, 'set_state'):
            from simple_soccer_sim3 import RobotState
            robot.set_state(RobotState.GOALKEEPING)
        if abs(bearing) > 0.2:
            return 'turn_left' if bearing > 0 else 'turn_right'
        return 'walk_forward'
    
    # Track ball vertically (move up/down to stay between ball and goal)
    # Clamp GK y-position to goal width
    target_y = np.clip(ball.y, -GOAL_WIDTH / 2 + 0.2, GOAL_WIDTH / 2 - 0.2)
    
    dy = target_y - robot.y
    if abs(dy) > 0.15:
        bearing = robot.get_bearing_to({'x': robot.x, 'y': target_y})
        if abs(bearing) > 0.2:
            return 'turn_left' if bearing > 0 else 'turn_right'
        return 'walk_forward'
    
    if hasattr(robot, 'set_state'):
        from simple_soccer_sim3 import RobotState
        robot.set_state(RobotState.GOALKEEPING)
    return 'stay'


def _should_chase_ball(sim, robot, teammates, profile):
    """Determine if this robot should be the one chasing the ball."""
    ball_pos = {'x': sim.ball.x, 'y': sim.ball.y}
    my_dist = robot.get_distance_to(ball_pos)
    
    # Am I the closest teammate to the ball?
    for tm in teammates:
        if tm.id == robot.id:
            continue
        if hasattr(tm, 'is_incapacitated') and tm.is_incapacitated():
            continue
        if hasattr(tm, 'role') and tm.role.name == 'GOALKEEPER':
            continue
        
        tm_dist = tm.get_distance_to(ball_pos)
        
        # I should chase if I'm within intercept_urgency distance of being closest
        if tm_dist < my_dist - (profile.intercept_urgency * 0.1):
            return False  # Teammate is significantly closer
    
    return True


def _find_best_pass(sim, robot, teammates, profile, attack_direction):
    """Find the best passing target among teammates."""
    goal_x = (PITCH_LENGTH / 2) * attack_direction
    
    best_target = None
    best_score = -float('inf')
    
    my_dist_to_goal = np.sqrt((goal_x - robot.x)**2 + robot.y**2)
    
    for tm in teammates:
        if tm.id == robot.id:
            continue
        if hasattr(tm, 'is_incapacitated') and tm.is_incapacitated():
            continue
        if hasattr(tm, 'role') and tm.role.name == 'GOALKEEPER':
            continue
        
        # Don't pass back to who just passed to us
        if hasattr(sim, 'last_passer_id') and sim.last_passer_id == tm.id:
            continue
        
        tm_dist_to_goal = np.sqrt((goal_x - tm.x)**2 + tm.y**2)
        tm_dist_to_ball = tm.get_distance_to({'x': sim.ball.x, 'y': sim.ball.y})
        
        score = 0.0
        
        # Prefer teammates closer to goal (weighted by forward bias)
        if tm_dist_to_goal < my_dist_to_goal:
            score += (my_dist_to_goal - tm_dist_to_goal) * profile.pass_forward_bias
        
        # Prefer teammates who are forward in attack direction
        forward_diff = (tm.x - robot.x) * attack_direction
        if forward_diff > 0:
            score += forward_diff * profile.pass_forward_bias
        
        # Prefer reasonable passing distance
        if 1.0 < tm_dist_to_ball < 4.0:
            score += 2.0
        elif tm_dist_to_ball < 1.0:
            score += 0.5
        
        # Good spacing (different lane)
        if abs(tm.y - robot.y) > 0.5:
            score += 1.0
        
        if score > best_score:
            best_score = score
            best_target = tm
    
    return best_target, best_score


def _move_to_position(sim, robot, profile, attack_direction):
    """Move toward strategic home position, adjusted by profile."""
    
    # Get role-based home position
    home_x, home_y = _get_home_position(robot, profile, attack_direction)
    
    # Adjust toward ball (slight attraction)
    ball_weight = 0.15
    target_x = home_x + (sim.ball.x - home_x) * ball_weight
    target_y = home_y + (sim.ball.y - home_y) * ball_weight
    
    # Check if already at position
    dist_to_target = np.sqrt((target_x - robot.x)**2 + (target_y - robot.y)**2)
    
    if dist_to_target < 0.3:
        if hasattr(robot, 'set_state'):
            from simple_soccer_sim3 import RobotState
            robot.set_state(RobotState.POSITIONING)
        return 'stay'
    
    # Move toward position
    if hasattr(robot, 'set_state'):
        from simple_soccer_sim3 import RobotState
        robot.set_state(RobotState.POSITIONING)
    
    bearing = robot.get_bearing_to({'x': target_x, 'y': target_y})
    if abs(bearing) > 0.2:
        return 'turn_left' if bearing > 0 else 'turn_right'
    return 'walk_forward'


def _get_home_position(robot, profile, attack_direction):
    """Get the home formation position for a robot, adjusted by profile offsets."""
    
    # Base positions for blue team attacking right (+1)
    # Will be mirrored for red team attacking left (-1)
    role_name = robot.role.name if hasattr(robot, 'role') else 'ATTACKER'
    
    if role_name == 'GOALKEEPER':
        base_x = -3.5
        base_y = 0.0
    elif role_name == 'DEFENDER':
        base_x = -2.0 + profile.defensive_press_offset
        base_y = 0.0
    elif role_name == 'ATTACKER':
        base_x = 0.5 + profile.position_x_offset
        # Spread attackers vertically
        if hasattr(robot, 'id'):
            # Alternate up/down based on player ID
            base_y = (1.0 * profile.position_y_spread) * (1 if robot.id % 2 == 0 else -1)
        else:
            base_y = 0.0
    else:
        base_x = 0.0
        base_y = 0.0
    
    # Mirror for attack direction
    home_x = base_x * attack_direction
    home_y = base_y
    
    return home_x, home_y


def _estimate_goal_angle(robot, goal_x, attack_direction):
    """Estimate the open angle to the goal (degrees) — simplified."""
    goal_top_y = GOAL_WIDTH / 2
    goal_bot_y = -GOAL_WIDTH / 2
    
    # Angles to top and bottom of goal
    angle_top = np.arctan2(goal_top_y - robot.y, goal_x - robot.x)
    angle_bot = np.arctan2(goal_bot_y - robot.y, goal_x - robot.x)
    
    angle_diff = abs(angle_top - angle_bot)
    return np.degrees(angle_diff)


def _get_teammates(sim, robot):
    """Get list of robots on the same team."""
    return [r for r in sim.robots if r.team == robot.team]


def _get_opponents(sim, robot):
    """Get list of robots on the opposing team."""
    return [r for r in sim.robots if r.team != robot.team]
