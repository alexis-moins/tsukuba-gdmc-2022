from __future__ import annotations
from enum import Enum


class Resource(Enum):
    """"""

    NONE = -1
    BED = 0
    FOOD = 1
    WORK = 2
    DECORATION = 3
    UTILITY = 4

    @staticmethod
    def deserialize(_type: str) -> Resource:
        """Return the resource type corresponding to the given [_type]"""
        key = _type.upper()
        return Resource[key]
