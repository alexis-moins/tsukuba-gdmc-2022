from __future__ import annotations

import random
from abc import ABC
from abc import abstractmethod

from gdpc import lookup

_palettes_type = {'random': lambda replace: RandomPalette(replace),
                  'sequence': lambda replace: RandomSequencePalette(replace),
                  'one_color': lambda replace: [color + replace for color in lookup.COLORS],

                  'flowers': lambda replace: RandomPalette([flower for flower in lookup.FLOWERS]),
                  'potted_flowers': lambda replace: RandomPalette(
                      ['potted_' + flower.replace('minecraft:', '') for flower in
                       lookup.SHORTFLOWERS]),
                  'one_flower': lambda replace: [flower for flower in lookup.FLOWERS],

                  # You can add your custom type here
                  }


class Palette(ABC):
    """Abstract class representing a palette of bloc"""

    @abstractmethod
    def get_block_name(self):
        pass

    @staticmethod
    def deserialize(data: dict[str, dict[str, str | dict | list]]) -> dict[str, Palette | list]:
        return {bloc: _palettes_type[data[bloc]['type']](data[bloc]['replaced_by']) for bloc in data}

    @staticmethod
    def assemble(palettes: list[dict[str, Palette | list]]) -> dict[str, Palette | list]:
        final_palette = {}
        for pal in palettes:
            for key, value in pal.items():
                if key not in final_palette:
                    final_palette[key] = value
        return final_palette


class RandomPalette(Palette):
    """Palette of blocs giving bloc randomly, with weights"""

    def __init__(self, blocks_and_proba_or_list: dict[str, float] | list[str]):
        super().__init__()
        if isinstance(blocks_and_proba_or_list, dict):
            self.blocks = list(blocks_and_proba_or_list)
            self.proba = list(blocks_and_proba_or_list.values())
        else:
            self.blocks = blocks_and_proba_or_list
            self.proba = [1 for _ in range(len(self.blocks))]

    def get_block_name(self) -> str:
        """return a bloc name randomly, with weights, from its dict"""
        return random.choices(self.blocks, self.proba, k=1)[0]


class RandomSequencePalette(Palette):
    """palette of blocs giving blocs in a random sequence, that can be repeated or reshuffled"""

    def __init__(self, blocks: list[str], reshuffle: bool = True):
        super().__init__()
        self.blocks = blocks
        self.reshuffle = reshuffle
        random.shuffle(self.blocks)
        self.index = 0

    def get_block_name(self) -> str:
        """return a bloc name from the sequence"""
        block = self.blocks[self.index]

        self.index += 1  # increment index
        if self.index >= len(self.blocks):
            self.index = 0  # Reset if too big
            if self.reshuffle:  # reshuffle if allowed
                random.shuffle(self.blocks)
        return block


class OneBlockPalette(Palette):
    """Palette with one block"""

    def __init__(self, block_or_list_to_randomly_take_from: str | list[str]):
        data = block_or_list_to_randomly_take_from
        if isinstance(data, list):
            self.block = random.choice(data)
        else:
            self.block = data

    def get_block_name(self) -> str:
        """Return the same block every time"""
        return self.block
