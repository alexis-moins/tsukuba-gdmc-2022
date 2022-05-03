import textwrap
from typing import Counter

import networkx as nx

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

        self.graph = nx.Graph()
        self.roads: list[Coordinates] = list()

        for block in self.plot.get_blocks(Criteria.MOTION_BLOCKING_NO_TREES):
            self.graph.add_node(block.coordinates)

        for coordinates in self.graph.nodes.keys():
            for coord in coordinates.neighbours():
                if coord in self.graph.nodes.keys():
                    self.graph.add_edge(coordinates, coord)

    def add_building(self, building: Building, plot: Plot, rotation: int) -> None:
        """Add a new building to the current city"""
        plot.build_foundation()

        building.build(plot, rotation)
        self.buildings.append(building)

    def closest_coordinates(self, coordinates: Coordinates):
        """"""
        if len(self.roads) == 1:
            return self.roads[0]

        closest_coord = self.roads[0]
        min_distance = coordinates.distance(closest_coord)
        for coord in self.roads[1:]:
            if distance := coordinates.distance(coord) < min_distance:
                closest_coord = coord
                min_distance = distance

        return closest_coord

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

    def update(self):
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

    def display(self) -> None:
        print(f'population : {self.population}/{self.number_of_beds}')
        print(f'Food : {self.food_available} (since last year: +{self.food_production})')
        print(f'Work : {self.productivity} (since last year: +{max(0, min(self.work_production, self.population))})')
        print(f'Buildings : {len(self.buildings)}')

        counter = Counter(self.buildings)
        buildings = "\n".join(textwrap.wrap(", ".join([f"{building}: {value}" for building, value in counter.items()])))
        print(f'{buildings}')
