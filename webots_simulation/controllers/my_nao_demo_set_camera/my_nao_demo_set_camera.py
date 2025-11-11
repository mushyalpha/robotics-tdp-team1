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
        
        ''' === set initial head yaw&pitch ===
        # HeadYaw: 0 is straight ahead, >0 is look left
        # HeadPitch: 0 is horizontal, >0 is look down
        if self.HeadYaw and self.HeadPitch:
            initial_head_yaw = 0.0   # maintain straight ahead
            initial_head_pitch = 0.25  # look slightly down approx. 14 degrees(degrees=radians*180/pi)
            
            self.HeadYaw.setPosition(initial_head_yaw)
            self.HeadPitch.setPosition(initial_head_pitch)
            
        '''

        # start waving motion in a loop (if motion file loaded successfully)
        if self.hand_wave:
            self.hand_wave.setLoop(True)
            self.hand_wave.play()
            self.currently_playing = self.hand_wave
        else:
            print("WARNING: Hand wave motion not available. Controller may not function correctly.")


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

#        self.HeadYaw = self.robot.getDevice("HeadYaw")
#        self.HeadPitch = self.robot.getDevice("HeadPitch")


    def load_motion_files(self):
        """Load motion files from Webots installation directory.
        Tries multiple path locations to support different systems and installations.
        """
        base = None
        tried_paths = []
        
        # Strategy 1: Check environment variables for Webots installation path
        webots_home = os.environ.get('WEBOTS_HOME') or os.environ.get('WEBOTS_PATH')
        if webots_home:
            candidate = os.path.join(webots_home, "projects", "robots", "softbank", "nao", "motions")
            tried_paths.append(candidate)
            if os.path.exists(candidate):
                base = candidate.replace('\\', '/') + "/"
        
        # Strategy 2: Try common installation paths
        if not base:
            if os.name == 'nt':  # Windows
                possible_paths = [
                    "C:/Program Files/Webots/projects/robots/softbank/nao/motions/",
                    "C:/Program Files (x86)/Webots/projects/robots/softbank/nao/motions/",
                    "D:/Webots/projects/robots/softbank/nao/motions/",
                    os.path.expanduser("~/Webots/projects/robots/softbank/nao/motions/"),
                ]
            elif os.name == 'posix':  # Linux/Mac
                possible_paths = [
                    "/usr/local/webots/projects/robots/softbank/nao/motions/",
                    "/opt/webots/projects/robots/softbank/nao/motions/",
                    "/Applications/Webots/projects/robots/softbank/nao/motions/",
                    os.path.expanduser("~/webots/projects/robots/softbank/nao/motions/"),
                ]
            else:
                possible_paths = []
            
            tried_paths.extend(possible_paths)
            for path in possible_paths:
                # Normalize path separators for Webots (uses forward slashes)
                normalized_path = path.replace('\\', '/')
                if os.path.exists(normalized_path):
                    base = normalized_path
                    break
        
        # Strategy 3: Try relative path from controller (if motion files are in project)
        if not base:
            controller_dir = os.path.dirname(os.path.abspath(__file__))
            relative_paths = [
                os.path.join(controller_dir, "..", "..", "motions"),
                os.path.join(controller_dir, "..", "..", "..", "projects", "robots", "softbank", "nao", "motions"),
            ]
            tried_paths.extend([os.path.normpath(p).replace('\\', '/') for p in relative_paths])
            for rel_path in relative_paths:
                normalized_path = os.path.normpath(rel_path).replace('\\', '/') + "/"
                if os.path.exists(normalized_path):
                    base = normalized_path
                    break
        
        if not base:
            error_msg = (
                "ERROR: Could not find motion files directory.\n"
                "Please ensure Webots is installed and motion files are available at:\n"
                "  - projects/robots/softbank/nao/motions/\n"
                "Or set WEBOTS_HOME environment variable to your Webots installation directory.\n"
                "Tried paths:\n"
            )
            for path in tried_paths:
                error_msg += f"  - {path}\n"
            print(error_msg)
            raise FileNotFoundError("Motion files directory not found")
        
        print(f"Loading motion files from: {base}")
        
        # Load all motion files
        try:
            self.hand_wave = Motion(base + "HandWave.motion")
            self.forwards = Motion(base + "Forwards50.motion")
            self.backwards = Motion(base + "Backwards.motion")
            self.side_step_left = Motion(base + "SideStepLeft.motion")
            self.side_step_right = Motion(base + "SideStepRight.motion")
            self.turn_left_60 = Motion(base + "TurnLeft60.motion")
            self.turn_right_60 = Motion(base + "TurnRight60.motion")
            self.tai_chi = Motion(base + "TaiChi.motion")
            self.wipe_forehead = Motion(base + "WipeForehead.motion")
            print("All motion files loaded successfully.")
        except Exception as e:
            print(f"ERROR: Failed to load motion files: {e}")
            print(f"Make sure all motion files exist in: {base}")
            raise

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
   
