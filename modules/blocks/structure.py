from __future__ import annotations

import gdpc.interface as INTERFACE
from nbt.nbt import NBTFile, TAG_List

from modules.blocks.block import Block
from modules.blocks.collections.block_list import BlockList

from modules.utils.coordinates import Coordinates, Size


class Structure:
    """Class representing the minecraft construction of a structure block"""
    __slots__ = ['name', 'size', 'blocks', 'variations']

    def __init__(self, name: str, size: Size, blocks: BlockList) -> None:
        """Parameterized constructor creating a new minecraft structure"""
        self.name = name
        self.size = size
        self.blocks: tuple[BlockList] = tuple(blocks)
        self.variations: dict[str, BlockList] = dict()

    @staticmethod
    def parse_nbt_file(file_name: str, ) -> Structure:
        """Parse the nbt file found under resources.structure.{file_name}.nbt and return a structure object"""
        file = NBTFile(f'resources/structures/{file_name}.nbt')
        dimensions = [int(i.valuestr()) for i in file['size']]

        palette = file['palette']
        blocks = Structure.__parse_blocks(file['blocks'], palette)

        print(f'=> Parsed structure <{file_name}>')
        return Structure(name=file_name, size=Size(dimensions[0], dimensions[2]), blocks=blocks)

    @staticmethod
    def __parse_blocks(blocks: TAG_List, palette: TAG_List) -> BlockList:
        """Return a list of blocks parsed from the given blocks and palette"""
        return BlockList([Block.parse_nbt(block, palette) for block in blocks])

    def __get_blocks(self, start: Coordinates, angle: int, materials: dict[str, str]) -> BlockList:
        """Return the blocks of the structure, once their coordinates have been prepared for the given plot"""
        blocks = self.__get_variation(materials) if materials else self.blocks

        shift_due_to_rotation = Coordinates(0, 0, 0)
        if angle == 90:
            shift_due_to_rotation = Coordinates(self.size.z - 1, 0, 0)
        elif angle == 180:
            shift_due_to_rotation = Coordinates(self.size.x, 0, self.size.z - 1)
        elif angle == 270:
            shift_due_to_rotation = Coordinates(0, 0, self.size.x - 1)

        iterable = [block.rotate(angle).shift_position_to(start + shift_due_to_rotation) for block in blocks]
        return BlockList(iterable)

    def __get_variation(self, materials: dict[str, str]) -> BlockList:
        """Return the variation of the structure with the given materials"""
        variation = ', '.join([f'{k}: {v}' for k, v in materials.items()])
        if variation in self.variations.keys():
            return self.variations[variation]

        blocks = [block.replace_first(materials) for block in self.blocks]
        self.variations[variation] = blocks
        return BlockList(blocks)

    def get_size(self, rotation: int) -> Size:
        """Return the size of the structure after the given rotation"""
        return Size(self.size.z, self.size.x) if rotation == 90 or \
            rotation == 270 else Size(self.size.x, self.size.z)

    def build(self, start: Coordinates, rotation: int = 0, materials: dict[str, str] = None) -> None:
        """Build the given structure onto the current construction spot"""
        blocks = self.__get_blocks(start, rotation, materials=materials)

        for block in blocks:
            INTERFACE.placeBlock(*block.coordinates, block.full_name)

        INTERFACE.sendBlocks()