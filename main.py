import random
import time
from random import randint

from gdpc import geometry as GEO
from gdpc import interface as INTF
from gdpc import toolbox as TB
from gdpc import worldLoader as WL

STARTX, STARTY, STARTZ, ENDX, ENDY, ENDZ = INTF.requestBuildArea()  # BUILDAREA

# WORLDSLICE
# Using the start and end coordinates we are generating a world slice
# It contains all manner of information, including heightmaps and biomes
# For further information on what information it contains, see
#     https://minecraft.fandom.com/wiki/Chunk_format
#
# IMPORTANT: Keep in mind that a wold slice is a 'snapshot' of the world,
#   and any changes you make later on will not be reflected in the world slice
WORLDSLICE = WL.WorldSlice(STARTX, STARTZ,
                           ENDX + 1, ENDZ + 1)  # this takes a while

ROADHEIGHT = 0

# === STRUCTURE #3
# Here we are defining all of our functions to keep our code organised
# They are:
# - buildPerimeter()
# - buildRoads()
# - buildCity()


def buildPerimeter():
    """Build a wall along the build area border.
    In this function we're building a simple wall around the build area
        pillar-by-pillar, which means we can adjust to the terrain height
    """
    # HEIGHTMAP
    # Heightmaps are an easy way to get the uppermost block at any coordinate
    # There are four types available in a world slice:
    # - 'WORLD_SURFACE': The top non-air blocks
    # - 'MOTION_BLOCKING': The top blocks with a hitbox or fluid
    # - 'MOTION_BLOCKING_NO_LEAVES': Like MOTION_BLOCKING but ignoring leaves
    # - 'OCEAN_FLOOR': The top solid blocks
    heights = WORLDSLICE.heightmaps["MOTION_BLOCKING_NO_LEAVES"]

    print("Building east-west walls...")
    # building the east-west walls

    for x in range(STARTX, ENDX + 1):
        # the northern wall
        y = heights[(x, STARTZ)]
        GEO.placeCuboid(x, y - 2, STARTZ, x, y, STARTZ, "granite")
        GEO.placeCuboid(x, y + 1, STARTZ, x, y + 4, STARTZ, "granite_wall")
        # the southern wall
        y = heights[(x, ENDZ)]
        GEO.placeCuboid(x, y - 2, ENDZ, x, y, ENDZ, "red_sandstone")
        GEO.placeCuboid(x, y + 1, ENDZ, x, y + 4, ENDZ, "red_sandstone_wall")

    print("Building north-south walls...")
    # building the north-south walls
    for z in range(STARTZ, ENDZ + 1):
        # the western wall
        y = heights[(STARTX, z)]
        GEO.placeCuboid(STARTX, y - 2, z, STARTX, y, z, "sandstone")
        GEO.placeCuboid(STARTX, y + 1, z, STARTX, y + 4, z, "sandstone_wall")
        # the eastern wall
        y = heights[(ENDX, z)]
        GEO.placeCuboid(ENDX, y - 2, z, ENDX, y, z, "prismarine")
        GEO.placeCuboid(ENDX, y + 1, z, ENDX, y + 4, z, "prismarine_wall")


def buildRoads():
    """Build a road from north to south and east to west."""
    xaxis = STARTX + (ENDX - STARTX) // 2  # getting start + half the length
    zaxis = STARTZ + (ENDZ - STARTZ) // 2
    heights = WORLDSLICE.heightmaps["MOTION_BLOCKING_NO_LEAVES"]

    print("Calculating road height...")
    # caclulating the average height along where we want to build our road
    y = heights[(xaxis, zaxis)]
    for x in range(STARTX, ENDX + 1):
        newy = heights[(x, zaxis)]
        y = (y + newy) // 2
    for z in range(STARTZ, ENDZ + 1):
        newy = heights[(xaxis, z)]
        y = (y + newy) // 2

    # GLOBAL
    # By calling 'global ROADHEIGHT' we allow writing to ROADHEIGHT
    # If 'global' is not called, a new, local variable is created
    global ROADHEIGHT
    ROADHEIGHT = y

    print("Building east-west road...")
    # building the east-west road
    GEO.placeCuboid(xaxis - 2, y, STARTZ,
                    xaxis - 2, y, ENDZ, "end_stone_bricks")
    GEO.placeCuboid(xaxis - 1, y, STARTZ,
                    xaxis + 1, y, ENDZ, "gold_block")
    GEO.placeCuboid(xaxis + 2, y, STARTZ,
                    xaxis + 2, y, ENDZ, "end_stone_bricks")
    GEO.placeCuboid(xaxis - 1, y + 1, STARTZ,
                    xaxis + 1, y + 3, ENDZ, "air")

    print("Building north-south road...")
    # building the north-south road
    GEO.placeCuboid(STARTX, y, zaxis - 2,
                    ENDX, y, zaxis - 2, "end_stone_bricks")
    GEO.placeCuboid(STARTX, y, zaxis - 1,
                    ENDX, y, zaxis + 1, "gold_block")
    GEO.placeCuboid(STARTX, y, zaxis + 2,
                    ENDX, y, zaxis + 2, "end_stone_bricks")
    GEO.placeCuboid(STARTX, y + 1, zaxis - 1,
                    ENDX, y + 3, zaxis + 1, "air")


def buildCity():
    xaxis = STARTX + (ENDX - STARTX) // 2  # getting center
    zaxis = STARTZ + (ENDZ - STARTZ) // 2
    y = ROADHEIGHT

    print("Building city platform...")
    # Building a platform and clearing a dome for the city to sit in
    GEO.placeCenteredCylinder(xaxis, y, zaxis, 1, 21, "end_stone_bricks")
    GEO.placeCenteredCylinder(xaxis, y, zaxis, 1, 20, "gold_block")
    GEO.placeCenteredCylinder(xaxis, y + 1, zaxis, 3, 20, "air")
    GEO.placeCenteredCylinder(xaxis, y + 4, zaxis, 2, 19, "air")
    GEO.placeCenteredCylinder(xaxis, y + 6, zaxis, 1, 18, "air")
    GEO.placeCenteredCylinder(xaxis, y + 7, zaxis, 1, 17, "air")
    GEO.placeCenteredCylinder(xaxis, y + 8, zaxis, 1, 15, "air")
    GEO.placeCenteredCylinder(xaxis, y + 9, zaxis, 1, 12, "air")
    GEO.placeCenteredCylinder(xaxis, y + 10, zaxis, 1, 8, "air")
    GEO.placeCenteredCylinder(xaxis, y + 11, zaxis, 1, 3, "air")

    for i in range(50):
        buildTower(randint(xaxis - 20, xaxis + 20),
                   randint(zaxis - 20, zaxis + 20))

    # Place a book on a Lectern
    # See the wiki for book formatting codes
    INTF.placeBlock(xaxis, y, zaxis, "emerald_block")
    bookData = TB.writeBook("This book has a page!")
    TB.placeLectern(xaxis, y + 1, zaxis, bookData)


def buildTower(x, z):
    radius = 3
    y = ROADHEIGHT

    print(f"Building tower at {x}, {z}...")
    # if the blocks to the north, south, east and west aren't all gold
    if not (INTF.getBlock(x - radius, y, z) == "minecraft:gold_block"
            and INTF.getBlock(x + radius, y, z) == "minecraft:gold_block"
            and INTF.getBlock(x, y, z - radius) == "minecraft:gold_block"
            and INTF.getBlock(x, y, z + radius) == "minecraft:gold_block"):
        return  # return without building anything

    # lay the foundation
    GEO.placeCenteredCylinder(x, y, z, 1, radius, "emerald_block")

    # build ground floor
    GEO.placeCenteredCylinder(x, y + 1, z, 3, radius,
                              "lime_concrete", tube=True)

    # extend height
    height = randint(5, 20)
    GEO.placeCenteredCylinder(
        x, y + 4, z, height, radius, "lime_concrete", tube=True)
    height += 4

    # build roof
    GEO.placeCenteredCylinder(x, y + height, z, 1, radius, "emerald_block")
    GEO.placeCenteredCylinder(x, y + height + 1, z, 1,
                              radius - 1, "emerald_block")
    GEO.placeCenteredCylinder(x, y + height + 2, z, 1,
                              radius - 2, "emerald_block")
    GEO.placeCuboid(x, y + height, z, x, y + height
                    + 2, z, "lime_stained_glass")
    INTF.placeBlock(x, y + 1, z, "beacon")

    # trim sides and add windows and doors
    # GEO.placeCuboid(x + radius, y + 1, z, x + radius, y + height + 2, z, "air")
    GEO.placeCuboid(x + radius - 1, y + 1, z,
                    x + radius - 1, y + height + 2, z, "lime_stained_glass")
    # NOTE: When placing doors you need to place two blocks,
    #   the upper block defines the direction
    INTF.placeBlock(x + radius - 1, y + 1, z, "warped_door")
    INTF.placeBlock(x + radius - 1, y + 2, z,
                    "warped_door[facing=west, half=upper]")

    GEO.placeCuboid(x - radius, y + 1, z, x - radius, y + height + 2, z, "air")
    GEO.placeCuboid(x - radius + 1, y + 1, z,
                    x - radius + 1, y + height + 2, z, "lime_stained_glass")
    INTF.placeBlock(x - radius + 1, y + 1, z, "warped_door")
    INTF.placeBlock(x - radius + 1, y + 2, z,
                    "warped_door[facing=east, half=upper]")

    GEO.placeCuboid(x, y + 1, z + radius, x, y + height + 2, z + radius, "air")
    GEO.placeCuboid(x, y + 1, z + radius - 1,
                    x, y + height + 2, z + radius - 1, "lime_stained_glass")
    INTF.placeBlock(x, y + 1, z + radius - 1, "warped_door")
    INTF.placeBlock(x, y + 2, z + radius - 1,
                    "warped_door[facing=south, half=upper]")

    GEO.placeCuboid(x, y + 1, z - radius, x, y + height + 2, z - radius, "air")
    GEO.placeCuboid(x, y + 1, z - radius + 1,
                    x, y + height + 2, z - radius + 1, "lime_stained_glass")
    INTF.placeBlock(x, y + 1, z - radius + 1, "warped_door")
    INTF.placeBlock(x, y + 2, z - radius + 1,
                    "warped_door[facing=north, half=upper]")


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


def build_simple_house(start: tuple[int, int, int], size: tuple[int, int, int]):
    # Todo : finish the simple houses
    # body
    GEO.placeCuboid(start[0], start[1], start[2], start[0] + size[0] - 1, start[1] + size[1] - 1, start[2] + size[2] - 1,
                    "oak_planks", hollow=True)
    INTF.sendBlocks()
    # Todo : add direction
    # Door
    INTF.placeBlock(start[0] + size[0] // 2, start[1] + 1, start[2], "oak_door")
    INTF.placeBlock(start[0] + size[0] // 2, start[1] + 2, start[2], "oak_door[half=upper]")


def place_houses():
    occupied_spots = set()
    h_map = WORLDSLICE.heightmaps['MOTION_BLOCKING_NO_LEAVES']
    OFFSETX = ENDX - STARTX
    OFFSETZ = ENDZ - STARTZ
    center = (OFFSETX // 2, OFFSETZ // 2)
    coords_indices = [(x, z) for x in range(OFFSETX) for z in range(OFFSETZ)]
    house_padding = 2

    for i in range(10):
        iter_start = time.time()
        build_size = random.randint(5, 20), random.randint(4, 15), random.randint(5, 20)

        speed_factor = max(build_size) // 5
        best = get_best_area(h_map, coords_indices, center, occupied_spots, (build_size[0], build_size[2]), speed=speed_factor)
        best = (best[0] + STARTX, best[1] + STARTZ)

        house_start = (best[0], h_map[best], best[1])

        for x in range(-house_padding, build_size[0] + house_padding):
            for z in range(-house_padding, build_size[2] + house_padding):
                occupied_spots.add((house_start[0] + x, house_start[2] + z))

        build_simple_house(house_start, build_size)
        print(f"Placed house of size {build_size} at {best} in {time.time() - iter_start:.2f}s with speed {speed_factor}")


# === STRUCTURE #4
# The code in here will only run if we run the file directly (not imported)
# This prevents people from accidentally running your generator
if __name__ == '__main__':
    # NOTE: It is a good idea to keep this bit of the code as simple as
    #     possible so you can find mistakes more easily

    try:

        place_houses()

        # buildPerimeter()
        # buildRoads()
        # buildCity()

        print("Done!")
    except KeyboardInterrupt:   # useful for aborting a run-away program
        print("Pressed Ctrl-C to kill program.")
