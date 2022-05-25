import yaml
from time import sleep
from typing import Any, Iterator
from dataclasses import dataclass

import gdpc.interface as INTERFACE
from gdpc.worldLoader import WorldSlice
from nbt.nbt import MalformedFileError

from src.utils.coordinates import Coordinates
from src.simulation.buildings.relations import RelationsHandler

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

    x1, y1, z1, x2, y2, z2 = request_build_area()
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


def get_content(file: str) -> Any:
    """Return the content of the given [file]. The function will search the file
    under the the local 'resouces' directory"""
    with open(f'resources/{file}', 'r') as content:
        return yaml.safe_load(content)


# Mapping of a material and its replacement and keepProperties (tuple)
# TODO refactoring
BUILDING_MATERIALS: dict[str, tuple[str, bool]] = {}

# Mapping of a building name to its data dictionary
# It has the same structure as the resources/buildings.yaml
# file so check this file out for more information
BUILDINGS: dict[str, dict[str, Any]] = get_content('buildings.yaml')

# Mapping of palette groups and their corresponding block palettes
# It has the same structure as the resources/palettes.yaml
# file so check this file out for more information
PALETTE_GROUPS: dict[str, dict[str, Any]] = get_content('palettes.yaml')

# TODO doc
RELATIONS = RelationsHandler(get_content('relations.yaml'))
