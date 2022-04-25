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

    def get_rotated_direction(self, angle: float, _horizontal_directions=(NORTH, WEST, SOUTH, EAST)):
        index_shift = int(angle // 90)
        try:
            index_shift += _horizontal_directions.index(self)
        except ValueError:
            return self
        index_shift %= 4
        return _horizontal_directions[index_shift]


