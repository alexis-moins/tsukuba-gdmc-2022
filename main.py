from __future__ import annotations

import time
from dataclasses import astuple

import sys
import random
import launch_env

from gdpc import interface as INTF

from modules.blocks.structure import Structure
from modules.plots.plot import Plot
from modules.utils.loader import BUILD_AREA
from modules.simulation.simulation import Simulation


if __name__ == '__main__':

    if 'd' in sys.argv or 'D' in sys.argv or 'debug' in sys.argv or 'DEBUG' in sys.argv:
        launch_env.DEBUG = True

    INTF.setBuffering(True)
    INTF.placeBlockFlags(doBlockUpdates=True, customFlags='0100011')
    INTF.runCommand('gamerule randomTickSpeed 200')

    try:
        # Retrieve the default build area
        start, end = BUILD_AREA
        build_area = Plot.from_coordinates(start, end)

        INTF.runCommand(f'tp @a {build_area.start.x} 110 {build_area.start.z}')

        population = random.randrange(2, 4)
        simulation = Simulation(build_area, population=10, years=40)

        simulation.start()
        #
        # # Clearing drops & getting back to default tick speed
        # INTF.runCommand('kill @e[type=minecraft:item]')
        # INTF.runCommand('gamerule randomTickSpeed 3')

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

        # #  Move the following code into a method in SuburbPlot
        #

    except KeyboardInterrupt:   # useful for aborting a run-away program
        print("Pressed Ctrl-C to kill program.")
