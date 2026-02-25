# Robotics TDP: Team 1 Pitch Presentation

## Introduction

### Project Goal

Develop a simulation of 2 Robocup teams and their playing environment, and use this simulation to design and develop the behavioral algorithms for those teams

### Requirements Summary

* 2 teams of 4 NAO6 robots each with 3 behaviours: Goalkeeper, Defender, Striker
* Follow the general rules of soccer as outlined by RoboCup
* Totally autonomous with ability to react to state of play

### Presentation Structure

1. Introduction
2. Methodology
3. Results and Analysis
4. Conclusions
5. Demonstration

---

## Introduction: Project Structure

### Work Packages Overview

Six individual work packages (WPs) organized across Full Project, Simulation Phase, and Hardware Phase:

1. **Project Management and Specification** - Lead: Jie Shu
2. **Simulation Environment Development** - Lead: Bonolo Masima
3. **Guidance and Control** - Lead: Wang Zefu
4. **Behavioural Algorithms** - Lead: Chengjie Hao
5. **Integration** - Lead: Wang Jinghao
6. **Testing** - Lead: Ciaran Breen

### Project Organization

* Project Manager handles non-technical project tasks
* All team members lead one WP and will assist with others
* Project documentation and organization run with Microsoft Teams
* Simulation code version control, documentation, and collaboration using GitHub

---

## Methodology: Initial Plan

### Development Pipeline

```
NAO6 + Environment Model → 3D Physics Simulation (Webots) → 3D Controllers and Guidance (Python) → Behavioural Algorithms → Testing
```

**Key Components:**

* Webots simulation environment
* Walking gait derived from Webots motion files

---

## Methodology: Revised

### Updated Development Pipeline

```
NAO6 + Environment Model → 3D Physics Simulation (Webots) → 3D Controllers (Python) → Behaviour Testing
                                                            ↓
                                                  2D Behavioural Simulation → Behavioural Algorithms
```

### Issues Identified

1. Simulation time constraints
2. Sequential structure causes bottleneck in development

### Solution: 2D Simulation for Behavioral Development

1. Much quicker to run simulations
2. Start behavioral development while continually updating with kinematic parameters from 3D

### Performance Comparison

| Platform | Mode       | Sim Time (real/sim) |
| -------- | ---------- | ------------------- |
| Webots   | Normal     | 0.12                |
| Webots   | Fast       | 0.13                |
| Webots   | No Visuals | 0.26                |

---

## Results: 3D Simulation Kinematics

### Walking Performance

* **Max Stable Frequency:** 1.4 steps/s
* **Max Velocity:** 12 cm/s
* **Average Drift:** ~0.8 cm/m (@ max velocity)

### Turning (with PID balance control)

* **Average Yaw Speed:** 0.424 rad/s
* **Max Yaw Speed:** 0.831 rad/s

### Kicking

* **Kick Distance:** ~1.3m

### Recovery from Fall

* **Recovery Time:** ~26s (from lying on back)

---

## Results: 2D Behavior Testing

### Algorithm Variants Developed

* **Basic:** All robots chase ball (baseline behavior)
* **Positioning:** Closest robot chases, others freeze
* **Passing**

### 2D Simulation Features

* Ball trajectory realism: spin, friction
* Kick accuracy: Angular error increases with distance (0.15 radians)
* Maximum ball speed: 3.0 m/s
* Status Window added

---

## Conclusions

### Summary

* Defined final simulation workflow and completed development of simulation environment
* Developed 3D controllers and extracted key kinematic parameters
* Begun behavior development and optimization in 2D simulations
* Incremental algorithm development has proved to improve measurable performance and behaviour
* Key challenges: Overcoming bottleneck in development of 3D controllers and robot coordination

### Next Steps

**Evolving Behavioral Strategy:**

* Developing individual algorithms for Goalkeeper, Defender, Striker
* Optimization and evaluation of team strategies

**Improve 2D Simulation:**

* More realistic kinematics from 3D simulation tests
* Fully integrate RoboCup rules and match logic into tests

**Final Phase:**

* Integration into hardware and final testing

---

## Demonstration

*[Demonstration section]*

---

## Thank You for Listening!

**Any Questions?**

#UofGWorldChangers

@UofGlasgow
