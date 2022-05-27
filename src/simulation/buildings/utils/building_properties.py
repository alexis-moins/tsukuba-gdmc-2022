from __future__ import annotations
from dataclasses import dataclass
from typing import Any

from src.utils.resource import Resource
from src.simulation.buildings.utils.building_type import BuildingType


@dataclass(kw_only=True, frozen=True)
class BuildingProperties:
    """Represents the immutable properties of a building"""
    type: BuildingType
    resource: Resource
    padding: int = 5

    cost: int = 0
    maximum: int = 1
    is_extension: bool = False

    workers: int = 0
    number_of_beds: int = 0
    food_production: int = 0

    @staticmethod
    def deserialize(properties: dict[str, Any], resource: str, _type: str) -> BuildingProperties:
        """Return the building properties deserialized using the given [properties], [resource] and [_type]"""
        properties = {key.replace('-', '_'): value for key, value in properties.items()}

        properties['type'] = BuildingType.deserialize(_type)
        properties['resource'] = Resource.deserialize(resource)

        return BuildingProperties(**properties)
