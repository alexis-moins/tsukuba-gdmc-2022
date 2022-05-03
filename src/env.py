from dataclasses import dataclass
from time import sleep
from typing import Any
from typing import Iterator

import gdpc.interface as INTERFACE
import yaml
from gdpc.worldLoader import WorldSlice
from nbt.nbt import MalformedFileError

from src.simulation.buildings.building import Building
from src.utils.coordinates import Coordinates


@dataclass(frozen=True)
class BuildArea:
    """Light container class for the build area"""
    start: Coordinates
    end: Coordinates

    def __iter__(self) -> Iterator[Coordinates]:
        """Return an iterator over the current coordinates"""
        for coordinates in (self.start, self.end):
            yield coordinates


def get_build_area() -> BuildArea:
    """Fetch a new world slice either with a default area, """
    x1, y1, z1, x2, y2, z2 = INTERFACE.requestBuildArea()
    return BuildArea(Coordinates(x1, y1, z1), Coordinates(x2, y2, z2))


def get_world_slice() -> WorldSlice | None:
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
    WORLD = get_world_slice()


def get_content(file_name: str) -> Any:
    """Return the content of the file found under the 'resouces' directory"""
    with open(f'resources/{file_name}', 'r') as content:
        return yaml.safe_load(content)


# The default build are
BUILD_AREA = get_build_area()

# The world slice of the build area
WORLD = get_world_slice()

# Wether the simulation runs in debug mode or not
DEBUG = False

# Mapping of a material and its replacement and keepProperties (tuple)
BUILDING_MATERIALS: dict[str, tuple[str, bool]] = {}

# Mapping of a building name and its Building object
BUILDINGS: dict[str, Building] = {building['name']: Building.deserialize(building)
                                  for building in get_content('buildings.yaml')}
