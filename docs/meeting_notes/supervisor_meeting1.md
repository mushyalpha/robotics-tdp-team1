# Robotics TDP Team 1: Supervisor Meeting 1
**Date:** Thursday, 8th October  
**Location:** Rankine 401

## Project Management Breakdown Structure

The project is organized into six individual work packages (WPs) spanning the full project lifecycle, including simulation and hardware phases:

- **Behavioural Algorithms**
- **Operation**
- **Testing**
- **Simulation Environment Development**
- **Project Management and Specification**
- **Guidance and Control**

### Key Principles:
- Project Manager handles non-technical project tasks
- All team members lead one WP and assist with at least one other
- All team members are involved at all phases of project

## Waterfall Approach
*Adapted slightly to fit group capability*

---
## WP1: Project Management and Specification
**WP Manager:** Ciarán Breen  
**WP Team:** Everyone!

### Key Tasks:
- Handles all non-technical project tasks (scheduling, task and time management, meeting organization, etc.)
- Handles communication with supervisor and manager
- Lead requirements definition

### Deliverables:
- Project Plan + requirements
- Design Review Report

---

## WP2: Simulation Environment Development
**WP Manager:** Jie Shu  
**WP Team:** Ciarán Breen

### Key Tasks:
- Evaluate and choose appropriate simulation platform for NAO6, pitch, and ball
- Create initial simulation of NAO6 (to be handed over to WP3)
- Create and develop simulation of environment (pitch and ball)

### Deliverables:
Full simulation environment containing:
- NAO6 robots (without complex control)
- Pitch and Ball

---

## WP3: Guidance and Control
**WP Manager:** Bonolo Masima  
**WP Team:** Zefu Wang, Chengjie Hao

### Key Tasks:
- In simulation, take the model developed by WP2 and add low level control operations (e.g. movement, ball striking, tackling)
- Test operations in simulation
- Support integration of software into hardware
- Support operation and testing

### Deliverables:
- Fully validated simulation of NAO6 robot
- Integration of control software to hardware

---

## WP4: Behavioral Algorithm Development
**WP Manager:** Zefu Wang  
**WP Team:** Jinghao Wang

### Key Tasks:
- Create basic behavioral algorithm to allow robot operation
- Develop custom behaviors for Goalkeeper, Defender, Attackers
- Optimize tactical behavior
- Test algorithms in simulation

### Deliverables:
High Level Behavioral Algorithms for:
- Goalkeeper
- Defender
- Attacker

---

## WP5: Implementation
**WP Manager:** Chengjie Hao  
**WP Team:** Bonolo Masima, Jie Shu, Zefu Wang

### Key Tasks:
- Implementation of environment sensing hardware control
- Transfer of software (guidance and control, behavioral algorithms) to hardware
- Support for field test and final field test

### Deliverables:
- Fully operational set of robots
- Robots operating within physical pitch environment

---

## WP6: Testing
**WP Manager:** Jinghao Wang  
**WP Team:** Ciarán Breen

### Key Tasks:
- Organization of hardware system tests
- Feedback of test results to WP5
- Organization of final field test
- Reporting of test results

### Deliverables:
- Testing Plan
- Fully Validated System

---

## Gantt Chart
*Collapsed View - See attached diagram*

---

## Cost Estimate

**Project Duration:** 19 weeks total during term
- Week 3 (not incl. kickoff) – Week 10 in Semester 1 (8 weeks)
- Week 1 – Week 11 in Semester 2 (11 weeks)

**Time Allocation:** 10 hours per person per week (2hrs meetings + 8hrs technical)

### Cost Breakdown:
- **Team Staff Costs:** £250/hr × 10hrs × 6 team members × 19 weeks = **£285,000**
- **Expert Help:** 20hrs estimated (~ 1hr per week)
- **Expert Staff Costs:** £1250/hr × 20 hrs = **£25,000**

**Total Project Cost: £310,000**

---

## Action Items for Next Week

1. **Define simulation platform:** Webots + Matlab/ROS/Python?
2. **Define requirements** for each work package
3. **Set up document/code sharing service**
4. **Load NAO6 Template** in Webots