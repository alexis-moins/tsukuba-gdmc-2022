from __future__ import annotations
from collections import Counter
from re import match

import time
import random
from typing import Any, Dict

from gdpc import toolbox as TB
from gdpc import geometry as GEO
from gdpc import interface as INTF
from numpy import extract
from yaml import safe_load

from plots import construction_plot
from plots.plot import Plot
from plots.suburb_plot import SuburbPlot
from blocks.block import Block
from utils.criteria import Criteria
from utils.structure import Structure


def load_file(file_name: str) -> Any:
    """"""
    with open(f'resources/{file_name}.yaml', 'r') as file:
        data = safe_load(file)
    return data


if __name__ == '__main__':

    INTF.setBuffering(True)
    INTF.placeBlockFlags(doBlockUpdates=True, customFlags='0100011')

    try:
        # Retrieve the default build area
        build_area = Plot.get_build_area()

        command = f"tp @a {build_area.start.x} 110 {build_area.start.z}"
        INTF.runCommand(command)
        print(f'=> /{command}')

        surface = build_area.get_blocks_at_surface(Criteria.MOTION_BLOCKING_NO_LEAVES)

        most_used_wood = surface.filter(pattern='log').most_common_block
        input(f'=> Most used wood: {most_used_wood}')

        building_materials = dict()

        # TODO extract material i.e. oak from minecraft:oak_log[...]
        building_materials['oak'] = most_used_wood

        # Move this somewhere else
        structures = dict()
        structures['house1'] = Structure.parse_nbt_file('house1')
        structures['house2'] = Structure.parse_nbt_file('house2')

        suburb = SuburbPlot(x=10 + build_area.start.x, z=10 + build_area.start.z, size=(50, 50))
        suburb.remove_trees()

        houses = [structures['house1'], structures['house2']]

        #  Move the following code into a method in SuburbPlot
        for i in range(5):
            iter_start = time.time()

            random.shuffle(houses)
            house = houses[0]

            area = (house.size[0], house.size[2])
            construction_plot = suburb.get_construction_plot(area)

            if construction_plot:
                construction_plot.build(house, materials=building_materials)
                print(
                    f'\n=> Built structure {house.name} of size {house.size} at {construction_plot.build_start} in {time.time() - iter_start: .2f}s\n')

            print(f'=> Unable to find construction area for structure with size {house.size}')

        print('Done!')

    except KeyboardInterrupt:   # useful for aborting a run-away program
        print("Pressed Ctrl-C to kill program.")
