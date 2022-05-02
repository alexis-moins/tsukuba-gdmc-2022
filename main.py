from __future__ import annotations

import click
from distutils.command.build import build
from gdpc import interface as INTF

import env
from modules.blocks.block import Block
from modules.plots.plot import Plot
from modules.simulation.simulation import Simulation
from modules.utils.criteria import Criteria
from modules.utils.loader import BUILD_AREA


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
        env.DEBUG = True

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

    find_building_materials(build_area)
    simulation.start()

    INTF.runCommand('gamerule randomTickSpeed 3')
    INTF.runCommand('gamerule doEntityDrops true')


def find_building_materials(build_area: Plot):
    """"""
    surface = build_area.get_blocks(Criteria.MOTION_BLOCKING_NO_LEAVES)
    logs = surface.filter(pattern='_log')

    if logs:
        most_used_wood = Block.trim_name(logs.most_common, '_log')
        print(f'=> Most used wood: {most_used_wood}')

        env.BUILDING_MATERIALS['oak'] = (most_used_wood, True)
        env.BUILDING_MATERIALS['spruce'] = (most_used_wood, True)
        env.BUILDING_MATERIALS['birch'] = (most_used_wood, True)
    else:
        if 'sand' in surface.most_common:
            print("=> Selected sand palette")

            env.BUILDING_MATERIALS['cobblestone'] = ('red_sandstone', True)
            env.BUILDING_MATERIALS['oak_planks'] = ('sandstone', True)
            env.BUILDING_MATERIALS['oak_stairs'] = ('sandstone_stairs', True)
            env.BUILDING_MATERIALS['birch_stairs'] = ('sandstone_stairs', True)
            env.BUILDING_MATERIALS['oak_log'] = ('chiseled_sandstone', False)
            env.BUILDING_MATERIALS['grass_block'] = ('sand', False)
            env.BUILDING_MATERIALS['dirt'] = ('sand', False)


if __name__ == '__main__':
    try:
        prepare_environment()
    except KeyboardInterrupt:
        print("Pressed Ctrl-C to kill program.")
