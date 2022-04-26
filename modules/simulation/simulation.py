from typing import List


class Simulation:
    """"""

    def __init__(self, agent_number: int, round_number: int) -> None:
        """"""
        self.agent_number = agent_number
        self.round_number = round_number

        self.agents: List = [Agent() for _ in range(agent_number)]

    def start(self) -> None:
        """"""
