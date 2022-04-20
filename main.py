from __future__ import annotations


from typing import Dict


from gdpc import interface as INTF
from gdpc import toolbox as TB
from gdpc import worldLoader as WL

from build_area import BuildArea
from house_placer import place_houses

from utils import Block, Coordinates


build_area = BuildArea(BuildArea.start, BuildArea.end)
plot = BuildArea(Coordinates(0, 0, 0), Coordinates(10, 10, 10))

plot_one = Plot(Coordinates(0, 0, 0), Coordinates(10, 10, 10))


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
        build_area = BuildArea()

        command = f"tp @a {build_area.start.x} 110 {build_area.start.z}"
        INTF.runCommand(command)
        print(f'/{command}')

        surface_blocks = build_area.get_blocks_at_surface('MOTION_BLOCKING')

        # counter = Block.group_by_name(Block.filter('log', surface_blocks.values()))
        # most_used_block = get_most_used_block_of_type('log', surface_blocks)

        # print(f'most used wood: {most_used_block}')

        remove_filter = ['leaves', 'log', 'vine']

        amount = 0
        unwanted_blocks = Block.filter(remove_filter, surface_blocks.values())

        deleted_blocks = set()
        while unwanted_blocks:
            block = unwanted_blocks.pop()

            for coordinates in block.neighbouring_coordinates():
                if coordinates not in deleted_blocks and coordinates.is_in_area(build_area):
                    block_around = build_area.get_block_at(*coordinates)

                    if block_around in unwanted_blocks:
                        continue

                    if block_around.is_one_of(remove_filter):
                        unwanted_blocks.add(block_around)
                        INTF.placeBlock(*block_around.coordinates, 'tnt')

            INTF.placeBlock(*block.coordinates, 'air')
            deleted_blocks.add(block.coordinates)

            amount += 1
            print(f'Deleted {amount} blocks, still {len(unwanted_blocks)} to delete')

        INTF.sendBlocks()
        print(f'Deleted {amount} blocs')

        # main_building_block = str(most_used_block)
        # if 'log' in most_used_block:
        #     main_building_block = main_building_block.replace('log', 'planks')

        # place_houses(main_building_block)

        print("Done!")
    except KeyboardInterrupt:   # useful for aborting a run-away program
        print("Pressed Ctrl-C to kill program.")
