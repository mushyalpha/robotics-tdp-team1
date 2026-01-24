# WP4: Behavioral Algorithm Development - Development Log

**Work Package Manager:** Zefu Wang
**Team Members:** Jinghao Wang
**Duration:** October 2025 - February 2026

## Objectives

- Create basic behavioural algorithm to allow robot operation
- Develop custom behaviours for Goalkeeper, Defender, Attackers
- Optimise tactical behaviour
- Test algorithms in simulation

## Technical Requirements

- First: The robot can reliably walk
- Next: The robot can attempt to interact with the ball
- Final: The robot performs well across different environmental conditions

## Deliverables

- Definition of action space & observation space & reward function
- TensorBoard logs of training
- Three different role models (Goalkeeper, Defender, Attacker)

---

## Development Progress

### Week 1 (Oct 14-20, 2025)

- [ ] *Add your weekly progress here*

### Week 2 (Oct 21-27, 2025)

- [ ] *Add your weekly progress here*

### Week 3 (Oct 28 - Nov 3, 2025)

- [ ] *Add your weekly progress here*

---

## Technical Decisions

### Algorithm Choices

| Component            | Algorithm | Justification |
| -------------------- | --------- | ------------- |
| *Add your choices* |           |               |

### Architecture Decisions

| Decision               | Date | Rationale | Impact |
| ---------------------- | ---- | --------- | ------ |
| *Add decisions here* |      |           |        |

---

## Training Results

### Goalkeeper Behaviour

*Add training metrics and performance here*

### Defender Behaviour

*Add training metrics and performance here*

### Attacker Behaviour

17 December

09:59

Stage 1: Kick only demo

├─ Ball placed right in front of the robot's foot / we move the robot to the ball

Behaviour tree

├─ Play Shoot.motion to to kick the ball

├─ if motion is complete --> done

**Metrics**

kick motion complete

Ball moves

Kick execution time


Stage 2: GoToBall + Kick

├─ ball placed at different distances and role of the robot is to go to the ball

Behaviour tree

└─ if ball is not seen

    └─ turn and search ball

└─ Elif if ball dintance is out of shooting range

    └─ Go to ball (turn, walk forward, adjust as moving forward)

└─ trigger kick if within kicking distance

**Metrics**

**Time to reach kick distance, ball detection reliability, number of adjustments needed, ball travel distance**

---

### Team Coordination

### Dependencies on Other WPs

- **WP2:** Simulation environment for training
- **WP3:** Low-level control APIs and interfaces
- **WP5:** Hardware constraints and capabilities
- **WP6:** Testing scenarios and validation metrics

### Providing to Other WPs

- **WP5:** Trained behaviour models for hardware deployment
- **WP6:** Behaviour specifications for testing

---

*Last updated: October 17, 2025*
