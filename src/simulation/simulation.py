from typing import Literal
from colorama import Fore
from gdpc import interface

from src import view
from src.plots.plot import Plot, CityPlot
from src.simulation.event import get_event

from src.simulation.settlement import Settlement
from src.simulation.decisions import DecisionMaking, choose_building


class Simulation:
    """Simulates the generation of a human settlement"""

    def __init__(self, plot: Plot, simulation_end: int | Literal['auto'], *, building_selection: DecisionMaking = None):
        """Creates a new simulation on the given [plot]. The simulation will end at year
        [simulation end]. Alternatively, specifying [simulation end] to 'auto' will override
        the [simulation end] parameter and end the simulation once no buildings have been
        added for 5 consecutive years. Finally, the logic of selecting buildings will be
        handled by the optional [building selection] function (see module src.decisions)"""
        self.current_year = 0
        self.simulation_end = simulation_end

        # Wether the simulation should automatically stop or not
        self.auto = (simulation_end == 'auto' or simulation_end <= 0)

        # Use default logic if no one was given to the simulation
        self.choose_building = building_selection if building_selection else choose_building

        # If you have multiple cities, just give a subplot here
        x, y, z = plot.start

        # Clamp the city size to 250 by 250
        plot = CityPlot(x, y, z, plot.size.max_size(250))

        # TODO add logic for big plots
        self.settlements = [Settlement(plot)]

        # TODO maybe a History class
        self.history: list[str] = []

    def _get_settlements(self) -> list[Settlement]:
        """Return a list of valid settlement for the current year. This method takes the 'auto'
        attribute into account, meanning that if the simulation end is set to 'auto', only running
        settlements will be returned here"""
        return self.settlements if not self.auto else \
            [settlement for settlement in self.settlements if settlement.is_running]

    def start(self) -> None:
        """Start the simulation and generate the (possibly many) settlement(s). The
        simulation will stop if it reaches the year of the simulation end"""
        print(f'{Fore.YELLOW}***{Fore.WHITE} Starting simulation {Fore.YELLOW}***{Fore.WHITE}')

        main_settlement = self.settlements[0]
        main_settlement.deserialize_and_add_building(
            'town-hall', queue=['small-town-hall'], max_score=100_000)

        while self.auto or self.current_year < self.simulation_end:
            print(f'\n\n\n=> Start of year {Fore.RED}[{self.current_year}]{Fore.WHITE}')

            settlements = self._get_settlements()
            if not settlements:
                break

            for settlement in settlements:
                self.run_on(settlement)

            self.current_year += 1

        for settlement in self.settlements:
            settlement.build_roads()
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

        # general_data = f'{color}{building.name}§0\n{"=" * 18}\n'
        # general_data += f'Workers: {color}{len(building.workers)}/{building.properties.workers}§0\n'
        # general_data += f'Beds: {color}{len(building.inhabitants)}/{building.properties.number_of_beds}§0\n'
        # general_data += f'Food: {color}+{building.properties.food_production}§0'
        # # book_data = toolbox.writeBook(f'{general_data}\n\n' + '\n\n'.join(building.history),
        # #                               title=f'Year {year}\'s report',
        # #                               author='Settlement Construction Community (SCC)')
        # book_data = BookMaker(f'{general_data}\n\n' + '\n\n'.join(building.history),
        #                         title=f'Year {year}\'s report',
        #                         author='Settlement Construction Community (SCC)').write_book()
        # lectern_list = building.blocks.filter('lectern')

        #     interface.sendBlocks()

        #     if len(lectern_list):
        #         lectern: Block = lectern_list[0]
        #         interface.placeBlock(*lectern.coordinates, 'air')
        #         toolbox.placeLectern(*lectern.coordinates, book_data, facing=lectern.properties['facing'])

        # make a book
        # book_data = toolbox.writeBook('\n\n'.join(self.history), title='City history', author='The Mayor')
        # book_data = BookMaker('\n\n'.join(self.history), title='City history', author='The Mayor').write_book()
        # lectern_list = self.city.buildings[0].blocks.filter('lectern')
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

        view.display_constructible_buildings(buildings)

        chosen_building = self.choose_building(settlement, buildings)
        settlement.add_building(chosen_building)

        event = get_event(self.current_year)

        if event is not None:  # TODO do something with the history
            chronicle = event.resolve(settlement)
            self.history.append(chronicle)

        settlement.update(self.current_year)
        view.display_settlement(settlement)
