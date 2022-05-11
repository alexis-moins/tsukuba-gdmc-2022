from __future__ import annotations

import random
from dataclasses import dataclass
from dataclasses import replace
from typing import Any

from colorama import Fore
from gdpc import interface as INTERFACE, toolbox, lookup

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

    def __init__(self, name: str, properties: BuildingProperties, structure: Structure, extension: bool = False, maximum: int = 99):
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

    def get_entrance_shift(self) -> Coordinates:
        entrances = self.__structure.blocks.filter('emerald')
        if not entrances or len(entrances) < 1:
            return Coordinates(0, 0, 0)
        return entrances[0].coordinates

    def build(self, plot: Plot, rotation: int, city: Plot):
        """Build the current building onto the building's plot"""
        self.plot = plot
        self.rotation = rotation
        self._build_structure(self.__structure, self.plot, self.rotation)

        if self.properties.building_type is BuildingType.FARM and not self.is_extension:
            for coordinates in self.plot.surface(padding=6):
                if coordinates not in self.plot and coordinates.as_2D() not in city.all_roads:
                    surface = city.get_blocks(Criteria.MOTION_BLOCKING_NO_TREES)

                    if (block := surface.find(coordinates.as_2D())) is None:
                        continue

                    block_name = random.choices(['farmland', 'water'], [97, 3])[0]

                    INTERFACE.placeBlock(*block.coordinates, f'minecraft:{block_name}')

                    if block_name == 'farmland':
                        INTERFACE.placeBlock(*block.coordinates.shift(y=1), 'minecraft:wheat')


        self._place_sign(rotation)
        INTERFACE.sendBlocks()

    def _build_structure(self, structure: Structure, plot: Plot, rotation: int):
        self.blocks = structure.get_blocks(plot.start, rotation)
        self.entrances = self.blocks.filter('emerald')
        # Apply palette
        if self.properties.building_type in env.ALL_PALETTES:
            self._randomize_building(dict(env.ALL_PALETTES[self.properties.building_type]))
        for block in self.blocks:
            INTERFACE.placeBlock(*block.coordinates, block.full_name)

    def _place_sign(self, rotation: int):
        """Place a sign indicating informations about the building"""
        if not self.entrances:
            return None
        INTERFACE.sendBlocks()
        sign_coord = self.entrances[0].coordinates.shift(y=1)
        if env.DEBUG:
            self.build_sign_in_world(sign_coord, text1=self.name, text2=f'rotation : {self.rotation}', rotation=rotation)
        else:
            text = self.get_display_name()
            self.build_sign_in_world(sign_coord, text1=text[:15], text2=text[15:30], text3=text[30:45], text4=text[45:60], rotation=rotation)

        for entrance in self.entrances:
            neighbours = [self.plot.get_block_at(*coordinates)
                          for coordinates in entrance.neighbouring_coordinates()]

            block_name = BlockList(neighbours).without(
                ('air', 'grass', 'sand', 'water')).most_common

            if block_name is not None:
                INTERFACE.placeBlock(*entrance.coordinates, block_name)

    def grow_old(self, amount: int) -> None:
        """Make a building grow old"""

        # ensure it stays between 0 and 100
        amount = abs(amount) % 100
        sample: list[Block] = random.sample(self.blocks.without(('air', 'water')),
                                            amount * len(self.blocks.without(('air', 'water'))) // 100)

        for block in sample:

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

    def build_sign_in_world(self, coord: Coordinates, text1: str = "", text2: str = "", text3: str = "",
                            text4: str = "", rotation: int = 0):
        x, y, z = coord

        direction = toolbox.getOptimalDirection(x, y, z)
        minecraft_rotation = direction2rotation(direction)
        INTERFACE.placeBlock(x, y, z, f"oak_sign[rotation={minecraft_rotation}]")
        INTERFACE.sendBlocks()

        data = "{" + f'Text1:\'{{"text":"{text1}"}}\','
        data += f'Text2:\'{{"text":"{text2}"}}\','
        data += f'Text3:\'{{"text":"{text3}"}}\','
        data += f'Text4:\'{{"text":"{text4}"}}\'' + "}"
        INTERFACE.runCommand(f"data merge block {x} {y} {z} {data}")

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
    def __init__(self, name: str, properties: BuildingProperties, structures: list[Structure], is_extension: bool):
        super().__init__(name, properties, structures[0], is_extension)
        self.structures = structures

    @ staticmethod
    def deserialize(building: dict[str, Any]) -> Building:
        """Return a new building deserialized from the given dictionary"""

        properties = {key.replace(' ', '_'): value
                      for key, value in building['properties'].items()}

        action_type = ActionType[building['action'].upper()]
        building_type = BuildingType[building['type'].upper()]
        properties = BuildingProperties(**properties,
                                        action_type=action_type, building_type=building_type)

        structures = list(map(Structure.parse_nbt_file, building['path'].split(',')))
        return Mine(building['name'], properties, structures, is_extension=False)

    def build(self, plot: Plot, rotation: int, city: Plot, depth: int = 0):
        if not depth:
            depth = random.randint(2, 10)

        self.plot = plot
        self.rotation = rotation
        rotations = [270, 180, 90, 0]
        rotation_index = rotations.index(rotation) + 2  # set as starting rotation | need a 180 rotation between the
        # 2 modules

        start = plot.start

        for i in range(depth):
            rotation_index = (rotation_index + 1) % 4
            plot.start = plot.start.shift(y=-5)

            self._build_structure(self.structures[1], plot, rotations[rotation_index])

        # build top in last
        plot.start = start  # reset start
        self._build_structure(self.structures[0], plot, rotation)

        self.entrances = self.blocks.filter('emerald')
        self._place_sign(rotation)
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
