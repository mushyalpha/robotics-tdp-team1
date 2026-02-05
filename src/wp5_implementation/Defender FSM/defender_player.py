# defender_player.py
from __future__ import annotations
from types import SimpleNamespace
import time
from defender_fsm import DefenderFSM
from defender_states import Action


# ---------- Dummy motion (replace with real motion module) ----------
class DummyMotion:
    def walk_to(self, x: float, y: float, theta: float | None, speed: float):
        print(f"[MOTION] WALK_TO x={x:.2f} y={y:.2f} theta={None if theta is None else round(theta,2)} speed={speed}")

    def kick(self, dx: float, dy: float, power: float):
        print(f"[MOTION] KICK dir=({dx:.2f},{dy:.2f}) power={power}")

    def stop(self):
        print("[MOTION] STOP")

    def idle(self):
        print("[MOTION] IDLE")


# ---------- World builder (replace this with env + world_model integration) ----------
def build_dummy_world(t: float):
    """
    A tiny fake world snapshot for testing:
    - our goal at (-3, 0)
    - robot near goal
    - ball moves slowly towards our goal then across
    """
    our_goal = (-3.0, 0.0)
    robot_pose = (-2.0, 0.0, 0.0)  # x, y, theta

    # Ball moves with time
    bx = -0.5 - 0.15 * t
    by = 0.3 * (1.0 if int(t) % 4 < 2 else -1.0)
    vx = -0.15
    vy = 0.0

    # Game phase always playing for dummy
    phase = "PLAYING"

    world = SimpleNamespace(
        robot=SimpleNamespace(id=2, pose=robot_pose),
        ball=SimpleNamespace(pos=(bx, by), vel=(vx, vy)),
        game=SimpleNamespace(phase=phase),
        field=SimpleNamespace(our_goal=our_goal),
    )
    return world


# ---------- Action application ----------
def apply_action(motion: DummyMotion, action: Action):
    if action.type == "WALK_TO":
        x, y = action.target_xy if action.target_xy else (0.0, 0.0)
        motion.walk_to(x, y, action.target_theta, action.speed)
    elif action.type == "KICK":
        dx, dy = action.kick_dir if action.kick_dir else (1.0, 0.0)
        motion.kick(dx, dy, action.kick_power)
    elif action.type == "STOP":
        motion.stop()
    else:
        motion.idle()


# ---------- Main loop (MVP) ----------
def main():
    fsm = DefenderFSM()
    motion = DummyMotion()

    start = time.time()
    for _ in range(30):  # run 30 ticks
        t = time.time() - start
        world = build_dummy_world(t)

        action = fsm.tick(world)
        print(f"[FSM] state={fsm.get_state_name()} action={action.type}")

        apply_action(motion, action)
        time.sleep(0.2)


if __name__ == "__main__":
    main()
