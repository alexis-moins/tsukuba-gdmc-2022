from typing import Dict

from gdpc import geometry as GEO
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

    height = heightmap[(STARTX, STARTY)]
    INTF.runCommand(f"tp @a {STARTX} {height} {STARTZ}")
    print(f"/tp @a {STARTX} {height} {STARTZ}")

    print('biome: ' + WORLDSLICE.getPrimaryBiomeNear(STARTX, height, STARTZ))

    global most_used_block
    surface_blocks = get_surface_blocks_count(WORLDSLICE)
    most_used_block = get_most_used_block_of_type('log', surface_blocks)

    print(f'most used wood: {most_used_block}')

    surface_blocks = list()
    for x, rest in enumerate(WORLDSLICE.heightmaps['MOTION_BLOCKING']):
        for z, h in enumerate(rest):

            block = get_block_at(STARTX + x, h - 1, STARTZ + z, WORLDSLICE)
            surface_blocks.append(block)

    wood_blocks = Block.filter(['leaves', 'log'], surface_blocks)

    while wood_blocks:
        block = wood_blocks.pop(0)

        for coordinates in block.neighbouring_coordinates():
            block_below = get_block_at(*coordinates, WORLDSLICE)

            if block_below.is_one_of(['leaves', 'log']):
                wood_blocks.append(block_below)

        INTF.placeBlock(*block.coordinates, 'air')
        print(f'Deleted block {block}')
