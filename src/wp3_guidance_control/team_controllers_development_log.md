# WP3: Guidance and Control - Controllers Team Development Log

**Duration:** 10 October 2025 - 23 October 2026
**Scope:** Shared log for all WP3 controller work (walking, turning, balance)

Task 1: Walking Controller (Ciaran & Chengjie) – gait generation, speed control

Task 2: Turning Controller (Zefu, Bonolo & Jinghao) – in-place rotation, arc walking, sidestepping

Task 3: Balance Controller (Bonolo & Jie) – PID control, IMU processing, fall recovery

### What to document:

- **Progress updates** - What you completed this week
- **Technical decisions** - Why you chose approach A over B
- **Algorithm choices** - Add to "Algorithm Choices" table below
- **Parameter values** - How you determined thresholds/gains
- **Problems & solutions** - What didn't work and why
- **Test results** - Performance data from simulation

### **Template Entry example:**

- **Nov 13 - Ciaran:** Walking Controller: Gait Generation (Task 1.1)
  - **Design Decision:** Linear Inverted Pendulum Model (LIPM) for gait
  - **Rationale:** Widely used in humanoid robotics, proven stability
  - **Parameters chosen:**
    - Step length: 0.05 m (conservative start)
    - Step time: 0.8 s (slower = more stable)
  - **Test result:** Robot walks 2 m forward without falling
  - **Next steps:** Increase step length to 0.08 m, test on uneven terrain

## Tips for Good Logging

1. **Be specific about numbers** – e.g. `PID gains: Kp=0.5, Ki=0.1, Kd=0.05` (not just “adjusted PID”)
2. **Explain WHY** – Always include the reason behind a decision
3. **Record failures** – “Tried X but robot fell because Y” is very valuable
4. **Link to code** – Reference file names and functions where possible
5. **Update algorithm table** – When you fix on an approach, add it under *Algorithm Choices*

**Note:** This shared log makes report writing easier and helps the team understand each other's work!

---

## Objectives

- Implement motion control (walking, turning, balance)

## Development Progress

### Basic motion control

#### Week 6 (Nov 10 - Nov 16, 2025)

**Detailed Entries:**

- **Nov 13 - Balance team:** Balance Controller
  - **Design Decision:** Three zone stability architecture
    - **Safe zone:** 0.12 rad roll, 0.15/0.20 rad pitch (from NAO6Constraints)
    - **Balance zone:** 0.3 rad roll, 0.4 rad pitch (PID control can recover)
    - **Fall zone:** 0.7 rad roll, 0.8 rad pitch (requires fall recovery sequence)
  - **Rationale:** Progressive control strategy allows appropriate response based on severity
    - Minimal corrections in safe zone (energy efficient)
    - Active PID control in balance zone (maintains stability)
    - Emergency recovery in fall zone (prevents damage)
  - **Technical insight:** Body lean limits differ from joint limits
    - Joint limits = physical range of motion (hardware constraint)
    - Body lean limits = maximum tilt before CoM leaves support polygon (stability constraint)
  - Implemented `get_stability_state()`, `is_stable()`, `is_falling()` methods
  - Added angular velocity threshold (3.7 rad/s) for early fall detection
  - Next: Task 3.2 PID Controller implementation

---

## Technical Decisions

### Algorithm Choices

Task 3: Balance Controller (team: Bonolo & Jie)

| Component               | Algorithm                     | Justification                                                     |
| ----------------------- | ----------------------------- | ----------------------------------------------------------------- |
| Balance Control         | PID Controller                | Simple, proven, tunable for real-time control                     |
| Balance Stability Zones | Three-zone progressive system | Allows energy-efficient minimal correction vs aggressive recovery |
| IMU Data Processing     | Low-pass filter               | Reduces sensor noise while maintaining responsiveness             |
| Fall Detection          | Angle + angular velocity      | Combines current state with rate of change for early detection    |
| Zero Moment Point (ZMP) | Simplified CoM projection     | Computationally efficient for real-time stability verification    |
| Walking Gait            | TBD                           | Research needed                                                   |
|                         |                               |                                                                   |

---

## Testing Results

### Motion Control Tests

*No tests completed yet*

---

#### Issues and Solutions

### Current Issues

*None reported*

### Resolved Issues

*None yet*

### Research Papers

- *Add relevant papers as research progresses*

### Code Repositories

- *Add external libraries and references*

---

*Last updated: November 13, 2025*
