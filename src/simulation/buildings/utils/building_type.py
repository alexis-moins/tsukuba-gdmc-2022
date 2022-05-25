from __future__ import annotations
from enum import Enum


class BuildingType(Enum):
    """Enumeration of the different types of buildings"""

    NONE = 0

    # For houses
    HABITATION = 1

    # For
    FARM = 2

    #
    WOODCUTTING = 3

    #
    FORGING = 4

    #
    MINING = 5

    DECORATION = 6

    GRAVEYARD = 7

    WEDDING = 8

    BAKERY = 9

    TOWN_HALL = 10

    @staticmethod
    def deserialize(_type: str) -> BuildingType:
        """Return the building type corresponding to the given [_type]"""
        key = _type.upper()
        return BuildingType[key]
