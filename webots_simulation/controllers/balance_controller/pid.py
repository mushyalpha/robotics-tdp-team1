# pid_controller  2025.11.17
# instruction: parameter = the parameter you need to control, desire_para = your desired value
# dt = the time(always use timestep/1000.0, timestep=timestep = int(robot.getBasicTimeStep()))
# Kp,Kd,Ki= pid control parameter
# Imax = integral limit

from controller import Robot, Motion

def pid(parameter,desired_para,dt,Kp,Kd,Ki,Imax=1.0):
    prev_err= 0.0

    err = desired_para - parameter
    derivative = (err- prev_err) / dt
    integral += err*dt
    integral = max(min(integral, Imax), - Imax)
    prev_err = err

    output = Kp * err + Kd * derivative + Ki*integral

    return output
