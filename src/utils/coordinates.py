from __future__ import annotations

import math
import textwrap
from dataclasses import astuple
from dataclasses import dataclass
from typing import Any
from typing import Iterator

import numpy as np
from gdpc import interface
from nbt.nbt import TAG_List

from src.utils.direction import Direction


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

    def get_rotation_shift(self, rotation: int):
        shift_due_to_rotation = Coordinates(0, 0, 0)
        if rotation == 90:
            shift_due_to_rotation = Coordinates(self.z - 1, 0, 0)
        elif rotation == 180:
            shift_due_to_rotation = Coordinates(self.x - 1, 0, self.z - 1)
        elif rotation == 270:
            shift_due_to_rotation = Coordinates(0, 0, self.x - 1)
        return shift_due_to_rotation

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

    def min(self, value: int):
        """Return a new size of minimal size between the given value and the current size"""
        return Size(min(self.x, value), min(self.z, value))


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

    def neighbours(self, directions: tuple[Direction] = None) -> list[Coordinates]:
        """Return the list of neighbouring coordinates of the current coordinates"""
        if directions is None:
            directions = Direction
        return [self.towards(direction) for direction in directions]

    def with_points(self, x: int = None, y: int = None, z: int = None) -> Coordinates:
        """"""
        return Coordinates(x if x is not None else self.x,
                           y if y is not None else self.y,
                           z if z is not None else self.z)

    def towards(self, direction: Direction) -> Coordinates:
        """Return the next coordinates in the given direction (from the current coordinates)"""
        return Coordinates(self.x + direction.value[0], self.y + direction.value[1], self.z + direction.value[2])

    def distance(self, other: Any) -> int:
        """Return the Manhattan distance between two coordinates"""
        if not isinstance(other, Coordinates):
            raise Exception(f'Cannot compute distance between Coordinates and {type(other)}')

        difference = abs(self - other)
        return difference.x + difference.y + difference.z

    def shift(self, x: int = 0, y: int = 0, z: int = 0) -> Coordinates:
        """Return a new coordinates formed with the current coordinates whose values where shifted"""
        return Coordinates(self.x + x, self.y + y, self.z + z)

    def as_2D(self) -> Coordinates:
        """Return a new coordinates with y = 0"""
        return Coordinates(self.x, 0, self.z)

    def rotate(self, angle: int, rotation_point: Coordinates = None, compense_shift_size: Size = None) -> Coordinates:
        if not rotation_point:
            rotation_point = Coordinates(0, 0, 0)

        rotated_x, rotated_z = R(np.deg2rad(angle)) @ (self - rotation_point).xz
        rotated_x, rotated_z = round(rotated_x), round(rotated_z)

        new_point = Coordinates(rotated_x, self.y, rotated_z) + rotation_point
        if compense_shift_size:
            new_point = new_point + compense_shift_size.get_rotation_shift(angle)

        return new_point

    def around_2d(self, radius, y=None):
        if y is None:
            y = self.y
        point = self.with_points(y=y)
        for x in range(- radius, radius + 1, 1):
            for z in range(- radius, radius + 1, 1):
                yield point.shift(x=x, z=z)

    def line(self, length: int, direction: Direction):
        current = self
        for i in range(length):
            current = current.towards(direction)
            yield current

    def place_sign(self, text, replace_block: bool = False, rotation: int = 0):
        texts = textwrap.wrap(text, width=15) + ["", "", ""]

        data = "{" + f'Text1:\'{{"text":"{texts[0]}"}}\','
        data += f'Text2:\'{{"text":"{texts[1]}"}}\','
        data += f'Text3:\'{{"text":"{texts[2]}"}}\','
        data += f'Text4:\'{{"text":"{texts[3]}"}}\'' + "}"
        if replace_block:
            interface.placeBlock(self.x, self.y, self.z, f'oak_sign[rotation={rotation}]')
        interface.sendBlocks()
        interface.runCommand(f"data merge block {self.x} {self.y} {self.z} {data}")

    def angle(self, other: Coordinates):
        return math.atan2(self.z - other.z, self.x - other.x)

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
        return iter((self.x, self.y, self.z))

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
