from __future__ import annotations

from enum import Enum
from typing import Iterator, List
from dataclasses import astuple, dataclass


class Direction(Enum):
    """Enumeration representing all available directions"""
    UP = (0, 1, 0)
    DOWN = (0, -1, 0)
    NORTH = (0, 0, -1)
    SOUTH = (0, 0, 1)
    EAST = (1, 0, 0)
    WEST = (-1, 0, 0)


@dataclass(frozen=True)
class Coordinates:
    """Represents a set of x, y and z coordinates"""
    x: int
    y: int
    z: int

    def towards(self, direction: Direction) -> Coordinates:
        """Return the next coordinates in the given direction (from the current coordinates)"""
        return Coordinates(self.x + direction.value[0], self.y + direction.value[1], self.z + direction.value[2])

    def is_in_area(self, x1, y1, z1, x2, y2, z2) -> bool:
        """Return true if the current coordinates are in the given area"""
        return x1 <= self.x <= x2 and y1 <= self.y <= y2 and z1 <= self.z <= z2

    def __iter__(self) -> Iterator:
        """Return an iterator over the current coordinates"""
        coordinates = astuple(self)
        return iter(coordinates)


@dataclass(frozen=True)
class Block:
    """Represents a block in the world"""
    name: str
    coordinates: Coordinates

    def neighbouring_coordinates(self) -> List[Coordinates]:
        """Return the list of all this block's neighbouring coordinates"""
        return [self.coordinates.towards(direction) for direction in Direction]

    def is_one_of(self, patterns: List[str]) -> bool:
        """Return true if the current item's name matches one of the given patterns"""
        for pattern in patterns:
            if pattern in self.name:
                return True
        return False

    @staticmethod
    def filter(pattern: str | List[str], blocks: List[Block]) -> List[Block]:
        """Filter the given list of block and return the ones that contain the given pattern"""
        if type(pattern) == str:
            pattern = [pattern]

        iterator = filter(lambda block: block.is_one_of(pattern), blocks)
        return list(iterator)


def get_block_at(x: int, y: int, z: int, world) -> Block:
    """Return the block found at the given x, y, z coordinates in the world"""
    name = world.getBlockAt(x, y, z)
    return Block(name, Coordinates(x, y, z))
