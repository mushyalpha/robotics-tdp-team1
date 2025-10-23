# NAO6 Robot Soccer Team - TDP Team 1

**University of Glasgow - James Watt School of Engineering**
**Robotics Team Design Project M (ENG5325)**

## Getting Started

### Prerequisites

- **Python 3.8+**
- **Git**
- **Webots R2023b+** (download from [cyberbotics.com](https://cyberbotics.com/))

### Installation

#### 1. Clone the Repository

```bash
git clone https://github.com/mushyalpha/robotics-tdp-team1.git
cd robotics-tdp-team1
```

#### 2. Install Python Dependencies

**Windows:**

```bash
pip install -r requirements.txt
```

**Linux/Mac:**

```bash
pip3 install -r requirements.txt
# or use virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

#### 3. Install Webots

**Windows:**

- Download from: https://cyberbotics.com/
- Run installer and add to PATH

**Linux (Ubuntu/Debian):**

```bash
# Download .deb package from cyberbotics.com
sudo dpkg -i webots_2023b_amd64.deb
sudo apt-get install -f  # Fix dependencies if needed
```

**Mac:**

```bash
# Download .dmg from cyberbotics.com and install
# Or use Homebrew:
brew install --cask webots
```

### Webots Simulation Setup

**Important:** We use a **shared simulation environment** that gets updated collaboratively:

1. **Main simulation files** are in `webots_simulation/worlds/`
2. **Jie Shu (WP2)** maintains the master simulation files
3. **Always pull latest changes** before working on simulation
4. **Don't modify world files directly** - create feature branches for simulation changes
5. **Coordinate with WP2** before making major simulation changes

### Running Simulation

```bash
# Open Webots
# File > Open World > webots_simulation/worlds/nao_soccer_field.wbt
# Run simulation
```

## Git Workflow

### First Time Setup

1. **Install Git:** Download from [git-scm.com](https://git-scm.com/) (Windows) or use package manager (Linux/Mac)
2. **Configure Git:**
   ```bash
   git config --global user.name "Your Name"
   git config --global user.email "firstname.lastname@glasgow.ac.uk"
   ```
3. **Clone repository:**
   ```bash
   git clone https://github.com/mushyalpha/robotics-tdp-team1.git
   cd robotics-tdp-team1
   ```

### Essential Commands

| Task          | Command                                       |
| ------------- | --------------------------------------------- |
| Check status  | `git status`                                |
| Stage changes | `git add .`                                 |
| Commit        | `git commit -m "WP[X]: Brief description"`  |
| Push          | `git push origin branch-name`               |
| Pull latest   | `git pull origin develop`                   |
| Create branch | `git checkout -b feature/wp[X]-description` |
| Switch branch | `git checkout branch-name`                  |

### Daily Team Workflow

```bash
# 0. IMPORTANT: Save your work first!
# If you have uncommitted changes, either commit them or stash them:
git add .
git commit -m "WP[X]: Work in progress"
# OR: git stash  (to temporarily save changes)

# 1. Start with latest changes
git checkout develop
git pull origin develop

# 2. Create your feature branch  
git checkout -b feature/wp[X]-your-feature

# 3. Work on your code, then commit
git add .
git commit -m "WP[X]: What you implemented"

# 4. Push and create Pull Request on GitHub
git push origin feature/wp[X]-your-feature
```

### Branch Rules

- **`main`** - Protected, stable releases only
- **`develop`** - Integration branch, pull from here daily
- **`feature/wp[X]-description`** - Your work branches
- **Never commit directly to main/develop!**

### Common Git Issues

**"I have uncommitted changes and need to switch branches":**

```bash
# Option 1: Commit your work in progress
git add .
git commit -m "WP[X]: Work in progress - will continue later"

# Option 2: Stash changes temporarily
git stash
# ... do other work ...
git stash pop  # Restore your changes later
```

**"Git won't let me switch branches":**

```bash
# Check what's preventing the switch
git status

# Usually means you have uncommitted changes - see above solutions
```

**"I forgot to pull latest changes before starting work":**

```bash
# If you haven't committed yet, stash and pull
git stash
git checkout develop
git pull origin develop
git checkout your-feature-branch
git stash pop

# If you have committed, merge develop into your branch
git checkout develop
git pull origin develop
git checkout your-feature-branch
git merge develop
```

### Branch Cleanup & Management

**What Happens as You Work:**
As you create more feature branches, your local Git will accumulate old branches:

```bash
git branch  # Shows all your local branches
* develop
  feature/wp3-balance-controller     # Merged but still local
  feature/wp3-kick-algorithm        # Merged but still local  
  feature/wp3-walking-gait          # Merged but still local
  feature/wp3-vision-integration    # Currently working on
```

**GitHub Auto-Delete vs Local Cleanup:**

- **GitHub automatically deletes** remote branches after PR merge
- **Local branches remain** on your computer until you delete them

**Weekly Cleanup Workflow:**

```bash
# 1. Switch to develop and update
git checkout develop
git pull origin develop

# 2. See which branches are safe to delete (already merged)
git branch --merged develop

# 3. Delete merged local branches (excludes develop/main)
git branch --merged develop | grep -v develop | grep -v main | xargs git branch -d

# 4. Clean up remote tracking references
git remote prune origin

# 5. Check your clean branch list
git branch -v
```

**Manual Cleanup (Alternative):**

```bash
# Delete specific merged branch
git branch -d feature/wp3-balance-controller

# Force delete if Git complains (but you know it's merged)
git branch -D feature/wp3-old-experiment

# Check what's left
git branch
```

**Keep Your Workspace Clean:**

- **Delete branches immediately** after PR merge
- **Keep only active work** - if it's merged, delete it
- **Use descriptive names** so you remember what branches were for

### 🛠️ Recommended VS Code Extensions

**Essential for this project:**

- **Markdown All in One** - Preview, table of contents, auto-formatting
- **Markdown Preview Enhanced** - Advanced preview with diagrams
- **GitLens** - Supercharged Git capabilities, blame annotations, history
- **Python** - Python language support, debugging, IntelliSense
- **Pylance** - Fast Python language server
- **autoDocstring** - Generates Python docstrings automatically
- **Better Comments** - Colour-coded comment highlighting
- **Bracket Pair Colorizer 2** - Matching bracket colours
- **indent-rainbow** - Coloured indentation for better readability

**Install via VS Code:**

1. Press `Ctrl+Shift+X` (Extensions)
2. Search for extension name
3. Click "Install"

**Extension IDs for quick install:**

```
yzhang.markdown-all-in-one
shd101wyy.markdown-preview-enhanced
eamodio.gitlens
ms-python.python
ms-python.vscode-pylance
njpwerner.autodocstring
aaron-bond.better-comments
coenraads.bracket-pair-colorizer-2
oderwat.indent-rainbow
```

**Quick install:** `Ctrl+Shift+P` → "Extensions: Install Extensions" → paste IDs above

### 📚 Need More Help?

- **Comprehensive Guide:** [GitHub&#39;s Git Handbook](https://guides.github.com/introduction/git-handbook/)
- **Interactive Tutorial:** [Learn Git Branching](https://learngitbranching.js.org/)
- **Git Cheat Sheet:** [GitHub&#39;s Git Cheat Sheet](https://education.github.com/git-cheat-sheet-education.pdf)

## Project Structure

```
robotics-tdp-team1/
├── docs/                    # Documentation
│   ├── meeting_notes/       # Weekly meeting records
│   ├── user_guides/         # Setup and usage guides
│   └── design_reviews/      # Design review documents
├── webots_simulation/       # Simulation environment
│   ├── worlds/              # Webots world files
│   ├── controllers/         # Robot controllers
│   └── plugins/             # Custom plugins
├── src/                     # Source code
│   ├── wp3_guidance_control/# Low-level control algorithms
│   ├── wp4_behavioral/      # High-level behaviours
│   ├── vision/              # Computer vision modules
│   └── utils/               # Utility functions
├── tests/                   # Test suite
├── naoqi_integration/       # NAOqi and Choreographe files
├── hardware_integration/    # Hardware testing
└── config/                  # Configuration files
```

## Testing

```bash
# Run all tests
pytest tests/

# Run specific test
pytest tests/test_motion_control.py

# With coverage
pytest --cov=src tests/
```

## Documentation

- **Project Plan:** `docs/project_plan.md`
- **Requirements:** `docs/requirements.md`
- **Meeting Notes:** `docs/meeting_notes/`
- **Development Log:** `docs/development_log.md` *(daily entries required)*
- **Work Package Logs:** `docs/wp_logs/` *(detailed technical logs)*

## Contributing

### Coding Standards

- **Python:** Follow PEP 8, max 100 chars/line, 4 spaces (no tabs)
- **Naming:** `PascalCase` for classes, `snake_case` for functions, `UPPER_SNAKE_CASE` for constants
- **Docstrings:** Use Google style for all public functions/classes
- **Comments:** Explain *why*, not *what*

### Pull Request Rules

1. **Create feature branch:** `feature/wp[X]-description`
2. **Update documentation** if needed
3. **Get at least 1 review** before merging
4. **No direct commits** to main/develop

### Code Review Checklist

- [ ] Code follows style guide
- [ ] Tests pass and coverage adequate
- [ ] Documentation updated
- [ ] No obvious bugs or security issues
- [ ] Performance acceptable

### Work Package Responsibilities

- **WP2 (Jie Shu):** Simulation accuracy, world configs, performance
- **WP3 (Bonolo):** Control stability, clear APIs, safety
- **WP4 (Zefu):** Modular behaviours, state machines, decision logic
- **WP5 (Chengjie):** Hardware compatibility, deployment docs
- **WP6 (Jinghao):** Test coverage, procedures, metrics

## Development Logging

### Simplified Logging Process

**Team members:** Maintain your individual WP log weekly
**Technical Lead (Bonolo):** Consolidates key progress into main development log

### Your Responsibility: WP Log Only

**Each team member maintains:** `docs/wp_logs/wp[X]_[name]_log.md`

**Update weekly with:**

- What you accomplished this week
- Technical decisions and why you made them
- Any issues
- Dependencies on other WPs
- Commits/PRs for traceability

**Example WP Log Entry:**

```
#### Week 2 (Oct 21-27, 2025)
- Implemented PID balance controller with Kp=1.2, Ki=0.1, Kd=0.05
- Fixed ankle joint oscillation by adjusting damping parameters
- Tested walking on flat surface - 90% success rate
- Blocker: Need IMU calibration data from hardware team
- Next: Test on slopes, integrate with motion controller
- Related: commit abc123f, PR #15
```

## 🔗 Useful Links

- [RoboCup Official Website](https://www.robocup.org/)
- [RoboCup Humanoid League](https://humanoid.robocup.org/)
- [NAO6 Documentation](https://www.softbankrobotics.com/emea/en/nao)
- [Webots Documentation](https://cyberbotics.com/doc/guide/index)
- [Project Requirements Document](docs/requirements.md)
