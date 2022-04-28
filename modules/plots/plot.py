from __future__ import annotations
from typing import Generator

from numpy import ndarray
from gdpc import interface as INTF

import random
import launch_env
from modules.utils.criteria import Criteria
from modules.utils.coordinates import Coordinates, Size

from modules.blocks.block import Block
from modules.blocks.collections.block_list import BlockList

from modules.utils.loader import WORLD, BUILD_AREA, update_world_slice


class Plot:
    """Class representing a plot"""

    def __init__(self, x: int, y: int, z: int, size: Size) -> None:
        """Parameterised constructor creating a new plot inside the build area"""
        self.start = Coordinates(x, y, z)
        self.end = Coordinates(x + size.x, 255, z + size.z)
        self.size = size

        self.occupied_coordinates: set[Coordinates] = set()

        self.surface_blocks: dict[Criteria, BlockList] = {}
        self.offset = self.start - BUILD_AREA.start, self.end - BUILD_AREA.start

        # TODO change center into coordinates
        self.center = self.start.x + self.size.x // 2, self.start.z + self.size.z // 2

    @staticmethod
    def from_coordinates(start: Coordinates, end: Coordinates) -> Plot:
        """Return a new plot created from the given start and end coordinates"""
        return Plot(*start, Size.from_coordinates(start, end))

    def update(self) -> None:
        """Update the world slice and most importantly the heightmaps"""
        update_world_slice()
        self.surface_blocks.clear()

    def visualize(self, ground: str = 'orange_wool', criteria: Criteria = Criteria.MOTION_BLOCKING_NO_TREES) -> None:
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

        surface = []
        heightmap = self.get_heightmap(criteria)

        for x, rest in enumerate(heightmap):
            for z, h in enumerate(rest):
                coordinates = Coordinates(self.start.x + x, h - 1, self.start.z + z)
                surface.append(self.get_block_at(*coordinates))

        self.surface_blocks[criteria] = surface
        return BlockList(surface)

    def _get_blocks_no_trees(self) -> BlockList:
        """Return a list of block representing a heightmap without trees

        It is not perfect as sometimes, there can be flower or grass or other blocks between the ground and the '
        floating' logs, but it is good enough for our use"""
        surface = []
        heightmap = self.get_heightmap(Criteria.MOTION_BLOCKING_NO_LEAVES)

        for x, rest in enumerate(heightmap):
            for z, h in enumerate(rest):
                base_coord = Coordinates(self.start.x + x, h - 1, self.start.z + z)
                ground_coord = base_coord
                for ground_coord in self.__yield_until_ground(base_coord):
                    ground_coord = ground_coord.shift(0, -1, 0)
                surface.append(self.get_block_at(*ground_coord))

        self.surface_blocks[Criteria.MOTION_BLOCKING_NO_TREES] = surface
        return BlockList(surface)

    def get_subplot(self, size: Size, padding: int = 5, speed: int = 200, max_score: int = 500) -> Plot | None:
        """Return the best coordinates to place a building of a certain size, minimizing its score"""

        # TODO add .lower_than(max_height=200)
        surface = self.get_blocks(Criteria.MOTION_BLOCKING_NO_TREES)
        surface = surface.without('water').not_inside(self.occupied_coordinates)

        # DEBUG
        if launch_env.DEBUG:
            colors = ['magenta', 'lime', 'orange', 'purple', 'white']
            random.shuffle(colors)
            for block in surface:
                INTF.placeBlock(*block.coordinates, colors[0] + '_wool')

            INTF.sendBlocks()

        # >Get the minimal score in the coordinate list
        min_score = max_score

        for block in surface[::speed]:
            block_score = self.__get_score(block.coordinates, surface, size)

            if block_score < min_score:
                best_coordinates = block.coordinates
                min_score = block_score

        if launch_env.DEBUG:
            print(f'Best score : {min_score}')

        if min_score >= max_score:
            return None

        sub_plot = Plot(*best_coordinates, size=size)

        for coordinates in sub_plot:
            self.occupied_coordinates.add(coordinates.as_2D())

        return sub_plot

    def __get_score(self, coordinates: Coordinates, surface: BlockList, size: Size) -> float:
        """Return a score evaluating the fitness of a building in an area.
            The lower the score, the better it fits

            Score is calculated as follows :
            malus depending on the distance from the center of the area +
            Sum of all differences in the y coordinate
            """
        # apply malus to score depending on the distance to the 'center'

        # TODO Maybe improve this notation, quite not beautiful, set center as a coordinate ?
        # Would be great
        center = Coordinates(self.center[0], 0, self.center[1])
        score = coordinates.as_2D().distance(center) * .1

        # Score = sum of difference between the first point's altitude and the other
        for x in range(size.x):
            for z in range(size.z):
                current_coord = coordinates.shift(x, 0, z)
                current_block = surface.find(current_coord)

                if not current_block:
                    return 100_000_000

                score += abs(coordinates.y - current_block.coordinates.y)

        return score

    def remove_trees(self) -> None:
        """Remove all plants at the surface of the current plot"""
        pattern = ('log', 'bush', 'mushroom')
        surface = self.get_blocks(Criteria.MOTION_BLOCKING_NO_LEAVES)

        amount = 0
        unwanted_blocks = surface.filter(pattern).to_set()
        print(f'\n=> Removing trees on plot at {self.start} with size {self.size}')
        while unwanted_blocks:
            block = unwanted_blocks.pop()
            for coord in self.__yield_until_ground(block.coordinates):
                INTF.placeBlock(*coord, 'minecraft:air')
                amount += 1

        INTF.sendBlocks()
        print(f'=> Deleted {amount} blocs\n')
        self.update()

    def __yield_until_ground(self, coordinates: Coordinates):
        """Yield the coordinates """
        current_coord: Coordinates = coordinates
        while self.get_block_at(*current_coord).is_one_of(('air', 'leaves', 'log', 'vine')):
            yield current_coord
            current_coord = current_coord.shift(0, -1, 0)

    def build_foundation(self, block: str = 'minecraft:stone_bricks') -> None:
        """"""
        for coord in self.__iterate_over_air(self.start.y - 1):
            INTF.placeBlock(*coord, block)
        INTF.sendBlocks()

    def __iterate_over_air(self, max_y: int) -> Coordinates:
        for block in self.get_blocks(Criteria.WORLD_SURFACE):
            y_shift = 1
            while block.coordinates.y + y_shift <= max_y:
                yield block.coordinates.shift(0, y_shift, 0)
                y_shift += 1

    def __contains__(self, coordinates: Coordinates) -> bool:
        """Return true if the current plot contains the given coordinates"""
        return self.start.x <= coordinates.x < self.end.x and \
            self.start.y <= coordinates.y < self.end.y and \
            self.start.z <= coordinates.z < self.end.z

    def __iter__(self) -> Generator[Coordinates]:
        """Return a generator over the coordinates of the current plot"""
        padding = 5
        for x in range(-padding, self.size.x + padding):
            for z in range(-padding, self.size.z + padding):
                yield self.start.shift(x, 0, z)