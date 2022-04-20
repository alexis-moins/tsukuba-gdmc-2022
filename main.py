from __future__ import annotations


from typing import Dict


from gdpc import interface as INTF
from gdpc import toolbox as TB
from gdpc import worldLoader as WL

from build_area import BuildArea
from house_placer import place_houses

from utils import Block, Coordinates


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
        # Retreive the build area
        build_area = BuildArea(BuildArea.start, BuildArea.end)
        plot = BuildArea(Coordinates(10, 0, 10), Coordinates(20, 255, 20))

        command = f"tp @a {build_area.start.x} 110 {build_area.start.z}"
        INTF.runCommand(command)
        print(f'/{command}')

        b1 = build_area.get_blocks_at_surface('MOTION_BLOCKING')

        for coordinates in b1.keys():
            INTF.placeBlock(*coordinates, 'lime_stained_glass')

        b1 = plot.get_blocks_at_surface('MOTION_BLOCKING')
        for coordinates in b1.keys():
            INTF.placeBlock(*coordinates, 'orange_stained_glass')

        # main_building_block = str(most_used_block)
        # if 'log' in most_used_block:
        #     main_building_block = main_building_block.replace('log', 'planks')

        # place_houses(main_building_block)

        print("Done!")
    except KeyboardInterrupt:   # useful for aborting a run-away program
        print("Pressed Ctrl-C to kill program.")
