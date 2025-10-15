# NAO6 Robot Soccer Team - TDP Team 1

**University of Glasgow - James Watt School of Engineering**
**Robotics Team Design Project M (ENG5325)**
**Cyberphysical RoboCup Soccer Teams**

## Getting Started

### Prerequisites

- Python 3.8+
- Webots R2023b+ (download from [cyberbotics.com](https://cyberbotics.com/))
- Git

### Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/mushyalpha/robotics-tdp-team1.git
   cd robotics-tdp-team1
   ```
2. **Install Python dependencies:**

   ```bash
   pip install -r requirements.txt
   ```
3. **Install Webots:**

   - Download from: https://cyberbotics.com/
   - Install and add to PATH
4. **Install NAOqi SDK (for hardware phase):**

   - Download from Aldebaran/SoftBank Robotics
   - Follow installation guide in `docs/user_guides/naoqi_setup.md`

### Running Simulation

```bash
# Open Webots
# File > Open World > webots_simulation/worlds/nao_soccer_field.wbt
# Run simulation
```

## Development Workflow

### Branch Structure

- `main` - Stable releases only (protected)
- `develop` - Integration branch
- `feature/wp[X]-description` - Feature branches for each work package

### For Each Work Package

**Example for WP3 (Guidance & Control):**

```bash
# Create your feature branch
git checkout -b feature/wp3-motion-control

# Work on your code in src/wp3_guidance_control/

# Commit regularly
git add .
git commit -m "WP3: Implemented PID controller for walking"

# Push to GitHub
git push origin feature/wp3-motion-control

# Create Pull Request on GitHub for review
```

## 📂 Project Structure

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

- Project Plan: `docs/project_plan.md`
- Requirements: `docs/requirements.md`
- Meeting Notes: `docs/meeting_notes/`
- User Guides: `docs/user_guides/`
- GitHub Guide: `docs/user_guides/github_guide.md`

## Key Deliverables

### Simulation Phase (Oct 2025 - Feb 2026)

- [ ] Webots simulation environment with pitch and ball
- [ ] NAO6 robot models with basic locomotion
- [ ] Behavioral algorithms for goalkeeper, defender, attacker
- [ ] Design Review Presentation (Week of Feb 2, 2026)

### Hardware Phase (Feb 2026 - Apr 2026)

- [ ] Transfer algorithms to physical NAO6 robots
- [ ] Hardware system tests
- [ ] Field tests on physical pitch
- [ ] Final Presentation (Week of Mar 23, 2026)
- [ ] Final Report (Submit: Apr 20-24, 2026)

## 🤝 Contributing

See `docs/CONTRIBUTING.md` for:

- Coding standards
- Git workflow
- Testing requirements
- Code review process

## 🔗 Useful Links

- [RoboCup Official Website](https://www.robocup.org/)
- [RoboCup Humanoid League](https://humanoid.robocup.org/)
- [NAO6 Documentation](https://www.softbankrobotics.com/emea/en/nao)
- [Webots Documentation](https://cyberbotics.com/doc/guide/index)
- [Project Requirements Document](docs/requirements.md)
