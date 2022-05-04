import random
import textwrap
from typing import Counter

from colorama import Fore

from src.blocks.collections.block_list import BlockList
from src.plots.plot import Plot
from src.simulation.buildings.building import Building
from src.utils.criteria import Criteria


class City:
    def __init__(self, plot):
        self.plot = plot
        self.buildings: list[Building] = []
        self.professions = {}
        self.population = 5
        self.productivity = 5
        self.food_available = 5

    def add_building(self, building: Building, plot: Plot, rotation: int) -> None:
        """Add a new building to the current city"""

        area_with_padding = BlockList(
            list(map(lambda coord: self.plot.get_blocks(Criteria.MOTION_BLOCKING_NO_LEAVES).find(coord),
                     filter(lambda coord: coord in self.plot, plot.surface(3)))))
        plot.remove_trees(area_with_padding)

        plot.build_foundation()

        building.build(plot, rotation)
        self.buildings.append(building)

        if len(self.buildings) > 1:
            print(f'building road from {self.buildings[0]} to {self.buildings[1]}')
            # start = self.buildings[0].structure.entrance if self.buildings[0].structure.entrance is not None else self.buildings[0].plot.start
            # end = self.buildings[-1].structure.entrance if self.buildings[-1].structure.entrance is not None else self.buildings[-1].plot.start
            start = self.buildings[0].plot.start
            end = self.buildings[-1].plot.start
            self.plot.compute_roads(start, end)

            road_pattern = {'INNER': {'grass_path': 100}, 'MIDDLE': {'grass_path': 85, 'grass_block': 15},
                            'OUTER': {'grass_path': 75, 'grass_block': 15, 'coarse_dirt': 10}}

            slab_pattern = {'INNER': {'cobblestone_slab': 25, 'stone_slab': 25, 'andesite_slab': 25, 'granite_slab': 25},
                            'MIDDLE': {'cobblestone_slab': 25, 'stone_slab': 25, 'andesite_slab': 25, 'granite_slab': 25},
                            'OUTER': {'cobblestone_slab': 25, 'stone_slab': 25, 'andesite_slab': 25, 'granite_slab': 25}}

            self.plot.build_roads(road_pattern, slab_pattern)

    @property
    def number_of_beds(self) -> int:
        """Return the number of beds in the city"""
        return sum(building.properties.number_of_beds for building in self.buildings)

    @property
    def work_production(self) -> int:
        return sum(building.properties.work_production for building in self.buildings)

    @property
    def food_production(self):
        return sum(building.properties.food_production for building in self.buildings)

    def update(self) -> None:
        """Update the city's indicators and make the buildings grow old"""
        self.productivity = max(0, min(self.work_production, self.population))
        self.food_available += self.food_production

        # Increase population if enough food
        if self.food_available >= self.population:
            self.food_available -= self.population

            if self.number_of_beds >= self.population:
                max_children_amount = min(int(self.population // 2), self.number_of_beds - self.population)

                # add extra value if you don't want to go out of food immediately
                food_for_children = self.food_available - self.population
                self.population += max(0, min(food_for_children, max_children_amount))

        # Decrease population else
        else:
            # Feed with the remaining food and compute the missing food
            self.food_available -= self.population
            # Remove extra population
            self.population += self.food_available
            # reset food
            self.food_available = 0

        self.make_buildings_grow_old()

    def make_buildings_grow_old(self, amount: int = 35) -> None:
        """"""
        amount = abs(amount) % 100
        buildings: list[Building] = random.sample(self.buildings, amount * len(self.buildings) // 100)

        for building in buildings:
            building.grow_old(2)

    def display(self) -> None:
        """Display a summary of the city at the end of the current year"""
        print('==== Summary ====')
        print(
            f'\n   Population: {Fore.GREEN}{self.population}{Fore.WHITE}/{Fore.GREEN}{self.number_of_beds}{Fore.WHITE}')
        print(f'   Food: {Fore.GREEN}{self.food_available}{Fore.WHITE} ({Fore.GREEN}+{self.food_production}{Fore.WHITE})')

        work_variation = max(0, min(self.work_production, self.population))
        print(f'   Work: {Fore.GREEN}{self.productivity}{Fore.WHITE} ({Fore.GREEN}+{work_variation}{Fore.WHITE})')

        print(f'\n   Buildings ({Fore.GREEN}{len(self.buildings)}{Fore.WHITE}):')

        counter = Counter(self.buildings)
        buildings = "\n      ".join(textwrap.wrap(
            ", ".join([f"{building.name.lower().replace('_', ' ')}: {Fore.GREEN}{value}{Fore.WHITE}" for building, value in counter.items()])))
        print(f'\n      {buildings}')
