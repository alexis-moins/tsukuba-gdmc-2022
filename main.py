from __future__ import annotations

import time

import click
from colorama import Fore
from gdpc import interface as INTERFACE

from src import env
from src.utils import server
from src.blocks.block import Block
from src.plots.plot import Plot
from src.simulation.simulation import Simulation
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
@click.option('--show-time', default=False, is_flag=True, type=bool, show_default=True,
              help='Show time taken during generation')
@click.option('--profile-time', default=False, is_flag=True, type=bool, show_default=True,
              help='Show time profiling and output profiling file')
def prepare_environment(debug: bool, tick_speed: int, no_buffering: bool, tp: bool, drops: bool, years: int,
                        deterioration: int, auto_build_area: bool, show_time: bool, profile_time: bool) -> None:
    """Prepare the environment using CLI options"""
    env.DEBUG = debug
    env.TP = tp
    env.DETERIORATION = deterioration
    env.SHOW_TIME = show_time
    env.PROFILE_TIME = profile_time

    env.BUILD_AREA = env.get_build_area(auto_build_area)
    env.WORLD = env.get_world_slice()

    if auto_build_area:
        env.TP = False
        print(f'{Fore.YELLOW}***{Fore.WHITE} Set build area around the player {Fore.YELLOW}***{Fore.WHITE}')

    INTERFACE.setBuffering(not no_buffering)
    INTERFACE.placeBlockFlags(doBlockUpdates=True, customFlags='0100011')

    INTERFACE.runCommand(f'gamerule doTileDrops {str(drops).lower()}')
    INTERFACE.runCommand(f'gamerule randomTickSpeed {tick_speed}')

    if env.PROFILE_TIME:
        import cProfile
        import pstats

        with cProfile.Profile() as pr:
            start_simulation(years)

        stats = pstats.Stats(pr)
        stats.sort_stats(pstats.SortKey.TIME)
        stats.print_stats()
        stats.dump_stats(filename='profiler.prof')
    else:
        start_simulation(years)

    if env.SHOW_TIME:
        time_took = time.time() - env.start_time
        print(f'Process took {time_took:.2f} s.')


def start_simulation(years: int) -> None:
    """Launch the simulation"""
    start, end = env.BUILD_AREA
    build_area = Plot.from_coordinates(start, end)
    build_area.remove_lava()
    env.WORLD = env.get_world_slice()

    if env.TP:
        command = f'tp @a {build_area.start.x} 110 {build_area.start.z}'
        INTERFACE.runCommand(command)
        print(f'/{command}')

    find_building_materials(build_area)

    simulation = Simulation(build_area, years)
    simulation.start()

    INTERFACE.runCommand('gamerule randomTickSpeed 3')
    INTERFACE.runCommand('gamerule doEntityDrops true')


def find_building_materials(build_area: Plot):
    """"""
    surface = build_area.get_blocks(Criteria.MOTION_BLOCKING_NO_LEAVES)
    logs = surface.filter(pattern='_log')

    # TODO use Palettes
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

    server.send_buffer(force=True)
