# Section 3: Methodology (Behavioral Modeling)
*Author: Chengjie Hao*

## 3.9 Behavioral Model Creation
The fundamental objective of the behavioral modeling phase was to architect a decision-making framework capable of operating autonomously within the simulated 2D environment. Rather than relying on hardcoded, linear scripting, the architecture was designed around a highly decoupled Hierarchical Task-Space Model (HTSM). This design philosophy ensures that the underlying logic (the "Brain"), physical execution (the "Body"), and tactical modifiers (the "Personality") remain distinct, allowing for modular testing and rapid iteration.

### 3.9.1 Architectural Pillars
The simulation engine utilizes the `SoccerSimulator` class to manage the global match state, but the autonomous choices of each robotic agent are governed by three interacting pillars:

1.  **The FSM Decision Engine (Logic):** The core intelligence of the robot operates via a Finite State Machine (FSM), specifically executed through the `_update_tactics()` subsystem. The FSM dynamically evaluates the absolute pitch geometry during every simulation step. It calculates strict geometric relationships, such as the robot's proximity to the ball, the relative angle to the goal, and the dispersion of opposing players. Based on these geometric truths, the FSM transitions the robot into a designated `RobotState` (e.g., `CHASE_BALL`, `DRIBBLE`, `SHOOT`, or `RECOVER_POSITION`). Critically, this FSM is inherently neutral; it simply assigns the logically "correct" state without biasing aggressiveness or passivity.

2.  **The Physical Constraints Module (Execution):** Once the FSM assigns a `RobotState`, the `apply_action()` protocol processes the physical ramifications. This module acts as the physical translator, converting high-level states into simulated 2D force vectors. For example, if assigned the `SHOOT` state, the module generates a localized velocity vector directed toward the goal. Crucially, this module handles physics-engine constraints, such as modeling collisions via simulate_fall() if physical tolerances (like maximal dash speeds overlapping with enemy hitboxes) are breached, rendering the robot temporarily incapacitated.

3.  **The Behavioral Profile (Personality & Dials):** To prevent the logic from being rigid, the FSM does not evaluate raw integer magic numbers. Instead, it reads thresholds from a `BehaviorProfile` dataclass. This schema acts as the robot's personality, storing over fifteen unique attributes. These include:
    *   **Scalar Multipliers:** Dimensionless multipliers applied to physical outputs (e.g., `dash_power_multiplier`, `kick_power`).
    *   **Spatial Tolerances:** Strict geometric boundaries (e.g., `shoot_distance_max`, `chase_radius`) modeled in absolute meters on the pitch.
    *   **Logical Biases:** Weighting probabilities for state transitions (e.g., `shoot_over_pass_bias`).

### 3.9.2 Constructing the "Balanced Profile"
During initial methodology formulation, a primary iteration of the behaviour was authored: the "Balanced Profile." This profile populated the BehaviorProfile schema with neutral, mathematically central values. The design intent was stability; the state transitions were balanced equally between attacking rushes and defensive retreats. 

While the logical foundation proved highly stable and bug-free, the Balanced Profile resulted in frequent 0-0 "mirror match" deadlocks during preliminary testing against identical logic agents, due to symmetrical decision making across the pitch. This highlighted the need for the subsequent parameter optimization sweeps discussed later in this report, as the core logic proved effective, but the assigned parameter tolerances lacked the necessary clinical aggression to break mathematical parity.

## 3.10 Behavioral Testing
Validating the autonomous behavioral models necessitated a robust testing framework capable of operating faster than real-time to generate sufficient empirical data. 

### 3.10.1 Headless Testing Architecture
The simulation was upgraded to support a "headless" execution mode via `run_headless()`. By decoupling the graphical rendering (`matplotlib` visualizer) from the core physics engine, the behavioral loops could iterate computationally unchecked. This allowed a standard 20-minute (24,000 algorithmic step) match to resolve in seconds. Test harnesses were built using Python's `ProcessPoolExecutor` to distribute hundreds of these headless validation matches across multi-core processors in parallel.

### 3.10.2 Validation Criteria
Behavioral testing evaluated the agents purely on state-transition stability and spatial awareness. The baseline logic was tested against specific edge cases:
*   **Touchline Adherence:** Ensuring the FSM recognized out-of-bounds geometries and triggered appropriate throw-in or goal-kick resetting logic.
*   **Collision Recovery:** Ensuring that aggressively programmed agents, upon triggering a fall mechanic, successfully transitioned to a `RECOVER_POSITION` state rather than freezing.
*   The behavioral logic correctly satisfied all baseline requirements, clearing the framework for high-level tactical optimization.

## 3.11 Behavioral Performance Metrics
Evaluating tactical performance beyond simple win/loss binaries required the development of a granular analytics tracking system. A `MetricsCollector` class was tethered to the main simulation loop, recording discrete actions and spatial data points at every timestep.

### 3.11.1 Key Performance Indicators (KPIs)
To provide deep insights into robot decision-making accuracy, the following customized metrics were implemented into the tracking framework:
1.  **Total Shots & Shots on Target:** By counting the absolute volume of trigger events for the `SHOOT` state, combined with collision logic on the goal line, the model provides an exact conversion matrix, differentiating chaotic "spam" shooting from clinical accuracy.
2.  **Net Territory Gain:** Calculated by tracking the average positional shifting of the ball relative to the midfield line. This metric quantifies the efficacy of the robot's spatial pressing and defensive capabilities.
3.  **Possession Disparity:** Rather than tracking raw touch-counts (which skew inaccurately during dribbling anomalies), possession was mathematically modeled based on proximity thresholds to the ball over sustained computational frames.

These foundational metrics bridge the gap between abstract code and tangible soccer performance, laying the critical groundwork necessary to empirically evaluate the complex parameter optimization arrays discussed in the Results spanning Section 4.
