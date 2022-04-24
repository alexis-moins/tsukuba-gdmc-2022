from __future__ import annotations

from nbt.nbt import NBTFile, TAG_List
from typing import Dict, Generator, List, Tuple
# from plots.construction_plot import ConstructionPlot

from blocks.block import Block
from blocks.collections.block_list import BlockList


class Structure:
    """Class representing the minecraft construction of a structure block"""
    __slots__ = ('name', 'size', 'blocks', 'variations')

    def __init__(self, name: str, size: Tuple[int, int, int], blocks: Tuple[Block]) -> None:
        """Parameterized constructor creating a new minecraft structure"""
        self.name = name
        self.size = size
        self.blocks = blocks
        self.variations: Dict[str, BlockList] = dict()

    @staticmethod
    def parse_nbt_file(file_name: str) -> Structure:
        """Parse the nbt file found under resources.structure.{file_name}.nbt and return a structure object"""
        file = NBTFile(f'resources/structures/{file_name}.nbt')
        size = [int(i.valuestr()) for i in file['size']]

        palette = file['palette']
        blocks = Structure.__parse_blocks(file['blocks'], palette)

        return Structure(name=file_name, size=tuple(size), blocks=tuple(blocks))

    @staticmethod
    def __parse_blocks(blocks: TAG_List, palette: TAG_List) -> Generator[Block]:
        """Return a list of blocks parsed from the given blocks and palette"""
        return (Block.parse_nbt(block, palette) for block in blocks)

    def get_blocks(self, plot, materials: Dict[str, str]) -> Generator[Block]:
        """Return the blocks of the structure, once their coordinates have been prepared for the given plot"""
        blocks = self.__get_variation(materials) if materials else self.blocks
        return (block.shift_position_to(plot.build_start) for block in blocks)

    def __get_variation(self, materials: Dict[str, str]) -> BlockList:
        """Return the variation of the structure with the given materials"""
        variation = ', '.join([f'{k}: {v}' for k, v in materials.items()])
        if variation in self.variations.keys():
            return self.variations[variation]

        blocks = (block.replace_first(materials) for block in self.blocks)
        self.variations[variation] = blocks
        return blocks
