"""
Simple Soccer Simulation with Visualization - VERSION 1 (BASIC)
Shows decision tree evolution in a controllable environment

VERSION 1 FEATURES:
- Basic ball physics (velocity + friction)
- Perfect straight-line kicks (no accuracy errors)
- No spin effects
- Simple collision with walls
"""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.animation import FuncAnimation, PillowWriter
from datetime import datetime
import time
import os

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
    Basic soccer ball physics:
    - Velocity-based movement with friction
    - No spin effects
    - Perfect straight-line movement
    - Energy loss on wall bounces
    """
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0
        self.friction = 0.92  # Realistic grass friction (lower = more friction)
        self.min_velocity = 0.05  # Stop ball if moving too slowly
    
    def update(self, dt=0.1):
        # Apply velocity with realistic time step
        self.x += self.vx * dt
        self.y += self.vy * dt
        
        # Apply friction (exponential decay - realistic for rolling ball)
        self.vx *= self.friction
        self.vy *= self.friction
        
        # Stop ball if moving very slowly (avoid infinite rolling)
        speed = np.sqrt(self.vx**2 + self.vy**2)
        if speed < self.min_velocity:
            self.vx = 0.0
            self.vy = 0.0
        
        # Bounce off walls with energy loss
        if self.x < -PITCH_LENGTH/2:
            self.x = -PITCH_LENGTH/2
            self.vx = -self.vx * 0.6  # Lose energy on bounce
        elif self.x > PITCH_LENGTH/2:
            self.x = PITCH_LENGTH/2
            self.vx = -self.vx * 0.6
        
        if self.y < -PITCH_WIDTH/2:
            self.y = -PITCH_WIDTH/2
            self.vy = -self.vy * 0.6
        elif self.y > PITCH_WIDTH/2:
            self.y = PITCH_WIDTH/2
            self.vy = -self.vy * 0.6

class SoccerSimulator:
    def __init__(self, decision_algorithm='basic'):
        self.ball = Ball(0, 0)
        self.robots = []
        self.decision_algorithm = decision_algorithm
        self.time = 0
        self.goals_scored = 0
        
        # Create team (4 players: 1 goalkeeper, 1 defender, 2 attackers)
        positions = [
            (-3.5, 0),   # Goalkeeper (ID: 1)
            (-2, 0),     # Defender (ID: 2)
            (0, -1),     # Attacker 1 (ID: 3)
            (0, 1),      # Attacker 2 (ID: 4)
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
            # Basic kick: perfect straight line towards goal
            dx = PITCH_LENGTH/2 - self.ball.x
            dy = 0 - self.ball.y
            dist = np.sqrt(dx**2 + dy**2)
            if dist > 0:
                # Kick power: fixed power
                kick_power = 1.8
                # Add current ball velocity (momentum transfer)
                self.ball.vx = (dx / dist) * kick_power + self.ball.vx * 0.3
                self.ball.vy = (dy / dist) * kick_power + self.ball.vy * 0.3
                
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
                    # Pass power: gentler than shot, perfect aim
                    pass_power = 1.2
                    self.ball.vx = (dx / dist) * pass_power
                    self.ball.vy = (dy / dist) * pass_power
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
        self.ax.plot(self.sim.ball.x, self.sim.ball.y, 'o', 
                    color='white', markersize=10, 
                    markeredgecolor='black', markeredgewidth=2)
        
        # Draw ball velocity vector (for debugging physics)
        ball_speed = np.sqrt(self.sim.ball.vx**2 + self.sim.ball.vy**2)
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
                    f'VERSION 1 (BASIC) | Algorithm: {self.sim.decision_algorithm} | Time: {self.sim.time} | Goals: {self.sim.goals_scored} | Ball Speed: {ball_speed:.2f}',
                    ha='center', fontsize=12, fontweight='bold', color='white')
        
        return []
    
    def run(self, frames=500, save_gif=False, gif_filename=None):
        """Run the animation and optionally save as GIF"""
        anim = FuncAnimation(self.fig, self.update, frames=frames, 
                           interval=50, blit=True)
        
        if save_gif:
            if gif_filename is None:
                # Generate timestamp-based filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                algo = self.sim.decision_algorithm
                gif_filename = f"sim1_{algo}_{timestamp}.gif"
            
            # Ensure output directory exists
            output_dir = "animation_outputs"
            os.makedirs(output_dir, exist_ok=True)
            gif_path = os.path.join(output_dir, gif_filename)
            
            print(f"Saving animation to {gif_path}...")
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

def main():
    print("=" * 60)
    print("Soccer Simulation VERSION 1 - Basic Physics")
    print("=" * 60)
    print("\nFEATURES:")
    print("  ✓ Basic velocity and friction")
    print("  ✓ Perfect straight-line kicks (unrealistic)")
    print("  ✓ No spin effects")
    print("  ✓ No environmental factors")
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
    
    print(f"\nRunning VERSION 1 (BASIC) with {algorithm} algorithm...")
    print("Ball moves in perfect straight lines - not realistic!")
    if save_gif:
        print(f"Recording {num_frames} frames for GIF export...")
    print("Close the window to exit.\n")
    
    sim = SoccerSimulator(decision_algorithm=algorithm)
    viz = Visualizer(sim)
    viz.run(frames=num_frames, save_gif=save_gif)

if __name__ == "__main__":
    main()
