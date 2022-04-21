from __future__ import annotations

import time
from typing import Dict, List, Tuple

from gdpc import interface as INTF
from gdpc import worldLoader as WL

from numpy import ndarray
from nbt.nbt import MalformedFileError

from utils.block import Block
from utils.coordinates import Coordinates
from utils.criteria import Criteria


def default_build_area_coordinates() -> tuple[Coordinates, Coordinates]:
    """Return a tuple of the starting and end coordinates of the requested build area"""
    x1, y1, z1, x2, y2, z2 = INTF.requestBuildArea()
    return Coordinates(x1, y1, z1), Coordinates(x2, y2, z2)


def get_world_slice(retry_amount: int = 10, retry_wait_time: int = 1):
    default_start, default_end = default_build_area_coordinates()
    while retry_amount:
        try:
            return WL.WorldSlice(default_start.x, default_start.z, default_end.x + 1, default_end.z + 1)
        except MalformedFileError:
            retry_amount -= 1
            time.sleep(retry_wait_time)
    print(f'[ERROR] : Could not get a world slice in {retry_amount} try')


class Plot:
    """Represents a build area"""
    default_start, default_end = default_build_area_coordinates()

    _world = get_world_slice()

    def __init__(self, x: int, z: int, size: Tuple[int, int]) -> None:
        """Parameterised constructor creating a new plot inside the build area"""
        self.start = Coordinates(x, 0, z)
        self.end = Coordinates(x + size[0], 255, z + size[1])
        self.size = size

        self.surface_blocks: Dict[Criteria, ndarray] = dict()

        self.center = self.start.x + self.size[0] // 2, self.start.z + self.size[1] // 2
        self.offset = self.start - Plot.default_start, self.end - Plot.default_start

    def __contains__(self, coordinates: Coordinates) -> bool:
        """Return true if the current plot contains the given coordinates"""
        return \
            self.start.x <= coordinates.x <= self.end.x and \
            self.start.y <= coordinates.y <= self.end.y and \
            self.start.z <= coordinates.z <= self.end.z

    @staticmethod
    def get_build_area() -> Plot:
        """Return the plot of the default build area"""
        coord_a, coord_b = default_build_area_coordinates()
        size = abs(coord_a - coord_b)
        return Plot(x=coord_a.x, z=coord_a.z, size=(size.x, size.z))

    def update(self) -> None:
        """Update the world slice and most importantly the heightmaps"""
        Plot._world = get_world_slice()
        self.surface_blocks = dict()

    def visualize(self, ground: str = 'blue_stained_glass') -> None:
        """Change the blocks at the surface of the plot to visualize it"""
        for block in self.get_blocks_at_surface(Criteria.MOTION_BLOCKING):
            INTF.placeBlock(*block.coordinates, ground)

    def get_block_at(self, x: int, y: int, z: int) -> Block:
        """Return the block found at the given x, y, z coordinates in the world"""
        name = self._world.getBlockAt(x, y, z)
        return Block(name, Coordinates(x, y, z))

    def get_heightmap(self, criteria: Criteria) -> ndarray:
        """Return the desired heightmap of the given type"""
        if criteria.name in self._world.heightmaps.keys():
            return self._world.heightmaps[criteria.name][self.offset[0].x:self.offset[1].x, self.offset[0].z:self.offset[1].z]
        return list()

    def get_blocks_at_surface(self, criteria: Criteria) -> List[Block]:
        """Return a list of the blocks at the surface of the plot, using the given criteria"""
        if criteria in self.surface_blocks.keys():
            return self.surface_blocks[criteria]

        surface = list()
        heightmap = self.get_heightmap(criteria)

        for x, rest in enumerate(heightmap):
            for z, h in enumerate(rest):
                coordinates = Coordinates(self.start.x + x, h - 1, self.start.z + z)
                surface.append(self.get_block_at(*coordinates))

        self.surface_blocks[criteria] = surface
        return surface

    def remove_trees(self) -> None:
        """Remove all vegetation at the surface of the current plot"""
        remove_filter = ['leaves', 'log', 'vine', 'stern', 'cocoa', 'bush', 'mushroom']

        surface_blocks = self.get_blocks_at_surface(Criteria.WORLD_SURFACE)

        amount = 0
        deleted_blocks = set()
        unwanted_blocks = Block.filter(remove_filter, surface_blocks)

        print(f'=> Removing surface vegetation on plot at {self.start}')
        while unwanted_blocks:
            block = unwanted_blocks.pop()

            for coordinates in block.neighbouring_coordinates():
                if coordinates not in deleted_blocks and coordinates in self:
                    block_around = self.get_block_at(*coordinates)

                    if block_around in unwanted_blocks:
                        continue

                    if block_around.is_one_of(remove_filter):
                        unwanted_blocks.add(block_around)
                        INTF.placeBlock(*block_around.coordinates, 'tnt')

            INTF.placeBlock(*block.coordinates, 'air')
            deleted_blocks.add(block.coordinates)
            amount += 1

        INTF.sendBlocks()
        print(f'=> Deleted {amount} blocs')
        self.update()
