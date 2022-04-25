from __future__ import annotations

from typing import Any, Dict, List, Tuple
from dataclasses import dataclass, field

from gdpc.lookup import BLOCKS
from nbt.nbt import TAG_Compound, TAG_List

from utils.direction import Direction
from utils.coordinates import Coordinates


@dataclass(frozen=True)
class Block:
    """Represents a block in the world"""
    name: str
    coordinates: Coordinates
    properties: Dict[str, str | Direction] = field(default_factory=dict)

    @staticmethod
    def parse_nbt(block: TAG_Compound, palette: TAG_List) -> Block:
        """Return a new block object parsed from the given NBT tag compound and palette"""
        index = int(block['state'].valuestr())
        name = palette[index]['Name'].valuestr()

        properties = dict()
        if 'Properties' in palette[index].keys():
            properties = Block.__parse_properties(palette[index]['Properties'])

        coordinates = Coordinates.parse_nbt(block['pos'])
        return Block(name, coordinates, properties=properties)

    @staticmethod
    def __parse_properties(properties: TAG_Compound) -> Dict[str, Any]:
        """Return a dictionary of the given pared properties"""
        return {key: (Direction.parse_nbt(value) if key == 'facing' else value)
                for key, value in properties.iteritems()}

    @staticmethod
    def deserialize(name: str, coordinates: Coordinates) -> Block:
        """"""
        properties = {}
        if '[' in name:
            raw_properties = name.split('[')
            name = raw_properties[0]
            properties = dict((key.strip(), value.strip())
                              for key, value in (element.split(':')
                                                 for element in raw_properties[1][:-1].split(', ')))

        return Block(name, coordinates, properties=properties)

    @staticmethod
    def trim_name(name: str, pattern: str) -> str:
        """Trim the given block name to remove the given pattern, also gets rid of 'minecraft:"""
        return name.replace('minecraft:', '').replace(pattern, '')

    @property
    def full_name(self) -> str:
        """Return the full name of the block, properties included"""
        properties = [f'{key}={value}' for key, value in self.properties.items()]
        indicator = '[' + ', '.join(properties) + ']' if properties else ''
        return f'{self.name}{indicator}'

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
                    return Block(name, self.coordinates, properties=self.properties)
        return self

    def neighbouring_coordinates(self) -> List[Coordinates]:
        """Return the list of all this block's neighbouring coordinates"""
        return [self.coordinates.towards(direction) for direction in Direction]

    def shift_position_to(self, coordinates: Coordinates) -> Block:
        """Return a new block with the same name and properties but whose coordinates were shifted"""
        return Block(self.name, self.coordinates.shift(*coordinates), properties=self.properties)

    def is_one_of(self, pattern: Tuple[str]) -> bool:
        """Return true if the current item's name matches the given pattern"""
        for part in pattern:
            if part in self.name:
                return True
        return False

    def __hash__(self) -> int:
        """Return the hashed value of the current block"""
        return hash(self.coordinates)

    def __str__(self) -> str:
        """Return the string representation of the block"""
        return self.full_name

    def rotate(self, angle: float, rotation_point: Coordinates = Coordinates(0, 0, 0)) -> Block:

        properties = self.properties.copy()
        if 'facing' in properties:
            properties['facing'] = properties['facing'].get_rotated_direction(angle)

        return Block(self.name, self.coordinates.rotate(angle, rotation_point), properties)
