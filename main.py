from __future__ import annotations


from typing import Dict


from gdpc import interface as INTF
from gdpc import toolbox as TB
from gdpc import worldLoader as WL

from utils import Block, get_block_at

STARTX, STARTY, STARTZ, ENDX, ENDY, ENDZ = INTF.requestBuildArea()

WORLDSLICE = WL.WorldSlice(STARTX, STARTZ, ENDX + 1, ENDZ + 1)
heightmap = WORLDSLICE.heightmaps["MOTION_BLOCKING"]


def get_most_used_block_of_type(block_type: str, blocks: Dict[str, int]) -> str | None:
    """Return the block of the given type most represented in the given frequency dict"""
    iterator = filter(lambda k: block_type in k, blocks.keys())
    dicti = {key: blocks[key] for key in list(iterator)}

    if not dicti:
        return None

    return max(dicti, key=dicti.get)




def get_surface_blocks_count(world: WORLDSLICE) -> Dict[str, int]:
    """"""
    surface_blocks = dict()
    for x, rest in enumerate(world.heightmaps['MOTION_BLOCKING_NO_LEAVES']):
        for z, h in enumerate(rest):
            block = world.getBlockAt(STARTX + x, h - 1, STARTZ + z)
            if not block in surface_blocks.keys():
                surface_blocks[block] = 0
            surface_blocks[block] += 1

    return surface_blocks



if __name__ == '__main__':
    # NOTE: It is a good idea to keep this bit of the code as simple as
    #     possible so you can find mistakes more easily

    INTF.setBuffering(True)

    try:

        height = heightmap[(STARTX, STARTY)]
        INTF.runCommand(f"tp @a {STARTX} {height} {STARTZ}")
        print(f"/tp @a {STARTX} {height} {STARTZ}")

        global most_used_block
        surface_blocks = get_surface_blocks_count(WORLDSLICE)
        most_used_block = get_most_used_block_of_type('log', surface_blocks)

        print(f'most used wood: {most_used_block}')

        surface_blocks = list()
        for x, rest in enumerate(WORLDSLICE.heightmaps['MOTION_BLOCKING']):
            for z, h in enumerate(rest):
                block = get_block_at(STARTX + x, h - 1, STARTZ + z, WORLDSLICE)
                surface_blocks.append(block)

        unwanted_blocks = Block.filter(['leaves', 'log'], surface_blocks)

        amount = 0
        deleted_blocks = set()
        while unwanted_blocks:
            block = unwanted_blocks.pop(0)

            for coordinates in block.neighbouring_coordinates():
                if coordinates not in deleted_blocks and coordinates.is_in_area(STARTX, STARTY, STARTZ, ENDX, ENDY, ENDZ):
                    block_around = get_block_at(*coordinates, WORLDSLICE)

                    if block_around.is_one_of(['leaves', 'log']):
                        unwanted_blocks.append(block_around)

            INTF.placeBlock(*block.coordinates, 'air')
            deleted_blocks.add(block.coordinates)
            amount += 1
            if amount % 10000 == 0:
                print(f'Progress {amount}, to delete : {len(unwanted_blocks)}')

        print(f'Deleted {amount} blocs')

        main_building_block = str(most_used_block)
        if 'log' in most_used_block:
            main_building_block = main_building_block.replace('log', 'planks')

        place_houses(main_building_block)

        print("Done!")
    except KeyboardInterrupt:   # useful for aborting a run-away program
        print("Pressed Ctrl-C to kill program.")
