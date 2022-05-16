import random
import textwrap
from typing import Counter

from colorama import Fore

from src import env
from src.blocks.collections.block_list import BlockList
from src.plots.plot import Plot
from src.simulation.buildings.building import Building
from src.simulation.buildings.building_type import BuildingType
from src.utils.criteria import Criteria


class Villager:
    """"""

    def __init__(self) -> None:
        """"""
        self.name = 'Youri'
        self.productivity = 1
        self.house: Building = None
        self.work_place: Building = None


class City:
    def __init__(self, plot: Plot):
        self.plot = plot
        self.buildings: list[Building] = []
        self.professions = {}

        self.inhabitants = [Villager() for _ in range(5)]
        self.food_available = 5

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
        padding = 5
        if building.properties.building_type is BuildingType.FARM or building.properties.building_type is BuildingType.WOODCUTTING:
            padding = 8

        if building.properties.building_type is BuildingType.DECORATION:
            padding = 2

        area_with_padding = BlockList(
            list(map(lambda coord: self.plot.get_blocks(Criteria.MOTION_BLOCKING_NO_LEAVES).find(coord),
                     filter(lambda coord: coord in self.plot, plot.surface(padding)))))

        plot.remove_trees(area_with_padding)

        plot.build_foundation()

        print(f'{building} added to the settlement')

        building.build(plot, rotation, self.plot)
        self.buildings.append(building)

        if len(self.buildings) > 1 and not self.buildings[-1].is_extension:
            if env.DEBUG:
                print(f'building road from {self.buildings[0]} to {self.buildings[1]}')

            end = random.choice(
                self.buildings[0].entrances).coordinates if self.buildings[0].entrances else self.buildings[0].plot.start
            start = random.choice(
                self.buildings[-1].entrances).coordinates if self.buildings[-1].entrances else self.buildings[-1].plot.start

            self.plot.compute_roads(start, end)

            road_pattern = {
                'INNER': {'glowstone': 100},
                'MIDDLE': {'oak_planks'.replace('oak', env.BUILDING_MATERIALS['oak'][0] if 'oak' in env.BUILDING_MATERIALS else 'oak'): 100},
                'OUTER': {'note_block': 100}
            }

            slab_pattern = {
                'INNER': {'oak_slab'.replace('oak', env.BUILDING_MATERIALS['oak'][0] if 'oak' in env.BUILDING_MATERIALS else 'oak'): 100},
                'MIDDLE': {'oak_slab'.replace('oak', env.BUILDING_MATERIALS['oak'][0] if 'oak' in env.BUILDING_MATERIALS else 'oak'): 100},
                'OUTER': {'birch_slab': 100}
            }

            self.plot.build_roads(road_pattern, slab_pattern)

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
                self.inhabitants.extend([Villager() for _ in range(k)])

        # Decrease population else
        else:
            # Feed with the remaining food and compute the missing food
            self.food_available -= self.population
            # Remove extra population
            print(f'======= Check wether the population is decreased or notm it should ======')
            self.inhabitants.extend([Villager() for _ in range(self.food_available)])
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
            print(f'{villager.name.capitalize()} moved in {house}')

            if house.has_empty_beds():
                available_houses.append(house)

        # Then, give every inactive villager a place to work at (if possible)
        available_work_places = [building for building in self.buildings if building.can_offer_work()]

        for villager in self.inactive_villagers():
            if not available_work_places:
                break

            work_place = available_work_places.pop()
            work_place.add_worker(villager, year)
            print(f'{villager.name.capitalize()} started working at {work_place}')

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

        counter = Counter(self.buildings)
        buildings = "\n      ".join(textwrap.wrap(
            ", ".join([f"{building.name.lower().replace('_', ' ')}: {Fore.GREEN}{value}/{building.max_number}{Fore.WHITE}" for building, value in counter.items()])))
        print(f'\n      {buildings}')
