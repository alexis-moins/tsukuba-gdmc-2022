from __future__ import annotations

import time
import random
from typing import Dict

from gdpc import toolbox as TB
from gdpc import geometry as GEO
from gdpc import interface as INTF

from plots.plot import Plot
from plots.construction_plot import SuburbPlot, build_simple_house

from utils.block import Block
from utils.criteria import Criteria


def get_most_used_block_of_type(block_type: str, blocks: Dict[str, int]) -> str | None:
    """Return the block of the given type most represented in the given frequency dict"""
    iterator = filter(lambda k: block_type in k, blocks.keys())
    dicti = {key: blocks[key] for key in list(iterator)}

    if not dicti:
        return None

    return max(dicti, key=dicti.get)


if __name__ == '__main__':

    INTF.setBuffering(True)

    try:

        # Retrieve the default build area
        build_area = Plot.get_build_area()
        build_area.visualize()

        command = f"tp @a {build_area.start.x} 110 {build_area.start.z}"
        INTF.runCommand(command)
        print(f'=> /{command}\n')

        surface = build_area.get_blocks_at_surface(Criteria.MOTION_BLOCKING)
        counter = Block.group_by_name(surface)

        print(f'{counter}')
        print(counter.keys())

        # build_area.remove_trees()
        build_area.visualize()

        construction_area_1 = SuburbPlot(x=10, z=10, size=(50, 50))

        construction_area_1.remove_trees()
        construction_area_1.visualize(ground='orange_stained_glass')

        for i in range(5):
            iter_start = time.time()
            house_size = random.randint(5, 20), random.randint(4, 15), random.randint(5, 20)
            house_area = (house_size[0], house_size[2])
            house_construction_coord = construction_area_1.get_construction_plot(house_area)

            if house_construction_coord is None:
                continue

            house_construction_coord.build_simple_house()
            build_simple_house("oak_planks", house_construction_coord, house_size)


            print(f"Placed house of size {house_size} at {house_construction_coord} in {time.time() - iter_start:.2f}s")

        INTF.sendBlocks()
        print("Done!")

    except KeyboardInterrupt:   # useful for aborting a run-away program
        print("Pressed Ctrl-C to kill program.")
