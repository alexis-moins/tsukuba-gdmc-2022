from __future__ import annotations

import numpy as np
from nbt.nbt import TAG_List
from typing import Any, Iterator
from dataclasses import astuple, dataclass

from modules.utils.direction import Direction


def R(a: float):
    """a, angle in radians"""
    c, s = np.cos(a), np.sin(a)
    return np.array(((c, -s), (s, c)))


@dataclass(frozen=True)
class Size:
    """Class representing a 2 dimensional size"""
    x: int
    z: int

    @staticmethod
    def from_coordinates(start: Coordinates, end: Coordinates) -> Size:
        """Return a new size computed from the two given coordinates"""
        distance = abs(start - end)
        return Size(distance.x, distance.z)

    def __add__(self, other):
        if isinstance(other, Size):
            return Size(self.x + other.x, self.z + other.z)
        else:
            return Size(self.x + other, self.z + other)

    def __sub__(self, other):
        if isinstance(other, Size):
            return Size(self.x - other.x, self.z - other.z)
        else:
            return Size(self.x - other, self.z - other)



@dataclass(frozen=True)
class Coordinates:
    """Represents a set of x, y and z coordinates"""
    x: int
    y: int
    z: int

    @staticmethod
    def parse_nbt(position: TAG_List) -> Coordinates:
        """Return the coordinates cooresponding to the given NBT tag list"""
        return Coordinates(x=int(position[0].valuestr()),
                           y=int(position[1].valuestr()),
                           z=int(position[2].valuestr()))

    def neighbours(self) -> list[Coordinates]:
        """Return the list of neighbouring coordinates of the current coordinates"""
        return [self.towards(direction) for direction in Direction]

    def with_points(self, x: int = None, y: int = None, z: int = None) -> Coordinates:
        """"""
        return Coordinates(x if x else self.x,
                           y if y else self.y,
                           z if z else self.z)

    def towards(self, direction: Direction) -> Coordinates:
        """Return the next coordinates in the given direction (from the current coordinates)"""
        return Coordinates(self.x + direction.value[0], self.y + direction.value[1], self.z + direction.value[2])

    def distance(self, other: Any) -> int:
        """Return the Manhattan distance between two coordinates"""
        if not isinstance(other, Coordinates):
            raise Exception(f'Cannot compute distance between Coordinates and {type(other)}')

        difference = abs(self - other)
        return difference.x + difference.y + difference.z

    def shift(self, x: int, y: int, z: int) -> Coordinates:
        """Return a new coordinates formed with the current coordinates whose values where shifted"""
        return Coordinates(self.x + x, self.y + y, self.z + z)

    def as_2D(self) -> Coordinates:
        """Return a new coordinates with y = 0"""
        return Coordinates(self.x, 0, self.z)

    def rotate(self, angle: float, rotation_point: Coordinates = None) -> Coordinates:
        if not rotation_point:
            rotation_point = Coordinates(0, 0, 0)

        rotated_x, rotated_z = R(np.deg2rad(angle)) @ (self - rotation_point).xz
        rotated_x, rotated_z = round(rotated_x), round(rotated_z)
        return Coordinates(rotated_x, self.y, rotated_z) + rotation_point

    @property
    def xz(self):
        return self.x, self.z

    def __eq__(self, other: Any) -> bool:
        """Return true if the given coordinates are equals to the current ones"""
        if not isinstance(other, Coordinates):
            raise Exception(f'Cannot compare Coordinates and {type(other)}')

        return self.x == other.x and self.y == other.y and self.z == other.z

    def __iter__(self) -> Iterator[int]:
        """Return an iterator over the current coordinates"""
        coordinates = astuple(self)
        return iter(coordinates)

    def __sub__(self, other: Any) -> Coordinates:
        """Return the substraction between the current coordinates and the given ones"""
        if not isinstance(other, Coordinates):
            raise Exception(f'Cannot substract Coordinates and {type(other)}')

        return Coordinates(self.x - other.x, self.y - other.y, self.z - other.z)

    def __add__(self, other: Any) -> Coordinates:
        """Return the addition between the current coordinates and the given ones"""
        if not isinstance(other, Coordinates):
            raise Exception(f'Cannot add Coordinates and {type(other)}')

        return Coordinates(self.x + other.x, self.y + other.y, self.z + other.z)

    def __abs__(self) -> Coordinates:
        """Return the absolute value of the coordinates"""
        return Coordinates(abs(self.x), abs(self.y), abs(self.z))
