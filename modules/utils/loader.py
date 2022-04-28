from time import sleep
import gdpc.interface as INTERFACE
from gdpc.worldLoader import WorldSlice

from typing import Iterator
from dataclasses import astuple, dataclass

from nbt.nbt import MalformedFileError
from modules.blocks.structure import Structure
from modules.utils.coordinates import Coordinates

# Mapping of structure name -> Structure object
structures: dict[str, Structure] = {}

for file in ['house1', 'house2', 'house3']:
    __structure = Structure.parse_nbt_file(file)
    structures[file] = __structure


@dataclass(frozen=True)
class BuildArea:
    """Light container class for the build area"""
    start: Coordinates
    end: Coordinates

    def __iter__(self) -> Iterator[Coordinates]:
        """Return an iterator over the current coordinates"""
        for coordinates in (self.start, self.end):
            yield coordinates


def __fetch_build_area() -> BuildArea:
    """Fetch a new world slice either with a default area, """
    x1, y1, z1, x2, y2, z2 = INTERFACE.requestBuildArea()
    return BuildArea(Coordinates(x1, y1, z1), Coordinates(x2, y2, z2))


def __fetch_world_slice() -> WorldSlice | None:
    """Return a new WorldSlice object, snapshot of the world at the instant of the capture"""
    while retry_amount := 10:
        try:
            return WorldSlice(BUILD_AREA.start.x, BUILD_AREA.start.z,
                              BUILD_AREA.end.x + 1, BUILD_AREA.end.z + 1)
        except MalformedFileError:
            retry_amount -= 1
            sleep(2)
    print(f'Error: Could not get a world slice in {retry_amount} try')
    return None


def update_world_slice() -> None:
    """Fetch a new snapshot of the world. The new snapshot will override the last one"""
    world = __fetch_world_slice()


BUILD_AREA = __fetch_build_area()
WORLD = __fetch_world_slice()