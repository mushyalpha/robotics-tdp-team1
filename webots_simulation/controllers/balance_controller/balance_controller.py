from controller import Robot, Motion

path = r"../../motions/StandUpFromFront.motion"
stand_up_front = Motion(path)

# initial
robot = Robot()
timestep = int(robot.getBasicTimeStep())

imu  = robot.getDevice("InertialUnit"); imu.enable(timestep)
gyro = robot.getDevice("Gyro");         gyro.enable(timestep)
acc  = robot.getDevice("Accelerometer"); acc.enable(timestep)

LHipPitch = robot.getDevice("LHipPitch")
RHipPitch = robot.getDevice("RHipPitch")

# PID parameters
desired_pitch = 0.0
Kp = 2.0
Kd = 0.3
Ki = 1               # integral gain

previous_error = 0.0
integral = 0.0
I_MAX = 0.3           
LEAK_TAU = 8.0          # Integral leak time
EPS = 0.02              # minor error zone

# Limit
OUTPUT_LIMIT = 0.3
SLEW_LIMIT = 0.05       # Maximum change per cycle (anti-jitter)
prev_output = 0.0

# fall down detect
FALL_PITCH_LIMIT = 1.5
FALL_ROLL_LIMIT = 1.5
is_fallen = False

# stand up parameters
def prepare_for_front_stand():
    print("Adjusting arms for front stand-up posture...")
    pose = {
        "LShoulderPitch": 1.2,  # 手臂稍向下（贴近地面）
        "RShoulderPitch": 1.2,
        "LShoulderRoll": 0.3,   # 手臂稍往外打开
        "RShoulderRoll": -0.3,
        "LElbowYaw": -1.0,
        "RElbowYaw": 1.0,
        "LElbowRoll": -0.5,
        "RElbowRoll": 0.5,
    }
    for name, angle in pose.items():
        m = robot.getDevice(name)
        m.setPosition(angle)
    for _ in range(10):
        robot.step(timestep)


def play_recovery_motion():
    if pitch > 0:
        print("Recovering: StandUpFromFront.motion")
        prepare_for_front_stand()
        for _ in range(5): robot.step(timestep)
        stand_up_front.play()
    while not stand_up_front.isOver():
        robot.step(timestep)


# main loop
while robot.step(timestep) != -1:
    roll, pitch, yaw = imu.getRollPitchYaw()
    gx, gy, gz = gyro.getValues()  
    pitch_rate = gy

    # fall down detect
    if (abs(pitch) > FALL_PITCH_LIMIT or 
        (abs(roll) > 0.8 and abs(abs(roll) - 3.14) > 0.3)):
        print("Robot has fallen!")
        is_fallen = True

    if is_fallen:
        integral = 0.0  
        play_recovery_motion()
        is_fallen = False
        continue

    # PID controll
    error = desired_pitch - pitch
    derivative = -pitch_rate  

    # Integral
    if abs(error) < EPS and abs(prev_output) < OUTPUT_LIMIT * 0.95:
        integral += error * (timestep / 1000.0)
    integral *= (1.0 - (timestep / 1000.0) / LEAK_TAU)
    integral = max(min(integral, I_MAX), -I_MAX)

    # PID output
    output = -(Kp * error + Kd * derivative + Ki * integral)

    # output limit
    output = max(min(output, OUTPUT_LIMIT), -OUTPUT_LIMIT)
    delta = output - prev_output
    if delta > SLEW_LIMIT:
        output = prev_output + SLEW_LIMIT
    elif delta < -SLEW_LIMIT:
        output = prev_output - SLEW_LIMIT
    prev_output = output

    # impletation
    LHipPitch.setPosition(output)
    RHipPitch.setPosition(output)

    print(f"pitch={pitch:.3f}, error={error:.3f}, output={output:.3f}, I={integral:.3f}")
