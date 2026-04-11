# Presenter Notes — Results & Analysis
### ENG5326 Robotics M | Team 1 | Final Condensed Run

---

## Slide 1 — Methodology

**What to say:**
> "We wanted to test exactly how much each of our parameters influence key performance metrics.
> 
> We systematically adjusted each parameter across five different values, running over 1,050 simulations. This let us see how each change impacted our key metrics, like win rate and goal difference."

---

## Slide 2 — Performance Impact

**What to say:**
> "We focused on two key outcomes: win rate and goal difference. Two clear patterns stood out.
> 
> First is that when kick power is low, the win rate drops to 3.3%. But when we increase it to the power out, our win rate jumped to over 70%. 
> 
> Second, when robots only shoot close to the goal—within about 1 meter—our win rate rises to around 75%. But when they shoot from far away, they waste possession and performance drops sharply.
> 
> So the key takeaway is: dominate physically, and only take high-quality shots."

*(Data Reference for Presenter):*
| Condition | Win Rate | Goal Diff |
| :--- | :---: | :---: |
| Low Kick Power (0.85x) | 0.0% | -1.0 |
| **Max Kick Power (1.25x)** | **73.3%** | **+0.8** |
| Far Shooting (2.8m)| 10.0% | -1.2 |
| **Close Shooting (1.0m)**| **76.7%** | **+1.3** |
| **High Chase/Pressure (2.5m)** | **66.7%** | **+0.6** |

---

## Slide 3 — Offensive Engine Dynamics

**What to say:**
> "So the key idea here is simple: fewer, high-quality shots are far more effective than taking many low-probability ones.
> 
> Our data also shows that a high press is the best way to control the game.
> 
> So the idea here is if you get to the ball first, you completely control the game."

---

## Slide 4 — Synthesis & Optimal Robot Brain

**What to say:**
> "After over a thousand matches, a clear strategy emerged. The best strategy is to dominate physically, control the pitch, and only take the best shots.
> 
> We took these optimal parameters and applied them to our balanced strategy.
> 
> We kept the same baseline behaviour, but created two versions: a standard balanced team, and an optimised balanced team. This allowed us to directly compare the impact of our improvements in a controlled way.
> 
> So in the end, we’re not changing the system—we’re simply making a strong strategy even stronger."

---

*Presenter notes updated 23 March 2026 | Team 1 | ENG5326 Robotics M*
