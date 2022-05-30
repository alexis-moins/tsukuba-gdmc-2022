from __future__ import annotations

from typing import Dict, List, Tuple
from dataclasses import dataclass, replace, field

from gdpc import lookup
from nbt.nbt import TAG_Compound, TAG_List

from src.blocks.utils.block_properties import BlockProperties

from src.utils.direction import Direction
from src.utils.coordinates import Coordinates


@dataclass(frozen=True)
class Block:
    """Represents a block in the world, along with its coordinates and properties"""
    name: str
    coordinates: Coordinates
    properties: BlockProperties = field(default_factory=BlockProperties)

    @staticmethod
    def parse_nbt(block: TAG_Compound, palette: TAG_List) -> Block:
        """Return a new block object parsed from the given NBT [block] tag compound and [palette]"""
        index = int(block['state'].valuestr())
        name = palette[index]['Name'].valuestr()

        properties = BlockProperties()
        if 'Properties' in palette[index].keys():
            properties = BlockProperties.parse_nbt(palette[index]['Properties'])

        coordinates = Coordinates.parse_nbt(block['pos'])
        return Block(name, coordinates, properties)

    @staticmethod
    def deserialize(name: str, coordinates: Coordinates) -> Block:
        """"""
        properties = dict()

        if '[' in name:
            raw_properties = name.split('[')
            name = raw_properties[0]
            properties = dict((key.strip(), value.strip())
                              for key, value in (element.split('=')
                                                 for element in raw_properties[1][:-1].split(', ')))

        return Block(name, coordinates, properties=BlockProperties(properties))

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
        return block_name.split('[')[0] in lookup.BLOCKS

    def replace_first(self, materials: Dict[str, tuple[str, bool]]) -> Block:
        """Return a new block whose material has been replaced by the first match of the given building materials"""
        for material, replacement in materials.items():
            if material in self.name:
                name = self.name.replace(material, replacement[0])

                if Block.exists(name):
                    return Block(name, self.coordinates, properties=self.properties if replacement[1] else {})
        return self

    def neighbouring_coordinates(self, directions: tuple[Direction] = None) -> List[Coordinates]:
        """Return the list of all this block's neighbouring coordinates"""
        return self.coordinates.neighbours(directions)

    def shift_position_to(self, coordinates: Coordinates) -> Block:
        """Return a new block with the same name and properties but whose coordinates were shifted"""
        return Block(self.name, self.coordinates.shift(*coordinates), properties=self.properties)

    def is_one_of(self, pattern: str | Tuple[str, ...]) -> bool:
        """Return true if the current item's name matches the given pattern"""
        if type(pattern) == str:
            pattern = (pattern, )

        for part in pattern:
            if part in self.name:
                return True
        return False

    def rotate(self, angle: float, rotation_point: Coordinates = Coordinates(0, 0, 0)) -> Block:
        """Rotate the block coordinates and modify its properties to mimic rotation around a given rotation point"""
        if 'facing' in self.properties:
            self.properties['facing'] = self.properties['facing'].get_rotated_direction(angle)

        # invert axis between x and z
        if 'axis' in self.properties and (angle == 90 or angle == 270):
            if self.properties['axis'] == 'x':
                self.properties['axis'] = 'z'
            elif self.properties['axis'] == 'z':
                self.properties['axis'] = 'x'

        return replace(self, coordinates=self.coordinates.rotate(angle, rotation_point))

    def with_name(self, new_name: str, erase_properties: bool = False):
        """Return a block with the same properties and coordinates but different name"""
        if erase_properties:
            return replace(self, name=new_name, properties={})

        return replace(self, name=new_name)

    def __hash__(self) -> int:
        """Return the hashed value of the current block"""
        return hash(self.coordinates)

    def __str__(self) -> str:
        """Return the string representation of the block"""
        return self.full_name
