#!/usr/bin/env python3
"""
NAO Robot Soccer Demo Controller
整合转向、行走和射门功能的完整足球演示

功能：
1. 使用Supervisor API获取球的位置
2. 计算转向角度并执行转向
3. 在转向前放下手臂
4. 行走到球的位置
5. 执行射门动作
"""

import math
import os
import sys
import json
from controller import Robot, Supervisor, Motion
from scipy.interpolate import make_interp_spline
import pandas as pd
from typing import Dict, Any, Optional, Tuple


# ==================== Configuration ====================
MOTION_PATHS = {
    "L40":  "../../motions/TurnLeft40.motion",
    "L60":  "../../motions/TurnLeft60.motion", 
    "L180": "../../motions/TurnLeft180.motion",
    "R40":  "../../motions/TurnRight40.motion",
    "R60":  "../../motions/TurnRight60.motion",
}

STOP_THRESHOLD_DEG = 15.0
MAX_TURN_STEPS = 30
RESET_DURATION_S = 0.8

# 手臂放下姿势
ARM_DOWN_POSE = {
    'LShoulderPitch': 2.085, 'LShoulderRoll': 0.349, 'LElbowYaw': -1.396, 'LElbowRoll': -1.396,
    'RShoulderPitch': 2.085, 'RShoulderRoll': -0.349, 'RElbowYaw': 1.396, 'RElbowRoll': 1.396,
}

# PID重置姿势
RESET_POSE = {
    'LShoulderPitch': 2.085, 'LShoulderRoll': 0.349, 'LElbowYaw': -1.396, 'LElbowRoll': -1.396,
    'RShoulderPitch': 2.085, 'RShoulderRoll': -0.349, 'RElbowYaw': 1.396, 'RElbowRoll': 1.396,
    "LHipRoll":  +0.07, "RHipRoll":  -0.07,
    "LKneePitch": 0.18, "RKneePitch": 0.18,
    "LAnkleRoll": -0.035, "RAnkleRoll": +0.035,
    "LAnklePitch": -0.10, "RAnklePitch": -0.10,
    "LHipPitch":  0.00, "RHipPitch":  0.00
}

RESET_JOINTS = list(RESET_POSE.keys())

# 关节名称
JOINT_NAMES_L = ["LHipYawPitch", "LHipRoll", "LHipPitch", "LKneePitch", "LAnklePitch", "LAnkleRoll"]
JOINT_NAMES_R = ["RHipYawPitch", "RHipRoll", "RHipPitch", "RKneePitch", "RAnklePitch", "RAnkleRoll"]

# PID参数
PID_KP = 0.60
PID_KI = 0.00
PID_KD = 0.10
PID_MAX_STEP_RAD = 0.05


# ==================== Utility Functions ====================
def clamp(x, lo, hi):
    return max(lo, min(hi, x))

def wrap_to_pi(a: float) -> float:
    """Normalize to [-pi, pi]."""
    while a > math.pi:
        a -= 2 * math.pi
    while a < -math.pi:
        a += 2 * math.pi
    return a

def calculate_distance(pos1, pos2):
    """计算两点间的欧几里得距离"""
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(pos1, pos2)))

def calculate_angle(from_pos, to_pos):
    """计算从from_pos指向to_pos的角度（弧度）"""
    dx = to_pos[0] - from_pos[0]
    dy = to_pos[1] - from_pos[1]  # 假设Y是垂直轴
    return math.atan2(dy, dx)


# ==================== Joint PID Reset Class ====================
class JointPIDReset:
    def __init__(self, robot: Robot, timestep_ms: int, motor_names):
        self.robot = robot
        self.timestep_ms = timestep_ms
        self.dt = timestep_ms / 1000.0
        
        self.motors = {}
        self.sensors = {}
        self.limits = {}
        self.available = []
        
        for name in motor_names:
            m = robot.getDevice(name)
            if not m:
                print(f"[RESET] WARNING: motor not found: {name} (skipped)")
                continue
                
            ps = m.getPositionSensor()
            if not ps:
                print(f"[RESET] WARNING: PositionSensor not found for: {name} (skipped)")
                continue
                
            ps.enable(timestep_ms)
            self.motors[name] = m
            self.sensors[name] = ps
            self.available.append(name)
            
            try:
                self.limits[name] = (m.getMinPosition(), m.getMaxPosition())
            except Exception:
                self.limits[name] = (-float("inf"), float("inf"))
        
        if not self.available:
            raise RuntimeError("[RESET] No joints available for PID reset.")
            
        self.i_term = {n: 0.0 for n in self.available}
        self.prev_err = {n: 0.0 for n in self.available}
        self.Kp = PID_KP
        self.Ki = PID_KI
        self.Kd = PID_KD
        self.max_step = PID_MAX_STEP_RAD
        self.i_limit = 0.4

    def reset_integrators(self):
        for k in self.available:
            self.i_term[k] = 0.0
            self.prev_err[k] = 0.0

    def pid_reset_pose(self, pose_targets: dict, duration_s=0.8, tol_rad=0.04):
        steps = int(duration_s / self.dt)
        cur_target = {}
        for j in self.available:
            if j in pose_targets:
                cur_target[j] = self.sensors[j].getValue()

        for _ in range(steps):
            if self.robot.step(self.timestep_ms) == -1:
                break

            all_ok = True
            for j in self.available:
                if j not in pose_targets:
                    continue

                tgt = pose_targets[j]
                cur = self.sensors[j].getValue()
                err = tgt - cur

                if abs(err) > tol_rad:
                    all_ok = False

                derr = (err - self.prev_err[j]) / self.dt
                self.prev_err[j] = err

                self.i_term[j] += err * self.dt
                self.i_term[j] = clamp(self.i_term[j], -self.i_limit, self.i_limit)

                u = self.Kp * err + self.Ki * self.i_term[j] + self.Kd * derr
                delta = clamp(u, -self.max_step, self.max_step)
                cur_target[j] += delta

                mn, mx = self.limits[j]
                cur_target[j] = clamp(cur_target[j], mn, mx)
                self.motors[j].setPosition(cur_target[j])

            if all_ok:
                break


# ==================== Main Demo Controller Class ====================
class NAOSoccerDemoController:
    def __init__(self):
        # 初始化Supervisor
        self.supervisor = Supervisor()
        self.timestep = int(self.supervisor.getBasicTimeStep())
        print(f"[INIT] 时间步长: {self.timestep}ms")
        
        # 获取场景中的节点
        self.robot_node = self.supervisor.getSelf()
        self.ball_node = self.supervisor.getFromDef("ball")  # 假设球节点定义为BALL
        
        if self.ball_node is None:
            print("[ERROR] 未找到球节点，请确保球节点定义为DEF BALL")
            
        # 传感器设置
        self._setup_sensors()
        
        # Motion文件加载
        self._load_motions()
        
        # 关节控制
        self._setup_joints()
        
        # PID重置
        self.pid_reset = JointPIDReset(self.supervisor, self.timestep, RESET_JOINTS)
        
        # 行走相关设置
        self._setup_walking()
        
        # 射门相关设置  
        self._setup_shooting()
        
        # 状态机
        self.state = "idle"  # idle -> arm_down -> turn -> walk -> shoot -> done
        
    def _setup_sensors(self):
        """设置传感器"""
        # IMU
        for name in ["InertialUnit", "inertial unit", "imu", "IMU"]:
            try:
                self.imu = self.supervisor.getDevice(name)
                if self.imu:
                    self.imu.enable(self.timestep)
                    print(f"[IMU] 使用设备: {name}")
                    break
            except:
                continue
        else:
            raise RuntimeError("未找到IMU设备")
            
        # GPS
        try:
            self.gps = self.supervisor.getDevice("gps")
            if self.gps:
                self.gps.enable(self.timestep)
                print("[GPS] GPS设备已启用")
        except:
            self.gps = None
            print("[WARNING] 未找到GPS设备")
            
    def _load_motions(self):
        """加载motion文件"""
        self.motions = {}
        for key, path in MOTION_PATHS.items():
            if os.path.exists(path):
                self.motions[key] = Motion(path)
                print(f"[MOTION] 已加载 {key}: {path}")
            else:
                print(f"[WARNING] Motion文件未找到: {path}")
                
    def _setup_joints(self):
        """设置关节电机"""
        self.joint_names = [
            'LShoulderPitch', 'LShoulderRoll', 'LElbowYaw', 'LElbowRoll',
            'LHipYawPitch', 'LHipRoll', 'LHipPitch', 'LKneePitch', 
            'LAnklePitch', 'LAnkleRoll',
            'RHipYawPitch', 'RHipRoll', 'RHipPitch', 'RKneePitch', 
            'RAnklePitch', 'RAnkleRoll',
            'RShoulderPitch', 'RShoulderRoll', 'RElbowYaw', 'RElbowRoll'
        ]
        
        self.motors = {}
        self.sensors = {}
        
        for joint_name in self.joint_names:
            motor = self.supervisor.getDevice(joint_name)
            sensor = self.supervisor.getDevice(joint_name + "S")
            
            if motor:
                self.motors[joint_name] = motor
                motor.setVelocity(motor.getMaxVelocity() * 0.9)
                
            if sensor:
                self.sensors[joint_name] = sensor
                sensor.enable(self.timestep)

    def _load_gait_csv(self, filepath: str) -> Dict[str, Any]:
        """
        Load a gait CSV file and build cubic spline models for each joint.
        
        CSV must contain:
          frac_step, LHipYawPitch, LHipRoll, ... , RAnkleRoll
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Gait CSV file not found: {filepath}")
            
        df = pd.read_csv(filepath)
        if "frac_step" not in df.columns:
            raise ValueError(f"CSV {filepath} must contain a 'frac_step' column.")

        frac = df["frac_step"].to_numpy()
        step_min = float(frac[0])
        step_max = float(frac[-1])

        models: Dict[str, Any] = {}
        for col in df.columns:
            if col == "frac_step":
                continue
            y = df[col].to_numpy()
            # cubic spline interpolation
            models[col] = make_interp_spline(frac, y, k=3)

        return {
            "models": models,
            "step_min": step_min,
            "step_max": step_max,
        }

    def _setup_walking(self):
        """设置行走相关参数"""
        self.f0 = 1.0  # 步频
        
        # 行走步态文件路径
        controller_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(controller_dir, "..", ".."))
        gait_dir = os.path.join(project_root, "gait_templates")
        
        # 加载步态CSV文件
        try:
            self.start_gait = self._load_gait_csv(os.path.join(gait_dir, "motor_patterns_smooth_start.csv"))
            self.walk_gait = self._load_gait_csv(os.path.join(gait_dir, "motor_patterns_continous_gait.csv"))
            self.stop_gait = self._load_gait_csv(os.path.join(gait_dir, "motor_patterns_smooth_stop.csv"))
            print("[WALKING] 步态CSV文件加载成功")
        except Exception as e:
            print(f"[WALKING] 警告: 无法加载步态CSV文件: {e}")
            self.start_gait = None
            self.walk_gait = None
            self.stop_gait = None
        
        # 步态参数
        if self.walk_gait:
            self.walk_cycle_len = self.walk_gait["step_max"] - self.walk_gait["step_min"]
        else:
            self.walk_cycle_len = 1.0
        
        # 行走状态变量
        self.walk_state = "idle"  # start -> walk -> stop -> done
        self.start_phase = None
        self.walk_phase = 0.0
        self.stop_phase = None
        self.step_counter = 0
        self.prev_cycle_index = 0
        self.initial_pos = None
        self.target_distance = None
        self.stop_distance_offset = 0.05
        self.current_distance = 0.0
        
        # 中性姿势
        self.neutral = {
            'HipYawPitch': 0.0,
            'HipRoll': 0.0,
            'HipPitch': -0.5,
            'KneePitch': 1.0,
            'AnklePitch': -0.5,
            'AnkleRoll': 0.0,
        }
        
    def _setup_shooting(self):
        """设置射门关键帧"""
        self.shooting_keyframes = [
            
            {
            'name': '重心转移',
            'duration': 1.0,
            'positions': {
                'LShoulderPitch': 2.085, 'LShoulderRoll': 0.349, 'LElbowYaw': -1.396, 'LElbowRoll': -1.396,
                'LHipYawPitch': 0, 'LHipRoll': 0.021, 'LHipPitch': -0.538, 'LKneePitch': 1.031, 
                'LAnklePitch': -0.493, 'LAnkleRoll': -0.021,
                'RHipYawPitch': 0, 'RHipRoll': 0.021, 'RHipPitch': -0.54, 'RKneePitch': 1.034, 
                'RAnklePitch': -0.494, 'RAnkleRoll': -0.021,
                'RShoulderPitch': 2.085, 'RShoulderRoll': -0.349, 'RElbowYaw': 1.396, 'RElbowRoll': 1.396
            }
        },
            {
            'name': '右倾斜',
            'duration': 1.0,
            'positions': {
                'LShoulderPitch': 2.085, 'LShoulderRoll': 0.349, 'LElbowYaw': -1.396, 'LElbowRoll': -1.396,
                'LHipYawPitch': 0, 'LHipRoll': 0.394, 'LHipPitch': -0.527, 'LKneePitch': 0.976, 
                'LAnklePitch': -0.449, 'LAnkleRoll': -0.394,
                'RHipYawPitch': 0, 'RHipRoll': 0.3, 'RHipPitch': -0.521, 'RKneePitch': 0.962, 
                'RAnklePitch': -0.441, 'RAnkleRoll': -0.388,
                'RShoulderPitch': 2.085, 'RShoulderRoll': -0.349, 'RElbowYaw': 1.396, 'RElbowRoll': 1.396
            }
        },
            {
            'name': '抬腿蓄力',
            'duration': 1.0,
            'positions': {
                'LShoulderPitch': 2.085, 'LShoulderRoll': 0.349, 'LElbowYaw': -1.396, 'LElbowRoll': -1.396,
                'LHipYawPitch': 0, 'LHipRoll': 0.451, 'LHipPitch': -0.9, 'LKneePitch': 2,
                'RHipYawPitch': 0, 'RHipRoll': 0.3, 'RHipPitch': -0.7, 'RKneePitch': 1.1, 
                'RAnklePitch': -0.4, 'RAnkleRoll': -0.388,
                'RShoulderPitch': 2.085, 'RShoulderRoll': -0.349, 'RElbowYaw': 1.396, 'RElbowRoll': 1.396
            }
        },
        {
            'name': '最大抬腿',
            'duration': 1.0,
            'positions': {
                'LShoulderPitch': 1.3, 'LShoulderRoll': 0.349, 'LElbowYaw': -1.396, 'LElbowRoll': -1.396,
                'LHipYawPitch': 0.011, 'LHipRoll': 0.3, 'LHipPitch': -1.6, 'LKneePitch': 2.0 ,
                'LAnklePitch': -0.2, 'LAnkleRoll': -0.1,
                'RHipYawPitch': 0.011, 'RHipRoll': 0.33, 'RHipPitch': -1.2, 'RKneePitch': 0.966, 
                'RAnklePitch': -0.302, 'RAnkleRoll': -0.45,
                'RShoulderPitch': 2.085, 'RShoulderRoll': -0.349, 'RElbowYaw': 1.396, 'RElbowRoll': 0.5
            }
        },
        {
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
        },
        {
            'name': '恢复站立a',
            'duration': 1.5,
            'positions': {
                'LShoulderPitch': 2.085, 'LShoulderRoll': 0.349, 'LElbowYaw': -1.396, 'LElbowRoll': -1.396,
                'LHipYawPitch': 0, 'LHipRoll': 0.002, 'LHipPitch': -0.8, 'LKneePitch': 0.8, 
                'LAnklePitch': 0.0, 'LAnkleRoll': -0.002,
                'RHipYawPitch': 0, 'RHipRoll': 0.002, 'RHipPitch': -0.661, 'RKneePitch': 1.226, 
                'RAnklePitch': -0.565, 'RAnkleRoll': -0.25,
                'RShoulderPitch': 2.085, 'RShoulderRoll': -0.349, 'RElbowYaw': 1.396, 'RElbowRoll': 1.396
            }
        },
        {
            'name': '恢复站立b',
            'duration': 0.5,
            'positions': {
                'LShoulderPitch': 2.085, 'LShoulderRoll': 0.349, 'LElbowYaw': -1.396, 'LElbowRoll': -1.396,
                'LHipYawPitch': 0, 'LHipRoll': 0.002, 'LHipPitch': -0.663, 'LKneePitch': 1.232, 
                'LAnklePitch': -0.568, 'LAnkleRoll': -0.002,
                'RHipYawPitch': 0, 'RHipRoll': 0.002, 'RHipPitch': -0.661, 'RKneePitch': 1.226, 
                'RAnklePitch': -0.565, 'RAnkleRoll': -0.002,
                'RShoulderPitch': 2.085, 'RShoulderRoll': -0.349, 'RElbowYaw': 1.396, 'RElbowRoll': 1.396
            }
        }
        ]
    def _update_walking_distance(self) -> None:
        """Update self.current_distance (meters) using GPS, if available."""
        if self.gps is None:
            return

        pos = self.gps.getValues()  # [x, y, z]
        if self.initial_pos is None:
            # First call – define origin at motion start
            self.initial_pos = list(pos)
            self.current_distance = 0.0
            return

        dx = pos[0] - self.initial_pos[0]
        dy = pos[1] - self.initial_pos[1]  # assuming Y is vertical
        self.current_distance = math.hypot(dy, dx)
    
    def set_leg_pose(
        self,
        side: str,
        hip_yaw_pitch: float,
        hip_roll: float,
        hip_pitch: float,
        knee_pitch: float,
        ankle_pitch: float,
        ankle_roll: float,
    ) -> None:
        """Send a leg target joint configuration to the motors (side = 'L' or 'R')."""
        if f"{side}HipYawPitch" in self.motors:
            self.motors[f"{side}HipYawPitch"].setPosition(hip_yaw_pitch)
            self.motors[f"{side}HipRoll"].setPosition(hip_roll)
            self.motors[f"{side}HipPitch"].setPosition(hip_pitch)
            self.motors[f"{side}KneePitch"].setPosition(knee_pitch)
            self.motors[f"{side}AnklePitch"].setPosition(ankle_pitch)
            self.motors[f"{side}AnkleRoll"].setPosition(ankle_roll)

    def set_neutral_walking(self) -> None:
        """Set both legs to the neutral (standing) posture."""
        for side in ("L", "R"):
            self.set_leg_pose(
                side,
                self.neutral["HipYawPitch"],
                self.neutral["HipRoll"],
                self.neutral["HipPitch"],
                self.neutral["KneePitch"],
                self.neutral["AnklePitch"],
                self.neutral["AnkleRoll"],
            )

    def _apply_gait_models(self, models: Dict[str, Any], phase: float) -> None:
        """Evaluate joint splines at the given phase and send targets to the motors."""
        # Left leg
        l_hip_yaw = models["LHipYawPitch"](phase)
        l_hip_roll = models["LHipRoll"](phase)
        l_hip_pitch = models["LHipPitch"](phase)
        l_knee = models["LKneePitch"](phase)
        l_ankle_p = models["LAnklePitch"](phase)
        l_ankle_r = models["LAnkleRoll"](phase)

        # Right leg
        r_hip_yaw = models["RHipYawPitch"](phase)
        r_hip_roll = models["RHipRoll"](phase)
        r_hip_pitch = models["RHipPitch"](phase)
        r_knee = models["RKneePitch"](phase)
        r_ankle_p = models["RAnklePitch"](phase)
        r_ankle_r = models["RAnkleRoll"](phase)

        self.set_leg_pose("L", l_hip_yaw, l_hip_roll, l_hip_pitch,
                          l_knee, l_ankle_p, l_ankle_r)
        self.set_leg_pose("R", r_hip_yaw, r_hip_roll, r_hip_pitch,
                          r_knee, r_ankle_p, r_ankle_r)
    
    def step(self, n=1):
        """执行仿真步"""
        for _ in range(n):
            if self.supervisor.step(self.timestep) == -1:
                return False
        return True
        
    def yaw(self) -> float:
        """获取当前yaw角度"""
        return self.imu.getRollPitchYaw()[2]
        
    def get_robot_position(self):
        """获取机器人位置"""
        if self.robot_node:
            return self.robot_node.getPosition()
        return None
        
    def get_ball_position(self):
        """获取球的位置"""
        if self.ball_node:
            return self.ball_node.getPosition()
        return None
        
    def set_pose(self, positions):
        """设置机器人姿势"""
        for joint_name, angle in positions.items():
            if joint_name in self.motors:
                self.motors[joint_name].setPosition(angle)
                
    def wait_for_position_completion(self, target_positions, max_wait_time=5.0, tolerance=0.1):
        """等待关节到达目标位置"""
        start_time = self.supervisor.getTime()
        
        while True:
            reached = True
            for joint_name, target in target_positions.items():
                if joint_name in self.sensors:
                    current = self.sensors[joint_name].getValue()
                    if abs(current - target) > tolerance:
                        reached = False
                        break
                        
            if reached:
                return True
                
            elapsed = self.supervisor.getTime() - start_time
            if elapsed > max_wait_time:
                return False
                
            if not self.step(1):
                return False
                
    def execute_arm_down(self):
        """执行手臂放下动作"""
        print("[ARM_DOWN] 放下手臂...")
        self.set_pose(ARM_DOWN_POSE)
        success = self.wait_for_position_completion(ARM_DOWN_POSE, max_wait_time=3.0)
        if success:
            print("[ARM_DOWN] ✓ 手臂放下完成")
        return success
        
    def choose_motion_key(self, err_rad: float) -> str:
        """选择转向motion"""
        left = err_rad > 0
        mag = abs(err_rad)
        
        if left:
            if mag >= math.radians(140):
                return "L180"
            elif mag >= math.radians(50):
                return "L60"
            else:
                return "L40"
        else:
            if mag >= math.radians(50):
                return "R60"
            else:
                return "R40"
                
    def execute_turning(self, target_angle_deg):
        """执行转向到指定角度"""
        print(f"[TURN] 开始转向到 {target_angle_deg:.1f}°")
        
        self.step(8)  # 稳定传感器
        start_yaw = self.yaw()*100
        print(start_yaw)
        target_yaw_rad = start_yaw + target_angle_deg
        
        for i in range(MAX_TURN_STEPS):
            self.step(32)
            current_yaw = self.yaw()*100
            print(current_yaw)
            error_deg = target_yaw_rad - current_yaw
            error_rad = math.radians(error_deg)
            
            print(f"[TURN] 步骤{i}: 当前{current_yaw:+.1f}°, 误差{error_deg:+.1f}°")
            
            if abs(error_deg) <= STOP_THRESHOLD_DEG:
                print(f"[TURN] ✓ 转向完成，误差{error_deg:+.1f}°")
                return True
                
            key = self.choose_motion_key(error_rad)
            if key in self.motions:
                motion = self.motions[key]
                motion.play()
                while not motion.isOver():
                    if not self.step(10):
                        return False
                self.step(5)

        return False
        
    def execute_walking(self, target_distance):
        """完整的行走实现 - 基于原有WalkingMin算法"""
        print(f"[WALK] 开始行走 {target_distance:.2f}m")
        
        if not self.gps:
            print("[WALK] 无GPS，跳过行走")
            return True
            
        if not self.start_gait or not self.walk_gait or not self.stop_gait:
            print("[WALK] 步态文件未加载")
            return False
        
        # 设置目标距离和停止偏移
        self.target_distance = target_distance
        self.stop_distance_offset = 0.05
        
        # 重置行走状态
        self.walk_state = "start"
        self.start_phase = self.start_gait["step_min"]
        self.walk_phase = 0.0
        self.stop_phase = self.stop_gait["step_min"]
        self.step_counter = 0
        self.prev_cycle_index = 0
        self.initial_pos = None
        self.current_distance = 0.0
        
        EPS = 1e-6
        dt = self.timestep / 1000.0
        
        print("[WALK] 行走状态机: start -> walk -> stop -> done")
        
        while True:
            if not self.step(1):
                return False
                
            # 更新距离
            self._update_walking_distance()
            
            # START PHASE (one-shot)
            if self.walk_state == "start":
                dstep = dt * self.f0
                self.start_phase += dstep

                # Clamp to end of start gait
                if self.start_phase > self.start_gait["step_max"]:
                    self.start_phase = self.start_gait["step_max"]

                self._apply_gait_models(self.start_gait["models"], self.start_phase)

                # When start motion is finished, transition to walking
                if self.start_phase >= self.start_gait["step_max"] - EPS:
                    self.walk_state = "walk"
                    self.walk_phase = 0.0
                    self.prev_cycle_index = 0
                    self.step_counter = 0
                    print("[WALK] 开始阶段完成，进入行走阶段")

            # WALK PHASE (loop, distance-based)
            elif self.walk_state == "walk":
                dstep = dt * self.f0
                self.walk_phase += dstep     # unbounded "cycle phase"

                # Map to [step_min, step_max] via modulo to loop
                cycle_len = self.walk_cycle_len
                step_min = self.walk_gait["step_min"]
                local_phase = step_min + (self.walk_phase % cycle_len)

                self._apply_gait_models(self.walk_gait["models"], local_phase)

                # Count how many full cycles have passed (debug / fallback)
                cycles = self.walk_phase / cycle_len
                cycle_index = math.floor(cycles)

                if cycle_index > self.prev_cycle_index:
                    self.step_counter += (cycle_index - self.prev_cycle_index)
                    self.prev_cycle_index = cycle_index
                    print(f"[WALK] 完成步数: {self.step_counter}, 已行走: {self.current_distance:.2f}m")

                # Decide when to stop walking - distance-based
                effective_target = self.target_distance - self.stop_distance_offset
                if effective_target < 0.0:
                    effective_target = 0.0

                if self.current_distance >= effective_target:
                    self.walk_state = "stop"
                    self.stop_phase = self.stop_gait["step_min"]
                    print(f"[WALK] 达到目标距离，开始停止阶段")

            # STOP PHASE (one-shot)
            elif self.walk_state == "stop":
                dstep = dt * self.f0
                self.stop_phase += dstep

                if self.stop_phase > self.stop_gait["step_max"]:
                    self.stop_phase = self.stop_gait["step_max"]

                self._apply_gait_models(self.stop_gait["models"], self.stop_phase)

                if self.stop_phase >= self.stop_gait["step_max"] - EPS:
                    self.walk_state = "done"
                    print("[WALK] 停止阶段完成")

            # DONE / IDLE
            elif self.walk_state == "done":
                # return to neutral posture
                self.set_neutral_walking()
                break

        print(f"[WALK] ✓ 行走完成，总距离 {self.current_distance:.2f}m")

        print("[WALK] 等待机器人稳定...")
        stabilize_time = 2.0  # 稳定时间2秒
        stabilize_steps = int(stabilize_time * 1000 / self.timestep)

        for i in range(stabilize_steps):
            if not self.step(1):
                return False
            # 每隔一定步数显示稳定进度
            if i % (stabilize_steps // 4) == 0:
                progress = (i / stabilize_steps) * 100
                print(f"[WALK] 稳定中... {progress:.0f}%")

        print("[WALK] ✓ 机器人已稳定")
        return True
        
    def set_dynamic_velocity(self, keyframe_name, duration):
        """Dynamically set joint velocities based on keyframe name and duration"""
        # Base speed mapping (speed is inversely proportional to time)
        base_speed = 1.0
        
        # Adjust speed based on duration: shorter time = faster speed, longer time = slower speed
        speed_factor = base_speed / max(duration, 0.1)  # Avoid division by zero
        
        # Velocity strategy for different keyframes
        if keyframe_name == '快速前踢':
            # Kicking action requires high speed
            kick_speed = min(speed_factor * 3.0, 20.0)  # Max cap 20.0
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
            
        elif keyframe_name in [ '恢复站立a', '恢复站立b']:
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
        
        print(f"  [VELOCITY] {keyframe_name}, duration: {duration}s")
        if keyframe_name == '快速前踢':
            print(f"    踢腿速度: {kick_speed:.2f}, 支撑腿速度: {support_speed:.2f}, 手臂速度: {arm_speed:.2f}")
        else:
            print(f"    支撑速度: {support_speed:.2f}, 手臂速度: {arm_speed:.2f}")

    def get_current_joint_positions(self):
        """Read current positions of all joints"""
        positions = {}
        for joint_name in self.joint_names:
            if joint_name in self.sensors:
                positions[joint_name] = self.sensors[joint_name].getValue()
        return positions

    def print_joint_positions(self, stage_name):
        """Print current joint positions"""
        print(f"\n=== {stage_name} - 关节位置读取 ===")
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

    def execute_keyframe(self, keyframe):
        """Execute a single keyframe"""
        print(f"\n=== 执行关键帧: {keyframe['name']} ===")
        
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
            print(f"关键帧 {keyframe['name']} 执行失败")
            return False
        
        # Print joint positions after completion
        self.print_joint_positions(f"{keyframe['name']} 完成后")
        
        return True

    def execute_shooting(self):
        """Execute the full shooting motion - 完整保持原有算法逻辑"""
        print("=== 开始射门动作 ===")
        print("动作分析: 这是左脚射门动作")
        print("- 重心转移到右腿支撑")
        print("- 左腿后摆蓄力")
        print("- 快速前踢射门")
        print("- 恢复平衡\n")
        
        # Print initial joint positions
        self.print_joint_positions("初始状态")
        
        for i, keyframe in enumerate(self.shooting_keyframes, 1):
            print(f"\n步骤 {i}/{len(self.shooting_keyframes)}: 准备执行 {keyframe['name']}")
            
            if not self.execute_keyframe(keyframe):
                print("射门动作中断")
                return False
            
            if keyframe['name'] == '快速前踢':
                # 踢球动作后不需要额外稳定时间，直接继续
                continue
            else:
                # 额外稳定时间
                print("  等待姿态稳定...")
                for _ in range(20):
                    if not self.step(1):
                        return False
            
            print(f"✓ 关键帧 {keyframe['name']} 执行成功")
            
        print("=== 射门动作完成 ===")
        return True
        
    def run(self):
        """主循环"""
        print("=== NAO足球Demo开始 ===")
        
        # 初始稳定
        print("[INIT] 初始化中...")
        for _ in range(100):
            if not self.step(1):
                return
                
        while self.step(1):
            if self.state == "idle":
                # 获取球的位置
                ball_pos = self.get_ball_position()
                robot_pos = self.get_robot_position()
                
                if ball_pos is None or robot_pos is None:
                    print("[ERROR] 无法获取球或机器人位置")
                    continue
                    
                # 计算距离和角度
                distance = calculate_distance(robot_pos, ball_pos)
                angle_rad = calculate_angle(robot_pos, ball_pos)
                angle_deg = math.degrees(angle_rad)
                
                # 计算相对角度（相对于当前朝向）
                current_yaw = self.yaw()
                relative_angle = wrap_to_pi(angle_rad - current_yaw)
                relative_angle_deg = math.degrees(relative_angle)
                
                print(f"[INFO] 球距离: {distance:.2f}m, 相对角度: {relative_angle_deg:+.1f}°")
                
                # 如果距离太近，直接射门
                if distance < 0.2:
                    self.state = "shoot"
                    continue
                    
                # 如果需要转向
                if abs(relative_angle_deg) > STOP_THRESHOLD_DEG:
                    self.state = "arm_down"
                    self.target_turn_angle = relative_angle_deg
                    self.target_walk_distance = max(0, distance - 0.2)  # 走到距离球0.3m处
                else:
                    self.state = "walk"
                    self.target_walk_distance = max(0, distance - 0.2)
                    
            elif self.state == "arm_down":
                if self.execute_arm_down():
                    self.state = "turn"
                else:
                    print("[ERROR] 手臂放下失败")
                    break
                    
            elif self.state == "turn":
                if self.execute_turning(self.target_turn_angle):
                    self.state = "walk"
                else:
                    print("[ERROR] 转向失败")
                    break
                    
            elif self.state == "walk":
                if self.execute_walking(self.target_walk_distance):
                    self.state = "shoot"
                else:
                    print("[ERROR] 行走失败")
                    break
                    
            elif self.state == "shoot":
                if self.execute_shooting():
                    self.state = "done"
                    print("=== Demo完成 ===")
                else:
                    print("[ERROR] 射门失败")
                    break
                    
            elif self.state == "done":
                # 保持运行
                continue
                

if __name__ == "__main__":
    controller = NAOSoccerDemoController()
    controller.run()