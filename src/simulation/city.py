import networkx as nx
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

        self.graph = nx.Graph()
        self.roads: list[Coordinates] = list()

        for block in self.plot.get_blocks(Criteria.MOTION_BLOCKING_NO_TREES):
            self.graph.add_node(block.coordinates)

        for coordinates in self.graph.nodes.keys():
            for coord in coordinates.neighbours():
                if coord in self.graph.nodes.keys():
                    self.graph.add_edge(coordinates, coord)

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

        if len(self.buildings) == 2:
            print(f'building road from {self.buildings[0]} to {self.buildings[1]}')
            for coord in nx.dijkstra_path(self.graph, self.buildings[0].plot.start,
                                          self.buildings[1].plot.start):
                INTERFACE.placeBlock(*coord, 'minecraft:glowstone')
                self.roads.append(coord)

        elif len(self.buildings) >= 3 and self.roads:
            closest_road = self.closest_coordinates(coordinates)

            for coord in nx.dijkstra_path(self.graph, coordinates, closest_road):
                INTERFACE.placeBlock(*coord, 'minecraft:glowstone')

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
