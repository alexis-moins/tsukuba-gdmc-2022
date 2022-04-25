from __future__ import annotations

from typing import Dict, Tuple
from nbt.nbt import NBTFile, TAG_List
# from plots.construction_plot import ConstructionPlot

from modules.plots.plot import Plot
from modules.utils.coordinates import Coordinates

from modules.blocks.block import Block
from modules.blocks.collections.block_list import BlockList


class Structure:
    """Class representing the minecraft construction of a structure block"""
    __slots__ = ['name', 'size', 'blocks', 'variations']

    def __init__(self, name: str, size: Tuple[int, int, int], blocks: BlockList) -> None:
        """Parameterized constructor creating a new minecraft structure"""
        self.name = name
        self.size = size
        self.blocks: Tuple[BlockList] = tuple(blocks)
        self.variations: Dict[str, BlockList] = dict()

    @ staticmethod
    def parse_nbt_file(file_name: str) -> Structure:
        """Parse the nbt file found under resources.structure.{file_name}.nbt and return a structure object"""
        file = NBTFile(f'resources/structures/{file_name}.nbt')
        size = [int(i.valuestr()) for i in file['size']]

        palette = file['palette']
        blocks = Structure.__parse_blocks(file['blocks'], palette)

        print(f'=> Parsed structure <{file_name}>')
        return Structure(name=file_name, size=tuple(size), blocks=blocks)

    @ staticmethod
    def __parse_blocks(blocks: TAG_List, palette: TAG_List) -> BlockList:
        """Return a list of blocks parsed from the given blocks and palette"""
        return BlockList([Block.parse_nbt(block, palette) for block in blocks])

    def get_blocks(self, plot, materials: Dict[str, str], angle=0) -> BlockList:
        """Return the blocks of the structure, once their coordinates have been prepared for the given plot"""
        blocks = self.__get_variation(materials) if materials else self.blocks

        shift_due_to_rotation = Coordinates(0, 0, 0)
        if angle == 90:
            shift_due_to_rotation = Coordinates(self.size[2] - 1, 0, 0)
        elif angle == 180:
            shift_due_to_rotation = Coordinates(self.size[0] - 1, 0, self.size[2] - 1)
        elif angle == 270:
            shift_due_to_rotation = Coordinates(0, 0, self.size[0] - 1)

        return BlockList([block.rotate(angle).shift_position_to(plot.build_start + shift_due_to_rotation) for block in blocks])

    def __get_variation(self, materials: Dict[str, str]) -> BlockList:
        """Return the variation of the structure with the given materials"""
        variation = ', '.join([f'{k}: {v}' for k, v in materials.items()])
        if variation in self.variations.keys():
            return self.variations[variation]

        blocks = [block.replace_first(materials) for block in self.blocks]
        self.variations[variation] = blocks
        return BlockList(blocks)

    def get_area(self, rotation: float):
        if rotation == 90 or rotation == 270:
            return self.size[2], self.size[0]
        else:
            return self.size[0], self.size[2]