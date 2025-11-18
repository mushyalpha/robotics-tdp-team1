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

## Technical Decisions

### Architecture Decisions

| Decision                              | Date   | Rationale                                                 | Impact   |
| ------------------------------------- | ------ | --------------------------------------------------------- | -------- |
| Python for control algorithms         | Oct 17 | Team familiarity, NAOqi compatibility                     | Positive |
| Modular controller design             | Oct 17 | Easier testing and maintenance                            | Positive |
| Use NaoV6.proto as constraints source | Nov 3  | Ensures simulation accuracy, matches actual hardware      | Critical |
| Centralised team development log      | Nov 16 | Reduces overhead, centralises decisions, easier reporting | Positive |

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

*Last updated: November 16, 2025*
