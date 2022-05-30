from __future__ import annotations

from typing import Iterator
from dataclasses import dataclass, field
from collections.abc import MutableMapping

from nbt.nbt import TAG_Compound
from src.utils.direction import Direction


#
Property = str | Direction


@dataclass(slots=True)
class BlockProperties(MutableMapping):
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

    def __getitem__(self, key: str) -> Property:
        """"""
        return self.__properties.__getitem__(key)

    def __setitem__(self, key: str, value: Property) -> None:
        """"""
        self.__properties.__setitem__(key, value)

    def __delitem__(self, key: Property) -> None:
        """"""
        self.__properties.__delitem__(key)

    def __iter__(self) -> Iterator[str]:
        """"""
        return self.__properties.__iter__()

    def __len__(self) -> int:
        """Return the number of properties"""
        return len(self.__properties)

    def __str__(self) -> str:
        """"""
        return f'BlockProperties({{{self.__properties}}})'
