from __future__ import annotations

import math
import random
import textwrap
from dataclasses import dataclass
from dataclasses import replace
from typing import Any

from colorama import Fore
from gdpc import interface as INTERFACE
from gdpc import lookup

from src import env
from src.blocks.block import Block
from src.blocks.collections import palette
from src.blocks.collections.block_list import BlockList
from src.blocks.collections.palette import Palette, RandomPalette, OneBlockPalette
from src.blocks.structure import Structure
from src.plots.plot import Plot
from src.simulation.buildings.building_type import BuildingType
from src.utils import math_utils
from src.utils.action_type import ActionType
from src.utils.coordinates import Coordinates
from src.utils.coordinates import Size
from src.utils.criteria import Criteria
from src.utils.direction import Direction


@dataclass(kw_only=True)
class BuildingProperties:
    """Class representing the properties of a building"""
    cost: int
    building_type: BuildingType
    action_type: ActionType
    number_of_beds: int = 0
    workers: int = 0
    food_production: int = 0


class Building:
    """Class representing a list of blocks (structure) on a given plot"""

    def __init__(self, name: str, properties: BuildingProperties, structure: Structure, extension: bool = False,
                 maximum: int = 1):
        """Parameterised constructor creating a new building"""
        self.name = name
        self.properties = replace(properties)  # Return a copy of the dataclass
        self.structure = structure
        self.old_blocks: dict[Block, Block] = {}
        self.is_extension = extension
        self.max_number = maximum
        self.history = []

        self.inhabitants = set()
        self.workers = set()

        self.plot: Plot = None
        self.rotation: int = None
        self.blocks: BlockList = None
        self.entrances: BlockList = None
        self.display_name = None

    @staticmethod
    def deserialize(building_info: dict[str, Any]) -> Building:
        """Return a new building deserialized from the given dictionary"""
        original = building_info.copy()
        properties = {key.replace(' ', '_'): value
                      for key, value in building_info.pop('properties').items()}

        action_type = ActionType[building_info.pop('action').upper()]
        building_type = BuildingType[building_info.pop('type').upper()]
        properties = BuildingProperties(**properties,
                                        action_type=action_type, building_type=building_type)

        path = building_info.pop('path')
        if isinstance(path, list):
            path = path[0]
        structure = Structure.parse_nbt_file(path)

        build = Building(properties=properties, structure=structure, **building_info)

        if build.name == 'Mine':
            return Mine.deserialize_mine(original, build)
        elif build.name == 'Graveyard':
            return Graveyard(parent=build)
        elif build.name == 'Wedding Totem':
            return WeddingTotem(parent=build)
        elif build.name == 'Tower':
            return Tower.deserialize_tower(original, build)

        return build

    def has_empty_beds(self) -> bool:
        """"""
        return len(self.inhabitants) < self.properties.number_of_beds

    def can_offer_work(self) -> bool:
        """"""
        return len(self.workers) < self.properties.workers

    def add_inhabitant(self, villager, year: int) -> None:
        """"""
        self.inhabitants.add(villager)
        villager.house = self

        self.history.append(f'Year {year}:\n {villager.name} is now living in the {self.name.lower()}')

    def add_worker(self, villager, year: int) -> None:
        """"""
        self.workers.add(villager)
        villager.work_place = self
        self.history.append(f'Year {year}:\n {villager.name} has started working at the {self.name.lower()}')

    def get_size(self, rotation: int) -> Size:
        """Return the size of the building considering the given rotation"""
        return self.structure.get_size(rotation)

    def get_entrance_shift(self, rotation: int) -> Coordinates:
        entrances = self.structure.get_blocks(Coordinates(0, 0, 0), rotation).filter('emerald')
        if not entrances or len(entrances) < 1:
            return Coordinates(0, 0, 0)
        return entrances[0].coordinates

    def build(self, plot: Plot, rotation: int, city: Plot):
        """Build the current building onto the building's plot"""
        self.plot = plot
        self.rotation = rotation
        self._build_structure(self.structure, self.plot, self.rotation)

        surface = city.get_blocks(Criteria.MOTION_BLOCKING_NO_TREES)

        if self.properties.building_type is BuildingType.FARM and not self.is_extension:
            for coordinates in self.plot.surface(padding=6):
                if coordinates not in self.plot and coordinates.as_2D() not in city.all_roads:

                    if (block := surface.find(coordinates.as_2D())) is None:
                        continue

                    if block.name not in (
                            'minecraft:grass_block', 'minecraft:sand', 'minecraft:stone', 'minecraft:dirt'):
                        continue

                    block_name = random.choices(['farmland', 'water'], [90, 10])[0]

                    if block_name == 'water':
                        for c in block.neighbouring_coordinates(
                                (Direction.NORTH, Direction.SOUTH, Direction.EAST, Direction.WEST, Direction.DOWN)):
                            if city.get_block_at(*c).name in lookup.AIR + lookup.PLANTS + ('minecraft:snow',):
                                block_name = 'farmland'
                                break

                    INTERFACE.placeBlock(*block.coordinates, f'minecraft:{block_name}')

                    if block_name == 'farmland':
                        INTERFACE.placeBlock(*block.coordinates.shift(y=1), random.choice(lookup.CROPS))

        self._place_sign()
        INTERFACE.sendBlocks()

    def _build_structure(self, structure: Structure, plot: Plot, rotation: int,
                         force_palette: dict[str, Palette] = None):
        self.blocks = structure.get_blocks(plot.start, rotation)
        self.entrances = self.blocks.filter('emerald')
        # Apply palette
        if self.properties.building_type in env.ALL_PALETTES and force_palette is None:
            self._randomize_building(dict(env.ALL_PALETTES[self.properties.building_type]))
        elif force_palette is not None:
            self._randomize_building(force_palette)
        for block in self.blocks:
            INTERFACE.placeBlock(*block.coordinates, block.full_name)

    def _place_sign(self):
        """Place a sign indicating informations about the building"""
        if not self.blocks:
            return

        signs = self.blocks.filter('sign')
        if not signs:
            return

        signs[0].coordinates.place_sign(self.get_display_name())

    def grow_old(self, amount: int) -> None:
        """Make a building grow old"""

        # ensure it stays between 0 and 100
        amount = abs(amount) % 100
        sample: list[Block] = random.sample(self.blocks.without(('air', 'water')),
                                            amount * len(self.blocks.without(('air', 'water'))) // 100)

        for block in sample:

            if block.is_one_of(('lectern', 'rail', 'sign')):
                continue

            materials = {
                'cobblestone': ('mossy_cobblestone', True),
                'mossy_stone': ('cracked_stone', True),
                'stone': ('mossy_stone', True),
                'planks': ('stairs', False)
            }

            replacement = block.replace_first(materials)

            if replacement is not block and Block.exists(replacement.name):
                if 'stairs' in replacement.name:
                    facing = random.choice(['north', 'east', 'south', 'west'])
                    half = random.choice(['top', 'bottom'])
                    shape = random.choice(['inner_left', 'inner_right', 'outer_left', 'outer_right', 'straight'])
                    replacement = replace(replacement, properties={'facing': facing, 'half': half, 'shape': shape})
                self.old_blocks[block] = replacement

            else:
                population = (block.name, 'oak_leaves', 'cobweb')
                weights = (60, 30, 10)

                name = random.choices(population, weights, k=1)

                if name == block.name:
                    continue

                replacement = Block(name[0], block.coordinates, properties={
                    'persistent': 'true'} if name[0] == 'oak_leaves' else {})
                self.old_blocks[block] = replacement

            INTERFACE.placeBlock(*replacement.coordinates, replacement.full_name)

        INTERFACE.sendBlocks()

    def repair(self, amount: int) -> None:
        """"""
        for original_block in random.sample(list(self.old_blocks.keys()), amount):
            INTERFACE.placeBlock(*original_block.coordinates, original_block.full_name)
            del self.old_blocks[original_block]

        INTERFACE.sendBlocks()

    def __str__(self) -> str:
        """Return the string representation of the current building"""
        return f'{Fore.MAGENTA}{self.name}{Fore.WHITE}'

    def _randomize_building(self, palettes: dict[str, Palette | list]):
        """Create a new block list with modified blocks according to given palettes"""
        new_block_list = []

        # prepare palettes
        for key in palettes:
            if isinstance(palettes[key], list):
                palettes[key] = palette.OneBlockPalette(palettes[key])

        for b in self.blocks:
            current_name = b.name.replace('minecraft:', '')
            if current_name in palettes:
                new_block_list.append(b.with_name(palettes[current_name].get_block_name()))
            else:
                new_block_list.append(b)

        self.blocks = BlockList(new_block_list)

    def get_display_name(self):
        if not self.display_name:
            adjectives = ['beautiful', 'breakable', 'bright', 'busy', 'calm', 'charming', 'comfortable', 'creepy',
                          'cute',
                          'dangerous', 'dark', 'enchanting', 'evil', 'fancy', 'fantastic', 'fragile', 'friendly',
                          'lazy',
                          'kind',
                          'long', 'lovely', 'magnificent', 'muddy', 'mysterious', 'open', 'plain', 'pleasant', 'quaint']
            self.display_name = f'The {random.choice(adjectives)} {self.name.lower()}'
        return self.display_name


class ChildBuilding(Building):
    def __init__(self, parent: Building):
        super().__init__(parent.name, parent.properties, parent.structure, parent.is_extension, parent.max_number)


class Mine(ChildBuilding):
    def __init__(self, parent, structures):
        super().__init__(parent)
        self.structures = structures
        self.depth = None

    @staticmethod
    def deserialize_mine(building: dict[str, Any], parent: Building) -> Building:
        """Return a new building deserialized from the given dictionary"""
        structures = [Structure.parse_nbt_file(file) for file in building['path']]
        return Mine(parent, structures)

    def build(self, plot: Plot, rotation: int, city: Plot):
        if not self.depth:
            self.depth = random.randint(2, 10)

        self.plot = plot
        self.rotation = rotation
        rotations = [270, 180, 90, 0]
        rotation_index = rotations.index(rotation) + 2  # set as starting rotation | need a 180 rotation between the
        # 2 modules

        start = plot.start
        plot.start = plot.start.shift(y=1)

        for i in range(self.depth):
            rotation_index = (rotation_index + 1) % 4
            plot.start = plot.start.shift(y=-5)

            self._build_structure(self.structures[1], plot, rotations[rotation_index])

        plot.start = start  # reset start

        self._build_structure(self.structures[0], plot, rotation)

        # 1/2 chances of building a crane
        if random.randint(0, 1):
            # Yes it is cheating, but if you can, do it with a proper rotation system.
            if rotation == 0:
                plot.start = start.shift(x=-1, y=2, z=4)
            elif rotation == 90:
                plot.start = start.shift(x=-1, y=2, z=-1)
            elif rotation == 180:
                plot.start = start.shift(x=4, y=2, z=-1)
            elif rotation == 270:
                plot.start = start.shift(x=4, y=2, z=4)

            self._build_structure(self.structures[2], plot, rotation)

            plot.start = start.shift(x=4, y=4, z=4)
            max_depth = self.depth * 5 - 6
            rope_length = random.randint(1, max_depth)
            for i in range(rope_length):
                self._build_structure(self.structures[3], plot, rotation)
                plot.start = plot.start.shift(y=-1)
            plot.start = plot.start.shift(y=-5)
            self._build_structure(self.structures[4], plot, rotation)

        plot.start = start  # reset start
        self.entrances = self.blocks.filter('emerald')
        self._place_sign()
        INTERFACE.sendBlocks()


class Tower(ChildBuilding):
    def __init__(self, parent, structures):
        super().__init__(parent)
        self.structures = structures

    def build(self, plot: Plot, rotation: int, city: Plot):
        self.plot = plot
        self.rotation = rotation
        start = plot.start
        dict_palette = {'white_terracotta': OneBlockPalette([color + '_stained_glass' for color in lookup.COLORS])}
        self._build_structure(self.structures[0], plot, rotation, force_palette=dict_palette)

        plot.start = plot.start.shift(y=4)

        for i in range(random.randint(10, min(30, 255 - self.plot.start.y))):
            self._build_structure(self.structures[1], plot, rotation, force_palette=dict_palette)
            plot.start = plot.start.shift(y=1)

        self._build_structure(self.structures[2], plot, rotation, force_palette=dict_palette)
        plot.start = start  # reset start
        self.entrances = self.blocks.filter('emerald')
        self._place_sign()
        INTERFACE.sendBlocks()

    @staticmethod
    def deserialize_tower(building: dict[str, Any], parent: Building) -> Building:
        """Return a new building deserialized from the given dictionary"""
        structures = [Structure.parse_nbt_file(file) for file in building['path']]
        return Tower(parent, structures)


class ChildWithSlots(ChildBuilding):
    def __init__(self, parent: Building, slot_pattern: str):
        super().__init__(parent)
        self.free_slots: list[Block] = []
        self.occupied_slots: list[Block] = []
        self.slot_block = slot_pattern

    def build(self, plot: Plot, rotation: int, city: Plot):
        self.free_slots = list(self.structure.get_blocks(plot.start, rotation).filter(self.slot_block))
        super().build(plot, rotation, city)

    def get_free_slot(self):
        if not self.free_slots:
            return None
        slot = self.free_slots.pop()
        self.occupied_slots.append(slot)
        return slot


class Graveyard(ChildWithSlots):
    def __init__(self, parent: Building):
        super().__init__(parent, 'diamond_block')

    def add_tomb(self, villager, year: int, cause: str):
        slot = super().get_free_slot()
        if slot:
            INTERFACE.placeBlock(*slot.coordinates, 'stone_bricks')
            if self.entrances and self.entrances[0]:
                sign_angle = slot.coordinates.angle(self.entrances[0].coordinates)
                slot.coordinates.shift(y=1).place_sign(f'{villager.name} died of {cause} {villager.birth_year}-{year}',
                                                       replace_block=True,
                                                       rotation=math_utils.radian_to_orientation(sign_angle,
                                                                                                 -math.pi / 2))
                x, y, z = slot.coordinates
                INTERFACE.placeBlock(x, y - 1, z, 'air')
                INTERFACE.placeBlock(x, y - 2, z, 'air')
                INTERFACE.sendBlocks()
                INTERFACE.runCommand(f'summon zombie {x} {y - 2} {z} {{CustomName:"\\"{villager.name}\\""}}')

    def grow_old(self, amount: int) -> None:
        pass


class WeddingTotem(ChildWithSlots):
    def __init__(self, parent: Building):
        super().__init__(parent, 'cornflower')

    def add_wedding(self):
        slot = super().get_free_slot()
        if slot:
            INTERFACE.placeBlock(*slot.coordinates, random.choice(lookup.FLOWERS))
