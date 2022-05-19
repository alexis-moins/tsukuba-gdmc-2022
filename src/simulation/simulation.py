import random
from collections import Counter
from copy import deepcopy
from dataclasses import dataclass
from dataclasses import field
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


_descriptions: dict[str, list] = env.get_content('descriptions.yaml')


def get_description(event: str) -> str:
    """"""
    choice: dict = random.choice(_descriptions[event.lower()])
    _descriptions[event.lower()].remove(choice)

    if len(_descriptions[event.lower()]) == 0:
        del _descriptions[event.lower()]

    return choice


@dataclass(frozen=True)
class Event:
    """"""
    name: str
    is_dangerous: bool = field(default=False)
    kills: tuple[int, int] = field(default_factory=lambda: (0, 0))

    def resolve(self, city: City, year: int) -> str:
        """"""
        if self.is_dangerous:

            mod = 0
            for building in city.buildings:
                if building.name == 'Watch Tower':
                    mod = -2
                    break

            kills = max(0, min(random.randint(*self.kills), max(len(city.inhabitants) - 2 + mod, 2)))
            print(
                f'=> The {Fore.RED}{self.name.lower()}{Fore.WHITE} killed {Fore.RED}[{kills}]{Fore.WHITE} villagers this year')

            for v in random.sample(city.inhabitants, kills):
                city.villager_die(v, year, self.name.lower())

            description = get_description(self.name)
            description = description.format(victims=kills, direction=random.choice([
                'north', 'south', 'east', 'west']))

            if self.name.lower() not in _descriptions:
                events.remove(self)

            return f'Year {year}\n{description}'

        else:
            print(
                f'=> This year we celebrate {Fore.CYAN}{self.name.lower()}{Fore.WHITE}')

            if self.name == 'Wedding':
                city.wedding()

            return f'Year {year}\nen event'


events = [Event('Wedding'), Event('Wandering trader'), Event('Town Celebration'),
          Event('Fire', is_dangerous=True, kills=(1, 2)),
          Event('Barbarian attack', is_dangerous=True, kills=(2, 4)),
          Event('Wolf attack', is_dangerous=True, kills=(4, 4))]


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
        self.history: list[str] = []

    def start(self):
        year = 1

        # If you have multiple cities, just give a subplot here
        self.city = City(self.plot, year)
        self.decision_maker.city = self.city

        print(f'{Fore.YELLOW}***{Fore.WHITE} Starting simulation {Fore.YELLOW}***{Fore.WHITE}')

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

            if random.randint(1, 4) == 4:
                event = random.choice(events)
                self.history.append(event.resolve(self.city, year))
            else:
                print('=> No event this year')

            # Update city
            self.city.update(year)

            # self.city.make_buildings_grow_old()

            # self.city.repair_buildings()

            # End of turn
            self.city.display()
            year += 1

        self.city.spawn_villagers()
        self.city.plot.add_roads_signs(10, self.city.buildings)

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

        interface.sendBlocks()
        interface.setBuffering(False)

        # make a book
        book_data = toolbox.writeBook('\n\n'.join(self.history), title='City history', author='The Mayor')
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

        actions = [deepcopy(building) for building in env.BUILDINGS.values()
                   if building.properties.cost <= self.city.production_points
                   and building.properties.building_type is not BuildingType.DECORATION
                   and counter[building.name] < building.max_number]

        formatted = f"\n{' ' * 22}".join(wrap(", ".join(str(action) for action in actions), width=80))
        print(f'Available buildings: [{formatted}]')

        # TODO Change ActionType enum to be NOTHING, CONSTUCTION, REPARATION, etc
        return actions
