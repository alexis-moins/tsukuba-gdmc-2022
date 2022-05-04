from colorama import Fore

from src import env
from src.plots.plot import Plot
from src.simulation.buildings.building import Building
from src.simulation.city import City
from src.simulation.decisions.decision_maker import DecisionMaker


class Event:
    def __init__(self, name):
        self.name = name


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

        self.city: City = None
        self.events = []
        self.actions = []

    def start(self):
        year = 1

        # If you have multiple cities, just give a subplot here
        self.city = City(self.plot)
        self.decision_maker.city = self.city

        print('*** Starting simulation ***')

        print('Building the settlement\'s Town Hall')
        town_hall = env.BUILDINGS['TOWN_HALL']
        rotation = self.decision_maker.get_rotation()
        size = town_hall.get_size(rotation)
        plot = self.city.plot.get_subplot(size)

        self.city.add_building(town_hall, plot, rotation)

        while year < self.years:
            print(f'\n=> Start of year {year}')

            # Update city
            self.city.update()

            buildings = self.get_constructible_buildings()

            if buildings:
                rotation = self.decision_maker.get_rotation()
                choice, plot = self.decision_maker.choose_building(buildings, rotation)

                if choice is not None and plot is not None:
                    self.city.add_building(choice, plot, rotation)

            # Get event
            print('=> No event this year')

            # Update city
            self.city.update()

            # End of turn
            self.city.display()
            year += 1

    def get_constructible_buildings(self) -> list[Building]:
        """Return the available buildings for the year"""
        actions = [building for building in env.BUILDINGS.values()
                   if building.properties.cost <= self.city.productivity]

        # TODO Change ActionType enum to be NOTHING, CONSTUCTION, REPARATION, etc
        return actions
