import random
import textwrap
import time
from collections import Counter

from colorama import Fore
from gdpc import interface
from gdpc import lookup

from src import env
from src.blocks.collections.block_list import BlockList
from src.plots.plot import Plot
from src.simulation.buildings.building import Building
from src.simulation.buildings.building import Graveyard
from src.simulation.buildings.building import WeddingTotem
from src.simulation.buildings.building_type import BuildingType
from src.utils.criteria import Criteria


with open('resources/first-names.txt', 'r') as file:
    _first_names = file.read().splitlines()

with open('resources/last-names.txt', 'r') as file:
    _last_names = file.read().splitlines()


class Villager:
    """"""

    def __init__(self, birth_year: int) -> None:
        """"""
        self.name = f'{random.choice(_first_names)} {random.choice(_last_names)}'
        self.productivity = 1
        self.house: Building = None
        self.work_place: Building = None
        self.birth_year = birth_year

    def die(self, year: int, cause: str):
        if self.work_place:
            self.work_place.workers.remove(self)
            self.work_place.history.append(f'{self.name} died at {year} of {cause}')
        if self.house:
            self.house.inhabitants.remove(self)
            self.house.history.append(f'{self.name} died at {year} of {cause}')


class City:
    def __init__(self, plot: Plot, start_year: int):
        """"""
        self.plot = plot
        self.buildings: list[Building] = []
        self.graveyard: Graveyard | None = None
        self.wedding_totem: WeddingTotem | None = None
        self.start_year = start_year

        self.inhabitants = [Villager(start_year) for _ in range(5)]
        self.food_available = 5

        self.possible_light_blocks = ('minecraft:shroomlight', 'minecraft:sea_lantern',
                                      'minecraft:glowstone', 'minecraft:redstone_lamp[lit=true]')
        self.road_light = random.choice(self.possible_light_blocks)

    @property
    def population(self) -> int:
        """Return the number of inhabitants in the city"""
        return len(self.inhabitants)

    def inactive_villagers(self) -> list[Villager]:
        """Return the list of all villagers that don't have a job"""
        return [villager for villager in self.inhabitants if villager.work_place is None]

    def homeless_villagers(self) -> list[Villager]:
        """return the list of all villagers that don't have a house"""
        return [villager for villager in self.inhabitants if villager.house is None]

    @property
    def number_of_beds(self) -> int:
        """Return the number of beds in the city"""
        return sum(building.properties.number_of_beds for building in self.buildings)

    def add_building(self, building: Building, plot: Plot, rotation: int) -> None:
        """Add a new building to the current city"""

        if isinstance(building, Graveyard):
            self.graveyard = building
        elif isinstance(building, WeddingTotem):
            self.wedding_totem = building

        padding = 5
        if building.properties.building_type is BuildingType.FARM or building.properties.building_type is BuildingType.WOODCUTTING:
            padding = 8

        if building.properties.building_type is BuildingType.DECORATION:
            padding = 2

        area_with_padding = BlockList(
            list(map(lambda coord: self.plot.get_blocks(Criteria.MOTION_BLOCKING_NO_LEAVES).find(coord),
                     filter(lambda coord: coord in self.plot, plot.surface(padding)))))

        plot.remove_trees(area_with_padding)
        time.sleep(2)

        plot.build_foundation(self.plot)

        print(f'{building} added to the settlement')

        building.build(plot, rotation, self.plot)
        self.buildings.append(building)

        if len(self.buildings) > 1 and not self.buildings[-1].is_extension:
            if env.DEBUG:
                print(f'building road from {self.buildings[0]} to {self.buildings[1]}')

            road_done = False
            i = 0
            max_i = len(self.buildings) - 1
            while not road_done and i < max_i:
                end = self.buildings[i].get_entrance()
                start = self.buildings[-1].get_entrance()

                road_done = self.plot.compute_roads(start, end)
                i += 1

    @property
    def production_points(self) -> int:
        """"""
        return sum(len(building.workers) for building in self.buildings)

    @property
    def available_production(self) -> int:
        """"""
        return sum(building.properties.workers for building in self.buildings)

    @property
    def food_production(self):
        return sum(building.properties.food_production for building in self.buildings)

    def update(self, year: int) -> None:
        """Update the city's indicators"""
        self.food_available += self.food_production

        # Increase population if enough food
        if self.food_available >= self.population:
            # Feed everyone
            self.food_available -= self.population

            if self.number_of_beds >= self.population:
                max_children_amount = min(int(self.population // 2), self.number_of_beds - self.population)

                # add extra value if you don't want to go out of food immediately
                food_for_children = self.food_available - self.population
                k = max(0, min(food_for_children, max_children_amount))

                print(f'=> {Fore.CYAN}[{k}]{Fore.WHITE} new villager(s) born this year')
                self.inhabitants.extend([Villager(year) for _ in range(k)])

        # Decrease population else
        else:
            # Feed with the remaining food and compute the missing food
            self.food_available -= self.population
            # Remove extra population
            print(f'======= Check wether the population is decreased or notm it should ======')
            self.inhabitants.extend([Villager(year) for _ in range(self.food_available)])
            # reset food
            self.food_available = 0

        # Attributing villagers to buildings
        # First, give every homeless villager a house (if possible)
        available_houses = [building for building in self.buildings if building.has_empty_beds()]

        for villager in self.homeless_villagers():
            if not available_houses:
                break

            house = available_houses.pop()
            house.add_inhabitant(villager, year)

            if house.has_empty_beds():
                available_houses.append(house)

        # Then, give every inactive villager a place to work at (if possible)
        available_work_places = [building for building in self.buildings if building.can_offer_work()]

        for villager in self.inactive_villagers():
            if not available_work_places:
                break

            work_place = available_work_places.pop()
            work_place.add_worker(villager, year)

            if work_place.can_offer_work():
                available_work_places.append(work_place)

    def make_buildings_grow_old(self) -> None:
        """"""
        print(f'=> Deteriorating {Fore.RED}[{len(self.buildings)}]{Fore.WHITE} building(s)')

        for building in self.buildings:
            building.grow_old(env.DETERIORATION)

    def repair_buildings(self):
        """"""
        print(f'=> Repairing deteriorated buildings')

        for building in self.buildings:
            if building.old_blocks:

                if building.properties.workers == len(building.workers) and building.properties.number_of_beds == len(building.inhabitants):
                    building.repair(len(building.old_blocks))
                else:
                    building.repair(len(building.old_blocks) // 2)

    def display(self) -> None:
        """Display a summary of the city at the end of the current year"""
        print('==== Summary ====')
        print(
            f'\n   Population: {Fore.GREEN}{self.population}/{self.number_of_beds}{Fore.WHITE} ({Fore.GREEN}{len(self.inactive_villagers())}{Fore.WHITE} inactive)')
        print(f'   Food: {Fore.GREEN}{self.food_available}{Fore.WHITE} ({Fore.GREEN}{self.food_production}{Fore.WHITE} per year)')
        print(f'   Work: {Fore.GREEN}{self.production_points}/{self.available_production}{Fore.WHITE}')

        print(f'\n   Buildings {Fore.GREEN}[{len(self.buildings)}]{Fore.WHITE}\n')

        counter = Counter([building.name for building in self.buildings])
        buildings = "\n      ".join(textwrap.wrap(
            ", ".join([f"{building.name}: {Fore.GREEN}{counter[building.name]}/{building.max_number}{Fore.WHITE}" for building in self.buildings])))
        print(f'\n      {buildings}')

    def wedding(self):
        if self.wedding_totem:
            self.wedding_totem.add_wedding()

    def villager_die(self, villager: Villager, year: int, cause: str):
        if self.graveyard:
            self.graveyard.add_tomb(villager, year, cause)

        villager.die(year, cause)
        self.inhabitants.remove(villager)

    def spawn_villagers_and_guards(self):
        x, y, z = self.buildings[0].entrances[0].coordinates
        for villager in self.inhabitants:
            interface.runCommand(f'summon villager {x} {y + 1} {z} {{CustomName:"\\"{villager.name}\\""}}')
        for i in range(random.randint(5, 15)):
            interface.runCommand(f'summon iron_golem {x} {y + 1} {z} {{CustomName:"\\"Town Guard\\""}}')

    def end_simulation(self):
        # Build roads
        road_pattern = {
            'INNER': {self.road_light: 100},
            'MIDDLE': {'oak_planks'.replace('oak', env.BUILDING_MATERIALS['oak'][
                0] if 'oak' in env.BUILDING_MATERIALS else 'oak'): 100},
            'OUTER': {'note_block': 100}
        }

        slab_pattern = {
            'INNER': {'oak_slab[waterlogged=false]'.replace('oak', env.BUILDING_MATERIALS['oak'][
                0] if 'oak' in env.BUILDING_MATERIALS else 'oak'): 100},
            'MIDDLE': {'oak_slab[waterlogged=false]'.replace('oak', env.BUILDING_MATERIALS['oak'][
                0] if 'oak' in env.BUILDING_MATERIALS else 'oak'): 100},
            'OUTER': {leave + '[persistent=true]': 20 for leave in lookup.LEAVES}
        }
        self.plot.build_roads(road_pattern, slab_pattern)

        # Spawn villagers
        self.spawn_villagers_and_guards()

        # Add roads signs
        self.plot.add_roads_signs(10, self.buildings)
