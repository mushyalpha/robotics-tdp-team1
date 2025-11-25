# Bonolo Development Log

## Development Progress

#### Week 2 (Oct 13-19, 2025)

- **Oct 17 - Bonolo:** Project structure setup and initial file templates
  ├─ Created comprehensive README file explaining project structure
  ├─ Created initial code templates:
  │  ├─ balance_controller.py
  │  ├─ motion_controller.py
  │  ├─ kick_algorithm.py
  │  └─ trajectory_planner.py
  └─ **Time Spent:** 7 hours

#### Week 3 (Oct 20-26, 2025)

- **Oct 20-26 - Bonolo:** Team onboarding and GitHub workflow setup
  ├─ **GitHub workflow presentation (2 hours)**
  │  ├─ Created slides covering branching strategy, PR process, and collaborative development
  │  └─ Prepared handouts with quick reference commands
  ├─ **Development log templates (1 hour)**
  │  ├─ Created templates for all 6 work packages in `src/wp[X]_*/development_log.md`
  │  ├─ Standardised format for tracking technical progress and decisions
  │  └─ Documented logging requirements and entry format guidelines
  ├─ **GitHub workflow infrastructure (2 hours)**
  │  ├─ Set up branch protection rules and PR templates
  │  ├─ Configured repository structure for collaborative development
  │  ├─ Demonstrated workflow to team members
  │  └─ Day-to-day updating of the repository
  └─ **Codebase and documentation updates (2 hours)**
  ├─ Restructured project layout for clarity
  ├─ Updated README with current project status
  └─ Cleaned and organised documentation

#### Week 4 (Oct 27 - Nov 2, 2025)

- **Oct 27 - Nov 2 - Bonolo:** NAO6 research and initial testing
  ├─ Researched NAO6 kinematics
  ├─ Conducted initial motion testing in Webots
  └─ Created robot constraints file to define limitations of the robot

#### Week 5 (Nov 3 - Nov 9, 2025)

- **Nov 3 - Bonolo:** Major update to robot_constraints.py with actual NaoV6.proto values
  ├─ **Design Decision:** Use NaoV6.proto as authoritative source for robot constraints
  ├─ **Actions taken:**
  │  ├─ Compared legacy NAO.proto vs current NaoV6.proto
  │  ├─ Updated all joint torque values (significant percentage increases discovered)
  │  ├─ Added asymmetric leg joint limits (left vs right knee/ankle)
  │  └─ Verified file runs correctly with new values
  ├─ **Key findings:**
  │  ├─ All torque values were significantly underestimated (legacy NAO values)
  │  ├─ Identified asymmetric leg limits that weren't previously documented
  │  └─ This will enable more accurate motion planning and force control
  └─ **Time Spent:** 3 hours

#### Week 6 (Nov 10 - Nov 16, 2025)

- **Nov 10 - Bonolo:** Created detailed task assignments for WP3 team
  ├─ **Task 1:** Walking Controller (Ciaran & Chengjie)
  │  └─ Comprehensive gait generation, speed control
  ├─ **Task 2:** Turning Controller (Zefu, Bonolo & Jinghao)
  │  └─ In-place rotation, arc walking, sidestepping
  └─ **Task 3:** Balance Controller (Bonolo and Jie)
  └─ PID control, IMU processing, fall recovery
  └─ **Time Spent:** 1 hour
- **Nov 13 - Bonolo:** Balance Controller Task 3.1 Implementation
  ├─ **Design Decision:** Three-zone stability architecture
  │  ├─ **Safe zone:** 0.12 rad roll, 0.15/0.20 rad pitch (from NAO6Constraints)
  │  ├─ **Balance zone:** 0.3 rad roll, 0.4 rad pitch (PID control can recover)
  │  └─ **Fall zone:** 0.7 rad roll, 0.8 rad pitch (requires fall recovery sequence)
  ├─ **Rationale:** Progressive control strategy allows appropriate response based on severity
  │  ├─ Minimal corrections in safe zone (energy efficient)
  │  ├─ Active PID control in balance zone (maintains stability)
  │  └─ Emergency recovery in fall zone (prevents damage)
  ├─ **Technical insight:** Body lean limits differ from joint limits
  │  ├─ Joint limits = physical range of motion (hardware constraint)
  │  └─ Body lean limits = maximum tilt before CoM leaves support polygon (stability constraint)
  ├─ **Implementation:**
  │  ├─ Designed three-zone stability system (safe/balance/fall zones)
  │  ├─ Integrated NAO6Constraints body lean limits into stability logic
  │  ├─ Implemented stability state detection methods: `get_stability_state()`, `is_stable()`, `is_falling()`
  │  ├─ Added angular velocity threshold (3.7 rad/s) for early fall detection
  │  └─ Created Jupyter notebook for interactive development
  ├─ **Next steps:** Task 3.2 PID Controller implementation
  └─ **Time Spent:** 2.5 hours
- **Nov 13 - Bonolo:** Team Development Logging Strategy Refinement
  ├─ **Design Decision:** Centralised team log (`team_controllers_development_log.md`) instead of individual member logs
  ├─ **Rationale:**
  │  ├─ Reduces overhead for team members (no daily logging requirement)
  │  ├─ Centralises technical decisions for easier report writing
  │  ├─ Makes it easier for team to see each other's work and learn from decisions
  │  └─ Personal notes (Obsidian) remain private but key decisions are shared
  ├─ **Implementation:**
  │  ├─ Created shared log with clear structure for Tasks 1-3 (Walking, Turning, Balance controllers)
  │  ├─ Added template examples and logging guidelines
  │  ├─ Organised algorithm choices by task/controller
  │  └─ Separated personal detailed log (`bonolo_development_log.md`) from team log
  ├─ **Repository Management:**
  │  ├─ Added `obsidian/` to `.gitignore` to keep personal notes private
  │  ├─ Clarified Git workflow (no need to checkout develop for most operations)
  │  └─ Documented best practices for feature branch management
  ├─ **Impact:** Team now has clear, low-overhead process for documenting technical decisions
  └─ **Time Spent:** 1.5 hours
- **Nov 16 - Bonolo:** Repository Management and Git Workflow Refinement
  ├─ **Context:** Continued refinement of team development logging strategy and repository management practices
  ├─ **Actions taken:**
  │  ├─ Verified `.gitignore` was correctly configured to exclude `obsidian/` folder (personal notes)
  │  ├─ Fixed Git merge conflict by committing `.gitignore` changes before pulling from develop
  │  ├─ Successfully integrated latest develop branch changes into feature branch
  │  └─ Documented Git workflow clarification: no need to checkout develop for most operations
  ├─ **Key learnings:**
  │  ├─ `git pull origin develop` from feature branch merges develop into current branch (recommended workflow)
  │  ├─ Only need to checkout develop when creating new branches or reviewing develop state
  │  └─ Personal notes in Obsidian remain private while technical decisions are documented in team log
  ├─ **Impact:** Streamlined Git workflow reduces confusion and prevents merge conflicts
  └─ **Time Spent:** 1.5 hours
- **Nov 17 - Bonolo:** Webots Controller Debugging and Repository Management
  ├─ **Context:** my_nao_demo controller not working - robots not responding to keyboard input
  ├─ **Root Cause Analysis:**
  │  ├─ Identified console output was from balance_controller (different NAO robot), not my_nao_demo
  │  ├─ Discovered device naming mismatch: lowercase names ("accelerometer") vs actual NAO devices ("Accelerometer")
  │  └─ Controller was crashing on initialization due to NoneType errors when devices weren't found
  ├─ **Actions taken:**
  │  ├─ Fixed device names: "accelerometer" → "Accelerometer", "gyro" → "Gyro", "gps" → "GPS"
  │  ├─ Added safety checks (null validation) for all device initialization to prevent crashes
  │  ├─ Added position clamping (0.0 to 0.96) in set_hands_angle() to eliminate floating-point precision warnings
  │  └─ Controller now successfully initializes and responds to keyboard input
  ├─ **Repository Management - Webots World Files:**
  │  ├─ **Design Decision:** Template-based world file system to prevent simulation state commits
  │  ├─ **Implementation:**
  │  │  ├─ Created robocup_template.wbt as clean reference (tracked in git)
  │  │  ├─ Added robocup.wbt to .gitignore (local working copy, not tracked)
  │  │  └─ Documented workflow in team discussion for copying template when needed
  │  ├─ **Rationale:**
  │  │  ├─ Webots modifies .wbt files during simulation (robot positions, camera angles, physics state)
  │  │  ├─ Creates hundreds of lines of diff that aren't actual code changes
  │  │  └─ Template system allows local simulation without creating git noise
  │  └─ **Impact:** Team members can run simulations freely without committing simulation state
  ├─ **Key learnings:**
  │  ├─ Webots device names are case-sensitive - always check actual device names in PROTO files
  │  ├─ Multi-robot simulations require careful attention to which controller outputs which messages
  │  ├─ Defensive programming (null checks) prevents cascading failures in robotics controllers
  │  └─ Git workflow discussion: importance of pulling before pushing to prevent conflicts
  └─ **Time Spent:** 1 hour
- **Nov 17 (3:30-5:30 PM) - Bonolo:** Balance Controller Task 3.5 & 3.6 - Fall Recovery Architecture Design
  ├─ **Context:** Designing fall recovery sequences and balance adjustment calculations for NAO6
  ├─ **Design Decision:** Separate balance control from fall recovery with clear state transitions
  │  ├─ **Balance adjustments** (Task 3.5): PID-based corrections for small disturbances
  │  ├─ **Fall recovery sequences** (Task 3.6): Multi-phase scripted motions for getting up after falls
  │  └─ Both driven by real-time IMU + gyro data in Webots controller
  ├─ **Key Technical Insights:**
  │  ├─ **Hardware limits vs operational limits:** NAO6Constraints contains maximum possible values, not safe operating ranges
  │  │  ├─ Need to define safety margins (e.g., 80% of joint range) for control and recovery
  │  │  ├─ Robot becomes unstable (~0.15 rad pitch) well before reaching joint limits
  │  │  └─ Should use get_safe_joint_limit() when designing recovery keyframes
  │  ├─ **IMU reading importance:** Must read IMU every robot.step() to close feedback loop
  │  │  ├─ InertialUnit provides roll/pitch/yaw angles (rad)
  │  │  ├─ Gyro provides angular velocities (rad/s) for roll_rate, pitch_rate, yaw_rate
  │  │  └─ Enables reactive control vs open-loop pre-scripted motions
  │  ├─ **Threshold region refinement:** Clarified three-zone architecture needs explicit boundaries
  │  │  ├─ Safe zone: minimal/no correction (e.g., roll < 0.10, pitch < 0.10/0.12)
  │  │  ├─ Balance zone: PID active (e.g., roll < 0.25, pitch < 0.30)
  │  │  └─ Fall zone: recovery sequence triggered (e.g., roll > 0.6, pitch > 0.6, OR angular velocity > 3.7 rad/s)
  │  └─ **Fall detection:** Must combine angle AND angular velocity for early detection
  ├─ **Implementation Progress:**
  │  ├─ Completed `calculate_balance_adjustments()` design (Task 3.5)
  │  │  ├─ PID corrections applied to ankle roll/pitch (primary) and hip roll/pitch (secondary, 0.3-0.5x gain)
  │  │  ├─ Output clamping to ±0.2 rad per control cycle for safety
  │  │  └─ Ready for integration with real IMU data in Webots
  │  ├─ Completed `FallRecovery` class structure (Task 3.6)
  │  │  ├─ `detect_fall_direction()`: determines front/back/left/right from roll/pitch
  │  │  ├─ `get_recovery_sequence_front()`: 5-phase recovery (tuck → push → feet under body → stand → stable)
  │  │  ├─ `get_recovery_sequence_back()`: placeholder structure (to be tuned)
  │  │  └─ `update_recovery()`: phase timing (1 sec per phase) and completion detection
  │  └─ Fixed logic bug: `is_falling()` was always returning False (missing angular velocity check)
  ├─ **Testing Strategy Defined:**
  │  ├─ **Phase 1:** Prototype in Jupyter notebook with fake IMU data to verify state transitions
  │  ├─ **Phase 2:** Move logic into Webots controller (balance_controller.py)
  │  ├─ **Phase 3:** Test in Webots by manually pushing robot or using tipped initial poses
  │  ├─ **Phase 4:** Tune thresholds based on real behavior (e.g., "wobbly at 0.15 pitch")
  │  └─ **Phase 5:** Validate recovery sequences respect NAO6Constraints limits
  ├─ **Next Steps:**
  │  ├─ Complete Task 3.5 & 3.6 TODOs in balance_controller.ipynb
  │  ├─ Test balance adjustment logic with simulated IMU data
  │  ├─ Integrate FallRecovery into balance_controller.py for Webots testing
  │  ├─ Tune recovery sequence joint angles using NAO6Constraints.get_safe_joint_limit()
  │  └─ Begin Task 3.2 (PID Controller) and Task 3.3 (IMU Processing) if time permits
  └─ **Time Spent:** 2 hours

## Technical Decisions

### Architecture Decisions

| Decision                              | Date   | Rationale                                                 | Impact   |
| ------------------------------------- | ------ | --------------------------------------------------------- | -------- |
| Python for control algorithms         | Oct 17 | Team familiarity, NAOqi compatibility                     | Positive |
| Modular controller design             | Oct 17 | Easier testing and maintenance                            | Positive |
| Use NaoV6.proto as constraints source | Nov 3  | Ensures simulation accuracy, matches actual hardware      | Critical |
| Centralised team development log      | Nov 16 | Reduces overhead, centralises decisions, easier reporting | Positive |
| Template-based Webots world files     | Nov 17 | Prevents simulation state commits, reduces git noise      | Positive |

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

*Last updated: November 17, 2025*
