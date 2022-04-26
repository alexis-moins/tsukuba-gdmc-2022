from enum import Enum
from random import choice, randint, shuffle
from typing import List
from modules.blocks.structure import Structure
from modules.plots.construction_plot import ConstructionPlot

from modules.plots.plot import Plot
from modules.plots.suburb_plot import SuburbPlot


class Profession(Enum):
    """Enumeration of the available professions for agents"""

    # Cultivate the ground to get food
    FARMER = Structure.parse_nbt_file('house1')

    # Cuts down trees to get wood
    LUMBERJACK = Structure.parse_nbt_file('house2')


class City:
    """"""

    def __init__(self, plot: Plot, population: int) -> None:
        """"""
        self.plot = plot
        self.buildings = List[Building]
        self.inhabitants = [Villager(i, age=1) for i in range(population)]

        self.professions = dict()
        self.professions['available'] = [Profession.FARMER, Profession.LUMBERJACK]
        self.professions['given'] = []

        self.suburb = SuburbPlot(x=25 + self.plot.start.x, z=25 + self.plot.start.z, size=(100, 100))

    @property
    def population(self) -> int:
        """Return the number of inhabitants in the city"""
        return len(self.inhabitants)

    def get_construction_plot(self, area):
        """"""
        return self.suburb.get_construction_plot(area)


class Villager:
    def __init__(self, name: int, age: int = 0):
        self.name = name
        self.age = age

        self.happiness = 100
        self.profession: Profession = None

    def do_something(self, city: City):
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
            structure = self.profession.value

            rotation = choice([0, 90, 180, 270])
            area = structure.get_area(rotation)
            plot = city.get_construction_plot(area)

            if plot:
                plot.build(structure, rotation=rotation)
                print(f'villager {self.name} built a {structure.name} at {plot.build_start}')
            if self.age == 2 or self.age == 3:
                child = Villager(city.population)
                city.inhabitants.append(child)
                print(f'villager {self.name} has given birth to villager {child.name}')


class Event:
    def __init__(self, name):
        self.name = name


class Building:
    """"""

    def __init__(self, plot: ConstructionPlot) -> None:
        """Parameterized constructor creating a new building"""
        self.plot = plot


class Simulation:
    """Class representing the simulation of a settlement with agents"""

    def __init__(self, area: Plot, population: int = 2, years: int = 10) -> None:
        """Parameterised constructor creating a new simulation"""
        self.year = 0
        self.final_year = years
        self.city = City(area, population)
        area.remove_trees()

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
