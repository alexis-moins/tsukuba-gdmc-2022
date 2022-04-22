import time
from typing import Tuple

import nbt.nbt

from plots.plot import Plot
from utils.coordinates import Coordinates
from utils.criteria import Criteria
from gdpc import geometry as GEO
from gdpc import interface as INTF


class ConstructionPlot(Plot):

    def __init__(self, x: int, z: int, size: Tuple[int, int], build_start: Coordinates):
        super().__init__(x, z, size)
        self.build_start = build_start

    def build_foundation(self, foundation_level: int, main_block: str = 'stone_bricks') -> None:

        for coord in self._iterate_over_air(foundation_level):
            INTF.placeBlock(*coord, main_block)
        INTF.sendBlocks()

    def _iterate_over_air(self, max_y: int) -> Coordinates:
        for block in self.get_blocks_at_surface(Criteria.WORLD_SURFACE):
            y_shift = 1
            while block.coordinates.y + y_shift <= max_y:
                yield block.coordinates.shift(0, y_shift, 0)
                y_shift += 1

    def build_simple_house(self, main_bloc: str, height: int):
        """Build a 'house' of the main_bloc given, with north-west bottom corner as starting point, with the given size"""
        # Todo : finish the simple house

        self.build_foundation(self.build_start.y - 1)

        # body
        GEO.placeCuboid(self.build_start.x, self.build_start.y, self.build_start.z, self.build_start.x + self.size[0] - 1,
                        self.build_start.y + height - 1, self.build_start.z + self.size[1] - 1,
                        main_bloc, hollow=True)

        # Todo : add direction
        # Door
        INTF.placeBlock(self.build_start.x + self.size[0] // 2, self.build_start.y + 1, self.build_start.z, "oak_door")
        INTF.placeBlock(self.build_start.x + self.size[0] // 2, self.build_start.y + 2, self.build_start.z, "oak_door[half=upper]")
        INTF.sendBlocks()


HOUSES_SAVE_FILE = "resources/structures/houses"


def build_house_1(area, main_material):
    iter_start = time.time()
    file = nbt.nbt.NBTFile(HOUSES_SAVE_FILE + "/house1.nbt")
    size = [int(i.valuestr()) for i in file['size']]

    house_area = (size[0], size[2])

    house_construction_plot = area.get_construction_plot(house_area)

    if house_construction_plot is None:
        return

    structure_palette = file['palette']

    # Build the house using the blocks of the loaded struct
    for block in file['blocks']:
        block_coord_relative = [int(i.valuestr()) for i in block['pos']]
        block_coord = house_construction_plot.build_start.shift(*block_coord_relative)
        block_palette_id = int(block['state'].valuestr())

        block_material = structure_palette[block_palette_id]['Name'].valuestr()

        block_properties = ''
        if 'Properties' in structure_palette[block_palette_id].keys():
            properties_dict = structure_palette[block_palette_id]['Properties']
            block_properties = '[' + ", ".join(f'{k}={v}' for k, v in properties_dict.items()) + ']'
            print(block_properties)


        INTF.placeBlock(*block_coord, block_material + block_properties)

    print(
        f'=> Built house of size {size} at {house_construction_plot.build_start} in {time.time() - iter_start: .2f}s\n')

    INTF.sendBlocks()
