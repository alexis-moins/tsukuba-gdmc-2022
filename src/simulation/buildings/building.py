from __future__ import annotations

import random
import textwrap
from dataclasses import dataclass
from dataclasses import replace
from typing import Any

from colorama import Fore
from gdpc import interface as INTERFACE
from gdpc import lookup
from gdpc import toolbox

from src import env
from src.blocks.block import Block
from src.blocks.collections import palette
from src.blocks.collections.block_list import BlockList
from src.blocks.collections.palette import Palette
from src.blocks.structure import Structure
from src.plots.plot import Plot
from src.simulation.buildings.building_type import BuildingType
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

    def __init__(self, name: str, properties: BuildingProperties, structure: Structure, extension: bool = False, maximum: int = 1):
        """Parameterised constructor creating a new building"""
        self.name = name
        self.properties = replace(properties)  # Return a copy of the dataclass
        self.__structure = structure
        self.old_blocks: dict[Block, Block] = {}
        self.is_extension = extension
        self.max_number = maximum

        self.inhabitants = set()
        self.workers = set()

        self.plot: Plot = None
        self.rotation: int = None
        self.blocks: BlockList = None
        self.entrances: BlockList = None

    @staticmethod
    def deserialize(building: dict[str, Any]) -> Building:
        """Return a new building deserialized from the given dictionary"""
        if building['type'] == 'MINING':
            return Mine.deserialize(building.copy())

        properties = {key.replace(' ', '_'): value
                      for key, value in building.pop('properties').items()}

        action_type = ActionType[building.pop('action').upper()]
        building_type = BuildingType[building.pop('type').upper()]
        properties = BuildingProperties(**properties,
                                        action_type=action_type, building_type=building_type)

        structure = Structure.parse_nbt_file(building.pop('path'))
        return Building(properties=properties, structure=structure, **building)

    def has_empty_beds(self) -> bool:
        """"""
        return len(self.inhabitants) < self.properties.number_of_beds

    def can_offer_work(self) -> bool:
        """"""
        return len(self.workers) < self.properties.workers

    def add_inhabitant(self, villager) -> None:
        """"""
        self.inhabitants.add(villager)
        villager.house = self

    def add_worker(self, villager) -> None:
        """"""
        self.workers.add(villager)
        villager.work_place = self

    def get_size(self, rotation: int) -> Size:
        """Return the size of the building considering the given rotation"""
        return self.__structure.get_size(rotation)

    def get_entrance_shift(self, rotation: int) -> Coordinates:
        entrances = self.__structure.get_blocks(Coordinates(0, 0, 0), rotation).filter('emerald')
        if not entrances or len(entrances) < 1:
            return Coordinates(0, 0, 0)
        return entrances[0].coordinates

    def build(self, plot: Plot, rotation: int, city: Plot):
        """Build the current building onto the building's plot"""
        self.plot = plot
        self.rotation = rotation
        self._build_structure(self.__structure, self.plot, self.rotation)

        surface = city.get_blocks(Criteria.MOTION_BLOCKING_NO_TREES)

        if self.properties.building_type is BuildingType.FARM and not self.is_extension:
            for coordinates in self.plot.surface(padding=6):
                if coordinates not in self.plot and coordinates.as_2D() not in city.all_roads:

                    if (block := surface.find(coordinates.as_2D())) is None:
                        continue

                    if block.name not in ('minecraft:grass_block', 'minecraft:sand', 'minecraft:stone', 'minecraft:dirt'):
                        continue

                    block_name = random.choices(['farmland', 'water'], [90, 10])[0]

                    if block_name == 'water':
                        for c in block.neighbouring_coordinates((Direction.NORTH, Direction.SOUTH, Direction.EAST, Direction.WEST, Direction.DOWN)):
                            if city.get_block_at(*c).name in lookup.AIR + lookup.PLANTS + ('minecraft:snow',):
                                block_name = 'farmland'
                                break

                    INTERFACE.placeBlock(*block.coordinates, f'minecraft:{block_name}')

                    if block_name == 'farmland':
                        INTERFACE.placeBlock(*block.coordinates.shift(y=1), random.choice(lookup.CROPS))

        self._place_sign()
        INTERFACE.sendBlocks()

    def _build_structure(self, structure: Structure, plot: Plot, rotation: int):
        self.blocks = structure.get_blocks(plot.start, rotation)
        self.entrances = self.blocks.filter('emerald')
        # Apply palette
        if self.properties.building_type in env.ALL_PALETTES:
            self._randomize_building(dict(env.ALL_PALETTES[self.properties.building_type]))
        for block in self.blocks:
            INTERFACE.placeBlock(*block.coordinates, block.full_name)

    def _place_sign(self):
        """Place a sign indicating informations about the building"""
        if not self.blocks:
            return

        signs = self.blocks.filter('sign')
        if not signs:
            return
        x, y, z = signs[0].coordinates
        texts = textwrap.wrap(self.get_display_name(), width=15) + ["", "", ""]

        data = "{" + f'Text1:\'{{"text":"{texts[0]}"}}\','
        data += f'Text2:\'{{"text":"{texts[1]}"}}\','
        data += f'Text3:\'{{"text":"{texts[2]}"}}\','
        data += f'Text4:\'{{"text":"{texts[3]}"}}\'' + "}"
        INTERFACE.sendBlocks()
        INTERFACE.runCommand(f"data merge block {x} {y} {z} {data}")

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
        adjectives = ['beautiful', 'breakable', 'bright', 'busy', 'calm', 'charming', 'comfortable', 'creepy',
                      'cute',
                      'dangerous', 'dark', 'enchanting', 'evil', 'fancy', 'fantastic', 'fragile', 'friendly',
                      'lazy',
                      'kind',
                      'long', 'lovely', 'magnificent', 'muddy', 'mysterious', 'open', 'plain', 'pleasant', 'quaint']
        return f'The {random.choice(adjectives)} {self.name}'


class Mine(Building):
    def __init__(self, name: str, properties: BuildingProperties, structures: list[Structure], is_extension: bool, maximum):
        super().__init__(name, properties, structures[0], is_extension, maximum)
        self.structures = structures
        self.depth = None
        # self.crane = random.randint(0, 1)
        self.crane = True  # For test purpose, always true

    @staticmethod
    def deserialize(building: dict[str, Any]) -> Building:
        """Return a new building deserialized from the given dictionary"""

        properties = {key.replace(' ', '_'): value
                      for key, value in building['properties'].items()}

        action_type = ActionType[building['action'].upper()]
        building_type = BuildingType[building['type'].upper()]
        properties = BuildingProperties(**properties,
                                        action_type=action_type, building_type=building_type)

        structures = [Structure.parse_nbt_file(file) for file in building['path']]
        return Mine(building['name'], properties, structures, is_extension=False, maximum=building['maximum'])

    def build(self, plot: Plot, rotation: int, city: Plot):
        if not self.depth:
            self.depth = random.randint(2, 10)

        # rotation = 90
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

        if self.crane:
            plot.start = start.shift(x=-1, y=2, z=3).rotate(rotation, rotation_point=start)
            input(plot.start)
            self._build_structure(self.structures[2], plot, rotation)

        plot.start = start  # reset start
        self.entrances = self.blocks.filter('emerald')
        self._place_sign()
        INTERFACE.sendBlocks()


def direction2rotation(directions):
    """**Convert a direction to a rotation**.

    If a sequence is provided, the average is returned.
    """
    reference = {'north': 0, 'east': 4, 'south': 8, 'west': 12}
    if len(directions) == 1:
        rotation = reference[lookup.INVERTDIRECTION[directions[0]]]
    else:

        if len(directions) == 3:
            input(directions)
        rotation = 0
        # Compute average
        for direction in directions:
            rotation += reference[lookup.INVERTDIRECTION[direction]]
        rotation = round(rotation / len(directions))

        # rotate 180°
        rotation = rotation % 16

    return rotation
