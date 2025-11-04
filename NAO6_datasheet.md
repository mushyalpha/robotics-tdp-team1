# NAO6 Robot Datasheet

**Model:** H25600

**Version:** 10/2024

**Manufacturer:** Aldebaran Robotics

---

## Physical Characteristics

### General

* **Size (H×D×W):** 574×311×275 mm / 22.6×12.2×10.8 in
* **Weight:** 5.48 kg / 12.08 lb

---

## Brain System

### Motherboard

* **CPU:** Intel ATOM E3845 processor
* **Cache Memory:** 2 MB
* **Clock Speed:** 1.91 GHz
* **RAM:** 4 GB DDR3
* **Flash Memory:** 32 GB eMMC

---

## Human Interaction

### Languages

**Text to Speech & Automatic Speech Recognition:**
Czech, Danish, Dutch, English, Finnish, French, German, Italian, Japanese, Greek, Polish, European Portuguese, Brazilian Portuguese, Spanish, Swedish, Russian, Turkish, Arabic, Brazilian, Standard Mandarin, Taiwanese Mandarin, Norwegian

### Audio

#### Loud Speakers (Left & Right)

* **Diameter:** 40 mm
* **Impedance:** 4 Ω
* **Audio Power:** 87 dB ±3 dB
* **Frequency Range:** Up to ~20 kHz
* **Input:** 2 W

#### Microphones

* **Quantity:** 4 omnidirectional microphones on the head
* **Sensitivity:** -12 dBV/PA @1 KHz
* **Frequency Range:** 100 Hz to 10 KHz

### LEDs

| Placement    | Quantity | Description     |
| ------------ | -------- | --------------- |
| Tactile Head | 12       | 16 White levels |
| Eyes         | 2×8     | RGB Full Color  |
| Ears         | 2×10    | 16 Blue levels  |
| Chest Button | 1        | RGB Full Color  |
| Feet         | 2×1     | RGB Full Color  |

---

## 2D Cameras

### Camera Specifications

* **Cameras:** 2 front-mounted on head
* **Sensor Model:** OV5640
* **Sensor Type:** SoC - CMOS Image Sensor
* **Imaging Array Resolution:** 5 MP
* **Sensor Size:** 1/4 in
* **Active Pixels (H×V):** 2592 × 1944
* **Pixel Size:** 1.4 × 1.4 μm
* **Dynamic Range:** 68 dB @8x gain
* **Signal/Noise Ratio (max):** 36 dB
* **Responsivity:** 600 mV/lux-sec
* **Camera Output:** 640 × 480 @30 fps
* **Data Format:** YUY & RGB
* **Shutter Type:** Rolling Shutter/Frame Exposure
* **View Field:** 67.4° DFOV (56.3° HFOV, 43.7° VFOV)
* **Focus Range:** 10 cm ~ ∞ (≈ 4 in - ∞)
* **Focus Type:** Auto focus

### Frame Rates

| Resolution    | Top Camera  | Bottom Camera |
| ------------- | ----------- | ------------- |
| 320×240 px   | @15, 30 fps | @15, 30 fps   |
| 640×480 px   | @15, 30 fps | @15, 30 fps   |
| 1280×960 px  | @15, 30 fps | @10, 15 fps   |
| 1920×1080 px | @15, 30 fps | -             |
| 2560×1920 px | @15 fps     | -             |

*Note: The rate of the video stream will depend on the network and the video resolution chosen. All frame rates depend on the CPU usage. Values are measured with a CPU fully dedicated to image gathering.*

---

## Environment Sensors

### Inertial Unit

#### Gyrometer

* **Quantity:** 1
* **Axis:** 3
* **Precision:** 5%
* **Angular Speed:** 500°/s approx.

#### IMU (Inertial Measurement Unit)

* **Quantity:** 1
* **Axis:** 3
* **Precision:** 10%
* **Angular Speed:** 2 g approx.

### Sonar

* **Transmitters:** 2 on front
* **Receivers:** 2 on front
* **Frequency:** 40 kHz
* **Resolution:** 1 cm @50 cm
* **Detection Range:** 0.20 m to 0.80 m
* **Effective Cone:** 60°

---

## Buttons & Sensors

* **Chest Button:** Transmitter 1 & 2, Receiver 1 & 2
* **Foot Bumper**
* **Tactile Head**
* **Tactile Hand**

### Force Sensitive Resistors (FSR)

* **Range:** 0 to 25 N
* **Location:** 4 in each foot
* **Sensitivity:** 40 g approx.

---

## Energy

### Robot Battery

* **Battery Type:** Lithium-Ion
* **Nominal Voltage/Capacity:** 21.6 V / 2.9 Ah
* **Max Charge Voltage:** 25.2 V
* **Recommended Charge Current:** 1.8 A
* **Max Charge/Discharge Current:** 2.1 A / 2.0 A
* **Energy:** 62.5 Wh
* **Charging Duration:** 90 min
* **Run Time:**
  * Active use: 60 min
  * Normal use: 90 min

### Battery Charger

* **Input:** 100 to 240 VAC – 50/60 Hz – Max 1.2 A
* **Output:** 25.2 VDC – 2 A

---

## Motion

### Degrees of Freedom

* **Head:** 2
* **Arm (each):** 5
* **Pelvis:** 1
* **Leg (each):** 5
* **Hand (each):** 1

**Total:** 25 degrees of freedom

### Position of Motors

| Joint Name    | Motor Type | Gear Ratio |
| ------------- | ---------- | ---------- |
| HeadYaw       | 3          | 150.27     |
| HeadPitch     | 3          | 173.22     |
| ShoulderPitch | 4          | 150.27     |
| ShoulderRoll  | 3          | 173.22     |
| ElbowYaw      | 3          | 150.27     |
| ElbowRoll     | 3          | 173.22     |
| WristYaw      | 2          | 50.61      |
| Hand/Fingers  | 2          | 36.24      |
| HipYawPitch   | 1          | 201.3      |
| HipRoll       | 1          | 201.3      |
| HipPitch      | 5          | 130.85     |
| KneePitch     | 5          | 130.85     |
| AnklePitch    | 5          | 130.85     |
| AnkleRoll     | 1          | 201.3      |

### Motor Specifications

**All Motors:** Brush DC Coreless

#### Motor Type Details

| Specification           | Type 1     | Type 2     | Type 3      | Type 4      | Type 5     |
| ----------------------- | ---------- | ---------- | ----------- | ----------- | ---------- |
| Make                    | 22NT82213P | 17N88208E  | 16GT83210E  | DCX 16S     | 22NT Z20   |
| No Load Speed (rpm)     | 8700 ±10% | 8400 ±12% | 10700 ±10% | 11400 ±10% | 8700 ±10% |
| Stall Torque (mNm)      | 65 ±8%    | 9.4 ±8%   | 14.3 ±8%   | 22.4 ±10%  | 65 ±10%   |
| Continuous Torque (mNm) | 17.8 max   | 4.9 max    | 6.2 max     | 2.6 max     | 17.8 max   |

### Joint Movement Encoders

* **Type:** MRE (Magnetic Rotary Encoder)
* **Quantity:** 36
* **Technology:** Hall effect sensor
* **Precision:** 12 bits / 0.1°

---

## Connectivity

### Connection

* **Ethernet:** 1×RJ45 - 10/100/1000 BASE T
* **WiFi:** IEEE 802.11a/b/g/n
* **WPAN (Bluetooth):** IEEE 802.15.1, 4.0 (LE)

---

## Software

* **Operating System:** Open Nao Embedded GNU/Linux Distribution based on Gentoo
* **Architecture:** x86
* **Programming:**
  * Embedded: C++ / Python
  * Remote: Java

---

*www.aldebaran.com*
