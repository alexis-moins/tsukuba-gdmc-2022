from __future__ import annotations

import random
from collections import Counter
from collections.abc import Sequence
from typing import Any
from typing import Generator
from typing import Iterable
from typing import SupportsIndex

from src.blocks.block import Block
from src.blocks.collections.block_set import BlockSet
from src.utils.coordinates import Coordinates
from src.utils.coordinates import Size


class BlockList(Sequence):
    """Class representing a list of blocks, implements the abstract Sequence"""
    __slots__ = ['__blocks', '__coordinates']

    def __init__(self, iterable: Iterable[Block] = None):
        """Parameterised constructor creating a new list of blocks"""
        self.__blocks: list[Block] = list(iterable) if iterable else list()
        self.__coordinates = {block.coordinates.as_2D(): block for block in self.__blocks}

    @property
    def counter(self) -> Counter[str]:
        """Return the counter of the blocks in the given list of blocks"""
        names = (block.name for block in self)
        return Counter(names)

    @property
    def most_common(self) -> str | None:
        """Return the name of the most common block in the current list of blocks"""
        occurences = self.counter.most_common(1)
        return occurences[0][0] if occurences else None

    def insert(self, index: SupportsIndex, block: Block) -> None:
        """Insert the given block et the given index"""
        self.__blocks.insert(index, block)

    def filter(self, pattern: str | tuple[str, ...]) -> BlockList:
        """Return a sublist of blocks containing the given pattern in their name"""
        if type(pattern) == str:
            pattern = (pattern, )

        iterable = [block for block in self if block.is_one_of(pattern)]
        return BlockList(iterable)

    def without(self, pattern: str | tuple[str, ...]) -> BlockList:
        """Return a sublist of blocks not containing the given pattern in their name"""
        if type(pattern) == str:
            pattern = (pattern, )

        iterable = [block for block in self.__blocks if not block.is_one_of(pattern)]
        return BlockList(iterable)

    def not_inside(self, coordinates: set[Coordinates]) -> BlockList:
        """Return a sublist of blocks that are not inside of any of the given plots"""
        iterable = [block for block in self.__blocks if block.coordinates.as_2D() not in coordinates]
        return BlockList(iterable)

    def find(self, coordinates: Coordinates) -> Block | None:
        """Return the block at the given 2D coordinates"""
        if coordinates.as_2D() in self.__coordinates.keys():
            return self.__coordinates[coordinates.as_2D()]
        return None

    def near(self, coordinates: Coordinates, distance: int):
        """Return the list of block with a distance < the given distance"""
        iterable = [block for block in self.__blocks if block.coordinates.distance(coordinates) <= distance]
        return BlockList(iterable)

    def to_set(self) -> BlockSet:
        """Return the current block list converted into a block set"""
        return BlockSet(self)

    def __iter__(self) -> Generator[Block]:
        """Return a generator of the blocks in the current list"""
        return (block for block in self.__blocks)

    def __len__(self) -> int:
        """Return the length of the block list"""
        return len(self.__blocks)

    def __bool__(self) -> bool:
        """Return true if the current list is not empty, false otherwise"""
        return len(self.__blocks) > 0

    def __getitem__(self, *arguments) -> Any:
        """Return the block at the given index"""
        return self.__blocks.__getitem__(*arguments)

    def __str__(self) -> str:
        """Return the string representation of the current list"""
        names = [str(block) for block in self]
        return 'BlockList([' + ', '.join(names) + '])'

    def __add__(self, other: BlockList | list[Block]):
        if isinstance(other, BlockList):
            return BlockList(self.__blocks + other.__blocks)
        elif isinstance(other, list):
            return BlockList(self.__blocks + other)

    def random_elements(self, amount=1) -> BlockList:
        return BlockList(random.choices(self.__blocks, k=amount))
