from __future__ import annotations

from nbt.nbt import NBTFile, TAG_List
from typing import Generator, List, Tuple
# from plots.construction_plot import ConstructionPlot

from blocks.block import Block


class Structure:
    """Class representing the minecraft construction of a structure block"""

    def __init__(self, name: str, size: Tuple[int, int, int], blocks: List[Block]) -> None:
        """Parameterized constructor creating a new minecraft structure"""
        self.name = name
        self.size = size
        self.blocks = blocks

    @staticmethod
    def parse_nbt_file(file_name: str) -> Structure:
        """Parse the nbt file found under resources/structure/{file_name}.nbt and return a structure object"""
        file = NBTFile(f'resources/structures/{file_name}.nbt')
        size = [int(i.valuestr()) for i in file['size']]

        palette = file['palette']
        blocks = Structure.parse_blocks(file['blocks'], palette)

        return Structure(name=file_name, size=tuple(size), blocks=blocks)

    @staticmethod
    def parse_blocks(blocks: TAG_List, palette: TAG_List) -> List[Block]:
        """Return a list of blocks parsed from the given blocks and palette"""
        return [Block.parse_nbt(block, palette) for block in blocks]

    def get_blocks_for(self, plot) -> Generator[Block]:
        """Return the block"""
        return (block.shift_position_to(plot.build_start) for block in self.blocks)
