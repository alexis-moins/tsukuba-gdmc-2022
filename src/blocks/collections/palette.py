from __future__ import annotations
import dataclasses

import random
import functools
from abc import ABC, abstractmethod
from typing import Any

from src.blocks.block import Block

from src import env
import gdpc.lookup as LOOKUP


class Palette(ABC):
    """Abstract class representing a palette of blocks"""

    @staticmethod
    def parse_groups(palette_groups: list[str]) -> dict[str, Palette]:
        """Return a dictionary of block names and their corresponding Palettes. The different
        palettes are deserialized using the palette groups defined in module env and whose name
        are inside of the given [palette groups]"""
        palettes = [env.PALETTE_GROUPS[palette] for palette in palette_groups]
        to_deserialize = functools.reduce(lambda origin, new: origin | new, palettes)

        return {block: Palette.deserialize(palette)
                for block, palette in to_deserialize.items()}

    @staticmethod
    def deserialize(palette: dict[str, Any]) -> Palette:
        """Return a Palette obtained by deserializing the given [palette]"""
        palette_type = palette['type']
        constructor = PALETTE_TYPES[palette_type]
        return constructor(palette)

    @abstractmethod
    def get_block(self, block: Block) -> Block:
        """"""
        pass


class RandomPalette(Palette):
    """Palette of blocs giving bloc randomly, with weights"""

    def __init__(self, palette: dict[str, Any]):
        """Create a palette of blocks chosen randomly using the data from the given [palette]"""
        if 'lookup' in palette:
            lookup = palette['lookup']
            self.blocks = LOOKUP.__dict__[lookup]
        else:
            self.blocks = palette['blocks']

        self.prefix = palette.get('prefix', '')

        if type(self.blocks) == dict:
            self.population = self.blocks.keys()
            self.weights = self.blocks.values()

    def get_block(self, old_block: Block) -> Block:
        """Return a randomly selected block from the palette. If the palette 'blocks' attribute
        is a list, the block is randomly selected assuming all items have equal weight. If the
        attribute is a dictionary, the block is chosen using the weights in the dictionary"""
        if type(self.blocks) in [list, tuple]:
            block_name = random.choice(self.blocks)
        else:
            print(self.__dict__)
            choices = random.choices(
                list(self.population),
                list(self.weights), k=1)
            block_name = choices[0]

        block_name.replace(':', f':{self.prefix}')
        return dataclasses.replace(old_block, name=block_name)


class SequencePalette(Palette):
    """palette of blocs giving blocs in a random sequence, that can be repeated or reshuffled"""

    def __init__(self, palette: dict[str, Any]):
        """Create a Sequence Palette, where blocks are given in the order given in the 'blocks'
        list of the [palette]"""
        self.blocks: list[str] = palette['blocks']
        self.shuffle = palette.get('shuffle', True)

        self.index = 0
        if self.shuffle:
            random.shuffle(self.blocks)

    def get_block(self, block: Block) -> Block:
        """Return a block from the sequence palette."""
        block_name = self.blocks[self.index]

        self.index += 1

        if self.index >= len(self.blocks):
            self.index = 0

            if self.shuffle:
                random.shuffle(self.blocks)

        return Block.deserialize(block_name, block.coordinates)


class OneBlockPalette(Palette):
    """Represents a palette containing only one single block"""

    def __init__(self, palette: dict[str, Any]) -> None:
        """"""
        lookup = palette['lookup']
        self.block = random.choice(LOOKUP.__dict__[lookup])

    def get_block(self) -> str:
        """Return the same block every time"""
        return self.block


class ColorPalette(Palette):
    """Represents a palette of a single color"""

    def __init__(self, palette: dict[str, Any]) -> None:
        """Create a new color palette"""
        self.color = random.choice(LOOKUP.COLORS)

    def get_block(self, old_block: Block) -> Block:
        """Return a new block corresponding to the given [old block] once changed according
        to the current palette"""
        name = old_block.name.replace('white', self.color)
        return dataclasses.replace(old_block, name=name)


PALETTE_TYPES = {
    'COLOR': ColorPalette,
    'RANDOM': RandomPalette,
    'ONE BLOCK': OneBlockPalette,
    'SEQUENCE': SequencePalette
}
