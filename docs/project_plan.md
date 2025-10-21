# Project Plan - NAO6 Robot Soccer Team

## Executive Summary

This document outlines the project plan for Team 1's development of autonomous NAO6 robots for RoboCup Humanoid League soccer competition. The project runs from October 2025 to April 2026, divided into simulation and hardware phases.

## Project Objectives

### Primary Goals

1. Develop a complete Webots simulation environment for NAO6 robot soccer
2. Implement autonomous behavioral algorithms for robot players
3. Successfully transfer algorithms to physical NAO6 robots
4. Demonstrate competitive soccer-playing capabilities

### Success Criteria

- [ ] Functional simulation with 4v4 robot teams
- [ ] Three distinct player behaviors (Goalkeeper, Defender, Attacker)
- [ ] Successful hardware deployment
- [ ] Pass Design Review (February 2026)
- [ ] Complete field testing (March 2026)

## Work Package Structure

### WP1: Project Management

**Manager:** Ciarán Breen
**Duration:** Full project lifecycle

**Responsibilities:**

- Project scheduling and coordination
- Team communication
- Supervisor liaison
- Documentation management
- Time and cost tracking

**Deliverables:**

- Project plan
- Bi-weekly TAR reports
- Design review documentation
- Final report coordination

### WP2: Simulation Environment Development

**Manager:** Jie Shu
**Team:** Ciarán Breen
**Duration:** October 2025 - January 2026

**Responsibilities:**

- Webots platform setup
- Pitch and ball physics modeling
- Environment configuration
- Simulation optimization

**Deliverables:**

- Webots world files
- Environment documentation
- Physics validation results

### WP3: Guidance and Control

**Manager:** Bonolo Masima
**Team:** Zefu Wang, Chengjie Hao
**Duration:** November 2025 - March 2026

**Responsibilities:**

- Low-level robot control
- Motion primitives (walk, kick, turn)
- Balance and stability control
- Hardware integration support

**Deliverables:**

- Motion control library
- Control algorithms documentation
- Hardware calibration procedures

### WP4: Behavioral Algorithms

**Manager:** Zefu Wang
**Team:** Jinghao Wang
**Duration:** December 2025 - March 2026

**Responsibilities:**

- High-level decision making
- Role-specific behaviors
- Team coordination strategies
- Game state management

**Deliverables:**

- Behavioral state machines
- Strategy documentation
- Performance metrics

### WP5: Implementation

**Manager:** Chengjie Hao
**Team:** Bonolo Masima, Jie Shu, Zefu Wang
**Duration:** February 2026 - April 2026

**Responsibilities:**

- Hardware setup and configuration
- Software deployment to NAO6
- Sensor integration
- System integration

**Deliverables:**

- Deployment scripts
- Hardware configuration files
- Integration test results

### WP6: Testing

**Manager:** Jinghao Wang
**Team:** Ciarán Breen
**Duration:** January 2026 - April 2026

**Responsibilities:**

- Test planning and execution
- Performance evaluation
- Bug tracking and reporting
- Field test coordination

**Deliverables:**

- Test plans and procedures
- Test reports
- Performance analysis
- Bug tracking logs

## Timeline

### Phase 1: Simulation (October 2025 - February 2026)

#### October 2025

#### November 2025

#### December 2025

#### January 2026

#### February 2026

### Phase 2: Hardware (February 2026 - April 2026)

#### February 2026 (continued)

#### March 2026

#### April 2026

## Resource Allocation

### Human Resources

- 6 team members
- 10 hours/person/week estimated effort
- Total: 60 person-hours/week

### Technical Resources

- Webots simulation software
- NAO6 robots (provided by university)
- Choregraphe software
- Computing resources for simulation

### Budget Estimate

- Team Staff Costs: £250/hr × 10hrs × 6 members × 19 weeks = £285,000
- Expert Consultation: £1250/hr × 20hrs = £25,000
- **Total Project Cost: £310,000**

## Risk Management

### Technical Risks

| Risk                       | Probability | Impact | Mitigation                             |
| -------------------------- | ----------- | ------ | -------------------------------------- |
| Simulation accuracy issues | Medium      | High   | Early validation, iterative refinement |
| Hardware malfunction       | Low         | High   | Backup robots, careful handling        |
| Integration challenges     | Medium      | Medium | Incremental integration, testing       |
| Performance bottlenecks    | Medium      | Medium | Profiling, optimization                |

### Project Risks

| Risk                | Probability | Impact | Mitigation                         |
| ------------------- | ----------- | ------ | ---------------------------------- |
| Schedule delays     | Medium      | Medium | Buffer time, parallel development  |
| Team member absence | Low         | Medium | Knowledge sharing, documentation   |
| Scope creep         | Medium      | Medium | Clear requirements, change control |

## Communication Plan

### Regular Meetings

- **Weekly team meetings:** Thursdays 2-4pm
- **Supervisor meetings:** Bi-weekly, Thursdays
- **Technical sync-ups:** As needed

### Communication Channels

- GitHub: Code and documentation
- Teams/Discord: Daily communication
- Email: Official communications

### Reporting

- Bi-weekly TAR submissions
- Monthly progress reports
- Design review presentation
- Final presentation and report

## Quality Assurance

### Code Quality

- Peer code reviews via pull requests
- Automated testing (pytest)
- Coding standards documentation
- Continuous integration

### Documentation Standards

- README files for all modules
- Inline code documentation
- API documentation
- User guides

### Testing Strategy

- Unit testing for individual components
- Integration testing for subsystems
- System testing in simulation
- Field testing on hardware

## Success Metrics

### Simulation Phase

- [ ] Stable 30+ FPS simulation
- [ ] Complete 10-minute matches without crashes
- [ ] All three robot behaviors functional
- [ ] 80% test coverage

### Hardware Phase

- [ ] Successful deployment to all robots
- [ ] < 100ms control loop latency
- [ ] Successful ball tracking and kicking
- [ ] Complete match without falls

## Dependencies

### External Dependencies

- Webots software updates
- NAOqi SDK availability
- Hardware availability schedule
- University facility access

## Change Management

### Change Request Process

1. Submit issue on GitHub
2. Team discussion in weekly meeting
3. Impact assessment
4. Approval by PM and affected WP managers
5. Update documentation
6. Implement change

### Version Control

- Git for code management
- Semantic versioning for releases
- Tagged releases for milestones

---

*Document Version: 1.0*
*Last Updated: October 2025*
*Next Review: November 2025*
