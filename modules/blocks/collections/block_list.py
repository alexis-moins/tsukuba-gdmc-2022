from __future__ import annotations

from collections import Counter
from collections.abc import MutableSequence
from typing import Any, Collection, Iterable, Generator, SupportsIndex

from modules.blocks.block import Block
from modules.blocks.collections.block_set import BlockSet
from modules.utils.coordinates import Coordinates, Size


class BlockList(MutableSequence):
    """Class representing a list of blocks, implements the abstract MutableSequence"""
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

    def __getitem__(self, i: slice | SupportsIndex) -> Any:
        """Return the block at the given index"""
        return BlockList(self.__blocks[i])

    def __setitem__(self, i: slice | SupportsIndex, o: Block | Iterable[Block]) -> None:
        """Set a block at a certain index or slice"""
        self.__blocks[i] = o
        # TODO add to self.__coordinates

    def __delitem__(self, *args) -> None:
        """Delete the block at the given index or slice"""
        self.__blocks.__delitem__(*args)

    def __str__(self) -> str:
        """Return the string representation of the current list"""
        names = [str(block) for block in self]
        return 'BlockList([' + ', '.join(names) + '])'