from __future__ import annotations

import os
import sys
import random

from gdpc import toolbox as TB
from gdpc import geometry as GEO
from gdpc import interface as INTF

import launch_env

from modules.plots.plot import Plot
from modules.plots.suburb_plot import SuburbPlot
from modules.simulation.simulation import Simulation


if __name__ == '__main__':

    if 'd' in sys.argv or 'D' in sys.argv or 'debug' in sys.argv or 'DEBUG' in sys.argv:
        launch_env.DEBUG = True

    INTF.setBuffering(True)
    INTF.placeBlockFlags(doBlockUpdates=True, customFlags='0100011')

    try:

        # Retrieve the default build area
        build_area = Plot.get_build_area()
        print(f'Build area : {build_area.start}')

        suburb = SuburbPlot(x=build_area.start.x, z=build_area.start.z, size=build_area.size)
        span = 2
        suburb.compute_steep_map(span)
        suburb.visualize_steep_map(span)
        # command = f"tp @a {build_area.start.x} 110 {build_area.start.z}"
        # INTF.runCommand(command)
        # print(f'=> /{command}')
        #
        # build_area.remove_trees()
        #
        # population = random.randrange(2, 4)
        # simulation = Simulation(area=build_area, population=population, years=10)
        #
        # simulation.start()

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
        # for i in range(15):
        #     iter_start = time.time()

        #     house = random.choice(houses)

        #     rotations = [0, 90, 180, 270]
        #     rotation = random.choice(rotations)
        #     area = house.get_area(rotation)

        #     construction_plot = suburb.get_construction_plot(area)

        #     if construction_plot:
        #         construction_plot.build(house, materials=building_materials, rotation=rotation)
        #         print(
        #             f'\n=> Built structure {house.name} of size {house.size} at {construction_plot.build_start} in {time.time() - iter_start: .2f}s\n')
        #     else:
        #         print(f'=> Unable to find construction area for structure with size {house.size}')

    except KeyboardInterrupt:   # useful for aborting a run-away program
        print("Pressed Ctrl-C to kill program.")
