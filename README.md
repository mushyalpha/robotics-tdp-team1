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

#### 4. Install NAOqi SDK (for hardware phase)
- Download from Aldebaran/SoftBank Robotics
- Follow installation guide in `docs/user_guides/naoqi_setup.md`

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

| Task | Command |
|------|---------|
| Check status | `git status` |
| Stage changes | `git add .` |
| Commit | `git commit -m "WP[X]: Brief description"` |
| Push | `git push origin branch-name` |
| Pull latest | `git pull origin develop` |
| Create branch | `git checkout -b feature/wp[X]-description` |
| Switch branch | `git checkout branch-name` |

### Daily Team Workflow

```bash
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

### 📚 Need More Help?
- **Comprehensive Guide:** [GitHub's Git Handbook](https://guides.github.com/introduction/git-handbook/)
- **Interactive Tutorial:** [Learn Git Branching](https://learngitbranching.js.org/)
- **Git Cheat Sheet:** [GitHub's Git Cheat Sheet](https://education.github.com/git-cheat-sheet-education.pdf)

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
│   ├── wp4_behavioral/      # High-level behaviors
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

## Contributing

### Coding Standards
- **Python:** Follow PEP 8, max 100 chars/line, 4 spaces (no tabs)
- **Naming:** `PascalCase` for classes, `snake_case` for functions, `UPPER_SNAKE_CASE` for constants
- **Docstrings:** Use Google style for all public functions/classes
- **Comments:** Explain *why*, not *what*

### Pull Request Rules
1. **Create feature branch:** `feature/wp[X]-description`
2. **Write tests** for new features (aim for 70% coverage)
3. **Update documentation** if needed
4. **Get at least 1 review** before merging
5. **No direct commits** to main/develop

### Code Review Checklist
- [ ] Code follows style guide
- [ ] Tests pass and coverage adequate
- [ ] Documentation updated
- [ ] No obvious bugs or security issues
- [ ] Performance acceptable

### Work Package Responsibilities
- **WP2 (Jie Shu):** Simulation accuracy, world configs, performance
- **WP3 (Bonolo):** Control stability, clear APIs, safety
- **WP4 (Zefu):** Modular behaviors, state machines, decision logic
- **WP5 (Chengjie):** Hardware compatibility, deployment docs
- **WP6 (Jinghao):** Test coverage, procedures, metrics

## 🔗 Useful Links

- [RoboCup Official Website](https://www.robocup.org/)
- [RoboCup Humanoid League](https://humanoid.robocup.org/)
- [NAO6 Documentation](https://www.softbankrobotics.com/emea/en/nao)
- [Webots Documentation](https://cyberbotics.com/doc/guide/index)
- [Project Requirements Document](docs/requirements.md)
