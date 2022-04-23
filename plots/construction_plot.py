from __future__ import annotations

from re import Match
from typing import Dict, Tuple

from gdpc import geometry as GEO
from gdpc import interface as INTF

from plots.plot import Plot

from utils.criteria import Criteria
from utils.structure import Structure
from utils.coordinates import Coordinates


class ConstructionPlot(Plot):

    def __init__(self, x: int, z: int, size: Tuple[int, int], build_start: Coordinates):
        super().__init__(x, z, size)
        self.build_start = build_start

    def build_foundation(self, foundation_level: int, main_block: str = 'stone_bricks') -> None:

        for coord in self._iterate_over_air(foundation_level):
            INTF.placeBlock(*coord, main_block)
        INTF.sendBlocks()

    def _iterate_over_air(self, max_y: int) -> Coordinates:
        for block in self.get_blocks_at_surface(Criteria.WORLD_SURFACE):
            y_shift = 1
            while block.coordinates.y + y_shift <= max_y:
                yield block.coordinates.shift(0, y_shift, 0)
                y_shift += 1

    def build_simple_house(self, main_bloc: str, height: int):
        """Build a 'house' of the main_bloc given, with north-west bottom corner as starting point, with the given size"""
        # Todo : finish the simple house

        self.build_foundation(self.build_start.y - 1)

        # body
        GEO.placeCuboid(self.build_start.x, self.build_start.y, self.build_start.z, self.build_start.x + self.size[0] - 1,
                        self.build_start.y + height - 1, self.build_start.z + self.size[1] - 1,
                        main_bloc, hollow=True)

        # Todo : add direction
        # Door
        INTF.placeBlock(self.build_start.x + self.size[0] // 2, self.build_start.y + 1, self.build_start.z, "oak_door")
        INTF.placeBlock(self.build_start.x + self.size[0] // 2,
                        self.build_start.y + 2, self.build_start.z, "oak_door[half=upper]")
        INTF.sendBlocks()

    def build(self, structure: Structure, materials: Dict[str, str] = None) -> bool:
        """Build the given structure onto the current construction spot"""
        blocks = structure.get_blocks_for(self)

        # TODO
        # if materials:
        #     blocks = [block.convert(materials) for block in blocks]

        for block in blocks:
            INTF.placeBlock(*block.coordinates, block.name)

        INTF.sendBlocks()
