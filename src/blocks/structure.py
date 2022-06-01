from __future__ import annotations

from colorama import Fore
from nbt.nbt import NBTFile
from nbt.nbt import TAG_List

from src import env
from src.blocks.block import Block
from src.blocks.collections.block_list import BlockList
from src.utils.coordinates import Coordinates
from src.utils.coordinates import Size


#
_structures: dict[str, Structure] = dict()


def get_structure(file: str) -> Structure:
    """Return the Structure found in the given NBT [file]. Parse the file if the structure
    has not already been pased, otherwise simply return the corresponding structure"""
    if file in _structures:
        return _structures[file]

    structure = Structure.deserialize_nbt_file(file)
    _structures[file] = structure
    return structure


class Structure:
    """Class representing the minecraft construction of a structure block"""
    __slots__ = ['name', 'size', 'blocks', 'entrance', 'variations']

    def __init__(self, name: str, size: Size, blocks: BlockList) -> None:
        """Parameterized constructor creating a new minecraft structure"""
        self.name = name
        self.size = size

        self.blocks: BlockList = blocks
        self.variations: dict[str, BlockList] = dict()

    @staticmethod
    def deserialize_nbt_file(file_name: str, ) -> Structure:
        """Parse the nbt file found under resources.structure.{file_name}.nbt and return a structure object"""
        file = NBTFile(f'resources/structures/{file_name}')
        dimensions = [int(i.valuestr()) for i in file['size']]

        palette = file['palette']
        blocks = Structure.__parse_blocks(file['blocks'], palette)

        print(f'parsed structure {Fore.RED}<{file_name}>{Fore.WHITE}')
        return Structure(name=file_name, size=Size(dimensions[0], dimensions[2]), blocks=blocks)

    @staticmethod
    def __parse_blocks(blocks: TAG_List, palette: TAG_List) -> BlockList:
        """Return a list of blocks parsed from the given blocks and palette"""
        return BlockList([Block.parse_nbt(block, palette) for block in blocks])

    def get_blocks(self, start: Coordinates, rotation: int, *, apply_block_variation: bool = True) -> BlockList:
        """Return the blocks of the structure, once their coordinates have been prepared for the given plot. It means
        that coordinates will all be shifted in order to be relative to the new origin [start]. The structure also
        applies the given [rotation] to all the blocks."""
        if apply_block_variation:
            blocks = self.__get_variation(env.BUILDING_MATERIALS) if env.BUILDING_MATERIALS else self.blocks

        shift_due_to_rotation = self.size.get_rotation_shift(rotation)

        iterable = [block.rotate(rotation).shift_position_to(start + shift_due_to_rotation) for block in blocks]
        return BlockList(iterable)

    def __get_variation(self, materials: dict[str, str]) -> BlockList:
        """Return the variation of the structure with the given materials"""
        variation = ', '.join([f'{k}: {v[0]}' for k, v in materials.items()])
        if variation in self.variations.keys():
            return self.variations[variation]

        blocks = [block.replace_first(materials) for block in self.blocks]
        self.variations[variation] = blocks
        return BlockList(blocks)

    def get_size(self, rotation: int) -> Size:
        """Return the size of the structure after the given rotation"""
        return Size(self.size.z, self.size.x) if rotation == 90 or \
            rotation == 270 else Size(self.size.x, self.size.z)
