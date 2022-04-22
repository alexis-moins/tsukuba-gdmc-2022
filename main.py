from __future__ import annotations

import time
import random
from typing import Dict

from gdpc import toolbox as TB
from gdpc import geometry as GEO
from gdpc import interface as INTF

from plots import construction_plot
from plots.plot import Plot
from plots.suburb_plot import SuburbPlot


def get_most_used_block_of_type(block_type: str, blocks: Dict[str, int]) -> str | None:
    """Return the block of the given type most represented in the given frequency dict"""
    iterator = filter(lambda k: block_type in k, blocks.keys())
    dicti = {key: blocks[key] for key in list(iterator)}

    if not dicti:
        return None

    return max(dicti, key=dicti.get)


if __name__ == '__main__':

    INTF.setBuffering(True)
    INTF.placeBlockFlags(doBlockUpdates=True, customFlags='0000011')

    try:
        # Retrieve the default build area
        build_area = Plot.get_build_area()
        # build_area.visualize()

        command = f"tp @a {build_area.start.x} 110 {build_area.start.z}"
        INTF.runCommand(command)
        print(f'=> /{command}')

        most_used_wood = build_area.filter_most_used_blocks('log')
        if most_used_wood is None:
            most_used_wood = 'minecraft:oak_log'
        most_used_wood = most_used_wood.replace('minecraft:', '').replace('log', 'planks')
        print(f'=> Most used wood: {most_used_wood}')

        construction_area_1 = SuburbPlot(x=10 + build_area.start.x, z=10 + build_area.start.z, size=(50, 50))

        construction_area_1.remove_trees()
        # construction_area_1.visualize(ground='orange_stained_glass')

        for i in range(5):
            construction_plot.build_house_1(construction_area_1, most_used_wood)
        print('Done!')

    except KeyboardInterrupt:   # useful for aborting a run-away program
        print("Pressed Ctrl-C to kill program.")
