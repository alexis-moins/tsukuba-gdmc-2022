from __future__ import annotations

import click
from colorama import Fore
from gdpc import interface as INTERFACE

from src import env
from src.blocks.block import Block
from src.blocks.collections import palette
from src.blocks.structure import Structure
from src.plots.plot import Plot
from src.simulation.buildings.building import BuildingProperties, Building, Mine
from src.simulation.buildings.building_type import BuildingType
from src.simulation.decisions.smart import SmartDecisionMaker
from src.simulation.simulation import Simulation
from src.utils.action_type import ActionType
from src.utils.criteria import Criteria


@click.command()
@click.option('-t', '--tick-speed', default=200, type=int, show_default=True, help='Set the number of entities checked at each tick')
@click.option('--debug', is_flag=True, default=False, help='Launch the simulation in debug mode')
@click.option('--no-buffering', is_flag=True, default=False, help='Send blocks one at a time, without using a buffer')
@click.option('--tp/--no-tp', default=True, show_default=True, help='Teleport the player to the start of the building area')
@click.option('--drops', is_flag=True, default=False, help='Enable drops from entities (may cause issues)')
@click.option('-y', '--years', default=40, type=int, show_default=True, help='The number of years during which the simulation will run')
@click.option('-d', '--deterioration', default=5, type=int, show_default=True, help='The percentage of blocks in a building that will suffer from the passing of time')
@click.option('-a', '--auto-build-area', default=False, is_flag=True, type=bool, show_default=True, help='Automatically set the build area around the player\'s current position')
def prepare_environment(debug: bool, tick_speed: int, no_buffering: bool, tp: bool, drops: bool, years: int, deterioration: int, auto_build_area: bool) -> None:
    """Prepare the environment using CLI options"""
    env.DEBUG = debug
    env.TP = tp
    env.DETERIORATION = deterioration

    print()

    env.BUILD_AREA = env.get_build_area(auto_build_area)
    env.WORLD = env.get_world_slice()

    if auto_build_area:
        env.TP = False
        print(f'{Fore.YELLOW}***{Fore.WHITE} Set build area around the player {Fore.YELLOW}***{Fore.WHITE}')

    INTERFACE.setBuffering(not no_buffering)
    INTERFACE.placeBlockFlags(doBlockUpdates=True, customFlags='0100011')

    INTERFACE.runCommand(f'gamerule doTileDrops {str(drops).lower()}')
    INTERFACE.runCommand(f'gamerule randomTickSpeed {tick_speed}')

    start_simulation(years)


def start_simulation(years: int) -> None:
    """Launch the simulation"""
    start, end = env.BUILD_AREA
    build_area = Plot.from_coordinates(start, end)
    env.WORLD = env.get_world_slice()

    if env.TP:
        command = f'tp @a {build_area.start.x} 110 {build_area.start.z}'
        INTERFACE.runCommand(command)
        print(f'/{command}')

    find_building_materials(build_area)

    decision_maker = SmartDecisionMaker(build_area)
    simulation = Simulation(build_area, decision_maker, years)
    simulation.start()

    INTERFACE.sendBlocks()

    INTERFACE.runCommand('gamerule randomTickSpeed 3')
    INTERFACE.runCommand('gamerule doEntityDrops true')


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
