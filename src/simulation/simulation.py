import math
import random

from colorama import Fore
from gdpc import interface

from gdpc import toolbox
from src.simulation.buildings.building import Building

from src.simulation.decisions import DecisionMaking, choose_building

from src import env
from src.blocks.block import Block
from src.plots.plot import Plot
from src.simulation.settlement import Settlement

from src.simulation.events.event import get_event


class Simulation:
    """Simulates the generation of a human settlement"""

    def __init__(self, plot: Plot, simulation_end: int, building_selection: DecisionMaking | None = None):
        """Creates a new simulation on the given [plot]. The simulation will end at year
        [simulation end]. Finally, the logic of selecting buildings will be handled by
        the optional [building selection] function (see module src.decisions)"""
        self.__plot = plot
        self.current_year = 0
        self.simulation_end = simulation_end

        # TODO add logic for big plots
        self.settlements = [Settlement(self.__plot)]

        # Use default logic if no one was given to the simulation
        self.choose_building = building_selection if building_selection else choose_building

        # TODO maybe a History class
        self.history: list[str] = []

    def start(self) -> None:
        """Start the simulation and generate the (possibly many) settlement(s). The
        simulation will stop if it reaches the year of the simulation end"""
        print(f'{Fore.YELLOW}***{Fore.WHITE} Starting simulation {Fore.YELLOW}***{Fore.WHITE}')

        town_hall = Building.deserialize('Town Hall', env.BUILDINGS['Town Hall'])

        success = self.settlements[0].add_building(town_hall, max_score=100_000)

        if not success:
            town_hall = Building.deserialize('Town Hall', env.BUILDINGS['Small Town Hall'])
            self.settlements[0].add_building(town_hall)

        while self.current_year < self.simulation_end:
            print(f'\n\n\n=> Start of year {Fore.RED}[{self.current_year}]{Fore.WHITE}')

            for settlement in self.settlements:
                self.run_on(settlement)

            self.current_year += 1

        for settlement in self.settlements:
            settlement.end_simulation()
            settlement.grow_old()

        # TODO move in decoration logic in settlement ?

        # decoration_buildings = [building for building in env.BUILDINGS.values()
        #                         if building.properties.building_type is BuildingType.DECORATION]

        # print('\nAdding decorations:')
        # for decoration in random.choices(decoration_buildings, k=len(self.settlements.buildings) * 2):
        #     rotation = self.choose_building.get_rotation()
        #     plot = self.settlements.plot.get_subplot(decoration, rotation)

        #     if plot is not None:
        #         if plot.water_mode:
        #             continue
        #         else:
        #             self.settlements.add_building(decoration, plot, rotation)

        # coords = set([coord.as_2D() for coord in self.__plot.surface()]) - self.__plot.occupied_coordinates
        # surface = self.__plot.get_blocks(Criteria.WORLD_SURFACE)

        # chosen_coords = random.sample(coords, k=math.ceil(0.30 * len(coords)))

        # for coord, flower in zip(chosen_coords, random.choices(lookup.SHORTFLOWERS + ('minecraft:lantern',), k=len(chosen_coords))):
        #     if (real_block := surface.find(coord)).is_one_of('grass_block'):
        #         interface.placeBlock(*real_block.coordinates.shift(y=1), flower)

        print(
            f'\n{Fore.YELLOW}***{Fore.WHITE} Simulation ended at year {Fore.RED}{self.current_year}/{self.simulation_end}{Fore.WHITE} {Fore.YELLOW}***{Fore.WHITE}')

        interface.sendBlocks()
        interface.setBuffering(False)

        # # History of buildings
        # for building in self.settlements.buildings[1:]:
        #     colors = ('§6', '§7', '§9', '§a', '§b', '§c', '§d')
        #     color = random.choice(colors)

        #     general_data = f'{color}{building.name}§0\n{"=" * 18}\n'
        #     general_data += f'Workers: {color}{len(building.workers)}/{building.properties.workers}§0\n'
        #     general_data += f'Beds: {color}{len(building.inhabitants)}/{building.properties.number_of_beds}§0\n'
        #     general_data += f'Food: {color}+{building.properties.food_production}§0'
        #     book_data = toolbox.writeBook(f'{general_data}\n\n' + '\n\n'.join(building.history),
        #                                   title=f'Year {self.current_year}\'s report',
        #                                   author='Settlement Construction Community (SCC)')
        #     lectern_list = building.blocks.filter('lectern')

        #     interface.sendBlocks()

        #     if len(lectern_list):
        #         lectern: Block = lectern_list[0]
        #         interface.placeBlock(*lectern.coordinates, 'air')
        #         toolbox.placeLectern(*lectern.coordinates, book_data, facing=lectern.properties['facing'])

        # # make a book
        # book_data = toolbox.writeBook('\n\n'.join(self.history), title='City history', author='The Mayor')
        # lectern_list = self.settlements.buildings[0].blocks.filter('lectern')
        # if len(lectern_list):
        #     lectern: Block = lectern_list[0]
        #     toolbox.placeLectern(*lectern.coordinates, book_data, facing=lectern.properties['facing'])

        interface.setBuffering(True)
        interface.sendBlocks()

    def run_on(self, settlement: Settlement) -> None:
        """Run the simulation for 1 year on the given [settlement]. The simulation will try to add
        a new building, randomly generate an event and update the settlement's indicators"""
        settlement.update(self.current_year)
        buildings = settlement.get_constructible_buildings()

        # formatted = textwrap.fill(", ".join(str(building) for building in buildings), width=80)
        # print(f'Available buildings: [{formatted}]')

        chosen_building = self.choose_building(settlement, buildings)

        if chosen_building is not None:
            settlement.add_building(chosen_building)

        event = get_event(self.current_year)

        if event is not None:
            # TODO do something with the history
            self.history.append(event.resolve(settlement))

        settlement.update(self.current_year)
        settlement.display()
