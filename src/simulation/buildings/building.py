from __future__ import annotations
from abc import ABC, abstractclassmethod

import math
import random
from dataclasses import replace
from typing import Any, Callable

from colorama import Fore
from gdpc import lookup as LOOKUP
from gdpc import interface as INTERFACE
from src.simulation.villager import Villager

from src.utils import math_utils

from src.plots.plot import Plot
from src.blocks.block import Block
from src.blocks.structure import Structure, get_structure
from src.blocks.collections.block_list import BlockList
from src.blocks.utils.palette import OneBlockPalette, Palette


from src.utils.criteria import Criteria
from src.utils.direction import Direction
from src.utils.coordinates import Coordinates, Size

from src.simulation.buildings.utils.building_type import BuildingType
from src.simulation.buildings.utils.building_properties import BuildingProperties


# Tuple of available adjectives for building names
_adjectives = ('beautiful', 'breakable', 'bright', 'busy', 'calm', 'charming', 'comfortable', 'creepy', 'cute', 'dangerous', 'dark', 'enchanting', 'evil',
               'fancy', 'fantastic', 'fragile', 'friendly', 'lazy', 'kind', 'long', 'lovely', 'magnificent', 'muddy', 'mysterious', 'open', 'plain', 'pleasant', 'quaint')


class Blueprint(ABC):
    """Represents an abstract building plan regrouping usefull common methods"""

    def __init__(self, name: str, properties: BuildingProperties, structures: list[Structure], palettes: dict[str, Palette]):
        """Creates a new building with the given [name], [properties], basic [structures] and [palettes]
        that may dynamically change the blocks used in the different structures"""
        self.name = name
        self.properties = replace(properties)
        self.structures = structures
        self.palettes = palettes

        self.rotation = random.choice([0, 90, 180, 270])
        self.adjective = random.choice(_adjectives)

        self.workers = set()
        self.inhabitants = set()

        self.history = []
        self.entrance: Coordinates = None
        self.blocks: dict[Structure, BlockList] = {}

    @abstractclassmethod
    def build(self, plot: Plot, settlement: Plot) -> None:
        """Build the building onto the given [plot], using data from the [settlement]"""
        pass

    @staticmethod
    def deserialize(name: str, data: dict[str, Any]) -> Building:
        """Return a new building deserialized from the given [name] and [data]. The returned
        object might be any subclass of Blueprint as well, one of Mine, Graveyard, Wedding
        Totem and Tower"""
        data = dict(data)

        structures = [get_structure(path) for path in data.pop('path')]
        palettes = data.pop('palettes', [])

        properties = BuildingProperties.deserialize(data, data.pop('resource'), data.pop('type'))

        # Getting the class constructor
        constructor = BUILDING_CLASSES[properties.type] if properties.type in BUILDING_CLASSES else Building
        return constructor(name, properties, structures, Palette.parse_groups(palettes))

    @property
    def full_name(self) -> str:
        """Return the full name of the building. Full name is following this particular
        format: 'The {adjective} {name}' where adjective is randomly generated upon creating
        the instance, and name is the building's name"""
        return f'The {self.adjective} {self.name.lower()}'

    @property
    def has_empty_beds(self) -> bool:
        """Return true if the building has empty beds, return false otherwise"""
        return len(self.inhabitants) < self.properties.number_of_beds

    @property
    def can_offer_work(self) -> bool:
        """Return true if the building has available worker slots, return
        false otherwise"""
        return len(self.workers) < self.properties.workers

    def get_size(self) -> Size:
        """Return the size of the building considering the building rotation. This method uses the first
        structure associated with the building as the main building structure abd thus return its size"""
        return self.structures[0].get_size(self.rotation)

    def add_inhabitant(self, villager: Villager, year: int) -> None:
        """Add the given [villager] to to this building as a new inhabitant"""
        self.inhabitants.add(villager)
        villager.house = self

        self.history.append(f'Year {year}:\n {villager.name} is now living in the {self.name.lower()}')

    def add_worker(self, villager, year: int) -> None:
        """"""
        self.workers.add(villager)
        villager.work_place = self

        self.history.append(f'Year {year}:\n {villager.name} has started working at the {self.name.lower()}')

    def grow_old(self, amount: int) -> None:
        """Make a building grow old"""
        # TODO
        pass
        # # ensure it stays between 0 and 100
        # amount = abs(amount) % 100
        # sample: list[Block] = random.sample(self.blocks.without(('air', 'water')),
        #                                     amount * len(self.blocks.without(('air', 'water'))) // 100)

        # for block in sample:

        #     if block.is_one_of(('lectern', 'rail', 'sign')):
        #         continue

        #     materials = {
        #         'cobblestone': ('mossy_cobblestone', True),
        #         'mossy_stone': ('cracked_stone', True),
        #         'stone': ('mossy_stone', True),
        #         'planks': ('stairs', False)
        #     }

        #     replacement = block.replace_first(materials)

        #     if replacement is not block and Block.exists(replacement.name):
        #         if 'stairs' in replacement.name:
        #             facing = random.choice(['north', 'east', 'south', 'west'])
        #             half = random.choice(['top', 'bottom'])
        #             shape = random.choice(['inner_left', 'inner_right', 'outer_left', 'outer_right', 'straight'])
        #             replacement = replace(replacement, properties={'facing': facing, 'half': half, 'shape': shape})

        #     else:
        #         population = (block.name, 'oak_leaves', 'cobweb')
        #         weights = (60, 30, 10)

        #         name = random.choices(population, weights, k=1)

        #         if name == block.name:
        #             continue

        #         replacement = Block(name[0], block.coordinates, properties={
        #             'persistent': 'true'} if name[0] == 'oak_leaves' else {})

        #     INTERFACE.placeBlock(*replacement.coordinates, replacement.full_name)

        # INTERFACE.sendBlocks()

    def set_on_fire(self, amount: int) -> None:
        """"""
        pass
        # TODO
        # # ensure it stays between 0 and 100
        # amount = abs(amount) % 100
        # sample: list[Block] = random.sample(self.blocks.without(('air', 'water')),
        #                                     amount * len(self.blocks.without(('air', 'water'))) // 100)

        # for block in sample:

        #     if block.is_one_of(('lectern', 'rail', 'sign')):
        #         continue

        #     population = (block.name, 'basalt', 'magma_block', 'soul_sand', 'blackstone_stairs', 'air')
        #     weights = (5, 27, 25, 20, 20, 3)

        #     name = random.choices(population, weights, k=1)

        #     if name == block.name:
        #         continue

        #     if 'stairs' in name:
        #         facing = random.choice(['north', 'east', 'south', 'west'])
        #         half = random.choice(['top', 'bottom'])
        #         shape = random.choice(['inner_left', 'inner_right', 'outer_left', 'outer_right', 'straight'])
        #         replacement = replace(block, properties={'facing': facing, 'half': half, 'shape': shape})
        #     else:
        #         replacement = replace(block, name=name[0], properties={})

        #     INTERFACE.placeBlock(*replacement.coordinates, replacement.full_name)

        # INTERFACE.sendBlocks()

    def get_entrance_with_rotation(self, rotation: int) -> Coordinates:
        """"""
        entrances = self.structures[0].get_blocks(Coordinates(0, 0, 0), rotation).filter('emerald')
        if not entrances or len(entrances) < 1:
            return Coordinates(0, 0, 0)
        return entrances[0].coordinates

        # TODO
        # entrances = self.structures[0].blocks.filter('emerald')

        # if not entrances:
        #     return Coordinates(0, 0, 0)

        # return entrances[0].coordinates.rotate(rotation)

    def _find_entrance(self, start: Coordinates) -> Coordinates | None:
        """"""
        # TODO do it better
        if self.structures[0] in self.blocks:
            entrances = self.blocks[self.structures[0]].filter('emerald')
            return entrances[0].coordinates if entrances else start

        return None

    def _build_structure(self, structure: Structure, start: Coordinates, palettes: dict[str, Palette] | None = None):
        """Build the given [structure] at the given [start] coordinates, optionally using the
        given block [palettes] instead of the palettes from this building"""
        blocks = structure.get_blocks(start, self.rotation)

        # Use the blocks from the palettes
        blocks = blocks.apply_palettes(palettes if palettes else self.palettes)
        self.blocks[structure] = blocks

        if self.entrance is None:
            self.entrance = self._find_entrance(start)

        # Actually placing the blocks
        for block in blocks:
            # print(f'BUILD => {block.name} {block.coordinates} {block.properties}\n')
            INTERFACE.placeBlock(*block.coordinates, block.full_name)

    def _place_sign(self):
        """Place a sign indicating informations about the building"""
        first_structure = self.structures[0]
        signs = self.blocks[first_structure].filter('sign')

        if not signs:
            return

        signs[0].coordinates.place_sign(self.full_name)

    def __str__(self) -> str:
        """Return the string representation of the building"""
        return f'{Fore.MAGENTA}{self.name}{Fore.WHITE}'


class Building(Blueprint):
    """Represents a generic building"""

    def build(self, plot: Plot, settlement: Plot):
        """Build the building onto the given [plot], using data from the [settlement]"""
        for structure in self.structures:
            self._build_structure(structure, plot.start)

        self._place_sign()
        INTERFACE.sendBlocks()


class Tower(Building):
    def __init__(self, parent, structures):
        super().__init__(parent)
        self.structures = structures

    def build(self, plot: Plot, rotation: int, city: Plot):
        self.plot = plot
        self.rotation = rotation
        start = plot.start
        dict_palette = {'white_terracotta': OneBlockPalette([color + '_terracotta' for color in LOOKUP.COLORS])}
        self._build_structure(self.structures[0], plot, rotation, palettes=dict_palette)

        plot.start = plot.start.shift(y=4)

        for i in range(random.randint(10, min(30, 255 - self.plot.start.y))):
            self._build_structure(self.structures[1], plot, rotation, palettes=dict_palette)
            plot.start = plot.start.shift(y=1)

        self._build_structure(self.structures[2], plot, rotation, palettes=dict_palette)
        plot.start = start  # reset start
        self.entrance = self.blocks.filter('emerald')
        self._place_sign()
        INTERFACE.sendBlocks()

    @staticmethod
    def deserialize_tower(building: dict[str, Any], parent: Building) -> Building:
        """Return a new building deserialized from the given dictionary"""
        structures = [Structure.deserialize_nbt_file(file) for file in building['path']]
        return Tower(parent, structures)


class BuildingWithSlots(Building):
    def __init__(self, parent: Building, slot_pattern: str):
        super().__init__(parent)
        self.free_slots: list[Block] = []
        self.occupied_slots: list[Block] = []
        self.slot_block = slot_pattern

    def build(self, plot: Plot, rotation: int, city: Plot):
        self.free_slots = list(self.structures.get_blocks(plot.start, rotation).filter(self.slot_block))
        super().build(plot, rotation, city)

    def get_free_slot(self):
        if not self.free_slots:
            return None
        slot = self.free_slots.pop()
        self.occupied_slots.append(slot)
        return slot


class Graveyard(BuildingWithSlots):
    def __init__(self, parent: Building):
        super().__init__(parent, 'diamond_block')

    def add_tomb(self, villager, year: int, cause: str):
        slot = super().get_free_slot()
        if slot:
            INTERFACE.placeBlock(*slot.coordinates, 'stone_bricks')
            if self.entrance and self.entrance[0]:
                sign_angle = slot.coordinates.angle(self.entrance[0].coordinates)
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


class WeddingTotem(BuildingWithSlots):
    def __init__(self, parent: Building):
        super().__init__(parent, 'cornflower')

    def add_wedding(self):
        slot = super().get_free_slot()
        if slot:
            INTERFACE.placeBlock(*slot.coordinates, random.choice(LOOKUP.FLOWERS))


class Farm(Building):
    """"""

    def __init__(self, name: str, properties: BuildingProperties, structures: list[Structure], palettes: list[str] = None):
        """Creates a new building with the given [name], [properties] and basic [structure].
        Optionally, a [palette] can may be specified to dynamically change the blocks of the
        structure when generating on a plot"""
        super().__init__(name, properties, structures, palettes)

    def build(self, plot: Plot, settlement: Plot) -> None:
        """"""
        super().build(plot, settlement)

        surface = settlement.get_blocks(Criteria.MOTION_BLOCKING_NO_TREES)

        farm_field: set[Coordinates] = set()
        for coordinates in plot.surface(padding=6):
            if coordinates not in plot and coordinates.as_2D() not in settlement.all_roads:

                if (block := surface.find(coordinates.as_2D())) is None:
                    continue

                if block.name not in (
                        'minecraft:grass_block', 'minecraft:sand', 'minecraft:stone', 'minecraft:dirt', 'minecraft:podzol'):
                    continue

                farm_field.add(block.coordinates)
                block_name = random.choices(['farmland[moisture=7]', 'lapis_block'], [90, 10])[0]
                INTERFACE.placeBlock(*block.coordinates, f'minecraft:{block_name}')

                if 'farmland' in block_name:
                    INTERFACE.placeBlock(*block.coordinates.shift(y=1), random.choice(LOOKUP.CROPS))

        INTERFACE.sendBlocks()

        for coordinates in farm_field:
            block = plot.get_block_at(*coordinates)
            # print(block.name)
            if block.is_one_of('lapis'):
                for c in block.neighbouring_coordinates(
                        (Direction.NORTH, Direction.SOUTH, Direction.EAST, Direction.WEST, Direction.DOWN)):
                    if settlement.get_block_at(*c).name in LOOKUP.AIR + LOOKUP.PLANTS + ('minecraft:snow',):
                        INTERFACE.placeBlock(*block.coordinates, 'redstone_lamp[lit=true]')
                    else:
                        INTERFACE.placeBlock(*block.coordinates, 'water')


class Mine(Building):
    """"""

    def __init__(self, name: str, properties: BuildingProperties, structures: list[Structure], palettes: dict[str, Palette] | None = None):
        """Creates a new building with the given [name], [properties] and basic [structure].
        Optionally, a [palette] can may be specified to dynamically change the blocks of the
        structure when generating on a plot"""
        super().__init__(name, properties, structures, palettes)
        self.floor_number: int = random.randint(2, 10)

    def build(self, plot: Plot, settlement: Plot):
        """"""
        # set as starting rotation | need a 180 rotation between the 2 modules
        rotation_index = (270, 180, 90, 0).index(self.rotation) + 2

        stairs_start = plot.start.shift(y=1)
        for _ in range(self.floor_number):
            # Shift every coordinates by 180 at each iteration
            rotation_index = (rotation_index + 1) % 4
            stairs_start = stairs_start.shift(y=-5)

            self._build_structure(self.structures[1], stairs_start)

        self._build_structure(self.structures[0], plot.start)

        # 1/2 chances of building a crane
        if random.randint(0, 1):
            self._build_crane(plot.start)

        self._place_sign()
        INTERFACE.sendBlocks()

    def _build_crane(self, start: Coordinates) -> None:
        """Build a crane on top of the mine, """
        crane_coordinates = self.__get_crane_coordinates(start)
        self._build_structure(self.structures[2], crane_coordinates)

        center = start.shift(x=4, y=4, z=4)
        rope_length = random.randint(1, self.floor_number * 5 - 6)

        for _ in range(rope_length):
            self._build_structure(self.structures[3], center)
            center = center.shift(y=-1)

        self._build_structure(self.structures[4], center.shift(y=-1))

    def __get_crane_coordinates(self, start: Coordinates) -> Coordinates:
        """Return the starting position of the crane on the form of coordinates, relatively
        to the given [start]ing coordinates"""
        if self.rotation == 0:
            return start.shift(x=-1, y=2, z=4)

        if self.rotation == 90:
            return start.shift(x=-1, y=2, z=-1)

        if self.rotation == 180:
            return start.shift(x=4, y=2, z=-1)

        return start.shift(x=4, y=2, z=4)


    # Default dictionary mapping building type to their Building object
BUILDING_CLASSES: dict[BuildingType, Callable[..., Building]] = {
    BuildingType.FARM: Farm,
    BuildingType.MINING: Mine
}
