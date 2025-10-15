"""
Unit tests for motion control module.

Author: Team 1
Date: October 2025
"""

import pytest
import numpy as np
import sys
import os

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.wp3_guidance_control.motion_controller import MotionController, MotionCommand


class TestMotionController:
    """Test suite for MotionController class."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.controller = MotionController()
        
    def test_initialization(self):
        """Test controller initializes with correct defaults."""
        assert self.controller.current_command.vx == 0.0
        assert self.controller.current_command.vy == 0.0
        assert self.controller.current_command.vtheta == 0.0
        assert self.controller.is_walking is False
        
    def test_walk_forward(self):
        """Test forward walking command."""
        result = self.controller.walk(0.3, 0.0, 0.0)
        
        assert result is True
        assert self.controller.current_command.vx == 0.3
        assert self.controller.current_command.vy == 0.0
        assert self.controller.current_command.vtheta == 0.0
        assert self.controller.is_walking is True
        
    def test_walk_omnidirectional(self):
        """Test omnidirectional walking."""
        result = self.controller.walk(0.2, 0.1, 0.5)
        
        assert result is True
        assert self.controller.current_command.vx == 0.2
        assert self.controller.current_command.vy == 0.1
        assert self.controller.current_command.vtheta == 0.5
        
    def test_walk_speed_limits(self):
        """Test that speed limits are enforced."""
        # Test forward speed limit
        with pytest.raises(ValueError) as excinfo:
            self.controller.walk(0.6, 0.0, 0.0)
        assert "Forward velocity" in str(excinfo.value)
        
        # Test lateral speed limit
        with pytest.raises(ValueError) as excinfo:
            self.controller.walk(0.0, 0.4, 0.0)
        assert "Lateral velocity" in str(excinfo.value)
        
        # Test angular speed limit
        with pytest.raises(ValueError) as excinfo:
            self.controller.walk(0.0, 0.0, 1.5)
        assert "Angular velocity" in str(excinfo.value)
        
    def test_stop(self):
        """Test stopping motion."""
        # Start walking
        self.controller.walk(0.3, 0.1, 0.2)
        assert self.controller.is_walking is True
        
        # Stop
        result = self.controller.stop()
        
        assert result is True
        assert self.controller.current_command.vx == 0.0
        assert self.controller.current_command.vy == 0.0
        assert self.controller.current_command.vtheta == 0.0
        assert self.controller.is_walking is False
        
    def test_negative_velocities(self):
        """Test walking with negative velocities (backward/right/CW)."""
        result = self.controller.walk(-0.2, -0.1, -0.3)
        
        assert result is True
        assert self.controller.current_command.vx == -0.2
        assert self.controller.current_command.vy == -0.1
        assert self.controller.current_command.vtheta == -0.3
        
    def test_stand_posture(self):
        """Test transition to standing posture."""
        result = self.controller.stand()
        
        assert result is True
        assert self.controller.is_walking is False
        
    def test_sit_posture(self):
        """Test transition to sitting posture."""
        result = self.controller.sit()
        
        assert result is True
        assert self.controller.is_walking is False
        
    def test_odometry_reset(self):
        """Test odometry reset functionality."""
        # Get initial odometry
        x, y, theta = self.controller.get_odometry()
        assert x == 0.0
        assert y == 0.0
        assert theta == 0.0
        
        # Reset should work without error
        self.controller.reset_odometry()
        
        
class TestMotionCommand:
    """Test suite for MotionCommand dataclass."""
    
    def test_creation(self):
        """Test MotionCommand creation."""
        cmd = MotionCommand(0.1, 0.2, 0.3)
        
        assert cmd.vx == 0.1
        assert cmd.vy == 0.2
        assert cmd.vtheta == 0.3
        
    def test_zero_command(self):
        """Test zero motion command."""
        cmd = MotionCommand(0.0, 0.0, 0.0)
        
        assert cmd.vx == 0.0
        assert cmd.vy == 0.0
        assert cmd.vtheta == 0.0


@pytest.mark.parametrize("vx,vy,vtheta,expected", [
    (0.0, 0.0, 0.0, True),  # Stationary
    (0.5, 0.0, 0.0, True),  # Max forward
    (0.0, 0.3, 0.0, True),  # Max lateral
    (0.0, 0.0, 1.0, True),  # Max angular
    (0.3, 0.2, 0.5, True),  # Combined motion
])
def test_valid_motion_commands(vx, vy, vtheta, expected):
    """Test various valid motion commands."""
    controller = MotionController()
    result = controller.walk(vx, vy, vtheta)
    assert result == expected


@pytest.mark.parametrize("vx,vy,vtheta", [
    (0.6, 0.0, 0.0),   # Exceeds forward limit
    (0.0, 0.4, 0.0),   # Exceeds lateral limit
    (0.0, 0.0, 1.5),   # Exceeds angular limit
    (0.6, 0.4, 1.5),   # Exceeds all limits
])
def test_invalid_motion_commands(vx, vy, vtheta):
    """Test that invalid motion commands raise errors."""
    controller = MotionController()
    with pytest.raises(ValueError):
        controller.walk(vx, vy, vtheta)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
