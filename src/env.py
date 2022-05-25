import time
from dataclasses import dataclass
from time import sleep
from typing import Any
from typing import Iterator

import gdpc.interface as INTERFACE
import yaml
from gdpc import lookup
from gdpc.worldLoader import WorldSlice
from nbt.nbt import MalformedFileError

from src.blocks.collections import palette
from src.blocks.collections.palette import Palette
from src.simulation.buildings.building import Building
from src.simulation.buildings.building_type import BuildingType
from src.simulation.buildings.relations import RelationsHandler
from src.utils.coordinates import Coordinates

# The default build are
BUILD_AREA = None

# The world slice of the build area
WORLD = None

# Wether the simulation runs in debug mode or not
DEBUG = False

# Wether to teleport the player automatically or not
TP = True

# The percentage of blocks in a building that will suffer from the passing of time
DETERIORATION = 10

SHOW_TIME = False
start_time = time.time()


@dataclass(frozen=True)
class BuildArea:
    """Light container class for the build area"""
    start: Coordinates
    end: Coordinates

    def __iter__(self) -> Iterator[Coordinates]:
        """Return an iterator over the current coordinates"""
        for coordinates in (self.start, self.end):
            yield coordinates


def get_build_area(auto_build_area: bool = False) -> BuildArea:
    """Get the BUILD_AREA"""
    request_build_area = INTERFACE.requestPlayerArea if auto_build_area else INTERFACE.requestBuildArea

    x1, y1, z1, x2, y2, z2 = request_build_area(250, 250)
    return BuildArea(Coordinates(x1, y1, z1), Coordinates(x2, y2, z2))


def get_world_slice() -> WorldSlice | None:
    """Set the WORLD attribute"""
    while retry_amount := 10:
        try:
            return WorldSlice(BUILD_AREA.start.x, BUILD_AREA.start.z,
                              BUILD_AREA.end.x + 1, BUILD_AREA.end.z + 1)
        except MalformedFileError:
            retry_amount -= 1
            sleep(2)
    print(f'Error: Could not get a world slice in {retry_amount} try')


def get_content(file_name: str) -> Any:
    """Return the content of the file found under the 'resouces' directory"""
    with open(f'resources/{file_name}', 'r') as content:
        return yaml.safe_load(content)


# Mapping of a material and its replacement and keepProperties (tuple)
BUILDING_MATERIALS: dict[str, tuple[str, bool]] = {}

# Mapping of a building name and its Building object
BUILDINGS: dict[str, Building] = {building['name']: Building.deserialize(building)
                                  for building in get_content('buildings.yaml')}

# Build relations
_buildings = ()

RELATIONS = RelationsHandler(get_content('relations.yaml'))

ALL_PALETTES = {palette: Palette.deserialize(value) for palette, value in get_content('palettes.yaml').items()}
