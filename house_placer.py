from typing import Dict, Tuple

from gdpc import geometry as GEO
from gdpc import interface as INTF

import random
import time

from build_area import Plot
from utils import Coordinates, Block


class ConstructionPlot(Plot):
    _WORST_SCORE = 100_000_000

    def __init__(self, x: int, z: int, size: Tuple[int, int], construction_roof: int = 200):
        super().__init__(x, z, size)

        self.construction_roof = construction_roof
        self.occupied_coords = set()

        self.foundation_blocks: dict[Coordinates, Block] = dict()

    def _build_foundation_blocks(self) -> None:
        surface_blocks = dict()
        heightmap = self.get_heightmap("MOTION_BLOCKING_NO_LEAVES")

        for x, rest in enumerate(heightmap):
            for z, h in enumerate(rest):
                coordinates = Coordinates(self.start.x + x, h - 1, self.start.z + z)
                if coordinates in self.occupied_coords:
                    continue

                block = self.get_block_at(*coordinates)
                if not block.is_one_of(["water"]):
                    # We 'cancel' the Y in the dict, so we can access the neighbouring blocks later without knowing their Y
                    surface_blocks[coordinates.with_y(0)] = self.get_block_at(*coordinates)

        self.foundation_blocks =  surface_blocks

    def get_construction_spot(self):
        self._build_foundation_blocks()

    def _get_score(self, coord: Coordinates, size: Tuple[int, int]):
        # We don't want to be too high in the sky
        if coord.y > self.construction_roof:
            return ConstructionPlot._WORST_SCORE

        # apply malus to score depending on the distance to the 'center'
        score = coord.distance(self.center) * .1

        # Score = sum of difference between the first point's altitude and the other
        for x in range(size[0]):
            for z in range(size[1]):
                try:
                    current = coord.shift(x, 0, z)

                    score += abs(coord.y - self.foundation_blocks[current].coordinates.y)
                except IndexError:
                    # Out of bound :3
                    return ConstructionPlot._WORST_SCORE


def get_best_area(plot: Plot, occupied_coord, speed: int = 4, roof: int = 200):
    """Return the best coordinates to place a building of a certain size, minimizing its score.
    Score is defined by get_score function.

    heightmap
    """
    # Init best score, the lower the better, so we put it quite big at the start (normal scores should stay lower than 1000)
    coords = list(plot.get_blocks_at_surface("MOTION_BLOCKING_NO_LEAVES").keys())

    best_score = 100_000_000
    best_coord = coords[0]

    # Speed factor will make it only iterate over "len(heightmap) / speed" coords
    for coord in coords[::speed]:
        score = get_score(coord, plot, occupied_coord, size, roof)

        if score < best_score:
            best_score = score
            best_coord = coord

    # Return the minimal score
    return best_coord


def get_score(coord, plot: Plot, occupied_coord, size, roof):
    """Return a score evaluating the fitness of a building in an area.
    The lower the score, the better it fits"""



    height, width = size
    x, z = coord
    coord_high = heightmap[coord]

    # We don't want to be too high in the sky
    if coord_high > roof:
        return 100_000_000

    # apply bonus to score depending on the distance to the 'center'
    score = distance(coord, plot.center) * .1
    # Score = sum of difference between the first point's altitude and the other
    for i in range(height):
        for j in range(width):
            try:
                current = (x + i, z + j)
                if current in occupied_coord:
                    # Bad luck I guess :3
                    return 100_000_000
                score += abs(coord_high - heightmap[current])
            except IndexError:
                # Out of bound :3
                return 100_000_000

    return score



def build_simple_house(main_bloc: str, start: tuple[int, int, int], size: tuple[int, int, int]):
    """Build a 'house' of the main_bloc given, with north-west bottom corner as starting point, with the given size"""
    # Todo : finish the simple houses
    # body
    GEO.placeCuboid(start[0], start[1], start[2], start[0] + size[0] - 1, start[1] + size[1] - 1, start[2] + size[2] - 1,
                    main_bloc, hollow=True)
    INTF.sendBlocks()
    # Todo : add direction
    # Door
    INTF.placeBlock(start[0] + size[0] // 2, start[1] + 1, start[2], "oak_door")
    INTF.placeBlock(start[0] + size[0] // 2, start[1] + 2, start[2], "oak_door[half=upper]")


def place_houses(plot: Plot, amount: int, main_block: str):
    """More of a test function.
    Place a certain amount (20 at the moment) of randomly sized house in the build area, at the most convenient spots
    possible
    """
    occupied_spots = set()
    h_map = plot.get_heightmap('MOTION_BLOCKING_NO_LEAVES')
    OFFSETX = buildArea.ENDX - buildArea.STARTX
    OFFSETZ = buildArea.ENDZ - buildArea.STARTZ
    center = (OFFSETX // 2, OFFSETZ // 2)
    coords_indices = [(x, z) for x in range(OFFSETX) for z in range(OFFSETZ)]
    house_padding = 2

    for i in range(amount):
        iter_start = time.time()
        build_size = random.randint(5, 20), random.randint(4, 15), random.randint(5, 20)

        speed_factor = max(build_size) // 5
        best = get_best_area(h_map, coords_indices, center, occupied_spots, (build_size[0], build_size[2]), speed=speed_factor)
        best = (best[0] + buildArea.STARTX, best[1] + buildArea.STARTZ)

        house_start = (best[0], h_map[best], best[1])

        for x in range(-house_padding, build_size[0] + house_padding):
            for z in range(-house_padding, build_size[2] + house_padding):
                occupied_spots.add((house_start[0] + x, house_start[2] + z))

        build_simple_house(main_block, house_start, build_size)
        print(f"Placed house of size {build_size} at {best} in {time.time() - iter_start:.2f}s with speed {speed_factor}")

