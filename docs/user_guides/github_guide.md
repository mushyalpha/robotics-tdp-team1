# GitHub Guide for Team Members

## 📚 Table of Contents
1. [First Time Setup](#first-time-setup)
2. [Daily Workflow](#daily-workflow)
3. [Common Commands](#common-commands)
4. [Branch Naming Convention](#branch-naming-convention)
5. [Pull Request Process](#pull-request-process)
6. [Troubleshooting](#troubleshooting)

---

## 🚀 First Time Setup

### 1. Install Git

**Windows:**
```bash
# Download from https://git-scm.com/
# Run installer and follow instructions
```

**Mac:**
```bash
# Check if already installed
git --version

# If not installed, use Homebrew:
brew install git
```

**Linux:**
```bash
sudo apt-get update
sudo apt-get install git
```

### 2. Configure Git

```bash
# Set your name (use your real name)
git config --global user.name "Your Name"

# Set your email (use your University email)
git config --global user.email "firstname.lastname@glasgow.ac.uk"

# Optional: Set default editor
git config --global core.editor "code"  # for VS Code
```

### 3. Clone the Repository

```bash
# Navigate to where you want to store the project
cd ~/Documents/  # or wherever you prefer

# Clone the repository
git clone https://github.com/[USERNAME]/robotics-tdp-team1.git

# Enter the project directory
cd robotics-tdp-team1
```

### 4. Verify Setup

```bash
# Check you're in the right place
pwd  # Should show .../robotics-tdp-team1

# Check git status
git status  # Should show you're on main branch

# See all branches
git branch -a
```

---

## 💻 Daily Workflow

### Starting Your Work Session

```bash
# 1. Navigate to project directory
cd ~/Documents/robotics-tdp-team1

# 2. Switch to develop branch
git checkout develop

# 3. Get latest changes from team
git pull origin develop

# 4. Create your feature branch
git checkout -b feature/wp[X]-description
# Example: git checkout -b feature/wp3-walking-controller
```

### While Working

```bash
# Check what files you've changed
git status

# See specific changes in files
git diff

# Add specific files to staging
git add src/wp3_guidance_control/motion_controller.py

# Or add all changes (be careful!)
git add .

# Commit with descriptive message
git commit -m "WP3: Implemented PID controller for robot balance"

# Push your branch to GitHub
git push origin feature/wp3-walking-controller
```

### Commit Message Format

Use this format for clear commit messages:
```
WP[X]: Brief description of change

Longer explanation if needed (optional)
- Detail 1
- Detail 2
```

Examples:
```
WP3: Added forward kinematics for NAO6 leg

WP4: Implemented goalkeeper diving behavior
- Added collision detection
- Optimized reaction time

WP2: Fixed Webots world lighting issues
```

---

## 🔧 Common Commands

### Essential Commands

```bash
# Check current branch
git branch

# See commit history
git log --oneline -10  # Last 10 commits

# Switch to another branch
git checkout branch-name

# Create and switch to new branch
git checkout -b feature/new-feature

# Update your branch with latest develop
git checkout develop
git pull
git checkout your-branch
git merge develop
```

### Undoing Changes

```bash
# Discard changes in a file (before staging)
git checkout -- filename.py

# Unstage a file (after git add)
git reset HEAD filename.py

# Undo last commit (keep changes)
git reset --soft HEAD~1

# Undo last commit (discard changes) - CAREFUL!
git reset --hard HEAD~1
```

### Viewing Changes

```bash
# See all modified files
git status -s

# See changes in specific file
git diff src/wp3_guidance_control/motion.py

# See changes between branches
git diff develop..feature/wp3-walking

# See who changed what
git blame filename.py
```

---

## 🌳 Branch Naming Convention

Use descriptive branch names following this pattern:

```
feature/wp[X]-brief-description
bugfix/wp[X]-issue-description
hotfix/critical-issue
```

Examples:
- `feature/wp3-pid-controller`
- `feature/wp4-goalkeeper-behavior`
- `bugfix/wp2-webots-crash`
- `hotfix/simulation-memory-leak`

---

## 🔄 Pull Request Process

### 1. Push Your Branch

```bash
# Make sure all changes are committed
git status

# Push to GitHub
git push origin feature/your-branch-name
```

### 2. Create Pull Request on GitHub

1. Go to https://github.com/[USERNAME]/robotics-tdp-team1
2. Click "Compare & pull request" button
3. Fill in the PR template:

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update

## Work Package
WP[X]: [Work package name]

## Testing
- [ ] Tested in simulation
- [ ] Unit tests pass
- [ ] No linting errors

## Checklist
- [ ] Code follows project style
- [ ] Comments added where needed
- [ ] Documentation updated
- [ ] No merge conflicts
```

### 3. Request Review

- Assign reviewers (at least one team member)
- Link related issues
- Add appropriate labels

### 4. After Review

```bash
# If changes requested, make them in your branch
git add .
git commit -m "WP3: Addressed review comments"
git push origin feature/your-branch-name

# After approval and merge, clean up
git checkout develop
git pull
git branch -d feature/your-branch-name  # Delete local branch
```

---

## 🔥 Troubleshooting

### Merge Conflicts

```bash
# If you get merge conflicts
# 1. Open conflicted files
# 2. Look for <<<<<<< HEAD markers
# 3. Manually resolve conflicts
# 4. Remove conflict markers
# 5. Stage resolved files
git add resolved_file.py
# 6. Continue merge
git merge --continue
```

### Accidentally Committed to Wrong Branch

```bash
# If you committed to main/develop by mistake
# 1. Create new branch from current state
git checkout -b feature/correct-branch

# 2. Switch back to main/develop
git checkout develop

# 3. Reset to previous state
git reset --hard origin/develop

# 4. Continue work on correct branch
git checkout feature/correct-branch
```

### Can't Pull Due to Local Changes

```bash
# Option 1: Stash changes temporarily
git stash
git pull
git stash pop

# Option 2: Commit changes first
git add .
git commit -m "WIP: Work in progress"
git pull
```

---

## ⚠️ What NOT to Do

❌ **Never force push to shared branches**
```bash
git push -f  # DON'T DO THIS on main/develop
```

❌ **Never commit directly to main**
```bash
# Always work in feature branches!
```

❌ **Never commit sensitive information**
- Passwords
- API keys
- Personal data

❌ **Never commit large binary files**
- Use .gitignore for generated files
- Videos/datasets should be stored elsewhere

---

## 📞 Getting Help

### Resources
- Git Documentation: https://git-scm.com/doc
- GitHub Guides: https://guides.github.com/
- Interactive Tutorial: https://learngitbranching.js.org/

### Team Contacts
- **GitHub Lead:** Bonolo Masima
- **Project Manager:** Ciarán Breen

### Useful Commands for Help
```bash
# Get help for any git command
git help <command>
git help commit
git help merge

# Quick command reminder
git <command> -h
git commit -h
```

---

## 📝 Quick Reference Card

| Task | Command |
|------|---------|
| Clone repo | `git clone [url]` |
| Check status | `git status` |
| Create branch | `git checkout -b [branch-name]` |
| Switch branch | `git checkout [branch-name]` |
| Add changes | `git add .` |
| Commit | `git commit -m "[message]"` |
| Push | `git push origin [branch-name]` |
| Pull | `git pull origin [branch-name]` |
| See branches | `git branch -a` |
| See history | `git log --oneline` |
| See changes | `git diff` |

---

*Last updated: October 2025*
