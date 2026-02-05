# defender_fsm.py
from __future__ import annotations
from typing import Dict
from defender_states import DefenderState, HoldZone, InterceptBall, ClearBall, Action


class DefenderFSM:
    """
    Minimal defender FSM manager:
    - holds current state
    - checks transition
    - executes state
    """

    def __init__(self):
        self.states: Dict[str, DefenderState] = {
            "HoldZone": HoldZone(),
            "InterceptBall": InterceptBall(),
            "ClearBall": ClearBall(),
        }
        self.current_name = "HoldZone"
        self.current = self.states[self.current_name]

    def reset(self, initial_state: str = "HoldZone") -> None:
        if initial_state not in self.states:
            raise ValueError(f"Unknown state: {initial_state}")
        self.current_name = initial_state
        self.current = self.states[self.current_name]

    def tick(self, world) -> Action:
        next_name = self.current.check_transition(world)

        if next_name and next_name != self.current_name:
            if next_name not in self.states:
                raise ValueError(f"Transition to unknown state: {next_name}")

            self.current.on_exit(world)
            self.current_name = next_name
            self.current = self.states[self.current_name]
            self.current.on_enter(world)

        return self.current.execute(world)

    def get_state_name(self) -> str:
        return self.current_name
