
from gdpc import interface as INTERFACE

from src.blocks.collections.block_list import BlockList
from src.plots.plot import Plot
from src.simulation.buildings.building import Building
from src.utils.coordinates import Coordinates
from src.utils.criteria import Criteria


class City:
    def __init__(self, plot):
        self.plot = plot
        self.buildings: list[Building] = []
        self.professions = {}
        self.population = 5
        self.productivity = 5
        self.food_available = 5

    def add_building(self, building: Building, coord: Coordinates, rotation: int):
        padding = 3
        structure = building.structure
        size = structure.get_size(rotation)
        plot = Plot(*coord, size=size)

        building.plot = plot

        area_with_padding = BlockList(
            list(map(lambda coord: self.plot.get_blocks(Criteria.MOTION_BLOCKING_NO_LEAVES).find(coord),
                     filter(lambda coord: coord in self.plot, plot.surface(padding)))))
        plot.remove_trees(area_with_padding)

        plot.build_foundation()
        structure.build(coord, rotation=rotation)

        self.buildings.append(building)

        coordinates = plot.start

        if len(self.buildings) > 1:
            print(f'building road from {self.buildings[0]} to {self.buildings[1]}')
            # start = self.buildings[0].structure.entrance if self.buildings[0].structure.entrance is not None else self.buildings[0].plot.start
            # end = self.buildings[-1].structure.entrance if self.buildings[-1].structure.entrance is not None else self.buildings[-1].plot.start
            start = self.buildings[0].plot.start
            end = self.buildings[-1].plot.start
            self.plot.build_road(start, end)


    @property
    def bed_amount(self):
        return sum(b.bed_amount for b in self.buildings)

    @property
    def work_production(self):
        return sum(b.work_productivity for b in self.buildings)

    @property
    def food_production(self):
        return sum(b.food_productivity for b in self.buildings)

    def update(self):
        self.productivity = max(0, min(self.work_production, self.population))
        self.food_available += self.food_production

        # Increase population if enough food
        if self.food_available >= self.population:
            self.food_available -= self.population

            if self.bed_amount >= self.population:
                max_children_amount = min(int(self.population // 2), self.bed_amount - self.population)

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

    def __str__(self) -> str:
        return f'population : {self.population}/{self.bed_amount}' \
               f'\nFood : {self.food_available} (var: {self.food_production})' \
               f'\nWork : {self.productivity} (var : {max(0, min(self.work_production, self.population))})' \
               f'\nBuildings : {len(self.buildings)}' \
               f'\n{" - ".join(str(b) for b in self.buildings)}'
