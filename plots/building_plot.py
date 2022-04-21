from typing import Tuple

from plots.plot import Plot
from utils.coordinates import Coordinates
from utils.criteria import Criteria
from gdpc import geometry as GEO
from gdpc import interface as INTF


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

        start_y = self.get

        # body
        GEO.placeCuboid(self.start.x, self.start.y, self.start.z, self.start.x + self.size[0] - 1,
                        self.start.y + height - 1, self.start.z + self.size[2] - 1,
                        main_bloc, hollow=True)

        # Todo : add direction
        # Door
        INTF.placeBlock(self.start.x + self.size[0] // 2, self.start.y + 1, self.start.z, "oak_door")
        INTF.placeBlock(self.start.x + self.size[0] // 2, self.start.y + 2, self.start.z, "oak_door[half=upper]")
        INTF.sendBlocks()