#!/usr/bin/env python3

from controller import Robot
import math

class NAOShootController:
    def __init__(self):
        # Initialize the robot
        self.robot = Robot()
        self.timestep = int(self.robot.getBasicTimeStep())
        
        # Joint names extracted from the motion file (in order)
        self.joint_names = [
            'LShoulderPitch', 'LShoulderRoll', 'LElbowYaw', 'LElbowRoll',
            'LHipYawPitch', 'LHipRoll', 'LHipPitch', 'LKneePitch', 
            'LAnklePitch', 'LAnkleRoll',
            'RHipYawPitch', 'RHipRoll', 'RHipPitch', 'RKneePitch', 
            'RAnklePitch', 'RAnkleRoll',
            'RShoulderPitch', 'RShoulderRoll', 'RElbowYaw', 'RElbowRoll'
        ]
        
        # Get joint motors and sensors
        self.motors = {}
        self.sensors = {}
        for joint_name in self.joint_names:
            motor = self.robot.getDevice(joint_name)
            sensor = self.robot.getDevice(joint_name + "S")  # Position sensor
            if motor is not None:
                self.motors[joint_name] = motor
                print(f"✓ Found joint motor: {joint_name}")
            else:
                print(f"✗ Joint motor not found: {joint_name}")
            
            if sensor is not None:
                self.sensors[joint_name] = sensor
                sensor.enable(self.timestep)
                print(f"✓ Found joint sensor: {joint_name}S")
            else:
                print(f"✗ Joint sensor not found: {joint_name}S")
        
        # Extract keyframes from the motion file
        self.keyframes = self.extract_keyframes()
    
    def set_dynamic_velocity(self, keyframe_name, duration):
        """Dynamically set joint velocities based on keyframe name and duration"""
        # Base speed mapping (speed is inversely proportional to time)
        base_speed = 1.0
        
        # Adjust speed based on duration: shorter time = faster speed, longer time = slower speed
        speed_factor = base_speed / max(duration, 0.1)  # Avoid division by zero
        
        # Velocity strategy for different keyframes
        if keyframe_name == '快速前踢':
            # Kicking action requires high speed
            kick_speed = min(speed_factor * 3.0, 20.0)  # Max cap 6.0
            support_speed = min(speed_factor * 1.5, 2.0)  # Support leg remains relatively stable
            arm_speed = min(speed_factor * 1.0, 1.5)
            
            # Set kicking leg to high speed
            for j in ["LHipPitch","LKneePitch","LAnklePitch","LHipRoll","LAnkleRoll"]:
                if j in self.motors: 
                    self.motors[j].setVelocity(kick_speed)
                    
        elif keyframe_name in ['重心转移', '右倾斜']:
            # Weight transfer should be stable but not too slow
            support_speed = min(speed_factor * 1.2, 1.8)
            arm_speed = min(speed_factor * 0.8, 1.2)
            
        elif keyframe_name in ['准备姿势', '恢复站立']:
            # Preparation and recovery are relatively slow
            support_speed = min(speed_factor * 0.8, 1.2)
            arm_speed = min(speed_factor * 0.6, 1.0)
            
        else:
            # Default speed
            support_speed = min(speed_factor * 1.0, 1.5)
            arm_speed = min(speed_factor * 0.8, 1.2)
        
        # Set support joint velocities
        support_joints = ["LHipRoll","LHipPitch","LKneePitch","LAnklePitch","LAnkleRoll",
                          "RHipRoll","RHipPitch","RKneePitch","RAnklePitch","RAnkleRoll",
                          "LHipYawPitch","RHipYawPitch"]
        arm_joints = ["LShoulderPitch","LShoulderRoll","LElbowYaw","LElbowRoll",
                      "RShoulderPitch","RShoulderRoll","RElbowYaw","RElbowRoll"]
        
        # If not the fast kick keyframe, set all joint groups
        if keyframe_name != '快速前踢':
            for j in support_joints:
                if j in self.motors:
                    self.motors[j].setVelocity(support_speed)
                
        for j in arm_joints:
            if j in self.motors:
                self.motors[j].setVelocity(arm_speed)
        
        print(f"  Velocity set - keyframe: {keyframe_name}, duration: {duration}s")
        if keyframe_name == '快速前踢':
            print(f"    Kicking leg velocity: {kick_speed:.2f}, support leg velocity: {support_speed:.2f}, arm velocity: {arm_speed:.2f}")
        else:
            print(f"    Support velocity: {support_speed:.2f}, arm velocity: {arm_speed:.2f}")
    
    def get_current_joint_positions(self):
        """Read current positions of all joints"""
        positions = {}
        for joint_name in self.joint_names:
            if joint_name in self.sensors:
                positions[joint_name] = self.sensors[joint_name].getValue()
        return positions
    
    def print_joint_positions(self, stage_name):
        """Print current joint positions"""
        print(f"\n=== {stage_name} - Joint position readings ===")
        positions = self.get_current_joint_positions()
        for joint_name, position in positions.items():
            print(f"  {joint_name}: {position:.4f}")
        print("=" * 40)
    
    def check_position_reached(self, target_positions, tolerance=0.1):
        """Check whether the target positions have been reached"""
        current_positions = self.get_current_joint_positions()
        
        for joint_name, target in target_positions.items():
            if joint_name in current_positions:
                current = current_positions[joint_name]
                diff = abs(current - target)
                if diff > tolerance:
                    return False, joint_name, current, target
        return True, None, None, None
    
    def wait_for_position_completion(self, target_positions, max_wait_time=5.0, tolerance=0.1):
        """Wait for joints to reach target positions"""
        print("  Waiting for joints to reach target positions...")
        start_time = self.robot.getTime()
        
        while True:
            # Check whether targets are reached
            reached, failed_joint, current_pos, target_pos = self.check_position_reached(target_positions, tolerance)
            
            if reached:
                print("  ✓ All joints reached target positions")
                return True
            
            # Check for timeout
            elapsed_time = self.robot.getTime() - start_time
            if elapsed_time > max_wait_time:
                print(f"  ✗ Timeout! Joint {failed_joint} failed to reach target position")
                print(f"    Current position: {current_pos:.4f}, target position: {target_pos:.4f}")
                return False
            
            # Continue simulation
            if self.robot.step(self.timestep) == -1:
                return False
        
    def extract_keyframes(self):
        """Extract key shooting keyframes from the motion file"""
        # Select keyframes based on motion file analysis
        keyframes = []
        
        # Frame 1: Initial pose (Pose1)
        keyframes.append({
            'name': '准备姿势a',
            'duration': 0.1,
            'positions': {
                'LShoulderPitch': 2.085, 'LShoulderRoll': 0.349, 'LElbowYaw': -1.396, 'LElbowRoll': -1.396,
                'LHipYawPitch': 0, 'LHipRoll': 0, 'LHipPitch': 0, 'LKneePitch': 0.2, 
                'LAnklePitch': -0.1, 'LAnkleRoll': 0,
                'RHipYawPitch': 0, 'RHipRoll': 0, 'RHipPitch': 0, 'RKneePitch': 0.2, 
                'RAnklePitch': -0.1, 'RAnkleRoll': 0,
                'RShoulderPitch': 2.085, 'RShoulderRoll': -0.349, 'RElbowYaw': 1.396, 'RElbowRoll': 1.396
            }
        })
        
        keyframes.append({
            'name': '准备姿势b',
            'duration': 1.0,
            'positions': {
                'LShoulderPitch': 2.085, 'LShoulderRoll': 0.349, 'LElbowYaw': -1.396, 'LElbowRoll': -1.396,
                'LHipYawPitch': 0, 'LHipRoll': 0, 'LHipPitch': -0.1, 'LKneePitch': 0.8, 
                'LAnklePitch': -0.5, 'LAnkleRoll': 0,
                'RHipYawPitch': 0, 'RHipRoll': 0, 'RHipPitch': -0.1, 'RKneePitch': 0.8, 
                'RAnklePitch': -0.5, 'RAnkleRoll': 0,
                'RShoulderPitch': 2.085, 'RShoulderRoll': -0.349, 'RElbowYaw': 1.396, 'RElbowRoll': 1.396
            }
        })
        
        # Frame 22: Start of weight transfer (Pose22)
        keyframes.append({
            'name': '重心转移',
            'duration': 0.5,
            'positions': {
                'LShoulderPitch': 2.085, 'LShoulderRoll': 0.349, 'LElbowYaw': -1.396, 'LElbowRoll': -1.396,
                'LHipYawPitch': 0, 'LHipRoll': 0.021, 'LHipPitch': -0.538, 'LKneePitch': 1.031, 
                'LAnklePitch': -0.493, 'LAnkleRoll': -0.021,
                'RHipYawPitch': 0, 'RHipRoll': 0.021, 'RHipPitch': -0.54, 'RKneePitch': 1.034, 
                'RAnklePitch': -0.494, 'RAnkleRoll': -0.021,
                'RShoulderPitch': 2.085, 'RShoulderRoll': -0.349, 'RElbowYaw': 1.396, 'RElbowRoll': 1.396
            }
        })
        
        # Frame 38: Both legs tilt to the right
        keyframes.append({
            'name': '右倾斜',
            'duration': 0.3,
            'positions': {
                'LShoulderPitch': 2.085, 'LShoulderRoll': 0.349, 'LElbowYaw': -1.396, 'LElbowRoll': -1.396,
                'LHipYawPitch': 0, 'LHipRoll': 0.394, 'LHipPitch': -0.527, 'LKneePitch': 0.976, 
                'LAnklePitch': -0.449, 'LAnkleRoll': -0.394,
                'RHipYawPitch': 0, 'RHipRoll': 0.3, 'RHipPitch': -0.521, 'RKneePitch': 0.962, 
                'RAnklePitch': -0.441, 'RAnkleRoll': -0.388,
                'RShoulderPitch': 2.085, 'RShoulderRoll': -0.349, 'RElbowYaw': 1.396, 'RElbowRoll': 1.396
            }
        })
        
        # Frame 48: Start lifting the leg to build up power (Pose48)
        keyframes.append({
            'name': '抬腿蓄力',
            'duration': 0.3,
            'positions': {
                'LShoulderPitch': 2.085, 'LShoulderRoll': 0.349, 'LElbowYaw': -1.396, 'LElbowRoll': -1.396,
                'LHipYawPitch': 0, 'LHipRoll': 0.451, 'LHipPitch': -0.9, 'LKneePitch': 2,
                'RHipYawPitch': 0, 'RHipRoll': 0.3, 'RHipPitch': -0.7, 'RKneePitch': 1.1, 
                'RAnklePitch': -0.4, 'RAnkleRoll': -0.388,
                'RShoulderPitch': 2.085, 'RShoulderRoll': -0.349, 'RElbowYaw': 1.396, 'RElbowRoll': 1.396
            }
        })
        
        # Frame 65: Maximum right leg lift (Pose65)
        keyframes.append({
            'name': '最大抬腿',
            'duration': 1.5,
            'positions': {
                'LShoulderPitch': 1.3, 'LShoulderRoll': 0.349, 'LElbowYaw': -1.396, 'LElbowRoll': -1.396,
                'LHipYawPitch': 0.011, 'LHipRoll': 0.3, 'LHipPitch': -1.6, 'LKneePitch': 2.0 ,
                'LAnklePitch': -0.2, 'LAnkleRoll': -0.1,
                'RHipYawPitch': 0.011, 'RHipRoll': 0.33, 'RHipPitch': -1.2, 'RKneePitch': 0.966, 
                'RAnklePitch': -0.302, 'RAnkleRoll': -0.45,
                'RShoulderPitch': 2.085, 'RShoulderRoll': -0.349, 'RElbowYaw': 1.396, 'RElbowRoll': 0.5
            }
        })

        keyframes.append({
            'name': '快速前踢',
            'duration': 0.1,
            'positions': {
                'LShoulderPitch': 1.951, 'LShoulderRoll': 0.349, 'LElbowYaw': -1.396, 'LElbowRoll': -0.823,
                'LHipYawPitch': 0.011, 'LHipRoll': 0.3, 'LHipPitch': -1.6, 'LKneePitch': 0.0, 
                'LAnklePitch': 0.4, 'LAnkleRoll': -0.397761,
                'RHipYawPitch': 0.011, 'RHipRoll': 0.33, 'RHipPitch': -0.6, 'RKneePitch': 1.0, 
                'RAnklePitch': -0.5, 'RAnkleRoll': -0.45,
                'RShoulderPitch': 1.684, 'RShoulderRoll': -0.349, 'RElbowYaw': 1.396, 'RElbowRoll': 1.396
            }
        })
        

        # Frame 91: Recover standing
        keyframes.append({
            'name': '恢复站立',
            'duration': 1.5,
            'positions': {
                'LShoulderPitch': 2.085, 'LShoulderRoll': 0.349, 'LElbowYaw': -1.396, 'LElbowRoll': -1.396,
                'LHipYawPitch': 0, 'LHipRoll': 0.002, 'LHipPitch': -0.8, 'LKneePitch': 0.8, 
                'LAnklePitch': 0.0, 'LAnkleRoll': -0.002,
                'RHipYawPitch': 0, 'RHipRoll': 0.002, 'RHipPitch': -0.661, 'RKneePitch': 1.226, 
                'RAnklePitch': -0.565, 'RAnkleRoll': -0.25,
                'RShoulderPitch': 2.085, 'RShoulderRoll': -0.349, 'RElbowYaw': 1.396, 'RElbowRoll': 1.396
            }
        })
        
        keyframes.append({
            'name': '恢复站立',
            'duration': 0.5,
            'positions': {
                'LShoulderPitch': 2.085, 'LShoulderRoll': 0.349, 'LElbowYaw': -1.396, 'LElbowRoll': -1.396,
                'LHipYawPitch': 0, 'LHipRoll': 0.002, 'LHipPitch': -0.663, 'LKneePitch': 1.232, 
                'LAnklePitch': -0.568, 'LAnkleRoll': -0.002,
                'RHipYawPitch': 0, 'RHipRoll': 0.002, 'RHipPitch': -0.661, 'RKneePitch': 1.226, 
                'RAnklePitch': -0.565, 'RAnkleRoll': -0.002,
                'RShoulderPitch': 2.085, 'RShoulderRoll': -0.349, 'RElbowYaw': 1.396, 'RElbowRoll': 1.396
            }
        })
        
        return keyframes
    
    def set_pose(self, positions):
        """Set the robot pose"""
        for joint_name, angle in positions.items():
            if joint_name in self.motors:
                try:
                    self.motors[joint_name].setPosition(angle)
                except Exception as e:
                    print(f"Failed to set joint {joint_name}: {e}")
    
    def execute_keyframe(self, keyframe):
        """Execute a single keyframe"""
        print(f"\n=== Executing keyframe: {keyframe['name']} ===")
        
        # Set dynamic velocities based on the keyframe
        self.set_dynamic_velocity(keyframe['name'], keyframe['duration'])
        
        # Set target positions
        self.set_pose(keyframe['positions'])
        
        # Wait for joints to reach the target positions
        success = self.wait_for_position_completion(
            keyframe['positions'],
            max_wait_time=keyframe['duration'] + 2.0
        )
        
        if not success:
            print(f"Keyframe {keyframe['name']} execution failed")
            return False
        
        # Print joint positions after completion
        self.print_joint_positions(f"{keyframe['name']} After completion")
        
        return True
    
    def execute_shoot(self):
        """Execute the full shooting motion"""
        print("=== Starting shooting motion ===")
        print("Motion analysis: This is a left-foot shooting motion")
        print("- Transfer weight to the right leg for support")
        print("- Swing the left leg back to build up power")
        print("- Kick forward quickly with the left leg to shoot")
        print("- Recover and regain balance\n")
        
        # Print initial joint positions
        self.print_joint_positions("Initial state")
        
        for i, keyframe in enumerate(self.keyframes, 1):
            print(f"\nStep {i}/{len(self.keyframes)}: Preparing to execute {keyframe['name']}")
            
            if not self.execute_keyframe(keyframe):
                print("Motion interrupted")
                return False
            
            if keyframe['name'] == '快速前踢':
                continue
            else:
                # Extra stabilization time
                print("  Waiting for posture stabilization...")
                for _ in range(20):
                    if self.robot.step(self.timestep) == -1:
                        return False
            
            print(f"✓ Keyframe {keyframe['name']} executed successfully\n")
            
            print("=== Shooting motion completed ===")
        return True
    
    def run(self):
        """Main control loop"""
        print("NAO shooting controller started")
        print(f"Found {len(self.motors)} available joint motors")
        print(f"Found {len(self.sensors)} available joint sensors")
        
        # Wait for the robot to stabilize
        print("Waiting for the robot to stabilize...")
        for _ in range(200):
            if self.robot.step(self.timestep) == -1:
                return
        
        # Execute shooting motion
        self.execute_shoot()
        
        # Keep running
        print("Motion finished, keeping the controller running...")
        while self.robot.step(self.timestep) != -1:
            pass

# Entry point
if __name__ == "__main__":
    controller = NAOShootController()
    controller.run()
