"""
Simple Soccer Simulation with Visualization - VERSION 2
Shows decision tree evolution in a controllable environment

VERSION 2 IMPROVEMENTS:
- Realistic ball spin (Magnus effect) causing curved trajectories
- Kick/pass accuracy errors (players aren't perfect)
- Environmental factors (wind, grass bumps) affecting ball movement
- Power variation in kicks and passes
- Visual indicators for spin and ball speed
- Robot state machine with visual status display
- Fall/recovery simulation (representing 3D scenarios)
"""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.animation import FuncAnimation, PillowWriter
from datetime import datetime
from enum import Enum
import time
import os

# Field dimensions
PITCH_LENGTH = 9.0
PITCH_WIDTH = 6.0
GOAL_WIDTH = 2.6

# =============================================================================
# ROBOT STATE MACHINE
# =============================================================================

class RobotState(Enum):
    """Robot states representing both 2D actions and simulated 3D scenarios"""
    IDLE = "IDLE"                    # Standing still
    CHASING_BALL = "CHASING_BALL"    # Moving toward ball
    KICKING = "KICKING"              # Executing kick
    PASSING = "PASSING"              # Executing pass
    POSITIONING = "POSITIONING"      # Moving to strategic position
    FALLEN = "FALLEN"                # Simulating fall (from 3D)
    RECOVERING = "RECOVERING"        # Simulating recovery phase (from 3D)
    GOALKEEPING = "GOALKEEPING"      # Goalkeeper-specific tracking

class RobotRole(Enum):
    """Robot roles in the team"""
    GOALKEEPER = "GK"
    DEFENDER = "DEF"
    ATTACKER = "ATK"

# State colors for visualization
STATE_COLORS = {
    RobotState.IDLE: '#808080',           # Gray
    RobotState.CHASING_BALL: '#00FF00',   # Bright Green
    RobotState.KICKING: '#FF0000',        # Red
    RobotState.PASSING: '#FFA500',        # Orange
    RobotState.POSITIONING: '#00BFFF',    # Deep Sky Blue
    RobotState.FALLEN: '#8B0000',         # Dark Red
    RobotState.RECOVERING: '#FFD700',     # Gold
    RobotState.GOALKEEPING: '#9400D3',    # Dark Violet
}

# State abbreviations for compact display
STATE_ABBREV = {
    RobotState.IDLE: "IDL",
    RobotState.CHASING_BALL: "CHS",
    RobotState.KICKING: "KCK",
    RobotState.PASSING: "PAS",
    RobotState.POSITIONING: "POS",
    RobotState.FALLEN: "FAL",
    RobotState.RECOVERING: "REC",
    RobotState.GOALKEEPING: "GKP",
}

# =============================================================================
# ROBOT CLASS
# =============================================================================

class Robot:
    def __init__(self, x, y, team='blue', player_id=1, role=RobotRole.ATTACKER):
        # Position and movement
        self.x = x
        self.y = y
        self.home_x = x  # Home position for positioning behavior
        self.home_y = y
        self.heading = 0.0
        
        # Identity
        self.team = team
        self.id = player_id
        self.role = role
        self.color = 'blue' if team == 'blue' else 'red'
        
        # State machine
        self.state = RobotState.IDLE
        self.previous_state = RobotState.IDLE
        self.state_duration = 0  # How long in current state (timesteps)
        
        # Fall/recovery simulation (representing 3D scenarios)
        self.fall_probability = 0.002  # Small chance to fall each step
        self.recovery_time = 0         # Countdown timer for recovery
        self.recovery_duration = 30    # Steps needed to recover (represents ~3 seconds)
        
        # Action state (for multi-step actions)
        self.action_timer = 0
        self.kick_duration = 5   # Steps for kick animation
        self.pass_duration = 5   # Steps for pass animation
    
    def set_state(self, new_state, log=True):
        """Update robot state with optional logging"""
        if new_state != self.state:
            self.previous_state = self.state
            self.state = new_state
            self.state_duration = 0
            if log:
                print(f"[T={self.state_duration:04d}] Robot {self.id} ({self.role.value}): "
                      f"{self.previous_state.value} -> {new_state.value}")
        else:
            self.state_duration += 1
    
    def get_distance_to(self, target):
        dx = target['x'] - self.x
        dy = target['y'] - self.y
        return np.sqrt(dx**2 + dy**2)
    
    def get_bearing_to(self, target):
        dx = target['x'] - self.x
        dy = target['y'] - self.y
        angle_to_target = np.arctan2(dy, dx)
        bearing = angle_to_target - self.heading
        # Normalize
        bearing = bearing % (2 * np.pi)
        if bearing > np.pi:
            bearing = bearing - 2 * np.pi
        return bearing
    
    def simulate_fall(self):
        """Randomly trigger falls to simulate 3D instability"""
        if self.state not in [RobotState.FALLEN, RobotState.RECOVERING]:
            # Higher fall probability during dynamic actions
            fall_chance = self.fall_probability
            if self.state in [RobotState.KICKING, RobotState.PASSING]:
                fall_chance *= 3  # More likely to fall during kicks
            if self.state == RobotState.CHASING_BALL:
                fall_chance *= 1.5  # Slightly more likely while moving
            
            if np.random.random() < fall_chance:
                self.set_state(RobotState.FALLEN)
                self.recovery_time = self.recovery_duration
                return True
        return False
    
    def update_recovery(self):
        """Handle recovery from fallen state"""
        if self.state == RobotState.FALLEN:
            self.recovery_time -= 1
            if self.recovery_time <= self.recovery_duration // 2:
                self.set_state(RobotState.RECOVERING)
        elif self.state == RobotState.RECOVERING:
            self.recovery_time -= 1
            if self.recovery_time <= 0:
                self.set_state(RobotState.IDLE)
                return True  # Recovered
        return False
    
    def is_incapacitated(self):
        """Check if robot can't perform actions (fallen/recovering)"""
        return self.state in [RobotState.FALLEN, RobotState.RECOVERING]
    
    def get_state_info(self):
        """Get formatted state information for display"""
        role_str = self.role.value
        state_str = STATE_ABBREV[self.state]
        return f"R{self.id}[{role_str}]: {state_str}"

# =============================================================================
# BALL CLASS
# =============================================================================

class Ball:
    """
    Soccer ball with realistic physics:
    - Velocity-based movement with friction (grass resistance)
    - Spin effects (Magnus effect) causing ball to curve
    - Environmental factors (wind, grass bumps) for random perturbations
    - Kick/pass accuracy errors (players aren't perfect)
    - Energy loss on wall bounces
    """
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0
        self.friction = 0.92  # Realistic grass friction (lower = more friction)
        self.min_velocity = 0.05  # Stop ball if moving too slowly
        self.spin = 0.0  # Ball spin affects trajectory (Magnus effect)
        self.spin_decay = 0.95  # Spin decays over time
    
    def update(self, dt=0.1):
        # Calculate current speed
        speed = np.sqrt(self.vx**2 + self.vy**2)
        
        # Apply spin effect to trajectory (Magnus effect - ball curves)
        if speed > 0.1 and abs(self.spin) > 0.01:
            # Spin causes perpendicular force to velocity direction
            # Normalize velocity vector
            vx_norm = self.vx / speed
            vy_norm = self.vy / speed
            # Perpendicular vector (rotated 90 degrees)
            perp_x = -vy_norm
            perp_y = vx_norm
            # Apply spin force (proportional to speed and spin)
            spin_force = self.spin * speed * 0.05
            self.vx += perp_x * spin_force * dt
            self.vy += perp_y * spin_force * dt
        
        # Environmental factors - random small perturbations (grass bumps, wind gusts)
        if speed > 0.1:
            # Random deviation increases with speed
            wind_factor = 0.02 * speed
            self.vx += np.random.uniform(-wind_factor, wind_factor) * dt
            self.vy += np.random.uniform(-wind_factor, wind_factor) * dt
        
        # Apply velocity with realistic time step
        self.x += self.vx * dt
        self.y += self.vy * dt
        
        # Apply friction (exponential decay - realistic for rolling ball)
        self.vx *= self.friction
        self.vy *= self.friction
        
        # Decay spin over time
        self.spin *= self.spin_decay
        
        # Stop ball if moving very slowly (avoid infinite rolling)
        if speed < self.min_velocity:
            self.vx = 0.0
            self.vy = 0.0
            self.spin = 0.0
        
        # Bounce off walls with energy loss
        if self.x < -PITCH_LENGTH/2:
            self.x = -PITCH_LENGTH/2
            self.vx = -self.vx * 0.6  # Lose energy on bounce
            self.spin *= -0.7  # Reverse spin on bounce
        elif self.x > PITCH_LENGTH/2:
            self.x = PITCH_LENGTH/2
            self.vx = -self.vx * 0.6
            self.spin *= -0.7
        
        if self.y < -PITCH_WIDTH/2:
            self.y = -PITCH_WIDTH/2
            self.vy = -self.vy * 0.6
            self.spin *= -0.7
        elif self.y > PITCH_WIDTH/2:
            self.y = PITCH_WIDTH/2
            self.vy = -self.vy * 0.6
            self.spin *= -0.7

# =============================================================================
# SOCCER SIMULATOR
# =============================================================================

class SoccerSimulator:
    def __init__(self, decision_algorithm='basic', enable_falls=True):
        self.ball = Ball(0, 0)
        self.robots = []
        self.decision_algorithm = decision_algorithm
        self.time = 0
        self.goals_scored = 0
        self.enable_falls = enable_falls  # Toggle fall simulation
        
        # Create team (4 players: 1 goalkeeper, 1 defender, 2 attackers)
        team_config = [
            (-3.5, 0, RobotRole.GOALKEEPER),   # Goalkeeper (ID: 1)
            (-2, 0, RobotRole.DEFENDER),       # Defender (ID: 2)
            (0, -1, RobotRole.ATTACKER),       # Attacker 1 (ID: 3)
            (0, 1, RobotRole.ATTACKER),        # Attacker 2 (ID: 4)
        ]
        for i, (x, y, role) in enumerate(team_config):
            self.robots.append(Robot(x, y, 'blue', i+1, role))
        
        # State change log for analysis
        self.state_log = []
        
        # Passing statistics for V3 algorithm
        self.pass_count = 0           # Number of consecutive successful passes
        self.last_passer_id = None    # ID of last robot to pass
        self.min_passes_before_shot = 2  # Minimum passes before shooting allowed
        self.total_passes = 0         # Total passes in game
    
    def log_state_change(self, robot, old_state, new_state):
        """Log state changes for analysis"""
        self.state_log.append({
            'time': self.time,
            'robot_id': robot.id,
            'role': robot.role.value,
            'old_state': old_state.value,
            'new_state': new_state.value
        })
    
    def decide_action_v1_basic(self, robot):
        """V1: Everyone chases ball, kicks randomly"""
        # Skip if incapacitated
        if robot.is_incapacitated():
            return 'incapacitated'
        
        distance = robot.get_distance_to({'x': self.ball.x, 'y': self.ball.y})
        bearing = robot.get_bearing_to({'x': self.ball.x, 'y': self.ball.y})
        
        if distance <= 0.3:
            robot.set_state(RobotState.KICKING)
            return 'kick'
        elif abs(bearing) > 0.2:
            robot.set_state(RobotState.CHASING_BALL)
            return 'turn_left' if bearing > 0 else 'turn_right'
        else:
            robot.set_state(RobotState.CHASING_BALL)
            return 'walk_forward'
    
    def decide_action_v2_positioning(self, robot):
        """V2: Only closest player chases, others hold position"""
        # Skip if incapacitated
        if robot.is_incapacitated():
            return 'incapacitated'
        
        # Goalkeeper always tracks ball (special behavior)
        if robot.role == RobotRole.GOALKEEPER:
            return self.decide_goalkeeper_action(robot)
        
        # Find closest non-incapacitated robot to ball
        distances = []
        for r in self.robots:
            if r.is_incapacitated():
                distances.append(float('inf'))
            else:
                distances.append(r.get_distance_to({'x': self.ball.x, 'y': self.ball.y}))
        closest_idx = np.argmin(distances)
        
        if robot.id - 1 == closest_idx:
            # I'm closest, chase ball
            return self.decide_action_v1_basic(robot)
        else:
            # Hold position (move toward home position)
            dist_to_home = np.sqrt((robot.x - robot.home_x)**2 + (robot.y - robot.home_y)**2)
            if dist_to_home > 0.5:
                robot.set_state(RobotState.POSITIONING)
                # Move toward home
                bearing = robot.get_bearing_to({'x': robot.home_x, 'y': robot.home_y})
                if abs(bearing) > 0.2:
                    return 'turn_left' if bearing > 0 else 'turn_right'
                else:
                    return 'walk_forward'
            else:
                robot.set_state(RobotState.IDLE)
                return 'stay'
    
    def decide_goalkeeper_action(self, robot):
        """Special goalkeeper behavior: track ball along goal line"""
        # Track ball's y-position while staying near goal
        target_y = np.clip(self.ball.y, -GOAL_WIDTH/2 + 0.3, GOAL_WIDTH/2 - 0.3)
        target_x = -PITCH_LENGTH/2 + 0.5  # Stay close to goal
        
        distance_to_target = np.sqrt((robot.x - target_x)**2 + (robot.y - target_y)**2)
        
        if distance_to_target > 0.3:
            robot.set_state(RobotState.GOALKEEPING)
            bearing = robot.get_bearing_to({'x': target_x, 'y': target_y})
            if abs(bearing) > 0.2:
                return 'turn_left' if bearing > 0 else 'turn_right'
            else:
                return 'walk_forward'
        else:
            robot.set_state(RobotState.GOALKEEPING)
            # Face the ball
            bearing = robot.get_bearing_to({'x': self.ball.x, 'y': self.ball.y})
            if abs(bearing) > 0.1:
                return 'turn_left' if bearing > 0 else 'turn_right'
            return 'stay'
    
    def decide_action_v3_passing(self, robot):
        """V3: Emphasize passing to teammates before shooting"""
        # Skip if incapacitated
        if robot.is_incapacitated():
            return 'incapacitated'
        
        # Goalkeeper always tracks ball
        if robot.role == RobotRole.GOALKEEPER:
            return self.decide_goalkeeper_action(robot)
        
        distance = robot.get_distance_to({'x': self.ball.x, 'y': self.ball.y})
        
        if distance <= 0.3:
            # Robot has possession of the ball
            my_dist_to_goal = np.sqrt((PITCH_LENGTH/2 - robot.x)**2 + robot.y**2)
            
            # Find best passing target
            best_pass_target = None
            best_pass_score = -float('inf')
            
            for teammate in self.robots:
                if teammate.id != robot.id and not teammate.is_incapacitated():
                    # Skip goalkeeper for passing targets
                    if teammate.role == RobotRole.GOALKEEPER:
                        continue
                    
                    # Don't pass back to the robot who just passed to you
                    if self.last_passer_id == teammate.id:
                        continue
                    
                    tm_dist_to_goal = np.sqrt((PITCH_LENGTH/2 - teammate.x)**2 + teammate.y**2)
                    tm_dist_to_ball = teammate.get_distance_to({'x': self.ball.x, 'y': self.ball.y})
                    
                    # Calculate pass score based on multiple factors
                    pass_score = 0.0
                    
                    # Prefer teammates closer to goal
                    if tm_dist_to_goal < my_dist_to_goal:
                        pass_score += (my_dist_to_goal - tm_dist_to_goal) * 2.0
                    
                    # Prefer teammates who are forward (positive x direction)
                    if teammate.x > robot.x:
                        pass_score += (teammate.x - robot.x) * 1.5
                    
                    # Prefer teammates at reasonable distance (not too far)
                    if 1.0 < tm_dist_to_ball < 4.0:
                        pass_score += 2.0
                    elif tm_dist_to_ball < 1.0:
                        pass_score += 0.5  # Too close, not great
                    
                    # Prefer teammates in different lanes (good spacing)
                    if abs(teammate.y - robot.y) > 0.5:
                        pass_score += 1.0
                    
                    if pass_score > best_pass_score:
                        best_pass_score = pass_score
                        best_pass_target = teammate
            
            # Decision: Pass or Shoot?
            # Always pass if we haven't met minimum pass requirement
            if self.pass_count < self.min_passes_before_shot:
                if best_pass_target is not None:
                    robot.set_state(RobotState.PASSING)
                    self.last_passer_id = robot.id
                    return 'pass'
                else:
                    # No good pass target, must shoot
                    robot.set_state(RobotState.KICKING)
                    self.pass_count = 0  # Reset pass counter
                    self.last_passer_id = None
                    return 'kick'
            else:
                # Met minimum passes, now decide based on position
                # Only shoot if we're in a good position (close to goal and centered)
                in_shooting_position = (my_dist_to_goal < 2.5 and abs(robot.y) < 1.5)
                
                if in_shooting_position and (best_pass_score < 3.0 or best_pass_target is None):
                    # Good shooting position and no great pass option
                    robot.set_state(RobotState.KICKING)
                    self.pass_count = 0  # Reset pass counter
                    self.last_passer_id = None
                    return 'kick'
                elif best_pass_target is not None and best_pass_score > 1.0:
                    # Continue passing if there's a good target
                    robot.set_state(RobotState.PASSING)
                    self.last_passer_id = robot.id
                    return 'pass'
                else:
                    # Default to shooting
                    robot.set_state(RobotState.KICKING)
                    self.pass_count = 0
                    self.last_passer_id = None
                    return 'kick'
        
        return self.decide_action_v2_positioning(robot)
    
    def apply_action(self, robot, action):
        """Execute the action"""
        if action == 'incapacitated':
            return  # Robot can't act
        
        if action == 'turn_left':
            robot.heading += 0.15
        elif action == 'turn_right':
            robot.heading -= 0.15
        elif action == 'walk_forward':
            robot.x += 0.1 * np.cos(robot.heading)
            robot.y += 0.1 * np.sin(robot.heading)
        elif action == 'kick':
            # Realistic kick: direction towards goal with accuracy errors
            dx = PITCH_LENGTH/2 - self.ball.x
            dy = 0 - self.ball.y
            dist = np.sqrt(dx**2 + dy**2)
            if dist > 0:
                # Calculate intended direction
                intended_angle = np.arctan2(dy, dx)
                
                # Add kick accuracy error (players aren't perfect!)
                # Error increases with distance to target
                angle_error = np.random.normal(0, 0.15 + dist * 0.02)  # Radians
                actual_angle = intended_angle + angle_error
                
                # Kick power with variation
                base_power = 1.8
                power_variation = np.random.uniform(-0.3, 0.3)
                kick_power = base_power + power_variation
                
                # Apply kick in the (slightly inaccurate) direction
                self.ball.vx = np.cos(actual_angle) * kick_power + self.ball.vx * 0.3
                self.ball.vy = np.sin(actual_angle) * kick_power + self.ball.vy * 0.3
                
                # Add random spin to the ball (side spin from foot contact)
                self.ball.spin = np.random.uniform(-0.5, 0.5)
                
                # Cap maximum ball speed (realistic limit)
                max_speed = 3.0
                current_speed = np.sqrt(self.ball.vx**2 + self.ball.vy**2)
                if current_speed > max_speed:
                    self.ball.vx = (self.ball.vx / current_speed) * max_speed
                    self.ball.vy = (self.ball.vy / current_speed) * max_speed
        elif action == 'pass':
            # Find best passing target using V3 logic
            best_teammate = None
            best_pass_score = -float('inf')
            
            for tm in self.robots:
                if tm.id != robot.id and not tm.is_incapacitated():
                    # Skip goalkeeper
                    if tm.role == RobotRole.GOALKEEPER:
                        continue
                    
                    # Don't pass back to who just passed to you
                    if self.last_passer_id == tm.id:
                        continue
                    
                    tm_dist_to_ball = tm.get_distance_to({'x': self.ball.x, 'y': self.ball.y})
                    
                    # Simple scoring: prefer forward players at reasonable distance
                    pass_score = 0.0
                    if tm.x > robot.x:  # Forward pass
                        pass_score += (tm.x - robot.x) * 2.0
                    if 1.0 < tm_dist_to_ball < 4.0:  # Good distance
                        pass_score += 3.0
                    
                    if pass_score > best_pass_score:
                        best_pass_score = pass_score
                        best_teammate = tm
            
            if best_teammate:
                dx = best_teammate.x - self.ball.x
                dy = best_teammate.y - self.ball.y
                dist = np.sqrt(dx**2 + dy**2)
                if dist > 0:
                    # Calculate pass direction with accuracy error
                    intended_angle = np.arctan2(dy, dx)
                    
                    # Pass accuracy (better than shooting but still imperfect)
                    angle_error = np.random.normal(0, 0.08 + dist * 0.015)
                    actual_angle = intended_angle + angle_error
                    
                    # Pass power with slight variation (adjust power based on distance)
                    base_power = 0.8 + (dist * 0.2)  # Scale power with distance
                    power_variation = np.random.uniform(-0.2, 0.2)
                    pass_power = base_power + power_variation
                    
                    # Apply pass with variations
                    self.ball.vx = np.cos(actual_angle) * pass_power
                    self.ball.vy = np.sin(actual_angle) * pass_power
                    
                    # Add slight spin to pass
                    self.ball.spin = np.random.uniform(-0.3, 0.3)
                    
                    # Track pass statistics
                    self.pass_count += 1
                    self.total_passes += 1
                    print(f"[PASS #{self.total_passes}] Robot {robot.id} -> Robot {best_teammate.id} "
                          f"(Chain: {self.pass_count} consecutive passes)")
        # 'stay' does nothing
    
    def step(self):
        """One simulation step"""
        # Update fall/recovery states first
        for robot in self.robots:
            if self.enable_falls:
                robot.update_recovery()
                robot.simulate_fall()
        
        # Each robot decides and acts
        for robot in self.robots:
            if self.decision_algorithm == 'v1_basic':
                action = self.decide_action_v1_basic(robot)
            elif self.decision_algorithm == 'v2_positioning':
                action = self.decide_action_v2_positioning(robot)
            elif self.decision_algorithm == 'v3_passing':
                action = self.decide_action_v3_passing(robot)
            else:
                action = self.decide_action_v1_basic(robot)
            
            self.apply_action(robot, action)
        
        # Update ball physics
        self.ball.update()
        
        # Check for goal
        if self.ball.x > PITCH_LENGTH/2 - 0.2 and abs(self.ball.y) < GOAL_WIDTH/2:
            self.goals_scored += 1
            print(f"\n*** GOAL! Total: {self.goals_scored} ***")
            if self.decision_algorithm == 'v3_passing':
                print(f"    (After {self.pass_count} consecutive passes)")
                print(f"    Total passes this game: {self.total_passes}\n")
            # Reset
            self.ball = Ball(0, 0)
            # Reset robot positions and pass counters
            for robot in self.robots:
                robot.x = robot.home_x
                robot.y = robot.home_y
                robot.set_state(RobotState.IDLE, log=False)
            # Reset pass tracking
            self.pass_count = 0
            self.last_passer_id = None
        
        # Detect if ball is out of bounds (possession lost)
        if abs(self.ball.x) > PITCH_LENGTH/2 or abs(self.ball.y) > PITCH_WIDTH/2:
            if self.pass_count > 0:
                print(f"[OUT OF BOUNDS] Pass chain broken ({self.pass_count} passes)")
            self.pass_count = 0
            self.last_passer_id = None
        
        self.time += 1

# =============================================================================
# VISUALIZER
# =============================================================================

class Visualizer:
    def __init__(self, simulator):
        self.sim = simulator
        # Create figure with two subplots: main field and status panel
        self.fig = plt.figure(figsize=(14, 8))
        
        # Main field (left, larger)
        self.ax_field = self.fig.add_axes([0.05, 0.1, 0.65, 0.85])
        
        # Status panel (right side)
        self.ax_status = self.fig.add_axes([0.72, 0.1, 0.26, 0.85])
        self.ax_status.axis('off')
        
        self.setup_field()
        
    def setup_field(self):
        """Draw the soccer field"""
        self.ax_field.set_xlim(-PITCH_LENGTH/2 - 0.5, PITCH_LENGTH/2 + 0.5)
        self.ax_field.set_ylim(-PITCH_WIDTH/2 - 0.5, PITCH_WIDTH/2 + 0.5)
        self.ax_field.set_aspect('equal')
        
        # Field outline
        field = patches.Rectangle((-PITCH_LENGTH/2, -PITCH_WIDTH/2), 
                                 PITCH_LENGTH, PITCH_WIDTH,
                                 linewidth=2, edgecolor='white', 
                                 facecolor='green', alpha=0.3)
        self.ax_field.add_patch(field)
        
        # Center line
        self.ax_field.plot([0, 0], [-PITCH_WIDTH/2, PITCH_WIDTH/2], 'w-', linewidth=2)
        
        # Center circle
        circle = patches.Circle((0, 0), 0.5, linewidth=2, 
                               edgecolor='white', facecolor='none')
        self.ax_field.add_patch(circle)
        
        # Goals
        goal_left = patches.Rectangle((-PITCH_LENGTH/2 - 0.2, -GOAL_WIDTH/2),
                                     0.2, GOAL_WIDTH,
                                     linewidth=2, edgecolor='white',
                                     facecolor='none')
        goal_right = patches.Rectangle((PITCH_LENGTH/2, -GOAL_WIDTH/2),
                                      0.2, GOAL_WIDTH,
                                      linewidth=2, edgecolor='white',
                                      facecolor='none')
        self.ax_field.add_patch(goal_left)
        self.ax_field.add_patch(goal_right)
        
        self.ax_field.set_facecolor('darkgreen')
        self.ax_field.grid(True, alpha=0.3)
    
    def draw_status_panel(self):
        """Draw the robot status panel"""
        self.ax_status.clear()
        self.ax_status.axis('off')
        self.ax_status.set_xlim(0, 1)
        self.ax_status.set_ylim(0, 1)
        
        # Title
        self.ax_status.text(0.5, 0.97, 'ROBOT STATUS', ha='center', va='top',
                           fontsize=14, fontweight='bold', color='white',
                           bbox=dict(boxstyle='round', facecolor='#333333', edgecolor='white'))
        
        # Draw status for each robot
        y_pos = 0.88
        for robot in self.sim.robots:
            state_color = STATE_COLORS[robot.state]
            
            # Robot info box
            box_height = 0.18
            box = patches.FancyBboxPatch((0.05, y_pos - box_height), 0.9, box_height,
                                         boxstyle="round,pad=0.02",
                                         facecolor='#2a2a2a', edgecolor=state_color,
                                         linewidth=3)
            self.ax_status.add_patch(box)
            
            # Robot ID and role
            role_text = f"Robot {robot.id} [{robot.role.value}]"
            self.ax_status.text(0.1, y_pos - 0.03, role_text, 
                               fontsize=11, fontweight='bold', color='white', va='top')
            
            # State with color indicator
            state_text = robot.state.value
            self.ax_status.text(0.1, y_pos - 0.08, f"State: ", 
                               fontsize=10, color='gray', va='top')
            self.ax_status.text(0.28, y_pos - 0.08, state_text, 
                               fontsize=10, fontweight='bold', color=state_color, va='top')
            
            # Position info
            pos_text = f"Pos: ({robot.x:.1f}, {robot.y:.1f})"
            self.ax_status.text(0.1, y_pos - 0.13, pos_text, 
                               fontsize=9, color='lightgray', va='top')
            
            # State duration
            duration_text = f"Duration: {robot.state_duration} steps"
            self.ax_status.text(0.55, y_pos - 0.13, duration_text, 
                               fontsize=9, color='lightgray', va='top')
            
            y_pos -= 0.22
        
        # Legend
        y_pos -= 0.02
        self.ax_status.text(0.5, y_pos, 'STATE LEGEND', ha='center', va='top',
                           fontsize=10, fontweight='bold', color='white')
        
        y_pos -= 0.04
        legend_states = [
            (RobotState.IDLE, RobotState.CHASING_BALL),
            (RobotState.KICKING, RobotState.PASSING),
            (RobotState.POSITIONING, RobotState.GOALKEEPING),
            (RobotState.FALLEN, RobotState.RECOVERING),
        ]
        
        for state_pair in legend_states:
            for i, state in enumerate(state_pair):
                x_offset = 0.1 if i == 0 else 0.55
                color = STATE_COLORS[state]
                abbrev = STATE_ABBREV[state]
                
                # Color box
                legend_box = patches.Rectangle((x_offset, y_pos - 0.025), 0.08, 0.025,
                                              facecolor=color, edgecolor='white', linewidth=1)
                self.ax_status.add_patch(legend_box)
                
                # Label
                self.ax_status.text(x_offset + 0.1, y_pos - 0.012, abbrev, 
                                   fontsize=8, color='white', va='center')
            y_pos -= 0.04
        
        self.ax_status.set_facecolor('#1a1a1a')
        
    def update(self, frame):
        """Animation update function"""
        self.ax_field.clear()
        self.setup_field()
        
        # Run simulation step
        self.sim.step()
        
        # Draw robots with state-based coloring
        for robot in self.sim.robots:
            state_color = STATE_COLORS[robot.state]
            
            # Robot body (team color)
            self.ax_field.plot(robot.x, robot.y, 'o', color=robot.color, 
                              markersize=18, markeredgecolor=state_color, markeredgewidth=3)
            
            # Fallen indicator (X mark)
            if robot.state == RobotState.FALLEN:
                self.ax_field.plot(robot.x, robot.y, 'x', color='white', 
                                  markersize=12, markeredgewidth=3)
            elif robot.state == RobotState.RECOVERING:
                # Recovering indicator (spinning circle)
                angle = (self.sim.time * 0.3) % (2 * np.pi)
                rx = robot.x + 0.25 * np.cos(angle)
                ry = robot.y + 0.25 * np.sin(angle)
                self.ax_field.plot(rx, ry, 'o', color='gold', markersize=6)
            
            # Robot heading (only if not fallen)
            if not robot.is_incapacitated():
                dx = 0.3 * np.cos(robot.heading)
                dy = 0.3 * np.sin(robot.heading)
                self.ax_field.arrow(robot.x, robot.y, dx, dy, 
                                   head_width=0.15, head_length=0.1, 
                                   fc=robot.color, ec='white')
            
            # Player number
            self.ax_field.text(robot.x, robot.y, str(robot.id), 
                              ha='center', va='center', color='white', 
                              fontsize=9, fontweight='bold')
            
            # State label above robot
            state_abbrev = STATE_ABBREV[robot.state]
            self.ax_field.text(robot.x, robot.y + 0.4, state_abbrev,
                              ha='center', va='bottom', color=state_color,
                              fontsize=8, fontweight='bold',
                              bbox=dict(boxstyle='round,pad=0.1', facecolor='black', alpha=0.7))
        
        # Draw passing visualization for V3 algorithm
        if self.sim.decision_algorithm == 'v3_passing' and self.sim.pass_count > 0:
            # Draw passing chain indicator - connect robots with lines
            for robot in self.sim.robots:
                if robot.state == RobotState.PASSING:
                    # Find who they're passing to
                    best_target = None
                    best_score = -float('inf')
                    
                    for teammate in self.sim.robots:
                        if (teammate.id != robot.id and 
                            not teammate.is_incapacitated() and
                            teammate.role != RobotRole.GOALKEEPER):
                            
                            # Simple scoring
                            score = 0.0
                            if teammate.x > robot.x:
                                score += (teammate.x - robot.x) * 2.0
                            tm_dist = np.sqrt((teammate.x - robot.x)**2 + (teammate.y - robot.y)**2)
                            if 1.0 < tm_dist < 4.0:
                                score += 3.0
                            
                            if score > best_score:
                                best_score = score
                                best_target = teammate
                    
                    if best_target:
                        # Draw pass intention line
                        self.ax_field.plot([robot.x, best_target.x], 
                                          [robot.y, best_target.y],
                                          'o-', color='orange', linewidth=2, 
                                          markersize=5, alpha=0.6, 
                                          label='Pass Target' if robot.id == self.sim.robots[0].id else '')
        
        # Draw ball
        ball_speed = np.sqrt(self.sim.ball.vx**2 + self.sim.ball.vy**2)
        
        # Ball color intensity based on speed (more intense when moving fast)
        ball_alpha = min(1.0, 0.5 + ball_speed * 0.2)
        self.ax_field.plot(self.sim.ball.x, self.sim.ball.y, 'o', 
                          color='white', markersize=10, 
                          markeredgecolor='black', markeredgewidth=2, alpha=ball_alpha)
        
        # Draw spin indicator (curved arrow around ball)
        if abs(self.sim.ball.spin) > 0.05:
            spin_radius = 0.15
            spin_direction = 1 if self.sim.ball.spin > 0 else -1
            theta = np.linspace(0, 1.5 * np.pi * spin_direction, 20)
            spin_x = self.sim.ball.x + spin_radius * np.cos(theta)
            spin_y = self.sim.ball.y + spin_radius * np.sin(theta)
            self.ax_field.plot(spin_x, spin_y, 'c-', linewidth=2, alpha=0.6)
            # Arrow head for spin
            self.ax_field.plot(spin_x[-1], spin_y[-1], 'c>', markersize=8, alpha=0.6)
        
        # Draw ball velocity vector (for debugging physics)
        if ball_speed > 0.1:
            # Scale velocity vector for visibility
            vel_scale = 0.5
            self.ax_field.arrow(self.sim.ball.x, self.sim.ball.y, 
                               self.sim.ball.vx * vel_scale, 
                               self.sim.ball.vy * vel_scale,
                               head_width=0.3, head_length=0.2,
                               fc='yellow', ec='orange', alpha=0.7, linewidth=2)
        
        # Info text at top
        info_text = f'VERSION 2 | Algorithm: {self.sim.decision_algorithm} | ' \
                   f'Time: {self.sim.time} | Goals: {self.sim.goals_scored}'
        
        # Add pass statistics for V3 algorithm
        if self.sim.decision_algorithm == 'v3_passing':
            info_text += f' | Pass Chain: {self.sim.pass_count} | Total Passes: {self.sim.total_passes}'
        
        self.ax_field.text(0, PITCH_WIDTH/2 + 0.3, info_text,
                          ha='center', fontsize=11, fontweight='bold', color='white')
        
        # Draw prominent pass counter for V3 algorithm (when passing chain is active)
        if self.sim.decision_algorithm == 'v3_passing' and self.sim.pass_count > 0:
            # Large pass counter in corner
            counter_text = f"{self.sim.pass_count}"
            counter_label = "PASS\nCHAIN"
            
            # Position in top-left corner
            counter_x = -PITCH_LENGTH/2 + 0.8
            counter_y = PITCH_WIDTH/2 - 0.5
            
            # Draw background circle
            circle = patches.Circle((counter_x, counter_y), 0.4, 
                                   facecolor='orange', edgecolor='white', 
                                   linewidth=3, alpha=0.8)
            self.ax_field.add_patch(circle)
            
            # Draw counter number
            self.ax_field.text(counter_x, counter_y + 0.05, counter_text,
                              ha='center', va='center', color='white',
                              fontsize=24, fontweight='bold')
            
            # Draw label below
            self.ax_field.text(counter_x, counter_y - 0.2, counter_label,
                              ha='center', va='top', color='white',
                              fontsize=7, fontweight='bold')
        
        # Update status panel
        self.draw_status_panel()
        
        return []
    
    def run(self, frames=500, save_gif=False, gif_filename=None):
        """Run the animation and optionally save as GIF"""
        anim = FuncAnimation(self.fig, self.update, frames=frames, 
                           interval=50, blit=False)
        
        if save_gif:
            if gif_filename is None:
                # Generate timestamp-based filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                algo = self.sim.decision_algorithm
                gif_filename = f"sim2_{algo}_{timestamp}.gif"
            
            # Ensure output directory exists
            output_dir = "animation_outputs"
            os.makedirs(output_dir, exist_ok=True)
            gif_path = os.path.join(output_dir, gif_filename)
            
            print(f"\nSaving animation to {gif_path}...")
            print("This may take a minute...")
            
            # Save as GIF using PillowWriter
            writer = PillowWriter(fps=20)
            anim.save(gif_path, writer=writer)
            
            print(f"✓ Animation saved successfully!")
            print(f"  Location: {gif_path}")
            
            # Calculate file size
            file_size_mb = os.path.getsize(gif_path) / (1024 * 1024)
            print(f"  File size: {file_size_mb:.2f} MB")
        
        plt.show()

# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 70)
    print("Soccer Simulation VERSION 2 - Realistic Ball Physics + State Machine")
    print("=" * 70)
    print("\nNEW FEATURES:")
    print("  [Physics]")
    print("    - Ball spin (Magnus effect) - curved trajectories")
    print("    - Kick/pass accuracy errors")
    print("    - Environmental factors (wind, grass)")
    print("    - Power variations")
    print("  [State Machine]")
    print("    - Visual robot state display (color-coded)")
    print("    - Status panel showing all robot states")
    print("    - Fall/recovery simulation (3D scenario)")
    print("    - Console logging of state changes")
    print("=" * 70)
    print("\nChoose algorithm:")
    print("1. V1 Basic - Everyone chases ball, shoots immediately")
    print("2. V2 Positioning - Only closest chases, others hold positions")
    print("3. V3 Passing - Emphasizes player-to-player passing (min 2 passes before shot)")
    print("              * Orange lines show pass intentions")
    print("              * Pass counter displayed in top-left corner")
    print("              * Console logs all passes")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    algorithms = {
        '1': 'v1_basic',
        '2': 'v2_positioning',
        '3': 'v3_passing'
    }
    
    algorithm = algorithms.get(choice, 'v1_basic')
    
    # Ask about fall simulation
    fall_choice = input("\nEnable fall simulation? (y/n, default=y): ").strip().lower()
    enable_falls = fall_choice != 'n'
    
    # Ask about saving as GIF
    save_choice = input("\nSave animation as GIF? (y/n, default=n): ").strip().lower()
    save_gif = save_choice == 'y'
    
    num_frames = 1000
    if save_gif:
        frame_input = input(f"Number of frames to record (default={num_frames}): ").strip()
        if frame_input:
            try:
                num_frames = int(frame_input)
            except ValueError:
                print(f"Invalid input, using default: {num_frames}")
    
    print(f"\nRunning VERSION 2 with {algorithm} algorithm...")
    print(f"Fall simulation: {'ENABLED' if enable_falls else 'DISABLED'}")
    if save_gif:
        print(f"Recording {num_frames} frames for GIF export...")
    print("Watch for curved ball trajectories and robot state changes!")
    print("State changes will be logged to console.")
    print("Close the window to exit.\n")
    print("-" * 70)
    
    sim = SoccerSimulator(decision_algorithm=algorithm, enable_falls=enable_falls)
    viz = Visualizer(sim)
    viz.run(frames=num_frames, save_gif=save_gif)

if __name__ == "__main__":
    main()
