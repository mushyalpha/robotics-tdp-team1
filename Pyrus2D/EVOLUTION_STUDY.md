# Decision Tree Evolution Study

## Overview
This study demonstrates the progressive evolution of soccer AI decision-making algorithms, from basic reactive behavior to sophisticated multi-agent coordination.

## Evolution Stages

### Version 1: Basic (Baseline)
- **Behavior**: Chase ball → Kick randomly towards goal
- **Decision Tree Depth**: 1 level
- **Algorithms**: None (pure reactive)

### Version 2: Positioning
- **Added**: Formation-based positioning
- **Behavior**: Players have home positions, coordinate who chases ball
- **Decision Tree Depth**: 2 levels

### Version 3: Passing
- **Added**: Pass evaluation algorithm
- **Behavior**: Can pass to teammates, considers receiver positions
- **Decision Tree Depth**: 3 levels
- **Algorithm**: BhvPassGen (evaluates 25+ pass options per decision)

### Version 4: Smart Shooting
- **Added**: Goal angle analysis, goalkeeper awareness
- **Behavior**: Shoots only when good opportunity exists
- **Decision Tree Depth**: 4 levels
- **Algorithm**: BhvShhotGen (analyzes 25 goal target points)

### Version 5: Full System
- **Added**: Dribbling, blocking, tackling, set plays
- **Behavior**: Complete soccer AI with all strategies
- **Decision Tree Depth**: 5+ levels
- **Algorithms**: All generators + defensive behaviors

## Running the Study

### 1. Start the Server
```bash
# In WSL
cd ~/rcssserver/build
./rcssserver
```

### 2. Run Evolution Tests
```bash
# In Windows PowerShell (with venv activated)
python run_evolution_test.py
```

This will:
- Test each version for 5 games
- Collect logs for each game
- Save results in `evolution_results/`

### 3. Analyze Results
```bash
python analyze_evolution.py
```

This generates:
- Performance metrics for each version
- Improvement percentages
- Summary JSON file

## Expected Results

You should see progressive improvement in:
- **Pass completion rate**: 0% → 60%+
- **Shot accuracy**: Random → Targeted
- **Ball possession**: Low → High
- **Team coordination**: None → Formation-based
- **Goals scored**: Rare → Regular

## Visualization

The logs can be replayed in rcssmonitor to visually compare:
```bash
rcssmonitor --log-file evolution_results/v1_basic/game_1/game.rcg
```

## Research Questions Answered

1. **Does adding decision tree complexity improve performance?**
   - Measure: Goals, possession, pass completion

2. **What's the marginal benefit of each algorithm?**
   - Compare v2 vs v1, v3 vs v2, etc.

3. **Is there a point of diminishing returns?**
   - Compare v4 vs v5 improvement vs v1 vs v2

4. **How does computational cost scale?**
   - Measure decision time per cycle

## Files Generated

```
evolution_results/
├── v1_basic/
│   ├── game_1/
│   ├── game_2/
│   └── ...
├── v2_positioning/
├── v3_passing/
├── v4_shooting/
├── v5_full/
└── summary.json
```

## Citation

If using this for research:
```
Decision Tree Evolution in Multi-Agent Soccer Simulation
Based on Pyrus2D framework (RoboCup 2D Soccer Simulation)
```
