from typing import Dict, List

from gdpc import interface as INTF
from gdpc import worldLoader as WL

import numpy as np

from utils import Block, Coordinates


class BuildArea:
    """Represents a build area"""
    # Just to unpack them with one requestBuildArea call
    start, end = (lambda x: (Coordinates(*x[:3]), Coordinates(*x[3:])))(INTF.requestBuildArea())
    world = WL.WorldSlice(start.x, start.z, end.x + 1, end.z + 1)

    def __init__(self, start: Coordinates, end: Coordinates) -> None:
        """Parameterised constructor creating a new plot inside the build area"""
        self.start = start
        self.end = end
        self.offset = start - BuildArea.start, end - BuildArea.start
        print(self.offset)

    def get_heightmap(self, heightmap: str) -> np.array:
        """Return the desired heightmap of the given type"""
        if heightmap in self.world.heightmaps.keys():
            return self.world.heightmaps[heightmap][self.offset[0].x:self.offset[1].x, self.offset[0].z:self.offset[1].z]
        return list()

    def get_blocks_at_surface(self, heightmap_type: str) -> Dict[Coordinates, Block]:
        """"""
        surface_blocks = dict()
        heightmap = self.get_heightmap(heightmap_type)

        for x, rest in enumerate(heightmap):
            for z, h in enumerate(rest):
                coordinates = Coordinates(self.start.x + x, h - 1, self.start.z + z)
                surface_blocks[coordinates] = self.get_block_at(*coordinates)

        return surface_blocks

    def get_block_at(self, x: int, y: int, z: int) -> Block:
        """Return the block found at the given x, y, z coordinates in the world"""
        name = self.world.getBlockAt(x, y, z)
        return Block(name, Coordinates(x, y, z))

    def remove_trees(self) -> None:
        """"""
        pass

