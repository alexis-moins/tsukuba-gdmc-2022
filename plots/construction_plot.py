import random
from typing import Dict, Tuple, Set

import numpy as np
from gdpc import geometry as GEO
from gdpc import interface as INTF

from plots.plot import Plot
from utils.block import Block
from utils.coordinates import Coordinates
from utils.criteria import Criteria


class ConstructionPlot(Plot):
    _WORST_SCORE = 100_000_000

    def __init__(self, x: int, z: int, size: Tuple[int, int], construction_roof: int = 200):
        super().__init__(x, z, size)

        self.construction_roof = construction_roof
        # Surface word here is to precise that we are working
        self.occupied_coords_surface: Set[Coordinates] = set()
        self.foundation_blocks_surface: Dict[Coordinates, Block] = dict()

    def _build_foundation_blocks(self) -> None:
        surface_blocks = dict()
        self._construction_heightmap = self.get_heightmap(Criteria.MOTION_BLOCKING_NO_LEAVES)

        for x, rest in enumerate(self._construction_heightmap):
            for z, h in enumerate(rest):
                coordinates = Coordinates(self.start.x + x, h - 1, self.start.z + z)

                if coordinates.as_2D() in self.occupied_coords_surface:
                    continue

                block = self.get_block_at(*coordinates)

                # We don't want to be on water or too high in the sky
                if not block.is_one_of(["water"]) and block.coordinates.y < self.construction_roof:

                    surface_blocks[coordinates.as_2D()] = self.get_block_at(*coordinates)

        self.foundation_blocks_surface = surface_blocks

    def get_construction_spot(self, size: Tuple[int, int], speed: int = None) -> Coordinates:
        """Return the best coordinates to place a building of a certain size, minimizing its score.
            Score is defined by get_score function.

            heightmap
            """
        if speed is None:
            # Auto speed depends on structure size, and is at least 1
            # Todo : Should depend on plot size too
            # speed = max(max(size[0], size[1]) // 5, 1)
            # print(f"Auto determined speed {speed} for house of size {size}")
            speed = 1

        # This will update the foundation_block dict, as well as the _construction_heightmap
        self._build_foundation_blocks()

        # DEBUG
        colors = ['green', 'pink', 'magenta', 'lime', 'yellow', 'orange', 'purple', 'gray', 'white']
        random.shuffle(colors)
        for coord_2d in self.foundation_blocks_surface:
            INTF.placeBlock(*self.foundation_blocks_surface[coord_2d].coordinates, colors[0] + '_wool')

        INTF.sendBlocks()
        # END DEBUG


        keys_list = list(self.foundation_blocks_surface.keys())

        # >Get the minimal score in the coordinate list
        min_score = ConstructionPlot._WORST_SCORE
        best_coord_2d = keys_list[0]

        for coord_2d in keys_list[::speed]:
            coord_score = self._get_score(coord_2d, size)

            if coord_score < min_score:
                best_coord_2d = coord_2d
                min_score = coord_score

        print(f'Best score : {min_score}')

        return self.foundation_blocks_surface[best_coord_2d].coordinates

    def _get_score(self, coord_2d: Coordinates, size: Tuple[int, int]) -> float:
        """Return a score evaluating the fitness of a building in an area.
            The lower the score, the better it fits

            Score is calculated as follows :
            malus depending on the distance from the center of the area +
            Sum of all differences in the y coordinate
            """
        # apply malus to score depending on the distance to the 'center'
        # Todo : Maybe improve this notation, quite not beautiful, set center as a coordinate ? Would be great
        score = coord_2d.distance(Coordinates(self.center[0], 0, self.center[1])) * .1

        evaluated_coord_y = self.foundation_blocks_surface[coord_2d].coordinates.y

        # Score = sum of difference between the first point's altitude and the other
        for x in range(size[0]):
            for z in range(size[1]):
                try:
                    current = coord_2d.shift(x, 0, z)
                    current_y = self.foundation_blocks_surface[current].coordinates.y

                    score += abs(evaluated_coord_y - current_y)

                except KeyError:
                    # Out of bound :3
                    return ConstructionPlot._WORST_SCORE
        return score

    def occupy_area(self, origin: Coordinates, size: Tuple[int, int], padding: int = 0) -> None:
        """Set all the coordinates in the size given, starting from the origin, and in the padding, as occupied, and so
        unusable as foundations for other constructions"""
        for x in range(-padding, size[0] + padding):
            for z in range(-padding, size[1] + padding):

                coord_2d = origin.shift(x, 0, z).as_2D()
                if coord_2d in self:
                    self.occupied_coords_surface.add(coord_2d)

        for coord_2d in self.occupied_coords_surface:
            try:
                INTF.placeBlock(*self.foundation_blocks_surface[coord_2d].coordinates, 'red_wool')
            except KeyError:
                pass
        INTF.sendBlocks()


def build_simple_house(main_bloc: str, start: Coordinates, size: tuple[int, int, int]):
    """Build a 'house' of the main_bloc given, with north-west bottom corner as starting point, with the given size"""
    # Todo : finish the simple houses
    # body
    GEO.placeCuboid(start.x, start.y, start.z, start.x + size[0] - 1, start.y + size[1] - 1, start.z + size[2] - 1,
                    main_bloc, hollow=True)

    # Todo : add direction
    # Door
    INTF.placeBlock(start.x + size[0] // 2, start.y + 1, start.z, "oak_door")
    INTF.placeBlock(start.x + size[0] // 2, start.y + 2, start.z, "oak_door[half=upper]")
    INTF.sendBlocks()
