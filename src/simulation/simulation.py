import random
from collections import Counter
from dataclasses import dataclass
from dataclasses import field
from os import kill
from textwrap import wrap

from colorama import Fore
from gdpc import interface
from gdpc import toolbox

from src import env
from src.blocks.block import Block
from src.plots.plot import Plot
from src.simulation.buildings.building import Building
from src.simulation.buildings.building_type import BuildingType
from src.simulation.city import City
from src.simulation.decisions.decision_maker import DecisionMaker


@dataclass(frozen=True)
class Event:
    """"""
    name: str
    is_dangerous: bool = field(default=False)
    deadliness: int = field(default=0)
    kills: tuple[int, int] = field(default_factory=lambda: (0, 0))

    def resolve(self, city: City) -> None:
        """"""
        if self.is_dangerous:
            if random.randint(1, 100) <= self.deadliness:
                kills = max(0, min(random.randint(*self.kills), len(city.inhabitants)))
                print(
                    f'=> The {Fore.RED}{self.name.lower()}{Fore.WHITE} killed {Fore.RED}[{kills}]{Fore.WHITE} villagers this year')
        else:
            print(
                f'=> This year we celebrate {Fore.CYAN}{self.name.lower()}{Fore.WHITE}')


events = (Event('Wedding'), Event('Wandering trader'), Event('Town Celebration'),
          Event('Fire', is_dangerous=True, deadliness=30, kills=(1, 2)),
          Event('Barbarian attack', is_dangerous=True, deadliness=50, kills=(2, 4)),
          Event('Wolves attack', is_dangerous=True, deadliness=30, kills=(4, 4)))


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

        print(f'{Fore.YELLOW}***{Fore.WHITE} Starting simulation {Fore.YELLOW}***{Fore.WHITE}')
        history = []

        town_hall = env.BUILDINGS['Town Hall']
        rotation = self.decision_maker.get_rotation()
        if env.DEBUG:
            print(f'rotation {rotation}')
        plot = self.city.plot.get_subplot(town_hall, rotation)

        self.city.add_building(town_hall, plot, rotation)
        self.city.update(0)
        self.city.display()

        while year < self.years:
            print(f'\n\n\n=> Start of year {Fore.RED}[{year}]{Fore.WHITE}')

            buildings = self.get_constructible_buildings()

            if buildings:
                rotation = self.decision_maker.get_rotation()
                choice, plot = self.decision_maker.choose_building(buildings, rotation)

                if choice is not None and plot is not None:
                    self.city.add_building(choice, plot, rotation)

            # Get event

            if random.randint(0, 1):
                event = random.choice(events)
                event.resolve(self.city)
                history.append((year, event))
            else:
                print('=> No event this year')

            # Update city
            self.city.update(year)

            self.city.make_buildings_grow_old()

            self.city.repair_buildings()

            # End of turn
            self.city.display()
            year += 1

        decoration_buildings = [building for building in env.BUILDINGS.values()
                                if building.properties.building_type is BuildingType.DECORATION]

        print('\nAdding decorations:')
        for decoration in random.choices(decoration_buildings, k=len(self.city.buildings)*2):
            rotation = self.decision_maker.get_rotation()
            plot = self.city.plot.get_subplot(decoration, rotation)

            if plot:
                self.city.add_building(decoration, plot, rotation)

        print(
            f'\n{Fore.YELLOW}***{Fore.WHITE} Simulation ended at year {Fore.RED}{year}/{self.years}{Fore.WHITE} {Fore.YELLOW}***{Fore.WHITE}')

        history_string = "\n\n".join(f'Year {year}: {event.name.lower()}' for year, event in history)
        print(f'City history : {history_string}')

        interface.sendBlocks()

        interface.setBuffering(False)

        # make a book
        book_data = toolbox.writeBook(history_string, title='City history', author='The Mayor')
        lectern_list = self.city.buildings[0].blocks.filter('lectern')
        if len(lectern_list):
            lectern: Block = lectern_list[0]
            toolbox.placeLectern(*lectern.coordinates, book_data, facing=lectern.properties['facing'])

        # History of buildings
        for building in self.city.buildings[1:]:
            colors = ('§6', '§7', '§9', '§a', '§b', '§c', '§d')
            color = random.choice(colors)

            general_data = f'{color}{building.name}§0\n{"=" * 18}\n'
            general_data += f'Workers: {color}{len(building.workers)}/{building.properties.workers}§0\n'
            general_data += f'Beds: {color}{len(building.inhabitants)}/{building.properties.number_of_beds}§0\n'
            general_data += f'Food: {color}+{building.properties.food_production}§0'
            book_data = toolbox.writeBook(f'{general_data}\n\n' + '\n\n'.join(building.history),
                                          title=f'Year {year}\'s report', author='Settlement Construction Community (SCC)')
            lectern_list = building.blocks.filter('lectern')

            interface.sendBlocks()

            if len(lectern_list):
                lectern: Block = lectern_list[0]
                interface.placeBlock(*lectern.coordinates, 'air')
                toolbox.placeLectern(*lectern.coordinates, book_data, facing=lectern.properties['facing'])

        interface.setBuffering(True)
        interface.sendBlocks()

    def get_constructible_buildings(self) -> list[Building]:
        """Return the available buildings for the year"""
        counter = Counter([building.name for building in self.city.buildings])

        actions = [building for building in env.BUILDINGS.values()
                   if building.properties.cost <= self.city.production_points
                   and building.properties.building_type is not BuildingType.DECORATION
                   and counter[building.name] < building.max_number]

        formatted = f"\n{' ' * 22}".join(wrap(", ".join(str(action) for action in actions), width=80))
        print(f'Available buildings: [{formatted}]')

        # TODO Change ActionType enum to be NOTHING, CONSTUCTION, REPARATION, etc
        return actions
