from __future__ import annotations
from modules.utils.loader import WORLD, BUILD_AREA, update_world_slice
from modules.utils.coordinates import Coordinates, Size
from modules.utils.criteria import Criteria
from modules.blocks.collections.block_list import BlockList
from modules.blocks.block import Block
from numpy import ndarray
from gdpc import interface as INTF
from gdpc import worldLoader as WL
from gdpc import interface as INTF, lookup
import numpy as np
from typing import Dict, Tuple
import time


class Plot:
    """Represents a build area"""

    def __init__(self, x: int, z: int, size: Size) -> None:
        """Parameterised constructor creating a new plot inside the build area"""
        self.start = Coordinates(x, 0, z)
        self.end = Coordinates(x + size.x, 255, z + size.z)
        self.size = size

        self.surface_blocks: dict[Criteria, BlockList] = {}
        self.offset = self.start - BUILD_AREA[0], self.end - BUILD_AREA[0]

        # TODO change center into coordinates
        self.center = self.start.x + self.size.x // 2, self.start.z + self.size.z // 2

    @staticmethod
    def from_coordinates(start: Coordinates, end: Coordinates) -> Plot:
        """Return a new plot created from the given start and end coordinates"""
        return Plot(start.x, start.z, Size.from_coordinates(start, end))

    def update(self) -> None:
        """Update the world slice and most importantly the heightmaps"""
        update_world_slice()
        self.surface_blocks.clear()

    def visualize(self, ground: str = 'blue_stained_glass', criteria: Criteria = Criteria.MOTION_BLOCKING) -> None:
        """Change the blocks at the surface of the plot to visualize it"""
        for block in self.get_blocks(criteria):
            INTF.placeBlock(*block.coordinates, ground)
        INTF.sendBlocks()

    def get_block_at(self, x: int, y: int, z: int) -> Block:
        """Return the block found at the given x, y, z coordinates in the world"""
        name = WORLD.getBlockAt(x, y, z)
        return Block.deserialize(name, Coordinates(x, y, z))

    def get_heightmap(self, criteria: Criteria) -> ndarray:
        """Return the desired heightmap of the given type"""
        if criteria.name in WORLD.heightmaps.keys():
            return WORLD.heightmaps[criteria.name][self.offset[0].x:self.offset[1].x, self.offset[0].z:self.offset[1].z]
        raise Exception(f'Invalid criteria: {criteria}')

    def get_blocks(self, criteria: Criteria) -> BlockList:
        """Return a list of the blocks at the surface of the plot, using the given criteria"""

        if criteria in self.surface_blocks.keys():
            return self.surface_blocks[criteria]

        # Little hack to have custom heightmaps
        if criteria == Criteria.MOTION_BLOCKING_NO_TREES:
            self.surface_blocks[Criteria.MOTION_BLOCKING_NO_TREES] = self._get_blocks_no_trees()
            return self.surface_blocks[Criteria.MOTION_BLOCKING_NO_TREES]

        surface = BlockList()
        heightmap = self.get_heightmap(criteria)

        for x, rest in enumerate(heightmap):
            for z, h in enumerate(rest):
                coordinates = Coordinates(self.start.x + x, h - 1, self.start.z + z)
                surface.append(self.get_block_at(*coordinates))

        self.surface_blocks[criteria] = surface
        return surface

    def _get_blocks_no_trees(self) -> BlockList:
        """Return a list of block representing a heightmap without trees

        It is not perfect as sometimes, there can be flower or grass or other blocks between the ground and the '
        floating' logs, but it is good enough for our use"""
        surface = BlockList()
        heightmap = self.get_heightmap(Criteria.MOTION_BLOCKING_NO_LEAVES)

        for x, rest in enumerate(heightmap):
            for z, h in enumerate(rest):
                base_coord = Coordinates(self.start.x + x, h - 1, self.start.z + z)
                ground_coord = base_coord
                for ground_coord in self._yield_until_ground(base_coord):
                    ground_coord = ground_coord.shift(0, -1, 0)
                surface.append(self.get_block_at(*ground_coord))

        self.surface_blocks[Criteria.MOTION_BLOCKING_NO_TREES] = surface
        return surface

    def remove_trees(self) -> None:
        """Remove all plants at the surface of the current plot"""
        pattern = ('log', 'bush', 'mushroom')
        surface = self.get_blocks(Criteria.MOTION_BLOCKING_NO_LEAVES)

        amount = 0
        unwanted_blocks = surface.filter(pattern)

        print(f'\n=> Removing trees on plot at {self.start} with size {self.size}')
        while unwanted_blocks:
            block = unwanted_blocks.pop()
            for coord in self._yield_until_ground(block.coordinates):
                INTF.placeBlock(*coord, 'minecraft:air')
                amount += 1

        INTF.sendBlocks()
        print(f'=> Deleted {amount} blocs\n')
        self.update()

    def _yield_until_ground(self, coordinates: Coordinates, match_of_not_ground: tuple[str, ...] = ('air', 'leaves',
                                                                                                    'log', 'vine')):
        """Yield the coordinates """
        current_coord: Coordinates = coordinates
        while self.get_block_at(*current_coord).is_one_of(match_of_not_ground):
            yield current_coord
            current_coord = current_coord.shift(0, -1, 0)

    def __contains__(self, coordinates: Coordinates) -> bool:
        """Return true if the current plot contains the given coordinates"""
        return \
            self.start.x <= coordinates.x < self.end.x and \
            self.start.y <= coordinates.y < self.end.y and \
            self.start.z <= coordinates.z < self.end.z
