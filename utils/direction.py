from enum import Enum


class Direction(Enum):
    """Enumeration representing all available directions"""
    UP = (0, 1, 0)
    DOWN = (0, -1, 0)
    NORTH = (0, 0, -1)
    SOUTH = (0, 0, 1)
    EAST = (1, 0, 0)
    WEST = (-1, 0, 0)
