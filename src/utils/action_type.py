from __future__ import annotations
from enum import Enum


class ResourceType(Enum):
    """"""

    NONE = -1
    BED = 0
    FOOD = 1
    WORK = 2
    DECORATION = 3
    UTILITY = 4

    @staticmethod
    def deserialize(_type: str) -> ResourceType:
        """Return the resource type corresponding to the given [_type]"""
        key = _type.upper()
        return ResourceType[key]
