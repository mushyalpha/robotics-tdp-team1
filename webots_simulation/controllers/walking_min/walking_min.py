from controller import Robot, Motor
import math

class WalkingMin:
    def __init__(self):
        self.robot = Robot()
        self.dt = int(self.robot.getBasicTimeStep()) / 1000.0  # seconds

        # 获取电机（保持与 NAO6 关节名一致）
        names_L = ["LHipYawPitch","LHipRoll","LHipPitch","LKneePitch","LAnklePitch","LAnkleRoll"]
        names_R = ["RHipYawPitch","RHipRoll","RHipPitch","RKneePitch","RAnklePitch","RAnkleRoll"]
        self.motors = {}
        for n in names_L + names_R:
            m = self.robot.getDevice(n)
            m.setPosition(0.0)
            m.setVelocity(m.getMaxVelocity()*0.6)  # 适度放宽电机速度
            self.motors[n] = m

        # 中立位（微屈膝、轻前倾，起点更稳）
        self.neutral = dict(HipYawPitch=0.0, HipRoll=0.0, HipPitch=-0.2,
                            KneePitch=0.4, AnklePitch=-0.2, AnkleRoll=0.0)
        self.set_neutral()

        # ——步态参数（固定常量）——
        self.f0 = 0.8               # 固定步频（Hz），先从 0.8~1.2 之间试
        self.phase = 0.0            # 全局相位
        # 摆幅基线（弧度）：可从小到大微调
        self.A_hip_pitch   = 0.18   # 髋前后摆幅（主驱动）
        self.A_knee        = 0.40   # 膝抬腿幅度
        self.A_ankle_pitch = 0.20   # 踝俯仰（脚尖上抬/下压）
        self.A_hip_roll    = 0.04   # 髋滚（左右平衡）
        self.A_ankle_roll  = 0.04   # 踝滚（左右平衡）
        # 轻微外八，落脚更稳
        self.yaw_out = 0.02

    def clamp(self, x, lo, hi):
        return max(lo, min(hi, x))

    def set_leg_pose(self, side, hip_yaw_pitch, hip_roll, hip_pitch, knee_pitch, ankle_pitch, ankle_roll):
        m = self.motors
        m[f"{side}HipYawPitch"].setPosition(hip_yaw_pitch)
        m[f"{side}HipRoll"].setPosition(hip_roll)
        m[f"{side}HipPitch"].setPosition(hip_pitch)
        m[f"{side}KneePitch"].setPosition(knee_pitch)
        m[f"{side}AnklePitch"].setPosition(ankle_pitch)
        m[f"{side}AnkleRoll"].setPosition(ankle_roll)

    def set_neutral(self):
        for s in ("L","R"):
            self.set_leg_pose(s,
                self.neutral["HipYawPitch"], self.neutral["HipRoll"],
                self.neutral["HipPitch"],    self.neutral["KneePitch"],
                self.neutral["AnklePitch"],  self.neutral["AnkleRoll"]
            )

    def run(self):
        while self.robot.step(int(self.dt*1000)) != -1:
            # 相位推进
            self.phase = (self.phase + 2.0*math.pi*self.f0*self.dt) % (2.0*math.pi)
            lp = self.phase
            rp = (self.phase + math.pi) % (2.0*math.pi)  # 右腿相位 = 左腿 + π（对摆）

            # ——左腿关节目标（正弦）——
            l_hip_pitch = self.neutral["HipPitch"]   + self.A_hip_pitch   * math.sin(lp)
            l_knee      = self.neutral["KneePitch"]  + self.A_knee        * math.sin(lp + 0.5*math.pi)
            l_ankle_p   = self.neutral["AnklePitch"] - self.A_ankle_pitch * math.sin(lp + 0.3*math.pi)
            l_hip_roll  = self.neutral["HipRoll"]    + self.A_hip_roll    * math.sin(lp + math.pi)
            l_ankle_r   = self.neutral["AnkleRoll"]  - self.A_ankle_roll  * math.sin(lp + math.pi)
            l_yaw       = +self.yaw_out

            # ——右腿关节目标（相位+π）——
            r_hip_pitch = self.neutral["HipPitch"]   + self.A_hip_pitch   * math.sin(rp)
            r_knee      = self.neutral["KneePitch"]  + self.A_knee        * math.sin(rp + 0.5*math.pi)
            r_ankle_p   = self.neutral["AnklePitch"] - self.A_ankle_pitch * math.sin(rp + 0.3*math.pi)
            r_hip_roll  = self.neutral["HipRoll"]    + self.A_hip_roll    * math.sin(rp + math.pi)
            r_ankle_r   = self.neutral["AnkleRoll"]  - self.A_ankle_roll  * math.sin(rp + math.pi)
            r_yaw       = -self.yaw_out

            # 夹限（安全范围，按 NAO 典型约束）
            def c(x, lo, hi): return self.clamp(x, lo, hi)
            L = (c(l_yaw,-0.5,0.5), c(l_hip_roll,-0.45,0.45), c(l_hip_pitch,-1.2,0.6),
                 c(l_knee,-0.1,2.6), c(l_ankle_p,-1.0,0.9),   c(l_ankle_r,-0.5,0.5))
            R = (c(r_yaw,-0.5,0.5), c(r_hip_roll,-0.45,0.45), c(r_hip_pitch,-1.2,0.6),
                 c(r_knee,-0.1,2.6), c(r_ankle_p,-1.0,0.9),   c(r_ankle_r,-0.5,0.5))

            self.set_leg_pose("L", *L)
            self.set_leg_pose("R", *R)

if __name__ == "__main__":
    WalkingMin().run()
