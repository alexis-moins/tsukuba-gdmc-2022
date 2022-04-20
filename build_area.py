from typing import Dict, List

from gdpc import interface as INTF
from gdpc import worldLoader as WL

from utils import Block, Coordinates


class BuildArea:
    """Represents a build area"""
    area_coordinates = INTF.requestBuildArea()
    start = Coordinates(*area_coordinates[:3])
    end = Coordinates(*area_coordinates[3:])
    world = WL.WorldSlice(start.x, start.z, end.x + 1, end.z + 1)

    def __init__(self, start: Coordinates, end: Coordinates) -> None:
        """Parameterised constructor creating a new plot inside the build area"""
        self.start = start
        self.end = end

    def get_heightmap(self, heightmap: str) -> List[List[int]]:
        """Return the desired heightmap of the given type"""
        if heightmap in self.world.heightmaps.keys():
            return self.world.heightmaps[heightmap]
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


class Plot(BuildArea):
    """Class representing a plot inside the general build area"""

    def __init__(self, start: Coordinates, end: Coordinates) -> None:
        """Parameterised constructor creating a new plot inside the build area"""
        self.start = start
        self.end = end
        self.build_area = BuildArea()
