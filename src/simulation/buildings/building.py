from __future__ import annotations

from dataclasses import dataclass
from dataclasses import replace
from typing import Any

from gdpc import interface as INTERFACE
from gdpc import toolbox as TOOLBOX

from src.blocks.collections.block_list import BlockList
from src.blocks.structure import Structure
from src.plots.plot import Plot
from src.simulation.buildings.building_type import BuildingType
from src.utils.action_type import ActionType
from src.utils.coordinates import Coordinates
from src.utils.coordinates import Size


@dataclass(kw_only=True)
class BuildingProperties:
    """Class representing the properties of a building"""
    cost: int
    number_of_beds: int = 0
    work_production: float = 0
    food_production: float = 0
    building_type: BuildingType
    action_type: ActionType


class Building:
    """Class representing a list of blocks (structure) on a given plot"""

    def __init__(self, name: str, properties: BuildingProperties, structure: Structure):
        """Parameterised constructor creating a new building"""
        self.name = name
        self.properties = replace(properties)  # Return a copy of the dataclass
        self.__structure = structure

        self.plot: Plot = None
        self.rotation: int = None
        self.blocks: BlockList = None
        self.entrances: BlockList = []

    @staticmethod
    def deserialize(building: dict[str, Any]) -> Building:
        """Return a new building deserialized from the given dictionary"""
        properties = {key.replace(' ', '_'): value
                      for key, value in building['properties'].items()}

        action_type = ActionType[building['action'].upper()]
        building_type = BuildingType[building['type'].upper()]
        properties = BuildingProperties(**properties,
                                        action_type=action_type, building_type=building_type)

        structure = Structure.parse_nbt_file(building['path'])
        return Building(building['name'], properties, structure)

    def get_size(self, rotation: int) -> Size:
        """Return the size of the building considering the given rotation"""
        return self.__structure.get_size(rotation)

    def build(self, plot: Plot, rotation: int):
        """Build the current building onto the building's plot"""
        self.plot = plot
        self.rotation = rotation

        self.blocks = self.__structure.get_blocks(plot.start, rotation)

        self.entrances = self.blocks.filter('emerald')
        print(f'=> Building entrances: {len(self.entrances)}')

        for block in self.blocks:
            INTERFACE.placeBlock(*block.coordinates, block.full_name)

        self.__place_sign()
        INTERFACE.sendBlocks()

    def __place_sign(self):
        """Place a sign indicating informations about the building"""
        if not self.entrances:
            return None

        sign_coord = self.entrances[0].coordinates.shift(y=1)
        TOOLBOX.placeSign(*sign_coord, rotation=0, text1=self.name)

        for entrance in self.entrances:
            neighbours = [self.plot.get_block_at(*coordinates)
                          for coordinates in entrance.neighbouring_coordinates()]

            block_name = BlockList(neighbours).without(
                ('air', 'grass', 'sand', 'water')).most_common

            if block_name is not None:
                INTERFACE.placeBlock(*entrance.coordinates, block_name)

    def __str__(self) -> str:
        """Return the string representation of the current building"""
        return self.name.upper()
