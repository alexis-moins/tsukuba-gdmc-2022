from __future__ import annotations

from typing import List, Tuple
from dataclasses import dataclass

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
            name += Block._parse_properties(palette[index]['Properties'])

        coordinates = Coordinates.parse_nbt(block['pos'])
        return Block(name=name, coordinates=coordinates)

    @staticmethod
    def _parse_properties(properties: TAG_Compound) -> str:
        """Return the string parsed from the given properties"""
        parsed_properties = [f'{k}={v}' for k, v in properties.items()]
        return '[' + ', '.join(parsed_properties) + ']'

    @staticmethod
    def extract_label(name: str) -> str | None:
        """"""
        splits = name.split(':')
        if '_' in splits[1]:
            return splits[1].split('_')[0]
        return splits[1]

    def neighbouring_coordinates(self) -> List[Coordinates]:
        """Return the list of all this block's neighbouring coordinates"""
        return [self.coordinates.towards(direction) for direction in Direction]

    def shift_position_to(self, coordinates: Coordinates) -> Block:
        """Return a new block with the same name and properties but whose coordinates were shifted"""
        return Block(name=self.name, coordinates=self.coordinates.shift(*coordinates))

    def is_one_of(self, patterns: Tuple[str]) -> bool:
        """Return true if the current item's name matches the given tuple of patterns"""
        for pattern in patterns:
            if pattern in self.name:
                return True
        return False
