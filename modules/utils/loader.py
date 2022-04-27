from distutils.command.build import build
import gdpc.interface as INTERFACE
from gdpc.worldLoader import WorldSlice
from numpy import intp

from modules.blocks.structure import Structure
from modules.utils.coordinates import Coordinates

# Mapping of structure name -> Structure object
structures: dict[str, Structure] = {}

for file in ['house1', 'house2', 'house3']:
    __structure = Structure.parse_nbt_file(file)
    structures[file] = __structure


def __fetch_coordinates() -> tuple[Coordinates, Coordinates]:
    """"""
    x1, y1, z1, x2, y2, z2 = INTERFACE.requestBuildArea()
    return Coordinates(x1, y1, z1), Coordinates(x2, y2, z2)


def __fetch_world_slice() -> WorldSlice:
    """Return a tuple of the starting and end coordinates of the requested build area"""
    return WorldSlice(BUILD_AREA[0].x, BUILD_AREA[0].z,
                      BUILD_AREA[1].x + 1, BUILD_AREA[1].z + 1)


def update_world_slice() -> None:
    """Fetch a new snapshot of the world. The new snapshot will override the last one"""
    world = __fetch_world_slice()


BUILD_AREA = __fetch_coordinates()
WORLD = __fetch_world_slice()
