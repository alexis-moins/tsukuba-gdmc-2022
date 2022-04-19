from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Tuple
from random import randint

from gdpc import geometry as GEO
from gdpc import interface as INTF
from gdpc import toolbox as TB
from gdpc import worldLoader as WL

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


def build_house():
    heights = WORLDSLICE.heightmaps["MOTION_BLOCKING_NO_LEAVES"]

    for x in range(STARTX, ENDX + 1):
        # the northern wall
        y = heights[(x, STARTZ)]
        GEO.placeCuboid(x, y - 2, STARTZ, x, y, STARTZ, most_used_block)
        GEO.placeCuboid(x, y + 1, STARTZ, x, y + 4, STARTZ, "granite_wall")

        y = heightmap[(x, ENDZ)]
        GEO.placeCuboid(x, y - 2, ENDZ, x, y, ENDZ, most_used_block)
        GEO.placeCuboid(x, y + 1, ENDZ, x, y + 4, ENDZ, "red_sandstone_wall")


@dataclass(frozen=True)
class Block:
    """Represents a block in the world"""
    name: str
    coordinates: Tuple[int]

    @property
    def coordinates_below(self) -> Tuple[int]:
        """Return the coordinates of the block below"""
        x, h, z = self.coordinates
        return x, h - 1, z

    @staticmethod
    def filter(pattern: str | List[str], blocks: List[Block]) -> List[Block]:
        """Filter the given list of block and return the ones that contain the given pattern"""
        if type(pattern) == str:
            pattern = [pattern]

        iterator = filter(lambda block: block.is_one_of(pattern), blocks)
        return list(iterator)

    def is_one_of(self, pattern: List[str]) -> bool:
        """"""
        for item in pattern:
            if item in self.name:
                return True
        return False


def get_block_at(x, h, z) -> Block:
    """"""
    coordinates = x, h, z
    name = WORLDSLICE.getBlockAt(*coordinates)
    return Block(name, coordinates)


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

            block = get_block_at(STARTX + x, h - 1, STARTZ + z)
            surface_blocks.append(block)

    wood_blocks = Block.filter(['leaves', 'log'], surface_blocks)

    while wood_blocks:
        block = wood_blocks.pop(0)

        block_below = get_block_at(*block.coordinates_below)
        if block_below.is_one_of(['leaves', 'air', 'log']):
            wood_blocks.append(block_below)

        INTF.placeBlock(*block.coordinates, 'air')
        print(f'Deleted block {block.name} at {block.coordinates}')
