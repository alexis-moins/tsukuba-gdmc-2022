from gdpc import geometry as GEO
from gdpc import interface as INTF

import random
import time


def get_best_area(heightmap, coords, center, occupied_coord, size, speed: int = 4, roof: int = 200):
    """Return the best coordinates to place a building of a certain size, minimizing its score.
    Score is defined by get_score function
    """
    # Init best score, the lower the better, so we put it quite big at the start (normal scores should stay lower than 1000)
    best_score = 100_000_000
    best_coord = coords[0]

    # Speed factor will make it only iterate over "len(heightmap) / speed" coords
    for coord in coords[::speed]:
        score = get_score(coord, center, heightmap, occupied_coord, size, roof)

        if score < best_score:
            best_score = score
            best_coord = coord

    return best_coord


def get_score(coord, center, heightmap, occupied_coord, size, roof):
    height, width = size
    x, z = coord
    coord_high = heightmap[coord]

    # We don't want to be too high in the sky
    if coord_high > roof:
        return 100_000_000

    # apply bonus to score depending on the distance to the 'center'
    score = distance(coord, center) * .1
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


def distance(a, b):
    """Return the Manhattan distance between two 2D points"""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def build_simple_house(main_bloc, start: tuple[int, int, int], size: tuple[int, int, int]):
    # Todo : finish the simple houses
    # body
    GEO.placeCuboid(start[0], start[1], start[2], start[0] + size[0] - 1, start[1] + size[1] - 1, start[2] + size[2] - 1,
                    main_bloc, hollow=True)
    INTF.sendBlocks()
    # Todo : add direction
    # Door
    INTF.placeBlock(start[0] + size[0] // 2, start[1] + 1, start[2], "oak_door")
    INTF.placeBlock(start[0] + size[0] // 2, start[1] + 2, start[2], "oak_door[half=upper]")


def place_houses(buildArea, main_block):
    occupied_spots = set()
    h_map = buildArea.WORLDSLICE.heightmaps['MOTION_BLOCKING_NO_LEAVES']
    OFFSETX = buildArea.ENDX - buildArea.STARTX
    OFFSETZ = buildArea.ENDZ - buildArea.STARTZ
    center = (OFFSETX // 2, OFFSETZ // 2)
    coords_indices = [(x, z) for x in range(OFFSETX) for z in range(OFFSETZ)]
    house_padding = 2

    for i in range(20):
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

