"""
Standalone Pyrus2D Log Visualizer
Replays game logs without needing rcssserver or rcssmonitor
Uses pygame for visualization
"""
import pygame
import sys
import os
import re
from pathlib import Path

# Initialize Pygame
pygame.init()

# Screen settings
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
FPS = 10

# Field dimensions (RoboCup 2D)
FIELD_LENGTH = 105.0  # meters
FIELD_WIDTH = 68.0
GOAL_WIDTH = 14.02

# Colors
GREEN = (34, 139, 34)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 100, 255)
RED = (255, 50, 50)
YELLOW = (255, 255, 0)
GRAY = (200, 200, 200)

class LogParser:
    """Parse Pyrus2D log files"""
    
    def __init__(self, log_dir):
        self.log_dir = Path(log_dir)
        self.frames = []
        self.current_frame = 0
        
    def parse_logs(self):
        """Parse all log files in directory"""
        print(f"Parsing logs from: {self.log_dir}")
        
        # Look for player log files
        log_files = list(self.log_dir.glob("*.log"))
        
        if not log_files:
            print("No log files found!")
            return False
        
        print(f"Found {len(log_files)} log files")
        
        # For now, create dummy data for visualization
        # In a real implementation, you'd parse the actual log format
        self.create_sample_data()
        return True
    
    def create_sample_data(self):
        """Create sample game data for demonstration"""
        # Simulate 300 frames of a game
        for frame_num in range(300):
            frame = {
                'time': frame_num,
                'ball': {
                    'x': -20 + (frame_num * 0.3),
                    'y': 0 + (frame_num % 20 - 10) * 0.5
                },
                'players': []
            }
            
            # Add 11 players for left team (blue)
            formations = [
                (-45, 0),   # Goalie
                (-30, -15), (-30, 15),  # Defenders
                (-15, -20), (-15, 0), (-15, 20),  # Midfielders
                (0, -15), (0, 15),  # Forwards
                (10, -10), (10, 0), (10, 10)  # Attackers
            ]
            
            for i, (base_x, base_y) in enumerate(formations):
                # Add some movement
                offset_x = (frame_num % 30 - 15) * 0.3
                offset_y = (frame_num % 20 - 10) * 0.2
                
                frame['players'].append({
                    'team': 'left',
                    'unum': i + 1,
                    'x': base_x + offset_x,
                    'y': base_y + offset_y,
                    'body_angle': 0
                })
            
            self.frames.append(frame)
        
        print(f"Created {len(self.frames)} frames of sample data")
    
    def get_frame(self, frame_num):
        """Get specific frame"""
        if 0 <= frame_num < len(self.frames):
            return self.frames[frame_num]
        return None
    
    def get_total_frames(self):
        return len(self.frames)

class FieldRenderer:
    """Render the soccer field"""
    
    def __init__(self, screen):
        self.screen = screen
        self.scale = min(SCREEN_WIDTH / (FIELD_LENGTH + 10), 
                        SCREEN_HEIGHT / (FIELD_WIDTH + 10))
        self.offset_x = SCREEN_WIDTH / 2
        self.offset_y = SCREEN_HEIGHT / 2
    
    def world_to_screen(self, x, y):
        """Convert world coordinates to screen coordinates"""
        screen_x = self.offset_x + x * self.scale
        screen_y = self.offset_y - y * self.scale  # Flip Y axis
        return int(screen_x), int(screen_y)
    
    def draw_field(self):
        """Draw the soccer field"""
        # Background
        self.screen.fill(GREEN)
        
        # Field outline
        half_length = FIELD_LENGTH / 2
        half_width = FIELD_WIDTH / 2
        
        corners = [
            self.world_to_screen(-half_length, -half_width),
            self.world_to_screen(half_length, -half_width),
            self.world_to_screen(half_length, half_width),
            self.world_to_screen(-half_length, half_width)
        ]
        pygame.draw.polygon(self.screen, WHITE, corners, 3)
        
        # Center line
        top = self.world_to_screen(0, half_width)
        bottom = self.world_to_screen(0, -half_width)
        pygame.draw.line(self.screen, WHITE, top, bottom, 2)
        
        # Center circle
        center = self.world_to_screen(0, 0)
        radius = int(9.15 * self.scale)  # 9.15m radius
        pygame.draw.circle(self.screen, WHITE, center, radius, 2)
        
        # Goals
        goal_half = GOAL_WIDTH / 2
        
        # Left goal
        left_goal_top = self.world_to_screen(-half_length, goal_half)
        left_goal_bottom = self.world_to_screen(-half_length, -goal_half)
        left_goal_back = self.world_to_screen(-half_length - 2, goal_half)
        left_goal_back_bottom = self.world_to_screen(-half_length - 2, -goal_half)
        
        pygame.draw.line(self.screen, WHITE, left_goal_top, left_goal_back, 3)
        pygame.draw.line(self.screen, WHITE, left_goal_bottom, left_goal_back_bottom, 3)
        pygame.draw.line(self.screen, WHITE, left_goal_back, left_goal_back_bottom, 3)
        
        # Right goal
        right_goal_top = self.world_to_screen(half_length, goal_half)
        right_goal_bottom = self.world_to_screen(half_length, -goal_half)
        right_goal_back = self.world_to_screen(half_length + 2, goal_half)
        right_goal_back_bottom = self.world_to_screen(half_length + 2, -goal_half)
        
        pygame.draw.line(self.screen, WHITE, right_goal_top, right_goal_back, 3)
        pygame.draw.line(self.screen, WHITE, right_goal_bottom, right_goal_back_bottom, 3)
        pygame.draw.line(self.screen, WHITE, right_goal_back, right_goal_back_bottom, 3)
    
    def draw_player(self, player):
        """Draw a player"""
        pos = self.world_to_screen(player['x'], player['y'])
        
        # Player color
        color = BLUE if player['team'] == 'left' else RED
        
        # Draw player circle
        pygame.draw.circle(self.screen, color, pos, 12)
        pygame.draw.circle(self.screen, WHITE, pos, 12, 2)
        
        # Draw player number
        font = pygame.font.Font(None, 20)
        text = font.render(str(player['unum']), True, WHITE)
        text_rect = text.get_rect(center=pos)
        self.screen.blit(text, text_rect)
    
    def draw_ball(self, ball):
        """Draw the ball"""
        pos = self.world_to_screen(ball['x'], ball['y'])
        pygame.draw.circle(self.screen, WHITE, pos, 8)
        pygame.draw.circle(self.screen, BLACK, pos, 8, 2)
    
    def draw_info(self, frame_num, total_frames, algorithm=""):
        """Draw information overlay"""
        font = pygame.font.Font(None, 30)
        
        # Frame counter
        text = font.render(f"Frame: {frame_num}/{total_frames}", True, WHITE)
        self.screen.blit(text, (10, 10))
        
        # Algorithm name
        if algorithm:
            text = font.render(f"Algorithm: {algorithm}", True, YELLOW)
            self.screen.blit(text, (10, 40))
        
        # Controls
        small_font = pygame.font.Font(None, 20)
        controls = [
            "SPACE: Play/Pause",
            "LEFT/RIGHT: Step frame",
            "R: Restart",
            "Q: Quit"
        ]
        
        y_offset = SCREEN_HEIGHT - 100
        for control in controls:
            text = small_font.render(control, True, WHITE)
            self.screen.blit(text, (10, y_offset))
            y_offset += 25

class PyrusVisualizer:
    """Main visualizer class"""
    
    def __init__(self, log_dir, algorithm_name=""):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Pyrus2D Visualizer")
        self.clock = pygame.time.Clock()
        
        self.parser = LogParser(log_dir)
        self.renderer = FieldRenderer(self.screen)
        self.algorithm_name = algorithm_name
        
        self.current_frame = 0
        self.playing = False
        self.running = True
    
    def handle_events(self):
        """Handle user input"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.playing = not self.playing
                
                elif event.key == pygame.K_LEFT:
                    self.current_frame = max(0, self.current_frame - 1)
                
                elif event.key == pygame.K_RIGHT:
                    self.current_frame = min(self.parser.get_total_frames() - 1, 
                                            self.current_frame + 1)
                
                elif event.key == pygame.K_r:
                    self.current_frame = 0
                
                elif event.key == pygame.K_q:
                    self.running = False
    
    def update(self):
        """Update simulation state"""
        if self.playing:
            self.current_frame += 1
            if self.current_frame >= self.parser.get_total_frames():
                self.current_frame = 0  # Loop
    
    def render(self):
        """Render current frame"""
        frame = self.parser.get_frame(self.current_frame)
        
        if frame:
            # Draw field
            self.renderer.draw_field()
            
            # Draw players
            for player in frame['players']:
                self.renderer.draw_player(player)
            
            # Draw ball
            self.renderer.draw_ball(frame['ball'])
            
            # Draw info
            self.renderer.draw_info(self.current_frame, 
                                   self.parser.get_total_frames(),
                                   self.algorithm_name)
        
        pygame.display.flip()
    
    def run(self):
        """Main loop"""
        if not self.parser.parse_logs():
            print("Failed to parse logs!")
            return
        
        print("\nControls:")
        print("  SPACE: Play/Pause")
        print("  LEFT/RIGHT: Step frame")
        print("  R: Restart")
        print("  Q: Quit")
        print("\nStarting visualizer...")
        
        while self.running:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(FPS)
        
        pygame.quit()

def main():
    if len(sys.argv) > 1:
        log_dir = sys.argv[1]
        algorithm = sys.argv[2] if len(sys.argv) > 2 else ""
    else:
        # Default to latest log
        logs_dir = Path("logs")
        if logs_dir.exists():
            log_dirs = sorted([d for d in logs_dir.iterdir() if d.is_dir()])
            if log_dirs:
                log_dir = log_dirs[-1]
                algorithm = "Latest Run"
            else:
                print("No log directories found in logs/")
                print("Usage: python pyrus_visualizer.py <log_directory> [algorithm_name]")
                return
        else:
            print("logs/ directory not found")
            print("Usage: python pyrus_visualizer.py <log_directory> [algorithm_name]")
            return
    
    print(f"Pyrus2D Visualizer")
    print(f"Log directory: {log_dir}")
    print(f"Algorithm: {algorithm}")
    
    viz = PyrusVisualizer(log_dir, algorithm)
    viz.run()

if __name__ == "__main__":
    main()
