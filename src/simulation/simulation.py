import math
import random
from cgitb import lookup
from collections import Counter
from copy import deepcopy, copy
from dataclasses import dataclass
from dataclasses import field
from textwrap import wrap

from colorama import Fore
from gdpc import interface
from gdpc import lookup
from gdpc import toolbox

from src import env
from src.blocks.block import Block
from src.plots.plot import Plot
from src.simulation.buildings.building import Building
from src.simulation.buildings.building_type import BuildingType
from src.simulation.city import City
from src.simulation.decisions.decision_maker import DecisionMaker
from src.utils.criteria import Criteria

_descriptions: dict[str, list] = env.get_content('descriptions.yaml')


def get_data(event: str) -> dict:
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
        if self.is_dangerous and year >= 10:

            # special effect depending on event
            if self.name == 'Wolf attack':
                dog_names = ["MAX", "KOBE", "OSCAR", "COOPER", "OAKLEY", "MAC", "CHARLIE", "REX ", "RUDY", "TEDDY ",
                             "BAILEY", "CHIP", "BEAR ", "CASH ", "WALTER", "MILO ", "JASPER", "BLAZE", "BENTLEY", "BO",
                             "OZZY", "Bella", "Luna", "Lucy", "Daisy", "Zoe", "Lily", "Lola", "Bailey", "Stella",
                             "Molly", "Coco", "Maggie", "Penny"]
                x, y, z = random.choice(city.buildings).get_entrance().coordinates
                y += 1
                for i in range(random.randint(5, 20)):
                    interface.runCommand(f'summon minecraft:wolf {x} {y} {z} {{CustomName:"\\"{random.choice(dog_names).capitalize()}\\""}}')

            mod = 0
            for building in city.buildings:
                if building.name == 'Watch Tower':
                    print('The tower is protecting us')
                    mod = -2
                    break

            kills = max(1, min(random.randint(*self.kills), max(len(city.inhabitants) - 2 + mod, 2)))
            print(
                f'=> The {Fore.RED}{self.name.lower()}{Fore.WHITE} killed {Fore.RED}[{kills}]{Fore.WHITE} villagers this year')

            for v in random.sample(city.inhabitants, kills):
                city.villager_die(v, year, self.name.lower())

            data = get_data(self.name)
            description = data.pop('description').format(
                victims=kills, **{key: random.choice(value) for key, value in data.items()})

            if self.name == 'Pillager attack':
                if 'tower' in description:
                    building = deepcopy(env.BUILDINGS['Watch Tower'])
                    rotation = random.choice([0, 90, 180, 270])
                    plot = city.plot.get_subplot(building, rotation, city_buildings=city.buildings)
                    if plot:
                        city.add_building(building, plot, rotation)
                        x, y, z = building.get_entrance().coordinates
                        y += 10
                        for i in range(random.randint(3, 10)):
                            interface.runCommand(f'summon minecraft:iron_golem {x} {y} {z}')
                    else:
                        description += "Unfortunately, we did not find a place to build it."

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
          Event('Pillager attack', is_dangerous=True, kills=(2, 4)),
          Event('Wolf attack', is_dangerous=True, kills=(4, 4))]


class Simulation:
    """"""

    def __init__(self, plot: Plot, decision_maker: DecisionMaker, years: int, friendliness: float = 1,
                 field_productivity: float = 1, humidity: float = 1):
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
        plot = self.city.plot.get_subplot(town_hall, rotation, max_score=100_000)

        if plot is None:
            town_hall = env.BUILDINGS['Small Town Hall']
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

        self.city.end_simulation()

        for building in random.sample(self.city.buildings, k=math.ceil(0.2 * len(self.city.buildings))):
            building.grow_old(random.randint(50, 75))

        decoration_buildings = [building for building in env.BUILDINGS.values()
                                if building.properties.building_type is BuildingType.DECORATION]

        print('\nAdding decorations:')
        for decoration in random.choices(decoration_buildings, k=len(self.city.buildings) * 2):
            rotation = self.decision_maker.get_rotation()
            plot = self.city.plot.get_subplot(decoration, rotation)

            if plot is not None:
                if plot.water_mode:
                    continue
                else:
                    self.city.add_building(decoration, plot, rotation)

        coords = set(self.plot.surface()) - self.plot.occupied_coordinates
        surface = self.plot.get_blocks(Criteria.WORLD_SURFACE)

        chosen_coords = random.sample(surface, k=math.ceil(0.30 * len(surface)))

        for block, flower in zip(chosen_coords, random.choices(lookup.SHORTFLOWERS, k=len(chosen_coords))):
            if (real_block := surface.find(block.coordinates)).is_one_of('grass_block'):
                interface.placeBlock(*real_block.coordinates.shift(y=1), flower)

        print(
            f'\n{Fore.YELLOW}***{Fore.WHITE} Simulation ended at year {Fore.RED}{year}/{self.years}{Fore.WHITE} {Fore.YELLOW}***{Fore.WHITE}')

        interface.sendBlocks()
        interface.setBuffering(False)

        # History of buildings
        for building in self.city.buildings[1:]:
            colors = ('§6', '§7', '§9', '§a', '§b', '§c', '§d')
            color = random.choice(colors)

            general_data = f'{color}{building.name}§0\n{"=" * 18}\n'
            general_data += f'Workers: {color}{len(building.workers)}/{building.properties.workers}§0\n'
            general_data += f'Beds: {color}{len(building.inhabitants)}/{building.properties.number_of_beds}§0\n'
            general_data += f'Food: {color}+{building.properties.food_production}§0'
            book_data = toolbox.writeBook(f'{general_data}\n\n' + '\n\n'.join(building.history),
                                          title=f'Year {year}\'s report',
                                          author='Settlement Construction Community (SCC)')
            lectern_list = building.blocks.filter('lectern')

            interface.sendBlocks()

            if len(lectern_list):
                lectern: Block = lectern_list[0]
                interface.placeBlock(*lectern.coordinates, 'air')
                toolbox.placeLectern(*lectern.coordinates, book_data, facing=lectern.properties['facing'])

        # make a book
        book_data = toolbox.writeBook('\n\n'.join(self.history), title='City history', author='The Mayor')
        lectern_list = self.city.buildings[0].blocks.filter('lectern')
        if len(lectern_list):
            lectern: Block = lectern_list[0]
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

        return actions
