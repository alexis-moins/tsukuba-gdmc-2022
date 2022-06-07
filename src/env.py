import yaml
import time
from typing import Any, Iterator
from dataclasses import dataclass

from gdpc import interface
from gdpc.worldLoader import WorldSlice
from nbt.nbt import MalformedFileError

from src.utils.coordinates import Coordinates, Size

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

PROFILE_TIME = False


@dataclass(frozen=True)
class BuildArea:
    """Light container class for the build area"""
    start: Coordinates
    end: Coordinates

    def __iter__(self) -> Iterator[Coordinates]:
        """Return an iterator over the current coordinates"""
        for coordinates in (self.start, self.end):
            yield coordinates

    def max_size(self, length: int):
        size = Size.from_coordinates(self.start, self.end)
        if size.x > length or size.z > length:
            extra_x = (size.x - length) // 2
            extra_z = (size.z - length) // 2
            new_start = self.start.shift(x=extra_x, z=extra_z)
            new_end = self.end.shift(x=-extra_x, z=-extra_z)
            return BuildArea(new_start, new_end)

        else:
            return self


def get_build_area(auto_build_area: bool = False) -> BuildArea:
    """Get the BUILD_AREA"""
    x1, y1, z1, x2, y2, z2 = INTERFACE.requestPlayerArea(250, 250) if auto_build_area else INTERFACE.requestBuildArea()
    return BuildArea(Coordinates(x1, y1, z1), Coordinates(x2, y2, z2)).max_size(250)  # Prevent from huge size input


def get_world_slice() -> WorldSlice | None:
    """Set the WORLD attribute"""
    while retry_amount := 20:
        try:
            return WorldSlice(BUILD_AREA.start.x, BUILD_AREA.start.z,
                              BUILD_AREA.end.x + 1, BUILD_AREA.end.z + 1)
        except MalformedFileError:
            retry_amount -= 1
            time.sleep(1)
    print(f'Error: Could not get a world slice in {retry_amount} try')


def get_content(file: str, *, YAML: bool = True) -> Any:
    """Return the content of the given YAML [file]. The function will search the
    file under the the local 'resouces' directory. Optionally, specifying [YAML]
    to false enables the function to parse txt files"""
    with open(f'resources/{file}', 'r') as content:
        return yaml.safe_load(content) if YAML else \
            content.read().splitlines()


def summon(entity: str, coordinates: Coordinates, *, name: str = '') -> None:
    """"""
    x, y, z = coordinates
    command = f'summon {entity} {x} {y} {z} {{CustomName:"\\"{name}\\""}}'
    interface.runCommand(command)


# Mapping of a material and its replacement and keepProperties (tuple)
# TODO refactoring with palettes
BUILDING_MATERIALS: dict[str, tuple[str, bool]] = {}

# Mapping of a building name to its data dictionary
# It has the same structure as the resources/buildings.yaml
# file so check this file out for more information
BUILDINGS: dict[str, dict[str, Any]] = get_content('buildings.yaml')

# Mapping of palette groups and their corresponding block palettes
# It has the same structure as the resources/palettes.yaml
# file so check this file out for more information
PALETTE_GROUPS: dict[str, dict[str, Any]] = get_content('palettes.yaml')

# List of all the different wolf names available during
# the simulation
WOLF_NAMES: list[str] = get_content('wolf-names.txt', YAML=False)

# List of all the different villager first names available
# during the simulation
FIRST_NAMES: list[str] = get_content('first-names.txt', YAML=False)

# List of all the different villager last names available
# during the simulation
LAST_NAMES: list[str] = get_content('last-names.txt', YAML=False)

# List of all the different building adjectives available
# during the simulation
ADJECTIVES: list[str] = get_content('building-adjectives.txt', YAML=False)
