from controller import Robot
import sys
import os

# project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
sys.path.insert(0, project_root)

from sidestepping_controller import SidesteppingController

robot = Robot()
timestep = int(robot.getBasicTimeStep())
dt = timestep / 1000.0

controller = SidesteppingController(robot)

# Configuration
MAX_STEPS = 10  
DIRECTION = 1.0  # 1.0 for left, -1.0 for right

# sidestepping
controller.start(direction=DIRECTION)

print("=" * 60)
print("WEBOTS SIDESTEP CONTROLLER INITIALIZED")
print("=" * 60)
print(f"Timestep: {timestep}ms ({dt:.4f}s)")
print(f"Direction: {'LEFT' if DIRECTION > 0 else 'RIGHT'}")
print(f"Max steps: {MAX_STEPS}")
print("=" * 60)

# Main control loop
loop_count = 0
last_print_time = 0.0

while robot.step(timestep) != -1:
    # Update controller
    joints = controller.update(dt)
    state = controller.get_state_info()
    
    # Calculate current time
    current_time = loop_count * dt
    
    # Print status every second
    if current_time - last_print_time >= 1.0:
        print(f"[{current_time:6.2f}s] "
              f"Steps: {state['step_count']:3d} | "
              f"Support: {state['support_foot']:5s} | "
              f"Progress: {state['cycle_progress']:5.1f}%")
        last_print_time = current_time
    
    loop_count += 1
    
    # Stop after reaching max steps
    if state['step_count'] >= MAX_STEPS:
        print("\n" + "=" * 60)
        print(f"COMPLETED {state['step_count']} STEPS")
        print(f"Total time: {current_time:.2f} seconds")
        print(f"Average time per step: {current_time/state['step_count']:.2f} seconds")
        print("=" * 60)
        
        controller.stop()
        break

# Final standing pose
print("\nReturning to standing pose...")
standing_pose = controller.get_standing_pose()
for _ in range(50):  # Hold for ~1.6 seconds
    robot.step(timestep)

print("Controller terminated successfully.")
