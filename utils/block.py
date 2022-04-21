from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Collection, Counter, List, Set

from utils.direction import Direction
from utils.coordinates import Coordinates


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
    def group_by_name(blocks: Collection[Block]) -> Counter[Any]:
        """Return a counter of the blocks in the given collection"""
        block_names = (block.name for block in blocks)
        return Counter(block_names)
