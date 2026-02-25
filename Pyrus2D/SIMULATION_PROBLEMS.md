# Soccer Simulation - Identified Problems & Action Plan

**Date:** February 2, 2026
**Target Date:** Wednesday, February 5, 2026
**Files Analyzed:** `simple_soccer_sim1.py`, `simple_soccer_sim2.py`

---

## Executive Summary

This document catalogs all identified problems in the 2D soccer simulation, organized by priority. The simulation currently lacks critical features needed for realistic robotic soccer gameplay, including proper role-based behavior, opponent teams, collision detection, and game state management.

---

## CRITICAL Issues - Must Fix by Wednesday

### 1. Robots Approach Ball Simultaneously

**What's the problem?**
All four robots on the team chase the ball at the same time, creating a chaotic "swarm" behavior where everyone converges on the ball location. This is unrealistic and inefficient.

**Why is this bad?**

- Wastes computational resources having all robots chase one target
- No strategic positioning for receiving passes or defending
- Creates overlapping robots
- Doesn't reflect real soccer where players have designated roles

**Technical Details:**
In `v1_basic` algorithm, every robot executes `decide_action_v1_basic()` which always returns actions to chase the ball. Even `v2_positioning` only slightly improves this by letting one robot chase while others literally freeze in place.

**Code Location:**

- `simple_soccer_sim1.py`, lines 111-121
- `simple_soccer_sim2.py`, lines 146-156

---

### 2. Ball Approach Priority System Is Broken

**What's the problem?**
The `v2_positioning` algorithm attempts to fix Problem #1 by only allowing the closest robot to chase the ball. However, robots that aren't chasing execute the `'stay'` action, which means they do absolutely nothing—they don't reposition, defend, or prepare to receive passes.

**Why is this bad?**

- Frozen robots can't react to changing game situations
- No dynamic repositioning based on ball movement
- The "closest robot" calculation doesn't account for robot velocity or momentum
- Maximum 2 robots should approach ball (one to kick, one as backup), not just 1

**Technical Details:**
The algorithm calculates distances at one moment in time but doesn't predict where robots and ball will be in the next few frames. A robot moving toward the ball might be farther away momentarily but will arrive first.

**Code Location:**

- `simple_soccer_sim1.py`, lines 123-135
- `simple_soccer_sim2.py`, lines 158-170

---

### 3. Ball Movement Physics ✓ (PARTIALLY SOLVED)

**What was the problem?**
In VERSION 1, the ball travels in perfect straight lines with no environmental factors, which is unrealistic.

**Current Status:**VERSION 2 (`simple_soccer_sim2.py`) has addressed this with:

- Magnus effect (spin causing curved trajectories)
- Wind factors and grass bumps (random perturbations)
- Kick/pass accuracy errors
- Power variations

**Remaining Question:**
Is the current implementation optimal for a 2D simulation? May need tuning of parameters like friction (0.92), spin decay (0.95), and force coefficients.

**Code Location:**

- `simple_soccer_sim2.py`, lines 48-127 (Ball class)

---

### 4. Ball Scores All The Time (No Goalkeeper Intelligence)

**What's the problem?**
There is no goalkeeper-specific AI. The robot designated as goalkeeper (ID: 1, positioned at `-3.5, 0`) uses the exact same ball-chasing logic as the attackers. It doesn't stay on the goal line, track the ball laterally, attempt saves, or position itself between the ball and goal.

**Why is this bad?**

- Goals are scored far too easily
- Doesn't reflect real robotic soccer where goalkeepers are specialized
- Makes the simulation unrealistic for testing attacking strategies
- Can't demonstrate defensive capabilities

**Technical Details:**
The goal detection at lines 284-288 (sim2) simply checks if the ball crosses the goal line within the goal width. No goalkeeper attempt to block is made because the goalkeeper has likely wandered away chasing the ball.

**Code Location:**

- Robot initialization: lines 136-144 (sim2)
- No goalkeeper-specific decision function exists

---

### 5. Status Window Needed

**What's the problem?**
There's no visual indication of what each robot is doing. Since this 2D simulation represents a 3D Webots simulation where robots can fall down and recover, there needs to be a status display showing robot states.

**Why is this bad?**

- Can't debug behavior algorithms without knowing robot states
- Can't tell if a robot is kicking, passing, positioning, or stuck
- Missing connection to real-world scenarios (fallen, recovering, etc.)
- Hard to demonstrate different strategies to observers

**What's needed?**Robot states should include:

- `IDLE` - Standing still
- `CHASING_BALL` - Moving toward ball
- `KICKING` - Executing kick
- `PASSING` - Executing pass
- `POSITIONING` - Moving to strategic position
- `FALLEN` - Simulating fall (from 3D)
- `RECOVERING` - Simulating recovery phase (from 3D)
- `GOALKEEPING` - Goalkeeper-specific tracking

Display this with:

- Color coding on robots (e.g., green outline = positioning, red = kicking)
- Status text panel on visualization
- State change logging to console

**Technical Details:**
Robot class has no `state` attribute. Need to add state machine and update visualization to display states.

---

## IMPORTANT - Design Issues

### 6. Robots Have No Real Strategy

**What's the problem?**
The `v3_passing` algorithm is extremely primitive. It only checks if a teammate is 1.0 meter closer to the goal before deciding to pass. This is not a real strategy.

**Why is this bad?**

- Only considers forward passes (no lateral or backward options)
- Doesn't check if passing lane is clear
- Doesn't consider teammate readiness or positioning
- No build-up play, ball retention, or strategic possession
- Can't implement supervisor's suggestion of "time to keep the ball"

**What's missing?**Real strategies should include:

- **Possession play:** Keep ball away from opponents
- **Passing triangles:** Create multiple passing options
- **Space creation:** Move to open space when not chasing ball
- **Defensive shape:** Maintain formation when opponent has ball
- **Counter-attack:** Fast transition from defense to offense

**Code Location:**

- `simple_soccer_sim1.py`, lines 137-153
- `simple_soccer_sim2.py`, lines 172-188

---

### 7. Defender Reaches Ball First (Positioning Issue)

**What's the problem?**You've observed that the defender (ID: 2) typically reaches the ball first, even though the attackers should be closer. This is counterintuitive given the initial positions:

- Goalkeeper: `(-3.5, 0)` - Distance to center: 3.5m
- Defender: `(-2, 0)` - Distance to center: 2.0m
- Attacker 1: `(0, -1)` - Distance to center: 1.0m
- Attacker 2: `(0, 1)` - Distance to center: 1.0m

**Why does this happen?**The issue likely stems from:

1. **Turning time:** Attackers may need to turn more to face the ball
2. **Movement algorithm:** All robots move at same speed (0.1 units/step)
3. **Starting orientations:** Robot headings may favor defender's approach angle
4. **Race conditions:** First robot to complete turn + movement wins

**Investigation needed:**
Log each robot's initial heading and bearing to ball to understand why defender arrives first.

**Code Location:**

- Robot initialization: lines 136-144
- Movement logic: lines 190-198

---

### 8. Robots Overlap (No Collision Detection)

**What's the problem?**
Multiple robots can occupy the same physical space. There's no collision detection or physics preventing robots from passing through each other.

**Why is this bad?**

- Completely unrealistic for physical robots
- Multiple robots can "kick" the ball simultaneously
- Can't test collision avoidance algorithms
- Doesn't prepare for 3D Webots simulation where collisions matter

**What's needed?**

- Define robot collision radius (e.g., 0.15m based on typical KidSize dimensions)
- Check for overlapping collision circles before movement
- Implement collision response (stop, bounce, or navigate around)
- Add collision avoidance to pathfinding

---

### 9. No Opponent Team

**What's the problem?**
Only the blue team exists. There are no opponent robots to play against.

**Why is this bad?**

- Can't test defensive strategies
- Can't demonstrate realistic game scenarios
- Can't measure algorithm performance against opposition
- Doesn't meet basic soccer simulation requirements

**What's needed?**Add 4 red team robots with:

- Mirrored starting positions (attacking opposite goal)
- Basic AI (even if simpler than blue team)
- Different colored visualization
- Opponent goal detection

**Code Location:**

- Team creation: lines 136-144 (only creates blue team)

---

### 10. Kick by Proximity Only (Bad Physics)

**What's the problem?**
A robot kicks the ball when within 0.3m distance, regardless of position relative to the ball. In real humanoid soccer, robots can only kick the ball when positioned behind it (in the direction they want to kick).

**Why is this bad?**

- Violates basic physics (can't push something you're not behind)
- Makes kicking too easy and unrealistic
- Doesn't reflect real humanoid robot constraints
- Can result in backwards or sideways "kicks" that make no sense

**What's needed?**Before kicking, robot should:

1. Calculate desired kick direction (toward goal)
2. Position itself behind the ball relative to that direction
3. Approach at correct angle (within ±30° of desired direction)
4. Only then execute kick

**Technical Details:**
Need to add approach angle validation:

```python
if distance <= 0.3:
    ball_to_goal = np.arctan2(goal_y - ball.y, goal_x - ball.x)
    robot_to_ball = np.arctan2(ball.y - robot.y, ball.x - robot.x)
    approach_angle = abs(ball_to_goal - robot_to_ball)
    if approach_angle < 0.5:  # ~30 degrees
        return 'kick'
```

**Code Location:**

- `simple_soccer_sim1.py`, lines 164-181
- `simple_soccer_sim2.py`, lines 199-230

---

## ADDITIONAL Problems Found

### HIGH Priority

#### 11. No Goalkeeper-Specific Behavior

*(See Problem #4 for details - this is a restatement emphasizing the goalkeeper role)*

**Additional requirements:**

- Stay within goal area (1m from goal line)
- Track ball position laterally (move left/right)
- Dive/save when ball approaches goal
- Don't chase ball beyond penalty area
- Clear ball when it enters goal area

---

#### 12. No Ball Possession Tracking

**What's the problem?**
The simulation has no concept of which robot "has" the ball. Any robot within 0.3m can kick, even if multiple robots are in range simultaneously.

**Why is this bad?**

- Can't implement "time to keep the ball" strategy suggested by supervisor
- Can't track possession statistics (important for analysis)
- Multiple robots might kick simultaneously, causing weird physics
- Can't implement dribbling behavior

**What's needed?**

- Add `ball_owner` variable (None or robot ID)
- Set owner when robot is within 0.2m and facing ball
- Clear owner when ball velocity > threshold (kicked away)
- Only allow ball owner to kick/pass
- Track possession time and switches

---

#### 13. No Game State Machine

**What's the problem?**
The simulation just runs continuously with no game states. Real soccer has distinct phases: kickoff, active play, goal scored, out of bounds, penalties, etc.

**Why is this bad?**

- Can't properly reset after goals (currently just spawns new ball instantly)
- Can't implement RoboCup restart procedures
- Can't run timed experiments (no clear start/end)
- Can't demonstrate full match scenarios

**What's needed (per RoboCup rules):**

- `KICKOFF` - Center circle positioning, no movement until whistle
- `PLAYING` - Normal gameplay
- `GOAL_SCORED` - Celebration, then reset to kickoff
- `OUT_OF_BOUNDS` - Throw-in, goal kick, or corner kick
- `PENALTY` - Penalty kick setup
- `HALFTIME` - Swap sides
- `FINISHED` - Match complete

---

#### 14. No Out-of-Bounds Handling

**What's the problem?**
When the ball reaches field boundaries, it bounces off invisible walls instead of going out of bounds.

**Why is this bad?**

- Violates RoboCup Law 9 (Ball In and Out of Play)
- Should trigger: throw-in (sidelines), goal kick (over goal line by attacker), or corner kick (over goal line by defender)
- Bouncing walls are completely unrealistic
- Can't test restart scenarios

**Technical Details:**
Current code at lines 109-126 (sim2) applies wall bounces with energy loss. Should instead set game state to `OUT_OF_BOUNDS` and determine restart type.

---

#### 15. Robot Speed Is Unrealistic

**What's the problem?**
Robots move instantly at constant speed (0.1 units per step = ~1 m/s if running at 10 Hz). No acceleration, deceleration, or speed limits. Direction changes are instantaneous.

**Why is this bad?**

- Real KidSize humanoid robots walk at ~0.2-0.3 m/s maximum
- No momentum or inertia
- Can't simulate slip/fall scenarios mentioned in requirements
- Makes simulation overly optimistic for strategy testing

**What's needed:**

- Maximum velocity limit (~0.3 m/s)
- Acceleration/deceleration (gradual speed changes)
- Turn rate limits (can't spin instantly)
- Reduced speed when ball is close (dribbling speed)

---

#### 16. No Robot-Robot Collision Avoidance

**What's the problem?**
Robots move completely independently with no awareness of teammate or opponent positions. Even before implementing collision physics, robots should avoid walking into each other.

**Why is this bad?**

- Causes overlapping (Problem #8)
- Real robots use vision to avoid collisions
- Part of coordination strategy
- Needed for realistic multi-robot scenarios

**What's needed:**

- Check for nearby robots before moving forward
- Add avoidance behavior (circle around obstacles)
- Maintain minimum separation (e.g., 0.4m between robots)

---

### MEDIUM Priority

#### 17. Pass Target Selection Too Simple

**What's the problem?**
Passing logic only considers teammates farther forward (positive x direction), missing many strategic opportunities.

**What's missing:**

- Lateral passes to switch play
- Back passes to goalkeeper or defenders for safety
- Checking if passing lane is clear
- Considering teammate's ability to receive (position, heading)
- Risk assessment (is opponent nearby?)

---

#### 18. Kick Always Aims at Goal Center

**What's the problem?**
All kicks aim for `(PITCH_LENGTH/2, 0)` - the exact center of the goal. This is predictable and ignores the goalkeeper position.

**What's needed:**

- Aim at goal corners (harder to save)
- Aim away from goalkeeper position
- Add shot accuracy based on distance and pressure
- Consider power vs. accuracy tradeoff

**Code Location:**

- `simple_soccer_sim1.py`, lines 166-167
- `simple_soccer_sim2.py`, lines 201-202

---

#### 19. No Penalty Area Logic

**What's the problem?**
Penalty areas are defined in RoboCup rules but not implemented in simulation.

**What's needed (per RoboCup rules):**

- Only goalkeeper can use hands/special handling in penalty area
- Fouls inside penalty area result in penalty kicks
- Penalty kick: 1v1 between kicker and goalkeeper from penalty mark
- Penalty area dimensions: 5m × 2m (KidSize)

---

#### 20. No Match Clock or Periods

**What's the problem?**
`self.time` is just a step counter, not a real game clock.

**What's needed (per RoboCup Law 7):**

- Two 10-minute halves (KidSize)
- Halftime: swap sides
- Overtime if tied (knockout matches)
- Display minutes:seconds on visualization
- Stop clock for injuries/delays (optional)

---

### LOWER Priority (Future Enhancements)

#### 21. No Dribbling Action

**What it is:**
Controlled ball movement while walking (keeping ball close to robot).

**Why it's lower priority:**
Can approximate with multiple small kicks. More important to get basic behaviors working first.

---

#### 22. No Stamina/Fatigue

**What it is:**
Robots slow down over time and need rest periods.

**Why it's lower priority:**
Not realistic for this 2D simulation meant for strategy testing. Real robots have battery constraints but don't fatigue like humans.

---

#### 23. Field Markings Incomplete

**What's missing:**
Visualization doesn't draw penalty areas, goal areas, or penalty marks defined in the field setup.

**Why it's lower priority:**
Doesn't affect simulation logic, only visual clarity. Would be nice to have for presentations.

---

## Recommended Action Plan for Wednesday

### Must Fix (Core Functionality)

| Priority | Task                                                                                               | Estimated Effort |
| -------- | -------------------------------------------------------------------------------------------------- | ---------------- |
| 1        | **Goalkeeper behavior** - Add goalkeeper-specific AI that stays on goal line and tracks ball | 2-3 hours        |
| 2        | **Ball approach priority** - Implement max 2 robots approach, others position strategically  | 2-3 hours        |
| 3        | **Add opponent team** - Create 4 red robots with basic opposing AI                           | 1-2 hours        |
| 4        | **Robot collision** - Add collision radius and prevent overlap                               | 1-2 hours        |
| 5        | **Status display** - Add robot state tracking and visual indicators                          | 1 hour           |

**Total: 7-11 hours** (achievable by Wednesday with focused work)

### Should Fix (Realism)

| Priority | Task                                                                             | Estimated Effort |
| -------- | -------------------------------------------------------------------------------- | ---------------- |
| 6        | **Kick approach angle** - Require robot to be behind ball before kicking   | 1-2 hours        |
| 7        | **Ball possession tracking** - Track which robot controls ball             | 1 hour           |
| 8        | **Game state** - Implement kickoff, playing, goal_scored states at minimum | 2 hours          |

**Total: 4-5 hours** (do if time permits)

---

## Testing Strategy

After fixes, test these scenarios:

1. **Goalkeeper Test:** Place ball near goal, verify goalkeeper stays and attempts save
2. **Approach Priority Test:** Drop ball in center, verify only 2 robots approach
3. **Opposition Test:** Run 4v4 match, verify both teams compete for ball
4. **Collision Test:** Force robots toward same point, verify they don't overlap
5. **Status Test:** Verify status colors/text update as robots change behaviors

---

## Notes

- This document will be updated as problems are resolved
- Mark resolved items with ✓
- Add new problems as discovered
- Reference RoboCup rules document for official specifications

---

**Last Updated:** February 2, 2026
**Next Review:** After Wednesday deadline
