from __future__ import annotations

from enum import Enum
from nbt.nbt import TAG_String


class Direction(Enum):
    """Enumeration representing all available directions"""

    # The direction upward
    UP = (0, 1, 0)

    # The direction downward
    DOWN = (0, -1, 0)

    # The direction to the north
    NORTH = (0, 0, -1)

    # The direction to the south
    SOUTH = (0, 0, 1)

    # The direction to the east
    EAST = (1, 0, 0)

    # The direction to the west
    WEST = (-1, 0, 0)

    @staticmethod
    def parse_nbt(value: TAG_String) -> Direction:
        """Return a direction parsed from the given nbt string tag"""
        direction = value.valuestr()
        return Direction[direction.upper()]

    def __str__(self) -> str:
        """Return the string representation of the direction"""
        return self.name.lower()
