from __future__ import annotations

from typing import Iterator
from dataclasses import dataclass, field
from collections.abc import Mapping

from nbt.nbt import TAG_Compound
from src.utils.direction import Direction


#
Property = str | Direction


@dataclass(slots=True)
class BlockProperties(Mapping):
    """Represents the any properties of a block in the world"""
    __properties: dict[str, Property] = field(default_factory=dict)

    @staticmethod
    def parse_nbt(properties: TAG_Compound) -> BlockProperties:
        """Return a dictionary of the given pared properties"""
        props = {key: (Direction.parse_nbt(value) if key == 'facing' else value.valuestr())
                 for key, value in properties.iteritems()}

        return BlockProperties(props)

    # [facing=north,axis=y]
    @staticmethod
    def deserialize(data: str) -> BlockProperties:
        """"""
        print(data)

    def rotate(self, angle: int) -> BlockProperties:
        """"""
        properties = dict(self.__properties)

        if 'facing' in self:
            properties['facing'] = self['facing'].get_rotated_direction(angle)

        # invert axis between x and z
        if 'axis' in self and (angle == 90 or angle == 270):

            if self['axis'] == 'x':
                properties['axis'] = 'z'

            elif self['axis'] == 'z':
                properties['axis'] = 'x'

        return BlockProperties(properties)

    def __getitem__(self, key: str) -> Property:
        """"""
        return self.__properties.__getitem__(key)

    def __iter__(self) -> Iterator[str]:
        """"""
        return self.__properties.__iter__()

    def __len__(self) -> int:
        """Return the number of properties"""
        return len(self.__properties)

    def __str__(self) -> str:
        """"""
        return f'BlockProperties({self.__properties})'
