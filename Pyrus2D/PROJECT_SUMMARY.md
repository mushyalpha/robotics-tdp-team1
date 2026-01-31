# Decision Tree Evolution in Soccer AI - Project Summary

## Project Overview
This project demonstrates the progressive evolution of decision-making algorithms in multi-agent soccer simulation, showing how behavioral complexity improves team performance from basic reactive behavior to sophisticated coordination.

## What We Built

### 1. Progressive Decision Tree Versions
We created 5 versions of decision-making algorithms, each building on the previous:

**Version 1: Basic (Baseline)**
- Simple reactive behavior: chase ball → kick randomly
- No coordination between players
- No strategic thinking
- File: `base/decision_v1_basic.py`

**Version 2: Positioning**
- Added formation-based positioning
- Players coordinate who chases the ball
- Home position awareness
- File: `base/decision_v2_positioning.py`

**Version 3: Passing**
- Integrated pass evaluation algorithm
- Players can pass to teammates
- Considers receiver positions and offside
- File: `base/decision_v3_passing.py`

**Version 4: Smart Shooting**
- Added goal angle analysis
- Goalkeeper awareness
- Shot selection based on opportunity quality
- File: `base/decision_v4_shooting.py`

**Version 5: Full System**
- Complete behavioral suite (dribbling, blocking, tackling)
- Advanced multi-agent coordination
- Professional-level play
- File: `base/decision.py` (original)

### 2. Testing Infrastructure

**Automated Testing**
- `run_evolution_test.py` - Automated testing script for all versions
- `test_version.bat` - Manual testing script for individual versions
- `analyze_evolution.py` - Performance analysis and metrics extraction

**Documentation**
- `EVOLUTION_STUDY.md` - Complete research methodology
- `QUICK_START.md` - Step-by-step testing guide
- `MANUAL_OBSERVATIONS.md` - Template for qualitative analysis

### 3. Visualization Tools

**Simple Soccer Simulator** (`simple_soccer_sim.py`)
- Standalone Python visualizer using matplotlib
- No server/monitor dependencies
- Built-in algorithms for demonstration
- Real-time animation of team behavior

**Pyrus2D Log Visualizer** (`pyrus_visualizer.py`)
- Pygame-based replay system
- Reads and visualizes game logs
- Frame-by-frame playback control

## Technical Architecture

### Core System: Pyrus2D
- RoboCup 2D Soccer Simulation framework
- 11-player team coordination
- Realistic physics and uncertainty
- Server-client architecture

### Key Behavioral Algorithms
Located in `base/` folder:

**Decision Making:**
- `decision.py` - Main decision tree
- `goalie_decision.py` - Goalkeeper-specific logic

**Action Generators (Core AI):**
- `generator_pass.py` - Evaluates 25+ pass options per decision
- `generator_shoot.py` - Analyzes 25 goal target points
- `generator_dribble.py` - Tests 16 different dribble angles
- `generator_clear.py` - Emergency ball clearing

**Behavior Modules:**
- `bhv_kick.py` - Shoot/pass/dribble selection
- `bhv_move.py` - Movement and positioning
- `bhv_block.py` - Defensive blocking with opponent prediction

**Strategy:**
- `strategy_formation.py` - Team formation management
- `stamina_manager.py` - Energy optimization

## Setup and Installation

### Prerequisites
- Python 3.10+
- WSL (Windows Subsystem for Linux) for server
- rcssserver (RoboCup Soccer Server)
- rcssmonitor (visualization tool)

### Python Dependencies
```
coloredlogs==15.0.1
humanfriendly==10.0
numpy==1.24.2
pyrusgeom==0.1.2
scipy==1.10.1
```

### Quick Setup
```powershell
# Windows - Create virtual environment
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# WSL - Start server
cd ~/rcssserver/build
./rcssserver

# WSL - Start monitor
cd ~/rcssmonitor/build
./rcssmonitor
```

## Running the Evolution Study

### Method 1: Manual Testing (Recommended)
```powershell
# Test each version individually
.\test_version.bat v1_basic
.\test_version.bat v2_positioning
.\test_version.bat v3_passing
.\test_version.bat v4_shooting
.\test_version.bat v5_full
```

**Important:** Restart the rcssserver between each test (Ctrl+C, then `./rcssserver`)

### Method 2: Automated Testing
```powershell
python run_evolution_test.py
```

### Method 3: Simple Simulator
```powershell
python simple_soccer_sim.py
# Choose algorithm version (1-3)
```

## Key Findings

### Observable Evolution
Even without scoring goals, the progression is clearly visible:

1. **V1 → V2:** Chaos to organization (spatial awareness)
2. **V2 → V3:** Individual to team play (passing coordination)
3. **V3 → V4:** Random to strategic (decision quality)
4. **V4 → V5:** Reactive to proactive (anticipation)

### Metrics to Measure
- Ball possession frequency
- Pass completion rate
- Shot accuracy (direction towards goal)
- Team spatial distribution
- Decision-making speed

## Challenges Encountered

### 1. Visualization Complexity
- **Issue:** rcssserver + rcssmonitor setup is complex (3+ hours)
- **Solution:** Created standalone visualizers (simple_soccer_sim.py)

### 2. Network Configuration
- **Issue:** WSL networking - Windows Python couldn't reach WSL server on localhost
- **Solution:** Used WSL IP address (172.28.57.9) in connection config

### 3. Server Capacity
- **Issue:** Server only accepts 11 players, rejects additional connections
- **Solution:** Restart server between tests

### 4. Log Generation
- **Issue:** Pyrus2D logs were empty/incomplete
- **Solution:** Focus on real-time observation and manual documentation

## Research Value

### Demonstrates:
1. **Progressive complexity** in AI decision-making
2. **Emergent behavior** from layered algorithms
3. **Multi-agent coordination** evolution
4. **Trade-offs** between complexity and performance

### Applications:
- Robotics coordination
- Autonomous vehicle fleets
- Distributed AI systems
- Game AI development

## File Structure
```
Pyrus2D-master/
├── base/                          # Behavioral algorithms
│   ├── decision.py               # Full version (V5)
│   ├── decision_v1_basic.py      # Evolution V1
│   ├── decision_v2_positioning.py # Evolution V2
│   ├── decision_v3_passing.py    # Evolution V3
│   ├── decision_v4_shooting.py   # Evolution V4
│   ├── generator_pass.py         # Pass algorithm
│   ├── generator_shoot.py        # Shooting algorithm
│   ├── generator_dribble.py      # Dribbling algorithm
│   └── bhv_*.py                  # Behavior modules
├── lib/                          # Core framework
├── logs/                         # Game logs
├── evolution_results/            # Test results
├── simple_soccer_sim.py          # Standalone visualizer
├── pyrus_visualizer.py           # Log replay tool
├── test_version.bat              # Manual testing script
├── run_evolution_test.py         # Automated testing
├── analyze_evolution.py          # Results analysis
├── EVOLUTION_STUDY.md            # Research methodology
├── QUICK_START.md                # Testing guide
└── MANUAL_OBSERVATIONS.md        # Observation template
```

## Next Steps

### For Further Development:
1. **Quantitative Analysis:** Parse logs to extract numerical metrics
2. **Opponent Testing:** Run against another team to measure goals
3. **Parameter Tuning:** Optimize kick power, positioning thresholds
4. **Visualization Enhancement:** Add decision tree visualization overlay
5. **Machine Learning:** Use collected data to train adaptive algorithms

### For Presentation:
1. Record video of each version playing
2. Create side-by-side comparison videos
3. Generate graphs showing metric improvements
4. Document specific behavioral examples
5. Prepare demo using simple_soccer_sim.py

## References

- **Pyrus2D Framework:** https://github.com/Pyrus2D/Pyrus2D
- **RoboCup Soccer Server:** https://github.com/rcsoccersim/rcssserver
- **RoboCup 2D Soccer Simulation:** https://rcsoccersim.github.io/

## Contact & Collaboration

This project demonstrates decision tree evolution in multi-agent systems. The framework is extensible and can be adapted for various research questions in AI coordination, planning, and learning.

---

**Last Updated:** January 2026
**Status:** Functional - Ready for testing and analysis
