from __future__ import annotations

from typing import Dict, Tuple

from gdpc import geometry as GEO
from gdpc import interface as INTF

from plots.plot import Plot

from utils.criteria import Criteria
from utils.structure import Structure
from utils.coordinates import Coordinates


class ConstructionPlot(Plot):

    def __init__(self, x: int, z: int, size: Tuple[int, int], build_start: Coordinates):
        """"""
        super().__init__(x, z, size)
        self.build_start = build_start

    def build_foundation(self, foundation_level: int, main_block: str = 'stone_bricks') -> None:
        """"""
        for coord in self._iterate_over_air(foundation_level):
            INTF.placeBlock(*coord, main_block)
        INTF.sendBlocks()

    def _iterate_over_air(self, max_y: int) -> Coordinates:
        for block in self.get_blocks(Criteria.WORLD_SURFACE):
            y_shift = 1
            while block.coordinates.y + y_shift <= max_y:
                yield block.coordinates.shift(0, y_shift, 0)
                y_shift += 1

    def build(self, structure: Structure, materials: Dict[str, str] = None, rotation=0) -> None:
        """Build the given structure onto the current construction spot"""
        self.build_foundation(self.build_start.y - 1)
        blocks = structure.get_blocks(plot=self, materials=materials, angle=rotation)

        for block in blocks:
            INTF.placeBlock(*block.coordinates, block.full_name)

        INTF.sendBlocks()
