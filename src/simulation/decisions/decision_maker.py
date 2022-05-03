import random

from src.plots.plot import Plot
from src.utils.coordinates import Coordinates
from src.utils.coordinates import Size
from src.utils.criteria import Criteria


class DecisionMaker:
    """"""

    def __init__(self):
        """"""
        self.city = None

    def choose_building(self, possible_actions, rotation: int):
        act = random.choice(possible_actions)
        print(f'Possible actions [{", ".join(str(a) for a in possible_actions)}] :: Chose {act}')
        return act

    def get_coordinates(self, plot: Plot, size: Size) -> Coordinates:
        plot = Plot(*plot.start, size=plot.size - size)
        return random.choice(plot.get_blocks(Criteria.MOTION_BLOCKING_NO_TREES)).coordinates

    def get_rotation(self) -> int:
        orientation = [0, 90, 180, 270]
        return random.choice(orientation)
