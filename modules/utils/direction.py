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

    UP_NORTH = (0, 1, -1)

    UP_SOUTH = (0, 1, 1)

    UP_EAST = (1, 1, 0)

    UP_WEST = (-1, 1, 0)

    DOWN_NORTH = (0, -1, -1)

    DOWN_SOUTH = (0, -1, 1)

    DOWN_EAST = (1, -1, 0)

    DOWN_WEST = (-1, -1, 0)

    @staticmethod
    def parse_nbt(value: TAG_String) -> Direction:
        """Return a direction parsed from the given nbt string tag"""
        direction = value.valuestr()
        return Direction[direction.upper()]

    def __str__(self) -> str:
        """Return the string representation of the direction"""
        return self.name.lower()

    def get_rotated_direction(self, angle: float):
        _horizontal_directions = (Direction.EAST, Direction.SOUTH, Direction.WEST, Direction.NORTH)
        index_shift = int(angle // 90)
        try:
            index_shift += _horizontal_directions.index(self)
        except ValueError:
            return self
        index_shift %= 4
        return _horizontal_directions[index_shift]
