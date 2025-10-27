# Team Coordination & Current Tasks

**Project:** NAO6 Robot Soccer Team - TDP Team 1
**Last Updated:** October 24, 2025

---

## Current Sprint / Week

**Week 2: October 21-27, 2025**

### Active Tasks

| Task                                    | Assigned To      | Status  | Priority | Due Date | Notes |
| --------------------------------------- | ---------------- | ------- | -------- | -------- | ----- |
|                                         |                  |         |          |          |       |
|                                         |                  |         |          |          |       |
|                                         |                  |         |          |          |       |
| Divide WP tasks into specific sub-tasks | Each team member | Pending | Medium   |          |       |

### WP2: Simulation Environment - Next Steps

**Completed:**

- Jie imported NAO6 proto file into soccer.wbt
- Uploaded to GitHub (awaiting review/approval)

**Required Tasks (Priority Order):**

1. **Team Configuration & Physics** *(1 person)*

   - Set two teams with different colors
   - Configure initial positions and rotations
   - Verify physical parameters: mass, friction, center of gravity
2. **Sensor Configuration** *(1-2 people)*

   - Set camera angle for each robot
   - Configure sensors: sonar, gyro, accelerometer
   - Set camera resolution
3. **Basic Controller Setup** *(1-2 people)*

   - Assign controller to each robot
   - Enable simple forward motion
   - Configure speed settings

**Decision Pending:**

- 🚨 Should we use built-in Webots controllers for testing algorithms to accelerate simulation development?

---

## Team Communication

### Recent Updates

**October 24, 2025 - Jie Shu (WP2)**

- Imported NAO6 proto file into soccer.wbt
- Uploaded changes to GitHub (awaiting review)
- Identified 3 next simulation tasks (see above)
- Need team decision on controller approach

---

## Decisions Needed

| Decision                                  | Proposer    | Status | Due Date  | Discussion                                             |
| ----------------------------------------- | ----------- | ------ | --------- | ------------------------------------------------------ |
| Controller approach for Webots simulation | Jie         | Open   | ASAP      | Use built-in Webots controllers vs custom controllers? |
| NAO6 alternatives                         | Team        | Open   | ASAP      | Investigate alternatives if NAO6 not available         |
| Task assignments for simulation tasks     | WP2 Manager | Open   | This week | Who takes which of the 3 tasks?                        |

---

## Blockers & Issues

| Issue                                      | Owner  | Impact | Status      | Blocking                      | Next Steps                   |
| ------------------------------------------ | ------ | ------ | ----------- | ----------------------------- | ---------------------------- |
| NAO6 availability unknown                  | Team   | High   | Open        | Simulation hardware decisions | Investigate alternatives     |
| Simulation not integrated to GitHub        | Bonolo | High   | In Progress | Collaborative development     | Complete PR review and merge |
| Missing justification for Webots templates | TBD    | Medium | Open        | Documentation                 | Document rationale           |

---

## Next Actions (By Priority)

### High Priority

1. ⚠️ Resolve NAO6 availability issue - investigate alternatives
2. ⚠️ Complete simulation GitHub integration (awaiting review)
3. ⚠️ Make decision on Webots controller approach
4. ⚠️ Assign team members to simulation tasks

### Medium Priority

1. Document Webots templates justification
2. Divide WP tasks into specific sub-tasks
3. Share Webots setup instructions with team

### Low Priority

- Review and update individual WP development logs
- Update meeting notes

---

## Work Package Status Overview

| WP                      | Manager       | Status         | Progress             | Next Milestone       | Blockers                 |
| ----------------------- | ------------- | -------------- | -------------------- | -------------------- | ------------------------ |
| WP1: Project Management | Ciarán Breen | 🟢 On Track    | Setup complete       | TAR document         | None                     |
| WP2: Simulation         | Jie Shu       | 🟡 In Progress | Proto file imported  | Team configuration   | Need NAO6 decision       |
| WP3: Guidance & Control | Bonolo Masima | 🟡 Setup       | Repo structure ready | GitHub workflow demo | None                     |
| WP4: Behavioral         | Zefu Wang     | 🔴 Not Started | -                    | -                    | Waiting on WP2           |
| WP5: Implementation     | Chengjie Hao  | 🔴 Not Started | -                    | -                    | Waiting on WP2, WP3      |
| WP6: Testing            | Jinghao Wang  | 🔴 Not Started | -                    | -                    | Waiting on all other WPs |

**Legend:** 🟢 On Track | 🟡 In Progress | 🟠 At Risk | 🔴 Blocked/Not Started

---

## Meeting Notes Summary

### Supervisor Meeting 3 - October 21, 2025

**Key Topics:**

- NAO5 vs NAO6 availability discussion
- Need to investigate NAO6 alternatives
- Simulation environment development priorities
- Modelling stage requirements

**Action Items:**

- Investigate NAO6 alternatives and availability
- Integrate simulation into GitHub repository
- Document justification for using Webots templates
- Divide WP into specific tasks

[See full notes: `docs/meeting_notes/supervisor_meeting3.md`]

---

## Project Statistics

| Metric                  | Current | Target | Status |
| ----------------------- | ------- | ------ | ------ |
| Total Development Hours | ~8      | 1140   | 🟢     |
| Active Team Members     | 6       | 6      | 🟢     |
| Code Coverage           | 0%      | 70%    | 🔴     |
| Completed Features      | 1       | TBD    | 🟢     |
| Tests Passing           | N/A     | 100%   | -      |

**Legend:** 🟢 On Track | 🟡 Attention Needed | 🔴 Behind Schedule

---

## GitHub Workflow

### Current Branches

- `main` - Production-ready code
- `develop` - Integration branch for all features
- `feature/wp3` - Work package 3 development
- *[Other feature branches as needed]*

### Pull Requests

- Jie's simulation changes (awaiting review)
- *[List active PRs here]*

---

## Team Information

| Name          | WP  | Role                          | Contact |
| ------------- | --- | ----------------------------- | ------- |
| Ciarán Breen | WP1 | Project Manager               |         |
| Jie Shu       | WP2 | Simulation Manager            |         |
| Bonolo Masima | WP3 | Guidance & Control Manager    |         |
| Zefu Wang     | WP4 | Behavioral Algorithms Manager |         |
| Chengjie Hao  | WP5 | Implementation Manager        |         |
| Jinghao Wang  | WP6 | Testing Manager               |         |

---

*This document is updated continuously. Team members should update their task status regularly.*
