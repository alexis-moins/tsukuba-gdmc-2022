from __future__ import annotations

import click

import random
import launch_env

from gdpc import interface as INTF

from modules.plots.plot import Plot
from modules.utils import simulation
from modules.utils.loader import BUILD_AREA

from modules.utils.criteria import Criteria
from modules.utils.simulation import Simulation, DecisionMaker, HumanPlayer, SmartDecisionMaker

def create_simulation() -> None:
    """"""


@click.command()
@click.option('-t', '--tick-speed', default=200, type=int, show_default=True, help='Set the number of entities checked at each tick')
@click.option('-d', '--debug', is_flag=True, default=False, help='Launch the simulation in debug mode')
@click.option('--no-buffering', is_flag=True, default=False, help='Send blocks one at a time, without using a buffer')
@click.option('--drops', is_flag=True, default=False, help='Enable drops from entities (may cause issues)')
@click.option('-y', '--years', default=10, type=int, show_default=True, help='The number of years during which the simulation will run')
@click.option('-p', '--population', default=5, type=int, show_default=True, help='The number of settlers at the start of the simulation')
def prepare_environment(debug: bool, tick_speed: int, no_buffering: bool, drops: bool, years: int, population: int) -> None:
    """Prepare the environment using CLI options"""
    if debug:
        launch_env.DEBUG = True

    INTF.setBuffering(not no_buffering)
    INTF.placeBlockFlags(doBlockUpdates=True, customFlags='0100011')

    INTF.runCommand(f'gamerule doTileDrops {str(drops).lower()}')
    INTF.runCommand(f'gamerule randomTickSpeed {tick_speed}')

    start_simulation(years, population)


def start_simulation(years: int, population: int) -> None:
    """"""
    # Retrieve the default build area
    start, end = BUILD_AREA
    build_area = Plot.from_coordinates(start, end)

    INTF.runCommand(f'tp @a {build_area.start.x} 110 {build_area.start.z}')
    simulation = Simulation(build_area, population=population, years=years)

    simulation.start()

    INTF.runCommand('gamerule randomTickSpeed 3')
    INTF.runCommand('gamerule doEntityDrops true')


if __name__ == '__main__':
    try:
        prepare_environment()

        # surface = build_area.get_blocks(Criteria.MOTION_BLOCKING_NO_LEAVES)

        # building_materials = dict()
        # logs = surface.filter(pattern='_log')

        # if logs:
        #     most_used_wood = Block.trim_name(logs.most_common, '_log')
        #     print(f'=> Most used wood: {most_used_wood}')

        #     building_materials['oak'] = most_used_wood
        #     building_materials['spruce'] = most_used_wood
        #     building_materials['birch'] = most_used_wood
        # else:
        #     if 'sand' in surface.most_common:
        #         print("Selected sand palette")

        #         building_materials['cobblestone'] = 'red_sandstone'
        #         building_materials['oak_planks'] = 'sandstone'
        #         building_materials['oak_stairs'] = 'sandstone_stairs'
        #         building_materials['birch_stairs'] = 'sandstone_stairs'
        # # Move this somewhere else
        # structures = dict()
        # structures['house1'] = Structure.parse_nbt_file('house1')
        # structures['house2'] = Structure.parse_nbt_file('house2')
        # structures['house3'] = Structure.parse_nbt_file('house3')

        # suburb = SuburbPlot(x=25 + build_area.start.x, z=25 + build_area.start.z, size=(100, 100))
        # suburb.remove_trees()
        # houses = [structures['house1'], structures['house2'], structures['house3']]

    except KeyboardInterrupt:
        print("Pressed Ctrl-C to kill program.")
