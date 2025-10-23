# WP3: Guidance and Control - Development Log

**Work Package Manager:** Bonolo Masima
**Team Members:** Zefu Wang, Chengjie Hao
**Duration:** October 2025 - February 2026

## Objectives

- Develop low-level control algorithms for NAO6 robot
- Implement motion control (walking, turning, balance)
- Create ball manipulation algorithms (kicking, dribbling)
- Integrate vision processing for ball and field detection
- Support hardware integration and testing

## Technical Requirements

- Walking speed:
- Stand-up time: <20s
- Kick accuracy:
- Vision processing:
- Control loop frequency:
- RoboCup rule compliance

---

## Development Progress

### Phase 1: Basic motion control framework

#### Week 2 (Oct 13-19, 2025)

- [X] Set up project structure and files
- [X] Create initial controller templates

**Detailed Entries:**

- **Oct 17 - Bonolo:** Created balance_controller.py, motion_controller.py, kick_algorithm.py, trajectory_planner.py templates

**Time Spent:** 7 hours

#### Week 3 (Oct 20-26, 2025)

- [ ] Define control system architecture
- [ ] Research NAO6 kinematics
- [ ] Implement basic walking algorithm
- [X] Set up simulation testing environment
- [ ] Define control interfaces

#### Week 4 (Oct 27 - Nov 2, 2025)

- [ ] Balance controller implementation
- [ ] Initial motion testing

### Phase 2: Core Development (Weeks 4-8)

**Target:** Functional motion and ball control

- [ ] PID controller implementation
- [ ] Walking gait optimisation
- [ ] Kick algorithm development
- [ ] Vision integration

### Phase 3: Integration (Weeks 9-12)

**Target:** System integration and testing

- [ ] Hardware integration
- [ ] Performance optimisation
- [ ] System testing

### Phase 4: Validation (Weeks 13-16)

**Target:** Final testing and validation

- [ ] Field testing
- [ ] Performance validation
- [ ] Documentation completion

---

## Technical Decisions

### Architecture Decisions

| Decision                      | Date   | Rationale                             | Impact   |
| ----------------------------- | ------ | ------------------------------------- | -------- |
| Python for control algorithms | Oct 17 | Team familiarity, NAOqi compatibility | Positive |
| Modular controller design     | Oct 17 | Easier testing and maintenance        | Positive |

### Algorithm Choices

| Component       | Algorithm      | Justification           |
| --------------- | -------------- | ----------------------- |
| Balance Control | PID Controller | Simple, proven, tunable |
| Walking Gait    | TBD            | Research needed         |
| Kick Control    | TBD            | Depends on ball physics |

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

---

## Code Metrics

| Metric               | Current | Target | Status |
| -------------------- | ------- | ------ | ------ |
| Lines of Code        | ~24     | TBD    | 🟡     |
| Test Coverage        | 0%      | 80%    | 🔴     |
| Functions Documented | 0%      | 100%   | 🔴     |
| Performance Tests    | 0       | 10+    | 🔴     |

---

## Resources and References

### Documentation

- [NAO6 Technical Specifications](https://www.softbankrobotics.com/emea/en/nao)
- [NAOqi Python SDK Documentation](http://doc.aldebaran.com/2-8/index.html)
- [RoboCup Humanoid League Rules](https://humanoid.robocup.org/)

### Research Papers

- *Add relevant papers as research progresses*

### Code Repositories

- *Add external libraries and references*

---

*Last updated: October 17, 2025*
