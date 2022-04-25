from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

from gdpc.lookup import BLOCKS
from nbt.nbt import TAG_Compound, TAG_List

from utils.direction import Direction
from utils.coordinates import Coordinates


@dataclass(frozen=True)
class Block:
    """Represents a block in the world"""
    name: str
    coordinates: Coordinates

    @staticmethod
    def parse_nbt(block: TAG_Compound, palette: TAG_List) -> Block:
        """Return a new block object parsed from the given NBT tag compound and palette"""
        index = int(block['state'].valuestr())
        name = palette[index]['Name'].valuestr()

        if 'Properties' in palette[index].keys():
            name += Block.__parse_properties(palette[index]['Properties'])

        coordinates = Coordinates.parse_nbt(block['pos'])
        return Block(name=name, coordinates=coordinates)

    @staticmethod
    def __parse_properties(properties: TAG_Compound) -> str:
        """Return the string parsed from the given properties"""
        parsed_properties = [f'{k}={v}' for k, v in properties.items()]
        return '[' + ', '.join(parsed_properties) + ']'

    @staticmethod
    def trim_name(name: str, pattern: str) -> List[str]:
        """Trim the given block name to remove the given pattern, also gets rid of 'minecraft:"""
        return name.replace('minecraft:', '').replace(pattern, '')

    @staticmethod
    def exists(block_name: str) -> bool:
        """Return true if the given block name exists in minecraft"""
        return block_name.split('[')[0] in BLOCKS

    def replace_first(self, materials: Dict[str, str]) -> Block:
        """Return a new block whose material has been replaced by the first match of the given building materials"""
        for material, replacement in materials.items():
            if material in self.name:
                name = self.name.replace(material, replacement)

                if Block.exists(name):
                    return Block(name=name, coordinates=self.coordinates)
        return self

    def neighbouring_coordinates(self) -> List[Coordinates]:
        """Return the list of all this block's neighbouring coordinates"""
        return [self.coordinates.towards(direction) for direction in Direction]

    def shift_position_to(self, coordinates: Coordinates) -> Block:
        """Return a new block with the same name and properties but whose coordinates were shifted"""
        return Block(name=self.name, coordinates=self.coordinates.shift(*coordinates))

    def is_one_of(self, pattern: Tuple[str]) -> bool:
        """Return true if the current item's name matches the given pattern"""
        for part in pattern:
            if part in self.name:
                return True
        return False

    def __str__(self) -> str:
        """Return the string representation of the block"""
        return self.name
