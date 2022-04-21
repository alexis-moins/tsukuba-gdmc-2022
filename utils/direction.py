from enum import Enum


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
