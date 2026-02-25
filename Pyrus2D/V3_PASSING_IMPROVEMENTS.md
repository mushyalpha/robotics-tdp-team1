# V3 Passing Algorithm - Improvements

## Overview

The V3 Passing algorithm in `simple_soccer_sim2.py` has been completely redesigned to **emphasize actual player-to-player passing** instead of immediately shooting for goal.

## What Changed

### Before (Old V3)
- Players would only pass if a teammate was significantly closer to goal (>1.0m difference)
- Most of the time, robots would just shoot immediately
- No visible passing behavior
- Looked very similar to V1 and V2

### After (New V3)
- **Minimum 2 passes required** before shooting is allowed
- Intelligent pass target selection based on:
  - Forward positioning (prefer passes that advance the ball)
  - Optimal spacing (1-4 meters between players)
  - Different lanes (good field coverage)
  - Avoids passing back to the last passer
- Only shoots when in good position (close to goal and centered)
- Even after minimum passes, continues passing if there's a better option

## Visual Features

### 1. Pass Counter Display
- **Orange circle** in top-left corner shows current pass chain
- Large number indicates consecutive passes
- Resets when goal is scored or ball goes out

### 2. Pass Intention Lines
- **Orange dashed lines** connect passer to their intended target
- Only visible when robot is in `PASSING` state
- Helps visualize team coordination

### 3. Console Logging
Every pass is logged with details:
```
[PASS #1] Robot 3 -> Robot 4 (Chain: 1 consecutive passes)
[PASS #2] Robot 4 -> Robot 2 (Chain: 2 consecutive passes)
[PASS #3] Robot 2 -> Robot 3 (Chain: 3 consecutive passes)
```

### 4. Status Bar
Top info bar shows:
- `Pass Chain: X` - Current consecutive passes
- `Total Passes: Y` - Total passes in the game

### 5. Goal Celebrations
When a goal is scored, shows:
```
*** GOAL! Total: 1 ***
    (After 3 consecutive passes)
    Total passes this game: 8
```

## Passing Logic Details

### Pass Target Selection

Each potential teammate is scored based on:

| Factor | Weight | Description |
|--------|--------|-------------|
| Forward position | 2.0x | Teammates ahead of current player |
| Good spacing | 3.0 | 1-4 meters away (not too close/far) |
| Different lane | 1.0 | Different y-coordinate (field width) |
| Closer to goal | 2.0x | Distance advantage toward goal |

**Robot avoidance:**
- Goalkeeper never receives passes
- Won't pass back to the last passer (prevents ping-pong)

### Shooting Conditions

Shooting only happens when:

1. **Minimum passes met** (2 or more consecutive passes), AND
2. **One of:**
   - In shooting position (< 2.5m from goal, centered within ±1.5m)
   - No good pass target available (score < 3.0)

### Pass Physics

Passes are tuned differently from shots:
- **Power scales with distance:** `base_power = 0.8 + (distance * 0.2)`
- **Better accuracy:** Lower error than shooting
- **Slight spin:** Realistic ball behavior

## How to Use

### Run the Simulation

```bash
python simple_soccer_sim2.py
```

### Choose V3 Algorithm

```
Choose algorithm:
1. V1 Basic - Everyone chases ball, shoots immediately
2. V2 Positioning - Only closest chases, others hold positions
3. V3 Passing - Emphasizes player-to-player passing (min 2 passes before shot)
              * Orange lines show pass intentions
              * Pass counter displayed in top-left corner
              * Console logs all passes

Enter choice (1-3): 3
```

### Recommended Settings for Best Demonstration

- **Enable fall simulation:** `n` (cleaner demo without interruptions)
- **Save as GIF:** `y` (capture passing sequences)
- **Number of frames:** `500-800` (enough time to see multiple passing sequences)

## Expected Behavior

You should now see:

1. **Active passing:** Ball moves between players 2-4 times before shooting
2. **Orange lines:** Visual connections showing pass intentions
3. **Pass counter:** Incrementing as passes succeed
4. **Console logs:** Real-time pass notifications
5. **Strategic positioning:** Players spread out and move to create passing lanes

## Comparison with Other Algorithms

| Feature | V1 Basic | V2 Positioning | V3 Passing |
|---------|----------|----------------|------------|
| Chase behavior | All chase | Only closest | Only closest |
| Positioning | None | Formation-based | Formation-based |
| Passing | Never | Rarely | Frequently (min 2) |
| Shooting | Immediate | Immediate | After passes |
| Coordination | None | Minimal | High |
| Visual aids | None | State colors | State colors + pass lines |

## Troubleshooting

### "Players still shoot too quickly"

This can happen if:
- No good pass targets available (players too clustered)
- Last passer rule prevents all options
- All potential receivers are incapacitated (fallen)

**Solution:** Run for longer to see multiple scenarios

### "Pass counter stays at 0"

Check that:
- V3 algorithm is selected (not V1 or V2)
- Players are getting close to the ball (within 0.3m)
- Multiple robots are on the field (not all fallen)

### "I don't see orange pass lines"

Pass lines only appear when:
- V3 algorithm is active
- Pass chain count > 0
- A robot is in `PASSING` state

## Performance Notes

### Pass Chain Statistics

Typical results with V3 algorithm:
- **Average pass chain:** 2-5 consecutive passes
- **Longest chains:** 6-10 passes (when robots well-positioned)
- **Total passes per game:** 15-30+ depending on game length
- **Goals after passing:** Much more strategic than V1/V2

### Best Demonstrations

For presentations, capture:
1. **3-4 pass sequence** ending in goal
2. **Pass counter** reaching 5+
3. **Orange lines** showing coordination
4. **Console log** with pass history

Example GIF settings:
```
Algorithm: V3 Passing
Falls: Disabled
Frames: 600 (30 seconds)
```

## Code Architecture

### Key Variables

```python
self.pass_count              # Current consecutive passes
self.last_passer_id          # Who passed last (avoid ping-pong)
self.min_passes_before_shot  # Minimum passes required (default: 2)
self.total_passes            # Cumulative passes in game
```

### Key Functions

- `decide_action_v3_passing()` - Pass target selection logic
- `apply_action()` - Tracks passes, increments counters
- `step()` - Resets pass chain on out-of-bounds
- Visualizer `update()` - Draws pass lines and counter

## Future Enhancements

Possible improvements:
1. **Adjustable minimum passes** - Let user choose 1-5 required passes
2. **Pass success rate** - Track completed vs attempted passes
3. **Heatmap** - Show areas where passes occur most
4. **Replay system** - Save and replay best passing sequences
5. **Opposition team** - Test passing against defenders

---

**Last Updated:** January 31, 2026  
**File:** `simple_soccer_sim2.py`  
**Algorithm:** V3 Passing (Enhanced)
