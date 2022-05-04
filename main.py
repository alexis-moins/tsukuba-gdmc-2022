from __future__ import annotations

import click
from gdpc import interface as INTF, lookup

from src import env
from src.blocks.block import Block
from src.blocks.collections import palette
from src.blocks.structure import Structure
from src.plots.plot import Plot
from src.simulation.buildings.building import BuildingProperties, Building
from src.simulation.buildings.building_type import BuildingType
from src.simulation.decisions.smart import SmartDecisionMaker
from src.simulation.simulation import Simulation
from src.utils.action_type import ActionType
from src.utils.criteria import Criteria


@click.command()
@click.option('-t', '--tick-speed', default=200, type=int, show_default=True, help='Set the number of entities checked at each tick')
@click.option('-d', '--debug', is_flag=True, default=False, help='Launch the simulation in debug mode')
@click.option('--no-buffering', is_flag=True, default=False, help='Send blocks one at a time, without using a buffer')
@click.option('--drops', is_flag=True, default=False, help='Enable drops from entities (may cause issues)')
@click.option('-y', '--years', default=40, type=int, show_default=True, help='The number of years during which the simulation will run')
def prepare_environment(debug: bool, tick_speed: int, no_buffering: bool, drops: bool, years: int) -> None:
    """Prepare the environment using CLI options"""
    if debug:
        env.DEBUG = True

    INTF.setBuffering(not no_buffering)
    INTF.placeBlockFlags(doBlockUpdates=True, customFlags='0100011')

    INTF.runCommand(f'gamerule doTileDrops {str(drops).lower()}')
    INTF.runCommand(f'gamerule randomTickSpeed {tick_speed}')

    start_simulation(years)


def start_simulation(years: int) -> None:
    """Launch the simulation"""
    start, end = env.BUILD_AREA
    build_area = Plot.from_coordinates(start, end)

    INTF.runCommand(f'tp @a {build_area.start.x} 110 {build_area.start.z}')

    find_building_materials(build_area)
    decision_maker = SmartDecisionMaker(build_area)

    simulation = Simulation(build_area, decision_maker, years)

    simulation.start()

    INTF.sendBlocks()

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


def test_palette():
    INTF.setBuffering(True)
    INTF.placeBlockFlags(doBlockUpdates=True, customFlags='0100011')

    struct = Structure.parse_nbt_file('house2_test_palette.nbt')

    building = Building('testHouse2', BuildingProperties(cost=10, building_type=BuildingType.NONE,
                                                         action_type=ActionType.BED), struct)

    palettes = {'lapis_block': palette.RandomSequencePalette(['chest', 'crafting_table', 'smoker', 'furnace', 'brewing_stand', 'cauldron', 'air']),
                'gold_block': palette.RandomPalette(['air', 'lantern'] + ['potted_' + flower.replace('minecraft:', '') for flower in lookup.SHORTFLOWERS]),
                'gold_ore' : palette.OneBlockPalette([color + '_carpet' for color in lookup.COLORS]),
                'diamond_block': palette.OneBlockPalette([color + '_bed' for color in lookup.COLORS]),
                'iron_block': palette.RandomPalette(['cyan_shulker_box', 'cartography_table', 'chest', 'air', 'jukebox', 'note_block']),
                'diamond_ore': palette.RandomPalette(['piston', 'dispenser', 'note_block', 'cobweb', 'end_portal_frame', 'skeleton_skull', 'air', 'barrel', 'hay_block']),
                'white_terracotta': palette.OneBlockPalette([color + '_terracotta' for color in lookup.COLORS]),
                'white_stained_glass': palette.OneBlockPalette([color + '_stained_glass' for color in lookup.COLORS])}

    rotation = 0
    start, end = env.BUILD_AREA
    build_area = Plot.from_coordinates(start, end)

    plot = build_area.get_subplot(building.get_size(rotation))

    building.build(plot, rotation, palettes)



if __name__ == '__main__':
    try:
        test_palette()

        # prepare_environment()
    except KeyboardInterrupt:
        print("Pressed Ctrl-C to kill program.")
