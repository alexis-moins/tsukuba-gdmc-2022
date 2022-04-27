from __future__ import annotations

import random
from typing import Dict, Tuple, Set

import numpy as np
from gdpc import geometry as GEO
from gdpc import interface as INTF


import launch_env
from modules.blocks.block import Block

from modules.plots.plot import Plot
from modules.plots.construction_plot import ConstructionPlot

from modules.utils.criteria import Criteria
from modules.utils.coordinates import Coordinates


class SuburbPlot(Plot):
    _WORST_SCORE = 100_000_000

    def __init__(self, x: int, z: int, size: Tuple[int, int], construction_roof: int = 200):
        super().__init__(x, z, size)

        self.construction_roof = construction_roof
        # Surface word here is to precise that we are working
        self.occupied_coords_surface: Set[Coordinates] = set()
        self.foundation_blocks_surface: Dict[Coordinates, Block] = dict()

        self.steep_map = None

    @staticmethod
    def _delta_sum(values: list, base: int):
        return sum(abs(base - v) for v in values)

    def compute_steep_map(self, span: int = 1):
        heightmap: np.ndarray = self.get_heightmap(Criteria.MOTION_BLOCKING_NO_LEAVES)
        shape = heightmap.shape
        print(f'default shape : {shape}')

        steep = np.empty(shape=(self.size[0] - 2 * span, self.size[1] - 2 * span))
        for i in range(span, self.size[0] - span):
            for j in range(span, self.size[1] - span):
                steep[i - span, j - span] = self._delta_sum(heightmap[i - span: i + 1 + span, j - span: j + 1 + span].flatten(), heightmap[i, j])

        print(steep)
        print(steep.shape)

        flat_steep = steep.flatten()

        ind_of_mins = np.argpartition(flat_steep, 20)[:20]
        print(f'indexes of mins {ind_of_mins}')
        print(f'values of mins {flat_steep[ind_of_mins]}')





    def _build_foundation_blocks(self) -> None:
        self.foundation_blocks_surface = {b.coordinates.as_2D(): b for b in filter(self._is_block_valid,
                                                                                   self.get_blocks(
                                                                                       Criteria.MOTION_BLOCKING_NO_LEAVES))}

    def _is_block_valid(self, b):
        return b.coordinates.y < self.construction_roof and not b.is_one_of(
            ["water"]) and b.coordinates.as_2D() not in self.occupied_coords_surface

    def get_construction_plot(self, area: Tuple[int, int], padding: int = 3, speed: int = None, max_score: int = 500) -> ConstructionPlot | None:
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
        if launch_env.DEBUG:
            colors = ['green', 'pink', 'magenta', 'lime', 'yellow', 'orange', 'purple', 'gray', 'white']
            random.shuffle(colors)
            for coord_2d in self.foundation_blocks_surface:
                INTF.placeBlock(*self.foundation_blocks_surface[coord_2d].coordinates, colors[0] + '_wool')

            INTF.sendBlocks()
        # END DEBUG

        keys_list = list(self.foundation_blocks_surface.keys())

        # >Get the minimal score in the coordinate list
        min_score = SuburbPlot._WORST_SCORE
        best_coord_2d = keys_list[0]

        for coord_2d in keys_list[::speed]:
            coord_score = self._get_score(coord_2d, area)

            if coord_score < min_score:
                best_coord_2d = coord_2d
                min_score = coord_score

        if launch_env.DEBUG:
            print(f'Best score : {min_score}')

        if min_score > max_score:
            return None

        best_coord = self.foundation_blocks_surface[best_coord_2d].coordinates

        self.occupy_area(best_coord, area, padding)

        return ConstructionPlot(x=best_coord_2d.x, z=best_coord_2d.z, size=area, build_start=best_coord)

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
                    return SuburbPlot._WORST_SCORE
        return score

    def occupy_area(self, origin: Coordinates, size: Tuple[int, int], padding: int = 0) -> None:
        """Set all the coordinates in the size given, starting from the origin, and in the padding, as occupied, and so
        unusable as foundations for other constructions"""
        for x in range(-padding, size[0] + padding):
            for z in range(-padding, size[1] + padding):

                coord_2d = origin.shift(x, 0, z).as_2D()
                if coord_2d in self:
                    self.occupied_coords_surface.add(coord_2d)

        # ONLY FOR DEBUG :D
        if launch_env.DEBUG:
            for coord_2d in self.occupied_coords_surface:
                try:
                    INTF.placeBlock(*self.foundation_blocks_surface[coord_2d].coordinates, 'red_wool')
                except KeyError:
                    pass
            INTF.sendBlocks()



