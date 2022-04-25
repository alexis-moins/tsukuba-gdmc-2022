from __future__ import annotations

from collections import Counter
from collections.abc import MutableSequence
from typing import Any, Iterable, Generator, List, SupportsIndex, Tuple

from modules.blocks.block import Block
from modules.blocks.collections.block_set import BlockSet


class BlockList(MutableSequence):
    """Class representing a list of blocks, implements the abstract MutableSequence"""
    __slots__ = ('__blocks', )

    def __init__(self, iterable: Iterable[Block] = None):
        """Parameterised constructor creating a new list of blocks"""
        self.__blocks: List[Block] = list(iterable) if iterable else list()

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

    def filter(self, pattern: str | Tuple[str]) -> BlockSet:
        """Return a sublist of blocks containing the given pattern in their name"""
        if type(pattern) == str:
            pattern = (pattern, )

        iterable = [block for block in self if block.is_one_of(pattern)]
        return BlockSet(iterable)

    def __iter__(self) -> Generator[Block]:
        """Return a generator of the blocks in the current list"""
        return (block for block in self.__blocks)

    def __len__(self) -> int:
        """Return the length of the block list"""
        return len(self.__blocks)

    def __bool__(self) -> bool:
        """Return true if the current list is not empty, false otherwise"""
        return len(self.__blocks) > 0

    def __getitem__(self, *args) -> Any:
        """Return the block at the given index"""
        return self.__blocks.__getitem__(*args)

    def __setitem__(self, *args) -> None:
        """Set a block at a certain index or slice"""
        self.__blocks.__setitem__(*args)

    def __delitem__(self, *args) -> None:
        """Delete the block at the given index or slice"""
        self.__blocks.__delitem__(*args)

    def __str__(self) -> str:
        """Return the string representation of the current list"""
        names = [str(block) for block in self]
        return 'BlockList([' + ', '.join(names) + '])'
