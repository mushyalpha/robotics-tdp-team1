# Section 4: Results and Analysis
*Author: Bonolo Masima*

## 4.2 Behavioral Parameter Optimisation Results

### 4.2.1 Introduction to the Parameter Optimization Sweep
The development of the Hierarchical Task-Space Model (detailed in Section 3.9) successfully yielded a highly robust, autonomous decision-making engine. However, the initial implementation of the "Balanced Profile," which assigned mathematically neutral values to all spatial thresholds and scalar multipliers, resulted in continuous 0-0 mirror-match deadlocks. When both teams share identical parameter profiles, the FSM produces perfectly mirrored decisions at every timestep, resulting in a Nash equilibrium where neither side can gain a strategic advantage [1]. While the core FSM logic proved exceptionally stable, it became empirically clear that achieving dominance required significantly tuning the robot's "personality" parameters to break this mathematical parity.

To solve this, an intensive parameter optimisation sweep was engineered. The baseline BehaviorProfile class exposed an initial array of 17 distinct tuning parameters, derived from the physical and tactical degrees of freedom available on the SoftBank NAO6 humanoid platform [5]. These ranged from low-level motor scalars (e.g., kick torque, walking gait speed) to high-level tactical thresholds (e.g., formation width, goalkeeper sweep distance). To empirically filter this scope, a "Micro-Pilot" experiment was conducted: a rapid pilot sweep using only 5 trials per level across a subset of parameters. Parameters producing negligible shifts in win rate, such as goalkeeper sweep radius and position Y-spread (formation width), were discarded as they exhibited less than 3% variance across their full tested range. By isolating variables that directly swayed the winning differential, the scope was filtered down to a primary focus on 7 highly impactful variables, allocating computational power only toward statistically significant metrics. The final 7 parameters selected were: maximum shooting distance, dash power multiplier, kick power, defensive press offset, chase radius, tackle aggression, and shoot-over-pass bias.

**Table 1: Parameter Definitions and Hardware Mapping**

| Parameter | Physical Meaning | Units | NAO6 Mapping |
| :--- | :--- | :--- | :--- |
| Dash Power Multiplier | Scales the robot's walking gait speed relative to baseline | Dimensionless scalar | Maps to the NAO6 joint motor velocity limits; 1.0× represents the default walking gait, while 1.3× approaches the platform's maximum sustainable stride frequency |
| Kick Power | Scales the force applied to the ball during a kick action | Dimensionless scalar | Corresponds to the torque output of the NAO6's leg actuators during the kick motion primitive |
| Shoot Distance Max | Maximum distance from the goal at which the robot will attempt a shot | Meters (m) | Defines the spatial trigger zone on the pitch; beyond this radius, the FSM will not transition to the SHOOT state |
| Chase Radius | Maximum distance from the ball at which a field player will sprint to contest possession | Meters (m) | Determines the spatial engagement zone; robots outside this radius ignore the ball and maintain formation |
| Defensive Press Offset | Vertical displacement of the defensive formation relative to the home position | Meters (m) | Positive values push defenders forward (high press); negative values drop them deeper toward their own goal |
| Tackle Aggression | Probability threshold for attempting a tackle when within range of an opponent with the ball | Dimensionless (0-1) | 0.0 = never tackles; 1.0 = always tackles when geometrically possible |
| Shoot-Over-Pass Bias | Weighting between shooting and passing when both options are geometrically available | Dimensionless (0-1) | 0.0 = always pass; 1.0 = always shoot |

These parameters were selected based on a combination of domain knowledge from RoboCup competition literature [4] and empirical observation from the Micro-Pilot results. In particular, parameters governing physical output (dash power, kick power) and spatial decision boundaries (shooting distance, chase radius) were hypothesised to have the greatest influence on match outcomes, as they directly determine whether a robot can reach the ball first and convert possession into goals.

### 4.2.2 Sweep Methodology and Justification
Breaking the mirror-match deadlocks necessitated an **Asymmetric Sensitivity Sweep** [2]. Rather than pitting two identically fluctuating teams against one another, a controlled methodology was established: the Red Team was strictly locked to the rigid, neutral Baseline profile, serving as a constant control group. Concurrently, the Blue Team acted as the experimental group, with a single parameter varied per sweep while all other parameters remained at baseline values. This one-factor-at-a-time (OFAT) isolation approach ensured observable effects could be attributed to the manipulated variable alone [3].

For each of the 7 filtered parameters, 5 discrete values were tested across a linearly interpolated scale. "Linearly interpolated" means the parameter's plausible operating range was divided into 5 equally spaced levels from its minimum to its maximum (e.g., Dash Power was tested at 0.7×, 0.85×, 1.0×, 1.15×, and 1.3×, where 1.0× represents the NAO6's default walking speed). To mitigate simulation anomalies, collision physics noise, and probabilistic variables inherent to stochastic simulation environments [6], **30 independent matches were executed per individual parameter level**. At 30 trials per condition, the Central Limit Theorem guarantees the sample mean distribution converges toward normality, enabling reliable comparison across levels. This dense repetition strategy across a full experimental sweep of 7 × 5 × 30 = **1,050 simulated matches** ensured high statistical significance, converting erratic simulation variance into clear, undeniable trend lines.

### 4.2.3 Physical Dominance: Kick Power and Speed Analysis
The analysis of the sweep data heavily underscored the sheer importance of physical superiority. Two primary scalar attributes, Kick Power and Dash Power Multiplier, exhibited the most drastic, undeniable impact on overall match Win Rates.

**Kick Power.** As demonstrated in Figure 1, scaling the robot's kick torque output yielded a near-binary success state. When kick power was restricted to its lowest tested output (0.85×), the experimental team achieved a critically low **3.3% Win Rate** with an average Goal Difference of −0.57. The robots, while logically intact, simply lacked the physical output to out-muscle the baseline opponent during loose-ball scrambles and contested clearances. However, when Kick Power was driven to its maximum constraint (1.25×), the Win Rate rose dramatically to **56.7%**, yielding an average Goal Difference of **+0.87** per match. This represents a 17-fold increase in win probability from a single scalar adjustment.

**Dash Power Multiplier.** The dash power sweep revealed an even more pronounced relationship. At the lowest tested walking speed (0.7×), the experimental team managed only a **6.7% Win Rate** with a severely negative Goal Difference of −1.37 and a territory gain deficit of −34.3. Conversely, at maximum dash power (1.3×), the Win Rate surged to **80.0%** with a Goal Difference of +1.20 and a dominant territory gain of +32.7; the fastest robots simply reached the ball first, dictating possession from the outset (see Figure 2).

*[Insert Figure 1: Win Rate Heatmap (heatmap_win_rate.png). Caption: "Figure 1: Win Rate (%) across all 7 parameters at 5 sweep levels. Darker shading indicates higher win rate relative to the parameter's range."]*

*[Insert Figure 2: Goal Difference Heatmap (heatmap_goal_difference.png). Caption: "Figure 2: Average Goal Difference across all 7 parameters at 5 sweep levels."]*

This establishes a critical conclusion for high-performance robot operation: regardless of the sophistication of the underlying FSM decision-making logic, if the hardware lacks the raw physical capabilities to outpace or outpower the opponent, absolute pitch control is inherently lost.

### 4.2.4 Quantity vs. Quality: Analyzing the Shots Metrics
A secondary prevailing pattern emerged when analyzing the spatial threshold parameters, heavily reinforcing a philosophy of "Quantity versus Quality." Utilizing the custom performance metrics framework (detailed in Section 3.11), the sweep exposed a dangerous inverse relationship between the pure volume of shots taken and the actual match Win Rate.

**Shooting Distance.** Analysis of the maximum shooting distance parameter provided profound clarity (Figure 3). When the robot was permitted to shoot freely from long range (2.8 m), it accumulated an average of 1,658 total shots per match alongside 251 shots on target. However, the resulting Win Rate collapsed to an absolute **0.0%** with a Goal Difference of −0.63. The robot frequently surrendered active possession by striking weak, low-probability shots directly into the goalkeeper or opposing defenders, generating chaotic rebounds without meaningful conversion.

Conversely, restricting the shooting trigger strictly to within extremely close proximity of the goal (1.0 m) reduced shot volume to 1,611 total shots per match. Yet this rigorous spatial constraint forced the robot into highly-disciplined, clinical attacking manoeuvres. While the raw volume of shots was comparable, the shots on target dropped to just 126, indicating the robot was attempting far fewer speculative strikes. The conversion rate skyrocketed, pushing the Win Rate to an elite **80.0%** alongside a maximum Goal Difference of **+1.47**.

**Shots on Target Analysis.** The shots on target heatmap (Figure 4) provides additional clarity on shot quality. Counterintuitively, high shots-on-target counts do not correlate with high win rates. At a shooting distance of 2.8 m, the team registered 251 shots on target yet won 0% of matches, while at 1.0 m, only 126 shots on target were recorded yet the team won 80%. This confirms that the metric tracking "on target" captures shots that reach the goal area but are easily saved by the goalkeeper. True offensive effectiveness is therefore measured not by shot volume, but by the geometric proximity and decisiveness of each attempt.

**Shoot-Over-Pass Bias.** The shoot-over-pass bias parameter further reinforced this finding. Setting the bias to its lowest value (0.1, heavily favouring passing) yielded a positive territory gain of +12.4, demonstrating superior spatial control of the pitch. While its raw win rate was modest at 13.3%, this reflected the fact that the parameter was swept in isolation; when combined with the optimal physical parameters, the disciplined passing philosophy compounds dramatically.

*[Insert Figure 3: Total Shots Heatmap (heatmap_total_shots.png). Caption: "Figure 3: Total shots per match across all 7 parameters at 5 sweep levels."]*

*[Insert Figure 4: Shots on Target Heatmap (heatmap_shots_on_target.png). Caption: "Figure 4: Shots on target per match across all 7 parameters. High counts do not correlate with high win rates, indicating that shot proximity, not volume, drives conversion."]*

### 4.2.5 Territorial and Defensive Analysis
Beyond offensive metrics, the sweep revealed critical patterns in spatial control of the pitch.

**Defensive Press Offset.** This parameter dictated how far forward the defensive line rested when without possession. At the deepest setting (−1.2 m), the team conceded territory heavily (territory gain of −26.1) and achieved only a 10.0% Win Rate. At the most aggressive forward press (+2.0 m), territory gain surged to +55.6 and possession climbed to 73.0%, producing a 56.7% Win Rate. However, +1.0 m was ultimately selected as the optimal value (discussed in Section 4.3.1) as a pragmatic balance between pressing intensity and defensive exposure.

**Chase Radius.** The chase radius controlled how far a field player would sprint to contest the ball. At the most restrictive setting (1.3 m), the robots effectively refused to engage in contestable situations, yielding a 0.0% Win Rate. The optimal peak occurred at 2.5 m (43.3% Win Rate, +0.43 Goal Difference), beyond which over-extension caused formation collapse; at 3.0 m, the Win Rate fell back to 23.3% with a severe territory deficit of −23.2.

**Tackle Aggression.** This parameter exhibited the flattest response curve of all 7 variables. Win rates ranged narrowly from 10.0% (at 0.2) to 16.7% (shared across three levels: 0.35, 0.7, and 0.85). While the isolated impact was modest, tackle aggression's contribution becomes significant when compounded with high dash power and forward pressing, as discussed in Section 4.3.2.

*[Insert Figure 5: Territory Gain Heatmap (heatmap_territory_gain.png). Caption: "Figure 5: Net Territory Gain across all 7 parameters at 5 sweep levels. Positive values indicate territorial dominance."]*

*[Insert Figure 6: Possession Heatmap (heatmap_possession.png). Caption: "Figure 6: Possession percentage across all 7 parameters at 5 sweep levels."]*

### 4.2.6 Limitations of the Sweep Methodology
While the 1,050-match sweep provides strong empirical evidence, several methodological limitations should be acknowledged.

First, the OFAT approach tests each parameter in isolation while holding all others at baseline. This means **interaction effects** between parameters are not captured. For example, the combined effect of high kick power and close shooting distance may be greater (or lesser) than the sum of their individual effects. A full factorial design would require 5^7 = 78,125 parameter combinations at 30 trials each, totalling over 2.3 million matches, which was computationally infeasible within the project timeline.

Second, a **simulation-to-reality transfer gap** exists inherently. The Webots physics engine [6] approximates real-world friction, collision dynamics, and motor response curves, but cannot perfectly replicate the physical behaviour of NAO6 hardware. Parameters that appear optimal in simulation (particularly extreme dash power values) may cause motor overheating or joint wear on the physical platform, which is why conservative selections were made for certain parameters in the Master List (Section 4.3.1).

Third, **tackle aggression produced an essentially flat, inconclusive response** in isolation. Its inclusion in the final Master List is justified by its compounding role within the synergistic strategy, but its individual contribution to performance cannot be confidently quantified from this dataset alone.


## 4.3 Behavioral Tactical Optimisation Results

### 4.3.1 Synthesis of the Optimal "Master List"
Extensive analysis of the 1,050 asymmetric simulated matches concluded with the synthesis of an optimal, data-driven "Master List." For each parameter, the value producing the highest win rate was identified as the primary candidate. In cases where multiple levels produced similar win rates, secondary metrics (goal difference, territory gain, and possession) were used as tie-breakers. Additionally, practical considerations regarding hardware sustainability, particularly motor wear and overheating risks inherent to physical RoboCup platforms [4], informed the final selection.

**Table 2: The Optimal Behavioral Master List**

| Parameter | Tested Range | Peak Win Rate Value | Optimal Selected | Justification |
| :--- | :--- | :--- | :--- | :--- |
| Shoot Distance Max | 1.0 – 2.8 m | 1.0 m (80.0%) | **1.0 m** | Clear peak; clinical shot philosophy |
| Dash Power Multiplier | 0.7× – 1.3× | 1.3× (80.0%) | **1.3×** | Clear peak; maximum mobility |
| Kick Power Multiplier | 0.85× – 1.25× | 1.25× (56.7%) | **1.25×** | Clear peak; physical dominance |
| Defensive Press Offset | −1.2 – +2.0 m | +2.0 m (56.7%) | **+1.0 m** | +2.0 m risks defensive exposure on counter-attacks; +1.0 m provides 33.3% WR with balanced risk |
| Chase Radius | 1.3 – 3.5 m | 2.5 m (43.3%) | **2.5 m** | Clear peak; beyond this, formation collapses |
| Tackle Aggression | 0.2 – 0.85 | 0.7 (16.7%) | **0.7** | Flat curve; 0.7 chosen for best goal difference (−0.07) among tied levels |
| Shoot-Over-Pass Bias | 0.1 – 0.9 | 0.5 (30.0%) | **0.1** | Selected for territory gain (+12.4) and passing discipline; compounds with close shooting distance |

### 4.3.2 Synergistic Geometry and Behavioral Integration
Individually, these optimal values improve specific mechanics; synergistically, they mathematically forge a relentlessly suffocating strategy. Integrating an expanded chase radius (2.5 m) with an aggressive defensive press offset (+1.0 m) physically forces the robot to rest higher up the pitch and furiously contest tackles in the opponent's half. When the ball is recovered through the 0.7 tackle aggression threshold, the strict 1.0 m shoot distance max ensures the robot carries the ball deep into the box before striking, immediately converting turnovers into clinically executed close-range finishes. The low shoot-over-pass bias (0.1) means the robot circulates possession patiently until the geometric conditions for a close-range shot are satisfied, rather than wasting possession on speculative long-range attempts.

This synergistic geometry is quantitatively validated by the territory gain and possession heatmaps (Figures 5 and 6). Parameters that independently push the robot forward (high dash power, forward press offset, expanded chase radius) compound to create an overwhelming high-press system, where the opponent is physically suffocated in their own half.

Crucially, **the underlying FSM logic code was not rewritten**. The core transition logic architected in Section 3.9 remained pristine. However, by integrating this optimized Master List back into the model's BehaviorProfile class, the robot's physical output and geometric constraints were decisively shifted towards maximal, clinical aggression, transforming a neutral decision-maker into a dominant tactical entity without altering a single line of behavioural code.

### 4.3.3 Final Validation Statistics
To mathematically validate the efficacy of the comprehensive Master List synthesis, a strict "Final Stress Test" was architected. The resulting "Optimised Balanced Team," utilising all 7 Master List parameters simultaneously, was pitted against the unmodified "Baseline Balanced Team" over a continuous **100-match protocol**, with each match running the full 20-minute RoboCup-compliant duration [4].

**Table 3: Final Validation Results (100 Matches)**

| Metric | Optimised Team (Blue) | Baseline Team (Red) |
| :--- | :--- | :--- |
| Win Rate | **99.0%** | 0.0% |
| Draw Rate | 1.0% | 1.0% |
| Avg Goals Per Match | **4.36** | 0.07 |
| Avg Goal Difference | **+4.29** | −4.29 |

The statistics are definitive proof of total system optimisation. Over the span of 100 matches, the Optimised team achieved an unparalleled **99.0% Win Rate** with a 1.0% Draw Rate. The Baseline team was held to a 0.0% Win Rate.

Offensively, the tactical adjustments yielded an average of **4.36 goals scored per match**, while the highly synergistic defensive pressing mechanics suppressed the opponent to an exceptionally low **0.07 goals conceded per match**, resulting in an average Goal Differential of **+4.29**. By purely optimising the behavioural tuning scalar and spatial parameters, without modifying any core decision-making logic, a stagnant, neutral robot was successfully transformed into an empirically proven, dominant tactical entity.

---

### References
[1] Nash, J.F. (1950) 'Equilibrium Points in N-Person Games', *Proceedings of the National Academy of Sciences*, 36(1), pp. 48-49.

[2] Montgomery, D.C. (2017) *Design and Analysis of Experiments*. 9th edn. John Wiley & Sons.

[3] Czitrom, V. (1999) 'One-Factor-at-a-Time versus Designed Experiments', *The American Statistician*, 53(2), pp. 126-131.

[4] RoboCup Federation (2024) *RoboCup Soccer Humanoid League Rules and Setup*. Available at: https://humanoid.robocup.org/materials/rules/ (Accessed: March 2026).

[5] SoftBank Robotics (2023) *NAO6 Technical Specifications*. Available at: https://www.aldebaran.com/en/nao (Accessed: March 2026).

[6] Cyberbotics Ltd. (2024) *Webots User Guide: Physics Engine*. Available at: https://cyberbotics.com/doc/guide (Accessed: March 2026).
