import numpy as np

robot = {'x': 0.0, 'y': 0.0, 'heading': 0.0}
ball = {'x': 2.0, 'y': 1.0}
goal = {'x': 4.5, 'y': 0.0}

pitch_length = 9.0 #m
pitch_width = 6.0
goal_width = 2.6

##pitch boundariies
Xs = (-4.5, 4.5)
Goals = (-1.3, 1.3)
Ys = (-3.0, 3.0)

def get_measurements(robot, ball):

    dx = ball["x"] - robot["x"] 
    dy = ball["y"] - robot["y"]

    distance = np.sqrt(dx**2 + dy**2)
    angle_to_ball = np.arctan2(dy, dx)
    
    bearing = angle_to_ball - robot["heading"]

    #normalise
    bearing = bearing % (2 * np.pi) 
    if bearing > np.pi:
        bearing = bearing - 2 * np.pi

    return distance, bearing

kick_dist = 0.2
angle_tolerance = 0.1 #5 degr

def decide_action(distance, bearing):

    if distance <= kick_dist:
        return "kick"

    if bearing > angle_tolerance:
        return "turn_left"

    elif bearing < - angle_tolerance:
        return "turn_right"

    else:
        return "walk_forward"

step_size = 0.1 
turn_rate = 0.1 
kick_power = 2.0

def apply_action(robot, ball, action):
    if action == "turn_left":
        robot['heading'] += turn_rate
    
    elif action == "turn_right":
        robot['heading'] -= turn_rate
    
    elif action == "walk_forward":
        robot['x'] += step_size * np.cos(robot['heading'])
        robot['y'] += step_size* np.sin(robot['heading'])
    
    elif action == "kick":
        dx = goal['x'] - ball['x']
        dy = goal['y'] - ball['y']
        dist = np.sqrt(dx**2 + dy**2)
        
        ball['x'] += (dx / dist) *kick_power
        ball['y'] += (dy / dist) *kick_power
        return 

def check_goal(ball):
    if ball['x'] > 4.5 and ball['y'] < 1.3 and ball['y'] > -1.3:
        return True
    return False

def run_experiment(trials=50):
    goals_scored = 0

    for i in range(trials):
        current_robot = {'x': 0.0, 'y': 0.0, 'heading': 0.0}
        current_ball = {
            'x': np.random.uniform(1.0, 4.0),
            'y': np.random.uniform(-2.5, 2.5)
        }

        for step in range(300):
            d, b = get_measurements(current_robot, current_ball)
            act = decide_action(d, b)
            apply_action(current_robot, current_ball, act)

            if act == "kick":
                if check_goal(current_ball):
                    goals_scored += 1
                break
                
    print(f"--- Experiment Results ---")
    print(f"Trials: {trials}")
    print(f"Goals:  {goals_scored}")
    print(f"Success Rate: {(goals_scored/trials)*100}%")

if __name__ == "__main__":
    run_experiment(50)