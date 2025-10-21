# Development Log

**Project:** NAO6 Robot Soccer Team - TDP Team 1
**Period:** October 2025 - March 2026

## How to Use This Log

### Logging Process (Simplified)

**Bonolo Masima** maintains this main development log by:

1. **Reviewing individual WP logs** weekly
2. **Consolidating key progress** into this main log
3. **Tracking overall project status** and dependencies
4. **Preparing summaries** for project reporting

### Team Member Responsibilities

- **Maintain your WP log** in `docs/wp_logs/wp[X]_[name]_log.md`
- **Update weekly** with your progress and decisions
- **Flag blockers** that need team coordination
- **Reference commits/PRs** for traceability

### Entry Format (Consolidated by Technical Lead)

```
**[Date] - [Name] (WP[X])** - [Time spent]
- Key accomplishments (consolidated from WP logs)
- Important blockers or team coordination needs
- Critical decisions or milestones
- Related: [commit hash / PR link if applicable]
```

---

## Week 1 (October 14-20, 2025)

**Oct 17 - Bonolo Masima (WP3)** - 3 hours

- Set up GitHub repository structure
- Cleaned up documentation and streamlined README
- Next: Demonstrate GitHub workflow to team
- Related: Multiple commits to main branch

**Oct 17 - Ciarán Breen (WP1)** - 2 hours

- Organized supervisor meeting notes
- Defined action items for team members
- Coordinated meeting schedules
- Next: Complete TAR document

**Oct 17 - Jie Shu (WP2)** - 2 hours

- Downloaded RoboCup template in Webots
- Loaded NAO6 robot and pitch simulation
- Explored Webots environment setup
- Next: Share Webots setup instructions with team

---

## Week 2 (October 21-27, 2025)

*[Team members add entries here]*

---

## Week 3 (October 28 - November 3, 2025)

*[Team members add entries here]*

---

## Monthly Summary Template

### Month: [Month Year]

#### Achievements by Work Package:

- **WP1 (Project Management):**
- **WP2 (Simulation):**
- **WP3 (Guidance & Control):**
- **WP4 (Behavioral Algorithms):**
- **WP5 (Implementation):**
- **WP6 (Testing):**

#### Key Milestones Reached:

- [ ] Milestone 1
- [ ] Milestone 2

#### Challenges & Solutions:

- **Challenge:** Description
  - **Solution:** How it was resolved

#### Next Month Priorities:

1. Priority 1
2. Priority 2
3. Priority 3

---

## Project Statistics

*Updated monthly by WP1 (Project Manager)*

| Metric                  | Current | Target | Status |
| ----------------------- | ------- | ------ | ------ |
| Total Development Hours | 0       | 1140   | 🟡     |
| Code Coverage           | 0%      | 70%    | 🔴     |
| Completed Features      | 0       | TBD    | 🔴     |
| Tests Passing           | 0       | 100%   | 🔴     |

**Legend:** 🟢 On Track | 🟡 Attention Needed | 🔴 Behind Schedule

---

## Tips for Effective Logging

### ✅ Good Entries:

```
**Oct 20 - Alice (WP3)** - 4 hours
- Implemented PID controller for robot balance with Kp=1.2, Ki=0.1, Kd=0.05
- Fixed issue with ankle joint oscillation by adjusting damping parameters
- Tested walking stability on flat surface - 90% success rate
- Blocker: Need IMU calibration data from hardware team
- Next: Integrate with motion controller, test on slopes
- Related: commit abc123f, PR #15
```

### ❌ Poor Entries:

```
**Oct 20 - Alice (WP3)** - 4 hours
- Worked on balance stuff
- Fixed some bugs
- Next: More work
```

### 🎯 What to Include:

- **Specific accomplishments** with measurable results
- **Technical details** (parameters, algorithms, test results)
- **Time investment** for project reporting
- **Blockers and dependencies** for team coordination
- **Code references** for traceability

### 📝 Monthly Review Process:

1. **Week 4 of each month:** All team members update their sections
2. **WP1 (Project Manager):** Compiles monthly summary
3. **Team meeting:** Review progress and adjust plans
4. **Archive:** Move completed months to separate file if needed

---

*Last updated: October 17, 2025*
