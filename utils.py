from __future__ import annotations

from enum import Enum
from typing import Collection, Counter, Dict, Iterator, List, Set
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

    def is_in_area(self, build_area) -> bool:
        """Return true if the current coordinates are in the given area"""
        x1, y1, z1 = build_area.start
        x2, y2, z2 = build_area.end
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
    def filter(pattern: str | List[str], blocks: List[Block]) -> Set[Block]:
        """Filter the given list of block and return the ones that contain the given pattern"""
        if type(pattern) == str:
            pattern = [pattern]

        iterator = filter(lambda block: block.is_one_of(pattern), blocks)
        return set(iterator)

    @staticmethod
    def group_by_name(blocks: List[Block]) -> Counter:
        """Return a counter of the blocks in the given list"""
        block_names = (block.name for block in blocks)
        return Counter(block_names)
