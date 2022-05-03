from __future__ import annotations

from dataclasses import dataclass
from dataclasses import replace
from typing import Any

from gdpc import interface as INTERFACE

from src.blocks.collections.block_list import BlockList
from src.blocks.structure import Structure
from src.plots.plot import Plot
from src.simulation.buildings.building_type import BuildingType
from src.utils.action_type import ActionType
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

        for block in self.blocks:
            INTERFACE.placeBlock(*block.coordinates, block.full_name)
        INTERFACE.sendBlocks()

    def __str__(self) -> str:
        """Return the string representation of the current building"""
        return self.name.upper()

    def __repr__(self) -> str:
        """"""
        return self.name.upper()
