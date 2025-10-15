"""
Trajectory Planner for NAO6 Robot

Plans paths and trajectories for robot movement avoiding obstacles.

Author: Team 1
Date: October 2025
"""

import numpy as np
from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class Waypoint:
    """Waypoint for trajectory."""
    x: float
    y: float
    theta: Optional[float] = None
    speed: float = 0.3


class TrajectoryPlanner:
    """
    Plans trajectories for robot navigation.
    
    Generates smooth paths between positions while avoiding
    obstacles and respecting robot dynamics.
    """
    
    def __init__(self):
        """Initialize trajectory planner."""
        # Field boundaries
        self.field_length = 9.0
        self.field_width = 6.0
        
        # Robot constraints
        self.max_speed = 0.5  # m/s
        self.max_acceleration = 1.0  # m/s^2
        self.min_turn_radius = 0.2  # meters
        
    def plan_path(self, start: Tuple[float, float],
                  goal: Tuple[float, float],
                  obstacles: List[Tuple[float, float]] = None) -> List[Waypoint]:
        """
        Plan path from start to goal avoiding obstacles.
        
        Args:
            start: Starting position (x, y)
            goal: Goal position (x, y)
            obstacles: List of obstacle positions
            
        Returns:
            List of waypoints forming the path
        """
        if obstacles is None:
            obstacles = []
            
        # Simple direct path if no obstacles
        if not self._path_blocked(start, goal, obstacles):
            return self._create_direct_path(start, goal)
            
        # Otherwise use simple obstacle avoidance
        return self._plan_with_obstacles(start, goal, obstacles)
    
    def _create_direct_path(self, start: Tuple[float, float],
                           goal: Tuple[float, float]) -> List[Waypoint]:
        """Create direct path between two points."""
        waypoints = []
        
        # Calculate distance and direction
        dx = goal[0] - start[0]
        dy = goal[1] - start[1]
        distance = np.sqrt(dx**2 + dy**2)
        
        if distance < 0.1:  # Already at goal
            return [Waypoint(goal[0], goal[1], speed=0.0)]
            
        # Create intermediate waypoints for smooth motion
        num_waypoints = max(2, int(distance / 0.5))  # Waypoint every 0.5m
        
        for i in range(num_waypoints + 1):
            t = i / num_waypoints
            x = start[0] + t * dx
            y = start[1] + t * dy
            
            # Vary speed - slow at start/end
            if i == 0 or i == num_waypoints:
                speed = 0.1
            else:
                speed = self.max_speed
                
            waypoints.append(Waypoint(x, y, speed=speed))
            
        return waypoints
    
    def _path_blocked(self, start: Tuple[float, float],
                     goal: Tuple[float, float],
                     obstacles: List[Tuple[float, float]]) -> bool:
        """Check if direct path is blocked by obstacles."""
        if not obstacles:
            return False
            
        for obstacle in obstacles:
            # Check if obstacle is near the direct path
            if self._point_near_line(obstacle, start, goal, threshold=0.5):
                return True
                
        return False
    
    def _point_near_line(self, point: Tuple[float, float],
                        line_start: Tuple[float, float],
                        line_end: Tuple[float, float],
                        threshold: float) -> bool:
        """Check if point is within threshold distance of line segment."""
        # Vector from start to end
        dx = line_end[0] - line_start[0]
        dy = line_end[1] - line_start[1]
        
        # Vector from start to point
        px = point[0] - line_start[0]
        py = point[1] - line_start[1]
        
        # Project point onto line
        line_length_sq = dx**2 + dy**2
        if line_length_sq == 0:
            # Start and end are same point
            dist = np.sqrt(px**2 + py**2)
        else:
            t = max(0, min(1, (px*dx + py*dy) / line_length_sq))
            projection_x = line_start[0] + t * dx
            projection_y = line_start[1] + t * dy
            
            # Distance from point to projection
            dist = np.sqrt((point[0] - projection_x)**2 + 
                          (point[1] - projection_y)**2)
            
        return dist < threshold
    
    def _plan_with_obstacles(self, start: Tuple[float, float],
                            goal: Tuple[float, float],
                            obstacles: List[Tuple[float, float]]) -> List[Waypoint]:
        """Plan path with simple obstacle avoidance."""
        waypoints = []
        
        # Find blocking obstacles
        blocking_obstacles = []
        for obstacle in obstacles:
            if self._point_near_line(obstacle, start, goal, threshold=0.5):
                blocking_obstacles.append(obstacle)
                
        if not blocking_obstacles:
            return self._create_direct_path(start, goal)
            
        # Simple avoidance: go around first obstacle
        obstacle = blocking_obstacles[0]
        
        # Calculate avoidance point (go to side of obstacle)
        dx = goal[0] - start[0]
        dy = goal[1] - start[1]
        
        # Perpendicular direction
        perp_x = -dy / np.sqrt(dx**2 + dy**2)
        perp_y = dx / np.sqrt(dx**2 + dy**2)
        
        # Avoidance waypoint (1m to the side)
        avoid_x = obstacle[0] + perp_x * 1.0
        avoid_y = obstacle[1] + perp_y * 1.0
        
        # Keep within field boundaries
        avoid_x = max(-self.field_length/2, min(self.field_length/2, avoid_x))
        avoid_y = max(-self.field_width/2, min(self.field_width/2, avoid_y))
        
        # Create path: start -> avoidance point -> goal
        waypoints.extend(self._create_direct_path(start, (avoid_x, avoid_y)))
        waypoints.extend(self._create_direct_path((avoid_x, avoid_y), goal)[1:])
        
        return waypoints
    
    def smooth_trajectory(self, waypoints: List[Waypoint]) -> List[Waypoint]:
        """
        Smooth trajectory for better robot motion.
        
        Args:
            waypoints: Original waypoints
            
        Returns:
            Smoothed waypoints
        """
        if len(waypoints) <= 2:
            return waypoints
            
        smoothed = [waypoints[0]]
        
        # Apply simple moving average
        window_size = 3
        for i in range(1, len(waypoints) - 1):
            start_idx = max(0, i - window_size // 2)
            end_idx = min(len(waypoints), i + window_size // 2 + 1)
            
            # Average position
            avg_x = np.mean([w.x for w in waypoints[start_idx:end_idx]])
            avg_y = np.mean([w.y for w in waypoints[start_idx:end_idx]])
            
            smoothed.append(Waypoint(avg_x, avg_y, speed=waypoints[i].speed))
            
        smoothed.append(waypoints[-1])
        
        return smoothed
