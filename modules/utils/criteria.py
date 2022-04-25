from enum import Enum


class Criteria(Enum):
    """Enumeration of the different criteria to select a heightmap"""

    # The top non-air blocks
    WORLD_SURFACE = 0

    # The top blocks with a hitbox or fluid
    MOTION_BLOCKING = 1

    # Like MOTION_BLOCKING but ignoring leaves
    MOTION_BLOCKING_NO_LEAVES = 2

    # The top solid blocks
    OCEAN_FLOOR = 3
