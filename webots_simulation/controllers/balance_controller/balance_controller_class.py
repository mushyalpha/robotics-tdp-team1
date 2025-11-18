from math import isnan

class BalanceController:
    """
    平衡控制器模块（双轴：pitch + roll）
    - 自动零点校准
    - PD 控制（可扩展成 PID）
    - 支持输出限幅 & 限速
    - 支持 base + delta 控制结构
    """

    def __init__(self, dt, 
                 Kp_pitch=2.0, Kd_pitch=0.3,
                 Kp_roll=1.5, Kd_roll=0.2,
                 out_limit=0.35,
                 slew_rate=0.05):

        self.dt = dt

        # --- pitch 控制增益 ---
        self.Kp_p = Kp_pitch
        self.Kd_p = Kd_pitch
        self.prev_err_p = 0.0

        # --- roll 控制增益 ---
        self.Kp_r = Kp_roll
        self.Kd_r = Kd_roll
        self.prev_err_r = 0.0

        # --- 控制输出限幅 ---
        self.out_limit = out_limit

        # --- 斜率限速（防跳变） ---
        self.slew = slew_rate
        self.prev_out_pitch = 0.0
        self.prev_out_roll = 0.0

        # --- 零点（开机自动标定） ---
        self.desired_pitch = 0.0
        self.desired_roll = 0.0
        self.calibrated = False

        # --- 外部控制开关 ---
        self.enabled = True


    # ======= 零点校准函数（开机后调用一次） =======
    def calibrate(self, pitch0, roll0):
        self.desired_pitch = pitch0
        self.desired_roll = roll0
        self.calibrated = True
        print(f"[BalanceController] calibrated: pitch0={pitch0:.3f}, roll0={roll0:.3f}")


    # ======= 主更新函数（每个 control step 调用一次） =======
    def update(self, pitch, roll, pitch_rate, roll_rate):
        """
        输入：IMU 值（pitch, roll）+ 陀螺角速度（pitch_rate, roll_rate）
        输出：delta_pitch, delta_roll（用于加在 base 角度上）
        """

        if not self.enabled:
            return 0.0, 0.0
        
        if not self.calibrated:
            # 未校准情况下不控制，避免瞬间跳变
            return 0.0, 0.0

        # ========== PITCH 轴控制 ==========
        err_p = self.desired_pitch - pitch
        d_p = (err_p - self.prev_err_p) / self.dt
        self.prev_err_p = err_p

        out_p = -(self.Kp_p * err_p + self.Kd_p * pitch_rate)

        # 限幅
        out_p = max(min(out_p, self.out_limit), -self.out_limit)

        # 限速
        delta_p = out_p - self.prev_out_pitch
        delta_p = max(min(delta_p, self.slew), -self.slew)
        out_p = self.prev_out_pitch + delta_p
        self.prev_out_pitch = out_p


        # ========== ROLL 轴控制 ==========
        err_r = self.desired_roll - roll
        d_r = (err_r - self.prev_err_r) / self.dt
        self.prev_err_r = err_r

        out_r = -(self.Kp_r * err_r + self.Kd_r * roll_rate)

        # 限幅
        out_r = max(min(out_r, self.out_limit), -self.out_limit)

        # 限速
        delta_r = out_r - self.prev_out_roll
        delta_r = max(min(delta_r, self.slew), -self.slew)
        out_r = self.prev_out_roll + delta_r
        self.prev_out_roll = out_r


        return out_p, out_r


    # ======= 清零（例如跌倒检测时用） =======
    def reset_output(self):
        self.prev_err_p = 0.0
        self.prev_err_r = 0.0
        self.prev_out_pitch = 0.0
        self.prev_out_roll = 0.0


    # ======= 启用/禁用控制器 =======
    def enable(self):
        self.enabled = True

    def disable(self):
        self.enabled = False
        self.reset_output()
