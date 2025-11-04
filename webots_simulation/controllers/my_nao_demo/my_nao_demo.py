from controller import Robot, Camera, Accelerometer, Gyro, GPS, InertialUnit, DistanceSensor, TouchSensor, LED, Motor, Keyboard, Motion
import math
import os


PHALANX_MAX = 8

class NaoDemo:
    def __init__(self):
        self.robot = Robot()
        self.time_step = int(self.robot.getBasicTimeStep())

        # simulated devices
        self.CameraTop = None
        self.CameraBottom = None
        self.us = [None, None]
        self.accelerometer = None
        self.gps = None
        self.gyro = None
        self.inertial_unit = None
        self.fsr = [None, None]
        self.lfoot_lbumper = None
        self.lfoot_rbumper = None
        self.rfoot_lbumper = None
        self.rfoot_rbumper = None
        self.leds = [None]*7
        self.lphalanx = [None]*PHALANX_MAX
        self.rphalanx = [None]*PHALANX_MAX
        self.RShoulderPitch = None
        self.LShoulderPitch = None

        self.hand_wave = None
        self.forwards = None
        self.backwards = None
        self.side_step_left = None
        self.side_step_right = None
        self.turn_left_60 = None
        self.turn_right_60 = None
        self.tai_chi = None
        self.wipe_forehead = None
        self.currently_playing = None

        self.maxPhalanxMotorPosition = [0]*PHALANX_MAX
        self.minPhalanxMotorPosition = [0]*PHALANX_MAX

        self.keyboard = self.robot.getKeyboard()
        self.keyboard.enable(10 * self.time_step)

        self.find_and_enable_devices()
        self.load_motion_files()
        self.print_help()

        # start waving motion in a loop
        self.hand_wave.setLoop(True)
        self.hand_wave.play()
        self.currently_playing = self.hand_wave

    def find_and_enable_devices(self):
        self.CameraTop = self.robot.getDevice("CameraTop")
        self.CameraBottom = self.robot.getDevice("CameraBottom")
        self.CameraTop.enable(4 * self.time_step)
        self.CameraBottom.enable(4 * self.time_step)

        self.accelerometer = self.robot.getDevice("accelerometer")
        self.accelerometer.enable(self.time_step)

        self.gyro = self.robot.getDevice("gyro")
        self.gyro.enable(self.time_step)

        self.gps = self.robot.getDevice("gps")
        self.gps.enable(self.time_step)

        self.inertial_unit = self.robot.getDevice("inertial unit")
        self.inertial_unit.enable(self.time_step)

        self.us[0] = self.robot.getDevice("Sonar/Left")
        self.us[1] = self.robot.getDevice("Sonar/Right")
        for s in self.us:
            s.enable(self.time_step)

        self.fsr[0] = self.robot.getDevice("LFsr")
        self.fsr[1] = self.robot.getDevice("RFsr")
        for s in self.fsr:
            s.enable(self.time_step)

        self.lfoot_lbumper = self.robot.getDevice("LFoot/Bumper/Left")
        self.lfoot_rbumper = self.robot.getDevice("LFoot/Bumper/Right")
        self.rfoot_lbumper = self.robot.getDevice("RFoot/Bumper/Left")
        self.rfoot_rbumper = self.robot.getDevice("RFoot/Bumper/Right")
        for s in [self.lfoot_lbumper, self.lfoot_rbumper, self.rfoot_lbumper, self.rfoot_rbumper]:
            s.enable(self.time_step)

        led_names = [
            "ChestBoard/Led", "RFoot/Led", "LFoot/Led",
            "Face/Led/Right", "Face/Led/Left", "Ears/Led/Right", "Ears/Led/Left"
        ]
        for i, name in enumerate(led_names):
            self.leds[i] = self.robot.getDevice(name)

        for i in range(PHALANX_MAX):
            self.lphalanx[i] = self.robot.getDevice(f"LPhalanx{i+1}")
            self.rphalanx[i] = self.robot.getDevice(f"RPhalanx{i+1}")
            if self.rphalanx[i]:
                self.maxPhalanxMotorPosition[i] = self.rphalanx[i].getMaxPosition()
                self.minPhalanxMotorPosition[i] = self.rphalanx[i].getMinPosition()

        self.RShoulderPitch = self.robot.getDevice("RShoulderPitch")
        self.LShoulderPitch = self.robot.getDevice("LShoulderPitch")

    def load_motion_files(self):
        # Get the directory where THIS Python file is located
        controller_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up one level (from controllers/nao_demo to webots_simulation)
        project_root = os.path.abspath(os.path.join(controller_dir, "..", ".."))
        # Build the path to motions folder
        motions_dir = os.path.join(project_root, "motions")
    
        # Print for debugging
        print("Loading motions from:", motions_dir)
    
        # Load all motions using relative paths
        self.hand_wave = Motion(os.path.join(motions_dir, "HandWave.motion"))
        self.forwards = Motion(os.path.join(motions_dir, "Forwards50.motion"))
        self.backwards = Motion(os.path.join(motions_dir, "Backwards.motion"))
        self.side_step_left = Motion(os.path.join(motions_dir, "SideStepLeft.motion"))
        self.side_step_right = Motion(os.path.join(motions_dir, "SideStepRight.motion"))
        self.turn_left_60 = Motion(os.path.join(motions_dir, "TurnLeft60.motion"))
        self.turn_right_60 = Motion(os.path.join(motions_dir, "TurnRight60.motion"))
        self.tai_chi = Motion(os.path.join(motions_dir, "TaiChi.motion"))
        self.wipe_forehead = Motion(os.path.join(motions_dir, "WipeForehead.motion"))

    def start_motion(self, motion):
        if self.currently_playing:
            self.currently_playing.stop()
        motion.play()
        self.currently_playing = motion

    def set_all_leds_color(self, rgb):
        for i in range(5):
            self.leds[i].set(rgb)
        self.leds[5].set(rgb & 0xff)
        self.leds[6].set(rgb & 0xff)

    def set_hands_angle(self, angle):
        for j in range(PHALANX_MAX):
            if self.rphalanx[j]:
                self.rphalanx[j].setPosition(angle)
            if self.lphalanx[j]:
                self.lphalanx[j].setPosition(angle)

    def print_help(self):
        print("----------nao_demo----------")
        print("Keyboard controls:")
        print("[↑][↓]: walk forward/backward")
        print("[←][→]: side steps")
        print("[Shift]+[←][→]: turn left/right")
        print("[A]: accelerometer")
        print("[G]: gyro")
        print("[S]: gps")
        print("[I]: inertial unit")
        print("[F]: foot sensors")
        print("[B]: bumpers")
        print("[U]: ultrasound")
        print("[7][8][9]: LED colors")
        print("[0]: turn off LEDs")
        print("[T]: tai chi")
        print("[W]: wipe forehead")
        print("[PgUp][PgDn]: open/close hands")

    def step(self):
        if self.robot.step(self.time_step) == -1:
            exit(0)

    def run(self):
        key = -1
        while self.robot.step(self.time_step) != -1:
            key = self.keyboard.getKey()
            if key == ord('T'):
                self.start_motion(self.tai_chi)
            elif key == ord('W'):
                self.start_motion(self.wipe_forehead)
            elif key == ord('7'):
                self.set_all_leds_color(0xff0000)
            elif key == ord('8'):
                self.set_all_leds_color(0x00ff00)
            elif key == ord('9'):
                self.set_all_leds_color(0x0000ff)
            elif key == ord('0'):
                self.set_all_leds_color(0x000000)
            elif key == 315:  # UP
                self.start_motion(self.forwards)
            elif key == 317:  # DOWN
                self.start_motion(self.backwards)
            elif key == 314:  # LEFT
                self.start_motion(self.side_step_left)
            elif key == 316:  # RIGHT
                self.start_motion(self.side_step_right)
            elif key == 366:  # PageUp
                self.set_hands_angle(0.96)
            elif key == 367:  # PageDown
                self.set_hands_angle(0.0)

if __name__ == "__main__":
    controller = NaoDemo()
    controller.run()
