from typing import Dict

from gdpc import geometry as GEO
from gdpc import interface as INTF
from gdpc import toolbox as TB
from gdpc import worldLoader as WL

from utils import Block, get_block_at

STARTX, STARTY, STARTZ, ENDX, ENDY, ENDZ = INTF.requestBuildArea()

WORLDSLICE = WL.WorldSlice(STARTX, STARTZ, ENDX + 1, ENDZ + 1)
heightmap = WORLDSLICE.heightmaps["MOTION_BLOCKING"]


def get_most_used_block_of_type(block_type: str, blocks: Dict[str, int]) -> str | None:
    """Return the block of the given type most represented in the given frequency dict"""
    iterator = filter(lambda k: block_type in k, blocks.keys())
    dicti = {key: blocks[key] for key in list(iterator)}

    if not dicti:
        return None

    return max(dicti, key=dicti.get)




def get_surface_blocks_count(world: WORLDSLICE) -> Dict[str, int]:
    """"""
    surface_blocks = dict()
    for x, rest in enumerate(world.heightmaps['MOTION_BLOCKING_NO_LEAVES']):
        for z, h in enumerate(rest):
            block = world.getBlockAt(STARTX + x, h - 1, STARTZ + z)
            if not block in surface_blocks.keys():
                surface_blocks[block] = 0
            surface_blocks[block] += 1

    return surface_blocks





def get_best_area(heightmap, coords, center, occupied_coord, size, speed=4, roof=200):

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


# Manhattan, you can tweak it later if you want
def distance(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def build_simple_house(main_bloc, start: tuple[int, int, int], size: tuple[int, int, int]):
    # Todo : finish the simple houses
    # body
    GEO.placeCuboid(start[0], start[1], start[2], start[0] + size[0] - 1, start[1] + size[1] - 1, start[2] + size[2] - 1,
                    "oak_planks", hollow=True)
    INTF.sendBlocks()
    # Todo : add direction
    # Door
    INTF.placeBlock(start[0] + size[0] // 2, start[1] + 1, start[2], "oak_door")
    INTF.placeBlock(start[0] + size[0] // 2, start[1] + 2, start[2], "oak_door[half=upper]")


def place_houses(main_block):
    occupied_spots = set()
    h_map = WORLDSLICE.heightmaps['MOTION_BLOCKING_NO_LEAVES']
    OFFSETX = ENDX - STARTX
    OFFSETZ = ENDZ - STARTZ
    center = (OFFSETX // 2, OFFSETZ // 2)
    coords_indices = [(x, z) for x in range(OFFSETX) for z in range(OFFSETZ)]
    house_padding = 2

    for i in range(20):
        iter_start = time.time()
        build_size = random.randint(5, 20), random.randint(4, 15), random.randint(5, 20)

        speed_factor = max(build_size) // 5
        best = get_best_area(h_map, coords_indices, center, occupied_spots, (build_size[0], build_size[2]), speed=speed_factor)
        best = (best[0] + STARTX, best[1] + STARTZ)

        house_start = (best[0], h_map[best], best[1])

        for x in range(-house_padding, build_size[0] + house_padding):
            for z in range(-house_padding, build_size[2] + house_padding):
                occupied_spots.add((house_start[0] + x, house_start[2] + z))

        build_simple_house(main_block, house_start, build_size)
        print(f"Placed house of size {build_size} at {best} in {time.time() - iter_start:.2f}s with speed {speed_factor}")

if __name__ == '__main__':
    # NOTE: It is a good idea to keep this bit of the code as simple as
    #     possible so you can find mistakes more easily

    try:

        height = heightmap[(STARTX, STARTY)]
        INTF.runCommand(f"tp @a {STARTX} {height} {STARTZ}")
        print(f"/tp @a {STARTX} {height} {STARTZ}")

        global most_used_block
        surface_blocks = get_surface_blocks_count(WORLDSLICE)
        most_used_block = get_most_used_block_of_type('log', surface_blocks)

        print(f'most used wood: {most_used_block}')

        surface_blocks = list()
        for x, rest in enumerate(WORLDSLICE.heightmaps['MOTION_BLOCKING']):
            for z, h in enumerate(rest):
                block = get_block_at(STARTX + x, h - 1, STARTZ + z)
                surface_blocks.append(block)

            block = get_block_at(STARTX + x, h - 1, STARTZ + z, WORLDSLICE)
            surface_blocks.append(block)

        while wood_blocks:
            block = wood_blocks.pop(0)

            block_below = get_block_at(*block.coordinates_below)
            if block_below.is_one_of(['leaves', 'air', 'log']):
                wood_blocks.append(block_below)

        for coordinates in block.neighbouring_coordinates():
            block_below = get_block_at(*coordinates, WORLDSLICE)

            if block_below.is_one_of(['leaves', 'log']):
                wood_blocks.append(block_below)

        INTF.placeBlock(*block.coordinates, 'air')
        print(f'Deleted block {block}')
        main_building_block = str(most_used_block)
        if 'log' in most_used_block:
            main_building_block = main_building_block.replace('log', 'planks')

        place_houses(main_building_block)

        # buildPerimeter()
        # buildRoads()
        # buildCity()

        print("Done!")
    except KeyboardInterrupt:   # useful for aborting a run-away program
        print("Pressed Ctrl-C to kill program.")
