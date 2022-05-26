import math
import random
import time
from cgitb import lookup
from collections import Counter
from copy import copy
from copy import deepcopy
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
from src.utils.book_maker import BookMaker
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
                building = random.choice(city.buildings)
                x, y, z = building.get_entrance()
                y += 1
                for i in range(random.randint(5, 20)):
                    interface.runCommand(
                        f'summon minecraft:wolf {x} {y} {z} {{CustomName:"\\"{random.choice(dog_names).capitalize()}\\""}}')

                building.update_name_adjective('wolves')

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
            description = ''
            if self.name != 'Fire':
                description = data.pop('description').format(
                    victims=kills, **{key: random.choice(value) for key, value in data.items()})

            if self.name == 'Pillager attack':

                if 'tower' in description:

                    towers_built = 0
                    for _ in range(random.randint(2, 5)):
                        building = deepcopy(env.BUILDINGS['Watch Tower'])
                        rotation = random.choice([0, 90, 180, 270])
                        plot = city.plot.get_subplot(building, rotation, city_buildings=city.buildings)
                        if plot:
                            city.add_building(building, plot, rotation)
                            x, y, z = building.get_entrance()
                            y += 10
                            for i in range(random.randint(3, 10)):
                                interface.runCommand(f'summon minecraft:iron_golem {x} {y} {z}')

                        towers_built += 1

                    if towers_built == 0:
                        description += "Unfortunately, we did not find a place to build it."

            if self.name == 'Fire':
                building = random.choice(city.buildings)
                building.set_on_fire(random.randint(65, 80))
                description = data.pop('description').format(
                    victims=kills, building=building, **{key: random.choice(value) for key, value in data.items()})
                building.history.append(
                    f'This building took fire during year {year}, taking the lives of {kills} people.')
                building.update_name_adjective('burnt')

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
        time_start = time.time()
        year = 1

        # If you have multiple cities, just give a subplot here
        self.city = City(self.plot, year)
        self.decision_maker.city = self.city

        print(f'{Fore.YELLOW}***{Fore.WHITE} Starting simulation {Fore.YELLOW}***{Fore.WHITE}')

        if env.SHOW_TIME:
            print(f'Current time {time.time() - env.start_time:.2f} s.')

        town_hall = env.BUILDINGS['Town Hall']
        rotation = self.decision_maker.get_rotation()
        if env.DEBUG:
            print(f'rotation {rotation}')
        plot = self.city.plot.get_subplot(town_hall, rotation)

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

        if env.SHOW_TIME:
            time_took = time.time() - time_start
            print(f'Finished simulation in {time_took:.2f} s.')
            print(f'Done {year} years, average : {time_took / max(1, year):.2f} s per year.')

        # time_decoration = time.time()
        # for building in random.sample(self.city.buildings, k=math.ceil(0.3 * len(self.city.buildings))):
        #     building.grow_old(random.randint(65, 80))
        #
        # decoration_buildings = [building for building in env.BUILDINGS.values()
        #                         if building.properties.building_type is BuildingType.DECORATION]

        # print('\nAdding decorations:')
        # for decoration in random.choices(decoration_buildings, k=len(self.city.buildings) * 2):
        #     rotation = self.decision_maker.get_rotation()
        #     plot = self.city.plot.get_subplot(decoration, rotation)
        #
        #     if plot is not None:
        #         if plot.water_mode:
        #             continue
        #         else:
        #             self.city.add_building(decoration, plot, rotation)
        #
        # coords = set([coord.as_2D() for coord in self.plot.surface()]) - self.plot.occupied_coordinates
        # surface = self.plot.get_blocks(Criteria.WORLD_SURFACE)
        #
        # chosen_coords = random.sample(coords, k=math.ceil(0.30 * len(coords)))
        #
        # for coord, flower in zip(chosen_coords,
        #                          random.choices(lookup.SHORTFLOWERS + ('minecraft:lantern',), k=len(chosen_coords))):
        #     if (real_block := surface.find(coord)).is_one_of('grass_block'):
        #         interface.placeBlock(*real_block.coordinates.shift(y=1), flower)
        #
        # if env.SHOW_TIME:
        #     time_took = time.time() - time_decoration
        #     print(f'Added decoration in {time_took:.2f} s.')

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
            # book_data = toolbox.writeBook(f'{general_data}\n\n' + '\n\n'.join(building.history),
            #                               title=f'Year {year}\'s report',
            #                               author='Settlement Construction Community (SCC)')
            book_data = BookMaker(f'{general_data}\n\n' + '\n\n'.join(building.history),
                                  title=f'Year {year}\'s report',
                                  author='Settlement Construction Community (SCC)').write_book()
            lectern_list = building.blocks.filter('lectern')

            interface.sendBlocks()

            if len(lectern_list):
                lectern: Block = lectern_list[0]
                interface.placeBlock(*lectern.coordinates, 'air')
                toolbox.placeLectern(*lectern.coordinates, book_data, facing=lectern.properties['facing'])

        # make a book
        # book_data = toolbox.writeBook('\n\n'.join(self.history), title='City history', author='The Mayor')
        book_data = BookMaker('\n\n'.join(self.history), title='City history', author='The Mayor').write_book()
        lectern_list = self.city.buildings[0].blocks.filter('lectern')
        if len(lectern_list):
            lectern: Block = lectern_list[0]
            toolbox.placeLectern(*lectern.coordinates, book_data, facing=lectern.properties['facing'])

        interface.setBuffering(True)
        interface.sendBlocks()

        if env.SHOW_TIME:
            time_took = time.time() - time_start
            print(f'Generation done in {time_took:.2f} s.')

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
