# Contributing Guidelines

## Welcome Contributors! 👋

Thank you for contributing to the NAO6 Robot Soccer Team project. This guide will help you understand our development workflow, coding standards, and contribution process.

## Table of Contents
1. [Getting Started](#getting-started)
2. [Development Workflow](#development-workflow)
3. [Coding Standards](#coding-standards)
4. [Testing Guidelines](#testing-guidelines)
5. [Documentation](#documentation)
6. [Pull Request Process](#pull-request-process)
7. [Code Review Guidelines](#code-review-guidelines)

## Getting Started

### Prerequisites
- Python 3.8+
- Git
- Webots R2023b+
- Code editor (VS Code recommended)

### Setup
1. Fork the repository (if external contributor)
2. Clone your fork/the repository
3. Install dependencies: `pip install -r requirements.txt`
4. Create a feature branch from `develop`

## Development Workflow

### Branch Strategy

We use Git Flow with the following branches:
- `main` - Production-ready code (protected)
- `develop` - Integration branch for features
- `feature/wp[X]-description` - Feature development
- `bugfix/wp[X]-description` - Bug fixes
- `hotfix/description` - Critical fixes for main

### Workflow Steps

1. **Create Issue**
   - Describe the feature/bug
   - Assign to appropriate WP
   - Add labels and milestone

2. **Create Branch**
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/wp3-walking-controller
   ```

3. **Develop Feature**
   - Write code following standards
   - Add tests
   - Update documentation

4. **Commit Changes**
   ```bash
   git add .
   git commit -m "WP3: Implement omnidirectional walking"
   ```

5. **Push & Create PR**
   ```bash
   git push origin feature/wp3-walking-controller
   # Create PR on GitHub
   ```

## Coding Standards

### Python Style Guide

We follow PEP 8 with these specifications:

#### Formatting
- Line length: 100 characters max
- Indentation: 4 spaces (no tabs)
- Blank lines: 2 between classes, 1 between methods

#### Naming Conventions
```python
# Classes: PascalCase
class RobotController:
    pass

# Functions/Methods: snake_case
def calculate_trajectory():
    pass

# Constants: UPPER_SNAKE_CASE
MAX_SPEED = 0.5

# Private methods: leading underscore
def _internal_function():
    pass
```

#### File Organization
```python
"""
Module description

Author: Your Name
Date: October 2025
"""

# Standard library imports
import os
import sys

# Third-party imports
import numpy as np
import cv2

# Local imports
from src.utils import logger
from src.vision import BallDetector

# Constants
DEFAULT_THRESHOLD = 0.5

# Classes and functions
class YourClass:
    """Class description."""
    
    def __init__(self):
        """Initialize the class."""
        pass
```

### Documentation Standards

#### Docstrings (Google Style)
```python
def calculate_kick_power(distance: float, angle: float) -> float:
    """Calculate required kick power based on distance and angle.
    
    Args:
        distance: Distance to target in meters
        angle: Angle to target in radians
        
    Returns:
        Kick power value between 0.0 and 1.0
        
    Raises:
        ValueError: If distance is negative
        
    Example:
        >>> power = calculate_kick_power(2.5, 0.785)
        >>> print(f"Kick power: {power:.2f}")
    """
    if distance < 0:
        raise ValueError("Distance cannot be negative")
    
    # Implementation
    return min(distance / 5.0, 1.0)
```

#### Inline Comments
```python
# Use comments sparingly for complex logic
velocity = distance / time  # m/s

# Multi-line comments for complex sections
# This section implements the PID controller for balance.
# The controller uses feedback from the IMU to maintain
# the robot's center of mass over the support polygon.
```

### Type Hints

Use type hints for better code clarity:

```python
from typing import List, Tuple, Optional, Dict

def process_vision_data(
    image: np.ndarray,
    threshold: float = 0.5
) -> Tuple[Optional[Ball], List[Robot]]:
    """Process camera image to detect objects."""
    pass
```

## Testing Guidelines

### Test Structure

Tests mirror the source code structure:
```
tests/
├── test_wp3_guidance_control/
│   ├── test_motion_controller.py
│   └── test_balance.py
├── test_wp4_behavioral/
│   └── test_goalkeeper.py
└── integration_tests/
    └── test_full_system.py
```

### Writing Tests

```python
import pytest
from src.wp3_guidance_control import MotionController

class TestMotionController:
    """Test suite for MotionController."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.controller = MotionController()
    
    def test_forward_walk(self):
        """Test forward walking command."""
        # Arrange
        speed = 0.3
        
        # Act
        result = self.controller.walk_forward(speed)
        
        # Assert
        assert result.success
        assert abs(result.actual_speed - speed) < 0.05
    
    def test_invalid_speed_raises_error(self):
        """Test that invalid speed raises ValueError."""
        with pytest.raises(ValueError):
            self.controller.walk_forward(-0.5)
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_wp3_guidance_control/test_motion.py

# Run with coverage
pytest --cov=src --cov-report=html

# Run only marked tests
pytest -m "unit"
```

### Test Requirements
- Minimum 70% code coverage
- All new features must have tests
- Tests must pass before PR merge

## Documentation

### Code Documentation
- All public functions/classes need docstrings
- Complex algorithms need inline comments
- Update README.md for new features

### Project Documentation
- Update relevant docs in `docs/` folder
- Include examples in docstrings
- Keep API documentation current

### Commit Messages

Format:
```
WP[X]: Brief description (50 chars max)

Longer explanation if needed. Wrap at 72 characters.
Explain what and why, not how.

- Bullet points for multiple changes
- Another change

Fixes #123
```

Examples:
```
WP3: Add PID controller for balance

Implemented a PID controller to maintain robot balance
during walking. Uses IMU feedback to adjust ankle joints.

- Added PIDController class
- Integrated with MotionController
- Added unit tests

Fixes #45
```

## Pull Request Process

### Before Creating PR

1. **Update from develop**
   ```bash
   git checkout develop
   git pull
   git checkout your-branch
   git merge develop
   ```

2. **Run tests**
   ```bash
   pytest
   ```

3. **Check code style**
   ```bash
   flake8 src/
   black --check src/
   ```

4. **Update documentation**

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Work Package
WP[X]: [Package name]

## Changes Made
- List key changes
- Another change

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Tested in simulation
- [ ] No linting errors

## Documentation
- [ ] Code has docstrings
- [ ] README updated (if needed)
- [ ] API docs updated (if needed)

## Screenshots (if applicable)
Add screenshots or videos

## Related Issues
Closes #123
Related to #456
```

### After Creating PR

1. Request review from at least one team member
2. Address review comments
3. Keep PR updated with develop
4. Ensure CI passes

## Code Review Guidelines

### For Reviewers

#### What to Check
- ✅ Code follows style guide
- ✅ Tests are adequate
- ✅ Documentation is clear
- ✅ No obvious bugs
- ✅ Performance is acceptable
- ✅ Security considerations

#### How to Review
1. Read PR description and related issue
2. Check out branch locally if needed
3. Run tests
4. Review code changes
5. Leave constructive feedback
6. Approve or request changes

#### Feedback Examples

Good feedback:
```
"Consider using a dictionary here instead of multiple if statements. 
It would be more readable and efficient. Example:
```python
actions = {
    'walk': self.walk,
    'kick': self.kick,
    'turn': self.turn
}
action = actions.get(command, self.default_action)
```"

Poor feedback:
```
"This code is bad. Rewrite it."
```

### For Authors

- Respond to all comments
- Push fixes as new commits (don't force-push)
- Request re-review after changes
- Be open to suggestions
- Explain decisions when needed

## Work Package Responsibilities

### WP-Specific Guidelines

#### WP2 (Simulation)
- Ensure physics accuracy
- Document world configurations
- Optimize for performance

#### WP3 (Control)
- Focus on stability and safety
- Provide clear APIs
- Document control parameters

#### WP4 (Behavior)
- Keep behaviors modular
- Use state machines
- Document decision logic

#### WP5 (Implementation)
- Ensure hardware compatibility
- Document deployment process
- Handle edge cases

#### WP6 (Testing)
- Comprehensive test coverage
- Document test procedures
- Track performance metrics

## Questions or Problems?

- Check existing issues/PRs
- Ask in team chat
- Contact WP lead
- Consult with Bonolo (GitHub lead)

---

*Thank you for contributing to our project!* 🤖⚽
