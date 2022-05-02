from enum import Enum
from random import choice
from random import shuffle

import gdpc.interface as INTF
from networkx import dijkstra_path
from networkx import Graph

from modules.blocks.collections.block_list import BlockList
from modules.blocks.structure import Structure
from modules.plots.plot import Plot
from modules.utils.coordinates import Coordinates
from modules.utils.criteria import Criteria
from modules.utils.loader import structures


class Profession(Enum):
    """Enumeration of the available professions for agents"""

    # Cultivate the ground to get food
    FARMER = structures['farm']

    # Cuts down trees to get wood
    LUMBERJACK = structures['sawmill']


class Building:
    """"""

    def __init__(self, plot: Plot, blocks: BlockList) -> None:
        """Parameterized constructor creating a new building"""
        self.plot = plot
        self.blocks = blocks


class Villager:
    def __init__(self, name: int, age: int = 0):
        self.name = name
        self.age = age

        self.happiness = 100
        self.profession: Profession = None

    def do_something(self, city):
        """"""
        if self.age == 5:
            if self.profession:
                city.inhabitants.remove(self)
                city.professions['given'].remove(self.profession)
                city.professions['available'].append(self.profession)
            print(f'villager {self.name} has died at age 5')

        elif self.age >= 1 and not self.profession and city.professions['available']:
            shuffle(city.professions['available'])
            self.profession = city.professions['available'].pop()
            city.professions['given'].append(self.profession)

            print(f'villager {self.name} chose profession {self.profession.name}')

        elif self.age >= 2 and self.profession:
            city.add_building(self.profession.value)

            if self.age == 2 or self.age == 3:
                child = Villager(city.population)
                city.inhabitants.append(child)
                print(f'villager {self.name} has given birth to villager {child.name}')


class City:
    """"""

    def __init__(self, plot: Plot, population: int) -> None:
        """"""
        self.plot = plot
        self.buildings: list[Coordinates] = []
        self.inhabitants = [Villager(i, age=1) for i in range(population)]

        self.graph = Graph()

        for block in self.plot.get_blocks(Criteria.MOTION_BLOCKING):
            self.graph.add_node(block.coordinates)

        for coordinates in self.graph.nodes.keys():
            for coord in coordinates.neighbours():
                if coord in self.graph.nodes.keys():
                    self.graph.add_edge(coordinates, coord)

        self.roads = []

        self.professions = dict()
        self.professions['available'] = [Profession.FARMER, Profession.LUMBERJACK]
        self.professions['given'] = []

    @property
    def population(self) -> int:
        """Return the number of inhabitants in the city"""
        return len(self.inhabitants)

    def add_building(self, structure: Structure) -> None:
        """"""
        rotation = choice([0, 90, 180, 270])
        size = structure.get_size(rotation)
        padding = 10
        plot = self.plot.get_subplot(size, padding=padding)

        if plot:
            area_with_padding = BlockList(
                list(map(lambda coord: self.plot.get_blocks(Criteria.MOTION_BLOCKING_NO_LEAVES).find(coord),
                         filter(lambda coord: coord in self.plot, plot.surface(padding)))))
            plot.remove_trees(area_with_padding)

            plot.build_foundation()

            structure.build(plot.start, rotation=rotation)

            print(f'=> New building <{structure.name}> added to the city at {plot.start}')
            coordinates = plot.start
            self.buildings.append(coordinates)

            # if len(self.buildings) == 2:
            #     print(f'building road from {self.buildings[0]} to {self.buildings[1]}')
            #     for coord in dijkstra_path(self.graph, self.buildings[0], self.buildings[1]):
            #         INTF.placeBlock(*coord, 'minecraft:red_wool')
            #         self.roads.append(coord)

            # elif len(self.buildings) >= 3 and self.roads:
            #     closest_road = self.closest_coordinates(coordinates)

            #     for coord in dijkstra_path(self.graph, coordinates, closest_road):
            #         INTF.placeBlock(*coord, 'minecraft:red_wool')

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


class Event:
    def __init__(self, name):
        self.name = name


class Simulation:
    """Class representing the simulation of a settlement with agents"""

    def __init__(self, area: Plot, population: int = 2, years: int = 10) -> None:
        """Parameterised constructor creating a new simulation"""
        self.year = 0
        self.final_year = years
        self.city = City(area, population)

    def start(self) -> None:
        """Start the simulation"""
        # TODO get the town center, place the main building
        print(f'==== Starting simulation ====')
        while self.year < self.final_year:
            print(f'\n=> Start of year {self.year}')
            print(f'=> Population is {self.city.population}')

            # Logic goes here
            for villager in self.city.inhabitants:
                villager.do_something(self.city)
                villager.age += 1

            if not self.city.inhabitants:
                print(f'\n=> No more inhabitants in the city!')
                break

            self.year += 1

        print(f'=> Simlation ended at year {self.year}/{self.final_year} with a population of {self.city.population}')
