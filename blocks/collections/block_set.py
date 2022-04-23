from __future__ import annotations

from collections import Counter
from collections.abc import MutableSet
from typing import Iterable, Iterator, Set, Tuple

from blocks.block import Block


class BlockSet(MutableSet):
    """Class representing a set of blocks, implements the abstract MutableSet"""

    def __init__(self, iterable: Iterable[Block] = None):
        """Parameterised constructor creating a new set of blocks"""
        self.__blocks: Set[Block] = set(iterable) if iterable else set()

    @property
    def counter(self) -> Counter[str]:
        """Return the counter of the blocks in the given set of blocks"""
        names = (block.name for block in self)
        return Counter(names)

    @property
    def most_common_block(self) -> str:
        """Return the name of the most common block in the current set of blocks"""
        occurences = self.counter.most_common(1)
        return occurences[0][0]

    def filter(self, pattern: str | Tuple[str]) -> BlockSet:
        """Return a subset of blocks containing the given pattern in their name"""
        if type(pattern) == str:
            pattern = (pattern, )

        iterable = [block for block in self if block.is_one_of(pattern)]
        return BlockSet(iterable)

    def add(self, block: Block) -> None:
        """Add the given block to the current set"""
        self.__blocks.add(block)

    def discard(self, block: Block) -> None:
        """Remove the given block from the current set"""
        self.__blocks.discard(block)

    def __iter__(self) -> Iterator[Block]:
        """Return an iterator of the blocks in the current set"""
        for block in self.__blocks:
            yield block

    def __contains__(self, *args) -> bool:
        """Return true if the given block is in the current set"""
        return self.__blocks.__contains__(*args)

    def __len__(self) -> int:
        """Return the length of the block set"""
        return len(self.__blocks)

    def __bool__(self) -> bool:
        """Return true if the current set is not empty, false otherwise"""
        return len(self.__blocks) > 0

    def __str__(self) -> str:
        """Return the string representation of the current set"""
        names = [str(block) for block in self]
        return 'BlockSet({' + ', '.join(names) + '})'
