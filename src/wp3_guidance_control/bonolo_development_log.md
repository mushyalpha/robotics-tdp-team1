# Bonolo Development Log

## Development Progress

#### Week 2 (Oct 13-19, 2025)

- [X] Set up project structure and files
- [X] Created comprehensive ReadMe file that explains our project structure
- [X] Create initial file code templates

**Detailed Entries:**

- **Oct 17 - Bonolo:** Created balance_controller.py, motion_controller.py, kick_algorithm.py, trajectory_planner.py templates

**Time Spent:** 7 hours

#### Week 3 (Oct 20-26, 2025)

- [X] Prepared mini presentation on GitHub workflow and repository structure for team onboarding (2 hours)
  - [X] Created slides covering branching strategy, PR process, and collaborative development
  - [X] Prepared handouts with quick reference commands
- [X] Created development log templates for all 6 work packages in **src/wp[X]_*/development_log.md** (1 hour)
  - [X] Standardised format for tracking technical progress and decisions
  - [X] Documented logging requirements and entry format guidelines
- [X] Implemented GitHub workflow infrastructure (2 hours)
  - [X] Set up branch protection rules and PR templates
  - [X] Configured repository structure for collaborative development
  - [X] Demonstrated workflow to team members
  - [X] day to day updating of the repository
- [X] Updated codebase files and documentation (2 hours)
  - [X] Restructured project layout for clarity
  - [X] Updated README with current project status
  - [X] Cleaned and organised documentation

#### Week 4 (Oct 27 - Nov 2, 2025)

- [X] Research NAO6 kinematics
- [X] Initial motion testing in webots
- [X] creating robot constraints file to define limitations of the robot

#### Week 5 (Nov 3 - Nov 9, 2025)

- [X] Update robot constraints from NaoV6.proto

  - [X] compared legacy NAO.proto vs current NaoV6.proto
  - [X] Updated all joint torque values (huge% increases)
  - [X] Added asymmetric leg joint limits (left vs right knee/ankle)
  - [X] Verified file runs correctly with new values

**Detailed Entries:**

- **Nov 3 - Bonolo:** Major update to robot_constraints.py with actual NaoV6.proto values
  - Discovered all torque values were significantly underestimated (legacy NAO values)
  - Identified asymmetric leg limits that weren't previously documented
  - This will enable more accurate motion planning and force control

**Time Spent:** 3 hours

#### Week 6 (Nov 10 - Nov 16, 2025)

- [X] Created detailed  task assignments for WP3 team (1 hours)

  - [X] Task 1: Walking Controller (Ciaran & Chengjie) - comprehensive gait generation, speed control
  - [X] Task 2: Turning Controller Zefu, Bonolo & Jinghao) - in-place rotation, arc walking, sidestepping
  - [X] Task 3: Balance Controller (for Bonolo and Jie) - PID control, IMU processing, fall recovery
- [X] Implemented Balance Controller - Task 3.1: Balance Parameters (1.5 hours)

  - [X] Designed three-zone stability system (safe/balance/fall zones)
  - [X] Integrated NAO6Constraints body lean limits into stability logic
  - [X] Implemented stability state detection methods
  - [X] Created Jupyter notebook for interactive development

**Detailed Entries:**

- **Nov 13 - Bonolo:** Balance Controller Task 3.1 Implementation
  - **Design Decision:** Three-zone stability architecture
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

**Time Spent:** 2.5 hours

### Phase 2: Guidance behaviour (4 Weeks)

**Target:** Functional motion and ball control

- [ ] PID controller implementation
- [ ] Walking gait optimisation
- [ ] Trajectory planning
- [ ] Kick algorithm development

---

## Technical Decisions

### Architecture Decisions

| Decision                              | Date   | Rationale                                            | Impact   |
| ------------------------------------- | ------ | ---------------------------------------------------- | -------- |
| Python for control algorithms         | Oct 17 | Team familiarity, NAOqi compatibility                | Positive |
| Modular controller design             | Oct 17 | Easier testing and maintenance                       | Positive |
| Use NaoV6.proto as constraints source | Nov 3  | Ensures simulation accuracy, matches actual hardware | Critical |

### Algorithm Choices

| Component               | Algorithm                     | Justification                                                     |
| ----------------------- | ----------------------------- | ----------------------------------------------------------------- |
| Balance Control         | PID Controller                | Simple, proven, tunable for real-time control                     |
| Balance Stability Zones | Three-zone progressive system | Allows energy-efficient minimal correction vs aggressive recovery |
| IMU Data Processing     | Low-pass filter               | Reduces sensor noise while maintaining responsiveness             |
| Fall Detection          | Angle + angular velocity      | Combines current state with rate of change for early detection    |
| Zero Moment Point (ZMP) | Simplified CoM projection     | Computationally efficient for real-time stability verification    |
| Walking Gait            | TBD                           | Research needed                                                   |
| Kick Control            | TBD                           | Depends on ball physics                                           |

---

## Testing Results

### Motion Control Tests

*No tests completed yet*

### Ball Manipulation Tests

*No tests completed yet*

### Integration Tests

*No tests completed yet*

---

## Issues and Solutions

### Current Issues

*None reported*

### Resolved Issues

*None yet*

### Research Papers

- *Add relevant papers as research progresses*

### Code Repositories

- *Add external libraries and references*

---

*Last updated: October 17, 2025*
