import random

from src.plots.plot import Plot
from src.simulation.buildings.building import Building
from src.simulation.buildings.building import Buildings
from src.simulation.decisions.decision_maker import DecisionMaker
from src.simulation.simulation import ActionTypes
from src.utils.coordinates import Coordinates
from src.utils.coordinates import Size

action_types = {Buildings.HOUSE.value[1]: ActionTypes.BED, Buildings.FARM.value[1]: ActionTypes.FOOD,
                Buildings.SAWMILL.value[1]: ActionTypes.WORK, Buildings.FORGE.value[1]: ActionTypes.WORK}


class SmartDecisionMaker(DecisionMaker):

    def __init__(self, plot: Plot):
        super().__init__()
        self.plot = plot
        self.chose_rotation = 0
        self.chose_coordinates = None
        self.action_choose: Building | None = None

    def get_action(self, possible_actions: list[Building]):
        print(f'Possible actions [{", ".join(str(a) for a in possible_actions)}]')

        # No point in computing anything if there is one option
        if len(possible_actions) == 1:
            return possible_actions[0]

        city_stats = [(self.city.bed_amount, ActionTypes.BED), (self.city.food_production, ActionTypes.FOOD),
                      (self.city.work_production, ActionTypes.WORK)]
        next_action_type = min(city_stats, key=lambda item: item[0])[1]
        priority_actions = []
        for a in possible_actions:
            if a in action_types and action_types[a] == next_action_type:
                priority_actions.append(a)

        # We check if there is a plot of a default size 20 by 20 available

        # TODO : make actions an enum with buildings accessibles to get the building size and know if we can build them
        dummy_plot = self.plot.get_subplot(Size(20, 20), occupy_coord=False)

        if dummy_plot:
            # TODO : Implement brain (Should be as good as Alexis' one (near perfect))
            # TODO : If plot is calculated according to the correct size of the building, store the chosen coordinate
            if priority_actions:
                action = random.choice(priority_actions)
                self.action_choose = action
                return action
            else:
                action = random.choice(possible_actions)
                self.action_choose = action
                return action
        else:
            return 'NOTHING'

    def get_coordinates(self, plot: Plot, size: Size) -> Coordinates:
        padding = 3
        if self.action_choose:
            subplot = self.plot.get_subplot(size, padding=padding, building_type=self.action_choose.build_type)
        else:
            subplot = self.plot.get_subplot(size, padding=padding)
        return subplot.start

    def get_rotation(self) -> int:
        # TODO : Implement brain here too
        orientation = [0, 90, 180, 270]
        self.chose_rotation = 0
        return random.choice(orientation)
