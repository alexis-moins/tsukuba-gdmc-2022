from __future__ import annotations

import random
import time
from typing import Dict

from gdpc import toolbox as TB
from gdpc import interface as INTF
from gdpc import geometry as GEO

from build_area import Plot
from construction_plot import ConstructionPlot, build_simple_house

from utils.coordinates import Coordinates


def get_most_used_block_of_type(block_type: str, blocks: Dict[str, int]) -> str | None:
    """Return the block of the given type most represented in the given frequency dict"""
    iterator = filter(lambda k: block_type in k, blocks.keys())
    dicti = {key: blocks[key] for key in list(iterator)}

    if not dicti:
        return None

    return max(dicti, key=dicti.get)


def test_areas():

    plot1 = Plot(Coordinates(10, 0, 10), Coordinates(110, 255, 35))
    plot2 = Plot(Coordinates(10, 0, 40), Coordinates(110, 255, 75))
    plot3 = Plot(Coordinates(10, 0, 80), Coordinates(110, 255, 105))

    plot1.visualize()

    plot2.remove_trees()

    plot3.remove_trees()
    plot3.visualize('orange_stained_glass')


if __name__ == '__main__':

    INTF.setBuffering(True)

    try:

        # Retrieve the default build area
        build_area = Plot.get_build_area()
        build_area.visualize()

        command = f"tp @a {build_area.start.x} 110 {build_area.start.z}"
        INTF.runCommand(command)
        print(f'/{command}')

        # build_area.get_blocks_at_surface('MOTION_BLOCKING')

        # build_area.get_block_usage()

        build_area.remove_trees()
        build_area.visualize()

        construction_area_1 = ConstructionPlot(x=10, z=10, size=(50, 50))

        construction_area_1.remove_trees()
        construction_area_1.visualize(block='orange_stained_glass')

        # get_most_used_block_of_type("log", )

        for i in range(5):
            iter_start = time.time()
            house_size = random.randint(5, 20), random.randint(4, 15), random.randint(5, 20)
            house_area = (house_size[0], house_size[1])
            house_construction_coord = construction_area_1.get_construction_spot(house_area)

            build_simple_house("oak_planks", house_construction_coord, house_size)
            construction_area_1.occupy_area(house_construction_coord, house_area, 3)

            print(f"Placed house of size {house_size} at {house_construction_coord} in {time.time() - iter_start:.2f}s")

        INTF.sendBlocks()
        print("Done!")

    except KeyboardInterrupt:   # useful for aborting a run-away program
        print("Pressed Ctrl-C to kill program.")
