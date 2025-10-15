"""
Goalkeeper Behavior Module

Implements high-level goalkeeper decision making and positioning strategies.

Author: Team 1
Date: October 2025
"""

import math
import numpy as np
from typing import Dict, Optional, Tuple
from enum import Enum


class GoalkeeperState(Enum):
    """Goalkeeper behavioral states."""
    READY = "ready"
    TRACKING = "tracking"
    POSITIONING = "positioning"
    DIVING = "diving"
    RECOVERING = "recovering"
    CLEARING = "clearing"


class GoalkeeperBehavior:
    """
    High-level behavioral controller for goalkeeper robot.
    
    Manages positioning, ball tracking, and save decisions based on
    game state and ball trajectory prediction.
    """
    
    def __init__(self):
        """Initialize goalkeeper behavior."""
        self.state = GoalkeeperState.READY
        self.last_ball_position = None
        self.ball_velocity = np.array([0.0, 0.0])
        
        # Goal dimensions
        self.goal_width = 2.6  # meters
        self.goal_x = -4.5  # X position of goal line
        
        # Positioning parameters
        self.optimal_distance = 0.5  # meters from goal line
        self.reaction_distance = 2.0  # meters - distance to start diving
        
    def update(self, robot_position: Dict, robot_orientation: Dict,
               ball_position: Optional[Dict]) -> Dict:
        """
        Update goalkeeper behavior and return action.
        
        Args:
            robot_position: Robot position {'x': float, 'y': float, 'z': float}
            robot_orientation: Robot orientation {'roll': float, 'pitch': float, 'yaw': float}
            ball_position: Ball position {'x': float, 'y': float} or None
            
        Returns:
            Action dictionary:
            {
                'type': 'move'|'dive'|'stand'|'clear',
                'target': target position,
                'direction': dive direction
            }
        """
        # Update ball tracking
        self._update_ball_tracking(ball_position)
        
        # State machine logic
        if self.state == GoalkeeperState.READY:
            return self._handle_ready_state(robot_position)
            
        elif self.state == GoalkeeperState.TRACKING:
            return self._handle_tracking_state(robot_position, ball_position)
            
        elif self.state == GoalkeeperState.POSITIONING:
            return self._handle_positioning_state(robot_position, ball_position)
            
        elif self.state == GoalkeeperState.DIVING:
            return self._handle_diving_state()
            
        elif self.state == GoalkeeperState.RECOVERING:
            return self._handle_recovering_state()
            
        else:
            return {'type': 'stand'}
    
    def _update_ball_tracking(self, ball_position: Optional[Dict]):
        """Update ball velocity estimation."""
        if ball_position is not None:
            if self.last_ball_position is not None:
                # Simple velocity estimation
                dt = 0.1  # Assume 10Hz update
                dx = ball_position.get('x', 0) - self.last_ball_position.get('x', 0)
                dy = ball_position.get('y', 0) - self.last_ball_position.get('y', 0)
                
                # Low-pass filter for velocity
                alpha = 0.3
                self.ball_velocity = alpha * np.array([dx/dt, dy/dt]) + \
                                    (1-alpha) * self.ball_velocity
                
            self.last_ball_position = ball_position
    
    def _handle_ready_state(self, robot_position: Dict) -> Dict:
        """Handle ready state - position in center of goal."""
        target_x = self.goal_x + self.optimal_distance
        target_y = 0.0  # Center of goal
        
        # Check if in position
        distance = math.sqrt((robot_position['x'] - target_x)**2 + 
                           (robot_position['y'] - target_y)**2)
        
        if distance > 0.1:  # 10cm tolerance
            self.state = GoalkeeperState.POSITIONING
            return {
                'type': 'move',
                'target': {'x': target_x, 'y': target_y}
            }
        
        # In position, start tracking
        self.state = GoalkeeperState.TRACKING
        return {'type': 'stand'}
    
    def _handle_tracking_state(self, robot_position: Dict, 
                              ball_position: Optional[Dict]) -> Dict:
        """Handle tracking state - track ball and adjust position."""
        if ball_position is None:
            return {'type': 'stand'}
        
        # Check if ball is approaching
        if self._is_ball_approaching(ball_position):
            # Predict interception point
            intercept_y = self._predict_interception(ball_position)
            
            # Check if diving is needed
            if abs(intercept_y) > 0.8:  # Ball going to side of goal
                if abs(intercept_y) < self.goal_width / 2:  # Within goal
                    self.state = GoalkeeperState.DIVING
                    return {
                        'type': 'dive',
                        'direction': 'left' if intercept_y > 0 else 'right'
                    }
            else:
                # Move to intercept
                target_x = self.goal_x + self.optimal_distance
                target_y = max(-self.goal_width/2 + 0.3, 
                             min(self.goal_width/2 - 0.3, intercept_y))
                
                return {
                    'type': 'move',
                    'target': {'x': target_x, 'y': target_y}
                }
        
        # Track ball position laterally
        target_y = self._calculate_lateral_position(ball_position)
        target_x = self.goal_x + self.optimal_distance
        
        return {
            'type': 'move',
            'target': {'x': target_x, 'y': target_y}
        }
    
    def _handle_positioning_state(self, robot_position: Dict,
                                 ball_position: Optional[Dict]) -> Dict:
        """Handle positioning state - move to optimal position."""
        # Calculate optimal position based on ball
        if ball_position:
            target_y = self._calculate_lateral_position(ball_position)
        else:
            target_y = 0.0
            
        target_x = self.goal_x + self.optimal_distance
        
        # Check if reached position
        distance = math.sqrt((robot_position['x'] - target_x)**2 + 
                           (robot_position['y'] - target_y)**2)
        
        if distance < 0.1:  # In position
            self.state = GoalkeeperState.TRACKING
            return {'type': 'stand'}
        
        return {
            'type': 'move',
            'target': {'x': target_x, 'y': target_y}
        }
    
    def _handle_diving_state(self) -> Dict:
        """Handle diving state - execute dive."""
        # After diving, go to recovery
        self.state = GoalkeeperState.RECOVERING
        return {'type': 'stand'}  # Placeholder - dive already initiated
    
    def _handle_recovering_state(self) -> Dict:
        """Handle recovery state - stand up and reposition."""
        # Simple recovery - return to ready state
        self.state = GoalkeeperState.READY
        return {'type': 'stand'}
    
    def _is_ball_approaching(self, ball_position: Dict) -> bool:
        """Check if ball is approaching the goal."""
        if ball_position is None:
            return False
            
        # Check if ball is moving toward goal
        ball_x = ball_position.get('x', 0)
        
        # Ball must be in our half and moving toward goal
        if ball_x > 0:  # Ball in opponent half
            return False
            
        # Check velocity toward goal
        return self.ball_velocity[0] < -0.5  # Moving toward our goal
    
    def _predict_interception(self, ball_position: Dict) -> float:
        """
        Predict where ball will cross goal line.
        
        Args:
            ball_position: Current ball position
            
        Returns:
            Predicted Y coordinate at goal line
        """
        if abs(self.ball_velocity[0]) < 0.1:  # Ball not moving much in X
            return ball_position.get('y', 0)
            
        # Time to reach goal line
        ball_x = ball_position.get('x', 0)
        time_to_goal = (self.goal_x - ball_x) / self.ball_velocity[0]
        
        if time_to_goal < 0:  # Ball moving away
            return 0.0
            
        # Predict Y position
        ball_y = ball_position.get('y', 0)
        predicted_y = ball_y + self.ball_velocity[1] * time_to_goal
        
        return predicted_y
    
    def _calculate_lateral_position(self, ball_position: Dict) -> float:
        """
        Calculate optimal lateral position based on ball position.
        
        Args:
            ball_position: Current ball position
            
        Returns:
            Target Y coordinate for goalkeeper
        """
        if ball_position is None:
            return 0.0
            
        ball_x = ball_position.get('x', 0)
        ball_y = ball_position.get('y', 0)
        
        # Calculate angle from goal center to ball
        dx = ball_x - self.goal_x
        
        if abs(dx) < 0.1:  # Ball very close
            return ball_y
            
        # Position proportionally between center and ball
        ratio = min(1.0, max(0.0, (4.5 + ball_x) / 4.5))
        target_y = ball_y * ratio
        
        # Limit to goal area
        max_y = self.goal_width / 2 - 0.3  # Leave margin
        target_y = max(-max_y, min(max_y, target_y))
        
        return target_y
