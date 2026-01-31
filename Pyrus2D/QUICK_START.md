# Quick Start: Testing Decision Tree Evolution

## Simple Manual Testing (Recommended)

### Step 1: Restart the Server
In WSL, stop the current server (Ctrl+C) and restart:
```bash
cd ~/rcssserver/build
./rcssserver
```

### Step 2: Start the Monitor
In another WSL terminal:
```bash
cd ~/rcssmonitor/build
./rcssmonitor
```

### Step 3: Test Each Version

In Windows PowerShell (with venv activated):

**Test Version 1 (Basic):**
```powershell
.\test_version.bat v1_basic
```

Watch the game in the monitor. When done, press any key to stop.

**Test Version 2 (Positioning):**
```powershell
.\test_version.bat v2_positioning
```

**Test Version 3 (Passing):**
```powershell
.\test_version.bat v3_passing
```

**Test Version 4 (Shooting):**
```powershell
.\test_version.bat v4_shooting
```

**Test Version 5 (Full):**
```powershell
.\test_version.bat v5_full
```

### Step 4: Compare Results

After each test, check the logs folder:
```
logs/
  2026-01-24-XX-XX-XX/  <- Latest test
```

## What to Observe

### Version 1 (Basic)
- Players all chase the ball
- Random kicks in any direction
- No coordination
- Chaotic movement

### Version 2 (Positioning)
- Players spread out on field
- Only closest player chases ball
- Better spacing
- Still random kicks

### Version 3 (Passing)
- Players pass to each other
- Better ball movement
- Still shoots randomly

### Version 4 (Shooting)
- Smart shots only when good angle
- Passes when can't shoot
- Much better goal attempts

### Version 5 (Full)
- Dribbling around opponents
- Defensive blocking
- Complete team coordination
- Professional-looking play

## Collecting Data

For each version, note:
- Goals scored (visible in monitor)
- Pass attempts (count in logs)
- Shot attempts (count in logs)
- Overall coordination quality

## Tips

1. **Restart server between tests** - Prevents connection errors
2. **Run each version for 2-3 minutes** - Enough to see patterns
3. **Take notes** - Write down what you observe
4. **Save interesting games** - The logs can be replayed later

## Troubleshooting

**Error: "no_more_player"**
- Server already has players connected
- Restart the server (Ctrl+C in WSL, then `./rcssserver`)

**Players not connecting**
- Check WSL IP hasn't changed: `hostname -I` in WSL
- Update `test_version.bat` if IP changed

**Game not starting**
- In monitor, click "Kick Off" or press K
- Or wait for timeout (server auto-starts after ~10 seconds)
