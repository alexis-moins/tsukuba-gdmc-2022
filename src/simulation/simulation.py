from enum import Enum

from src.plots.plot import Plot
from src.simulation.buildings.building import Building
from src.simulation.buildings.building import Buildings
from src.simulation.city import City
from src.simulation.decisions.decision_maker import DecisionMaker
from src.utils import loader


class Event:
    def __init__(self, name):
        self.name = name


class ActionTypes(Enum):
    BED = 0
    FOOD = 1
    WORK = 2


class Simulation:
    """"""

    def __init__(self, plot: Plot, decision_maker: DecisionMaker, years: int, friendliness: float = 1, field_productivity: float = 1, humidity: float = 1):
        """"""
        self.decision_maker = decision_maker
        self.humidity = humidity
        self.field_productivity = field_productivity
        self.friendliness = friendliness
        self.plot = plot
        self.years = years

        self.city = None
        self.events = []
        self.actions = []

    def start(self):
        year = 0

        # If you have multiple cities, just give a subplot here
        self.city = City(self.plot)
        self.decision_maker.city = self.city

        print('Starting Game !!')
        print('Give a rotation and a location for the Town hall')

        town_hall = Building(loader.structures['house1'], "Town hall", None, 10, 10, 10)
        r = self.decision_maker.get_rotation()
        coord = self.decision_maker.get_coordinates(self.city.plot, town_hall.structure.get_size(r))
        self.city.add_building(town_hall, coord, r)

        while year < self.years:

            # Update city
            self.city.update()

            action = self.decision_maker.get_action(self.get_available_actions())

            # Execute action
            for building in Buildings:
                cost, build = building.value
                if action == build:
                    if self.city.productivity >= cost:
                        rotation = self.decision_maker.get_rotation()
                        self.city.add_building(build,
                                               self.decision_maker.get_coordinates(self.city.plot,
                                                                                   build.structure.get_size(rotation)),
                                               rotation
                                               )
                        print(f'Added building {build}')
                    else:
                        print(f'Not enough productivity available for this ! {self.city.productivity}/{cost}')
                    break

            # Get event
            print('No event this year')

            # Update city
            # self.update_city()

            # End turn
            print(f'End of year {year}, current stats : {self.city}')
            # input('Enter to go to next year')
            year += 1

            # input('Enter to go to next year')

    def get_available_actions(self):
        actions = ['Nothing']
        for b in Buildings:
            if b.value[0] <= self.city.productivity:
                actions.append(b.value[1])
        return actions
