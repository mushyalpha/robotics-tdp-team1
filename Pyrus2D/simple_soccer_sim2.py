"""
Simple Soccer Simulation with Visualization - VERSION 2
Shows decision tree evolution in a controllable environment

VERSION 2 IMPROVEMENTS:
- Realistic ball spin (Magnus effect) causing curved trajectories
- Kick/pass accuracy errors (players aren't perfect)
- Environmental factors (wind, grass bumps) affecting ball movement
- Power variation in kicks and passes
- Visual indicators for spin and ball speed
"""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.animation import FuncAnimation
import time

# Field dimensions
PITCH_LENGTH = 9.0
PITCH_WIDTH = 6.0
GOAL_WIDTH = 2.6

class Robot:
    def __init__(self, x, y, team='blue', player_id=1):
        self.x = x
        self.y = y
        self.heading = 0.0
        self.team = team
        self.id = player_id
        self.color = 'blue' if team == 'blue' else 'red'
    
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

class SoccerSimulator:
    def __init__(self, decision_algorithm='basic'):
        self.ball = Ball(0, 0)
        self.robots = []
        self.decision_algorithm = decision_algorithm
        self.time = 0
        self.goals_scored = 0
        
        # Create team (5 players for simplicity)
        positions = [
            (-3, 0),    # Goalie
            (-2, -1.5), # Defender
            (-2, 1.5),  # Defender
            (0, -1),    # Midfielder
            (0, 1),     # Midfielder
        ]
        for i, (x, y) in enumerate(positions):
            self.robots.append(Robot(x, y, 'blue', i+1))
    
    def decide_action_v1_basic(self, robot):
        """V1: Everyone chases ball, kicks randomly"""
        distance = robot.get_distance_to({'x': self.ball.x, 'y': self.ball.y})
        bearing = robot.get_bearing_to({'x': self.ball.x, 'y': self.ball.y})
        
        if distance <= 0.3:
            return 'kick'
        elif abs(bearing) > 0.2:
            return 'turn_left' if bearing > 0 else 'turn_right'
        else:
            return 'walk_forward'
    
    def decide_action_v2_positioning(self, robot):
        """V2: Only closest player chases, others hold position"""
        # Find closest robot to ball
        distances = [r.get_distance_to({'x': self.ball.x, 'y': self.ball.y}) 
                    for r in self.robots]
        closest_idx = np.argmin(distances)
        
        if robot.id - 1 == closest_idx:
            # I'm closest, chase ball
            return self.decide_action_v1_basic(robot)
        else:
            # Hold position (simplified - just stay still)
            return 'stay'
    
    def decide_action_v3_passing(self, robot):
        """V3: Consider passing to teammates"""
        distance = robot.get_distance_to({'x': self.ball.x, 'y': self.ball.y})
        
        if distance <= 0.3:
            # Check if teammate is closer to goal
            my_dist_to_goal = np.sqrt((PITCH_LENGTH/2 - robot.x)**2 + robot.y**2)
            
            for teammate in self.robots:
                if teammate.id != robot.id:
                    tm_dist_to_goal = np.sqrt((PITCH_LENGTH/2 - teammate.x)**2 + teammate.y**2)
                    if tm_dist_to_goal < my_dist_to_goal - 1.0:
                        return 'pass'
            
            return 'kick'
        
        return self.decide_action_v2_positioning(robot)
    
    def apply_action(self, robot, action):
        """Execute the action"""
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
            # Pass to closest forward teammate
            best_teammate = None
            best_x = robot.x
            for tm in self.robots:
                if tm.id != robot.id and tm.x > best_x:
                    best_teammate = tm
                    best_x = tm.x
            
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
                    
                    # Pass power with slight variation
                    base_power = 1.2
                    power_variation = np.random.uniform(-0.2, 0.2)
                    pass_power = base_power + power_variation
                    
                    # Apply pass with variations
                    self.ball.vx = np.cos(actual_angle) * pass_power
                    self.ball.vy = np.sin(actual_angle) * pass_power
                    
                    # Add slight spin to pass
                    self.ball.spin = np.random.uniform(-0.3, 0.3)
        # 'stay' does nothing
    
    def step(self):
        """One simulation step"""
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
            # Reset
            self.ball = Ball(0, 0)
        
        self.time += 1

class Visualizer:
    def __init__(self, simulator):
        self.sim = simulator
        self.fig, self.ax = plt.subplots(figsize=(12, 8))
        self.setup_field()
        
    def setup_field(self):
        """Draw the soccer field"""
        self.ax.set_xlim(-PITCH_LENGTH/2 - 0.5, PITCH_LENGTH/2 + 0.5)
        self.ax.set_ylim(-PITCH_WIDTH/2 - 0.5, PITCH_WIDTH/2 + 0.5)
        self.ax.set_aspect('equal')
        
        # Field outline
        field = patches.Rectangle((-PITCH_LENGTH/2, -PITCH_WIDTH/2), 
                                 PITCH_LENGTH, PITCH_WIDTH,
                                 linewidth=2, edgecolor='white', 
                                 facecolor='green', alpha=0.3)
        self.ax.add_patch(field)
        
        # Center line
        self.ax.plot([0, 0], [-PITCH_WIDTH/2, PITCH_WIDTH/2], 'w-', linewidth=2)
        
        # Center circle
        circle = patches.Circle((0, 0), 0.5, linewidth=2, 
                               edgecolor='white', facecolor='none')
        self.ax.add_patch(circle)
        
        # Goals
        goal_left = patches.Rectangle((-PITCH_LENGTH/2 - 0.2, -GOAL_WIDTH/2),
                                     0.2, GOAL_WIDTH,
                                     linewidth=2, edgecolor='white',
                                     facecolor='none')
        goal_right = patches.Rectangle((PITCH_LENGTH/2, -GOAL_WIDTH/2),
                                      0.2, GOAL_WIDTH,
                                      linewidth=2, edgecolor='white',
                                      facecolor='none')
        self.ax.add_patch(goal_left)
        self.ax.add_patch(goal_right)
        
        self.ax.set_facecolor('darkgreen')
        self.ax.grid(True, alpha=0.3)
        
    def update(self, frame):
        """Animation update function"""
        self.ax.clear()
        self.setup_field()
        
        # Run simulation step
        self.sim.step()
        
        # Draw robots
        for robot in self.sim.robots:
            # Robot body
            self.ax.plot(robot.x, robot.y, 'o', color=robot.color, 
                        markersize=15, markeredgecolor='white', markeredgewidth=2)
            # Robot heading
            dx = 0.3 * np.cos(robot.heading)
            dy = 0.3 * np.sin(robot.heading)
            self.ax.arrow(robot.x, robot.y, dx, dy, 
                         head_width=0.15, head_length=0.1, 
                         fc=robot.color, ec='white')
            # Player number
            self.ax.text(robot.x, robot.y, str(robot.id), 
                        ha='center', va='center', color='white', 
                        fontsize=8, fontweight='bold')
        
        # Draw ball
        ball_speed = np.sqrt(self.sim.ball.vx**2 + self.sim.ball.vy**2)
        
        # Ball color intensity based on speed (more intense when moving fast)
        ball_alpha = min(1.0, 0.5 + ball_speed * 0.2)
        self.ax.plot(self.sim.ball.x, self.sim.ball.y, 'o', 
                    color='white', markersize=10, 
                    markeredgecolor='black', markeredgewidth=2, alpha=ball_alpha)
        
        # Draw spin indicator (curved arrow around ball)
        if abs(self.sim.ball.spin) > 0.05:
            spin_radius = 0.15
            spin_direction = 1 if self.sim.ball.spin > 0 else -1
            theta = np.linspace(0, 1.5 * np.pi * spin_direction, 20)
            spin_x = self.sim.ball.x + spin_radius * np.cos(theta)
            spin_y = self.sim.ball.y + spin_radius * np.sin(theta)
            self.ax.plot(spin_x, spin_y, 'c-', linewidth=2, alpha=0.6)
            # Arrow head for spin
            self.ax.plot(spin_x[-1], spin_y[-1], 'c>', markersize=8, alpha=0.6)
        
        # Draw ball velocity vector (for debugging physics)
        if ball_speed > 0.1:
            # Scale velocity vector for visibility
            vel_scale = 0.5
            self.ax.arrow(self.sim.ball.x, self.sim.ball.y, 
                         self.sim.ball.vx * vel_scale, 
                         self.sim.ball.vy * vel_scale,
                         head_width=0.3, head_length=0.2,
                         fc='yellow', ec='orange', alpha=0.7, linewidth=2)
        
        # Info text
        self.ax.text(0, PITCH_WIDTH/2 + 0.3, 
                    f'VERSION 2 | Algorithm: {self.sim.decision_algorithm} | Time: {self.sim.time} | Goals: {self.sim.goals_scored} | Ball Speed: {ball_speed:.2f} | Spin: {self.sim.ball.spin:.2f}',
                    ha='center', fontsize=12, fontweight='bold', color='white')
        
        return []
    
    def run(self, frames=500):
        """Run the animation"""
        anim = FuncAnimation(self.fig, self.update, frames=frames, 
                           interval=50, blit=True)
        plt.show()

def main():
    print("=" * 60)
    print("Soccer Simulation VERSION 2 - Realistic Ball Physics")
    print("=" * 60)
    print("\nNEW FEATURES:")
    print("  ✓ Ball spin (Magnus effect) - curved trajectories")
    print("  ✓ Kick/pass accuracy errors")
    print("  ✓ Environmental factors (wind, grass)")
    print("  ✓ Power variations")
    print("=" * 60)
    print("\nChoose algorithm:")
    print("1. V1 Basic - Everyone chases ball")
    print("2. V2 Positioning - Only closest chases")
    print("3. V3 Passing - Team coordination")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    algorithms = {
        '1': 'v1_basic',
        '2': 'v2_positioning',
        '3': 'v3_passing'
    }
    
    algorithm = algorithms.get(choice, 'v1_basic')
    
    print(f"\nRunning VERSION 2 with {algorithm} algorithm...")
    print("Watch for curved ball trajectories and spin effects!")
    print("Close the window to exit.\n")
    
    sim = SoccerSimulator(decision_algorithm=algorithm)
    viz = Visualizer(sim)
    viz.run(frames=1000)

if __name__ == "__main__":
    main()
