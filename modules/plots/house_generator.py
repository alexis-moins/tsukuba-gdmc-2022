# Class utility is only to load modules 1 time and store them
# Should be a singleton so
import random
from functools import reduce
from typing import List
from typing import Tuple

from gdpc import geometry
from gdpc import geometry as GEO
from gdpc import interface as INTF

from modules.blocks.structure import Structure
from modules.plots.construction_plot import ConstructionPlot
from modules.utils.coordinates import Coordinates
from modules.utils.direction import Direction


class HouseGenerator:
    def __init__(self):
        self.walls: dict[tuple, list[Structure]] = dict()
        self.walls[(2, 2)] = [Structure.parse_nbt_file('modules/walls/wall_2x1_plain_a')]
        self.walls[(3, 2)] = [Structure.parse_nbt_file('modules/walls/wall_3x2_plain_a')]
        self.walls[(4, 2)] = [Structure.parse_nbt_file('modules/walls/wall_4x2_plain_a')]
        self.walls[(5, 2)] = [Structure.parse_nbt_file('modules/walls/wall_5x2_window_a')]
        self.walls[(6, 2)] = [Structure.parse_nbt_file('modules/walls/wall_6x2_window_a')]
        self.walls[(7, 2)] = [Structure.parse_nbt_file('modules/walls/wall_7x2_window_a')]

        self.corners: dict[tuple, list[Structure]] = dict()
        self.corners[(2, 2)] = [Structure.parse_nbt_file('modules/corners/corner_2x2_plain_a')]
        self.corners[(3, 3)] = [Structure.parse_nbt_file('modules/corners/corner_3x3_plain_a')]
        self.corners[(4, 4)] = [Structure.parse_nbt_file('modules/corners/corner_4x4_plain_a')]



    # Could be a function in construction plot ?
    def build_house(self, storey_amount: int, profession: str, construction_plot: ConstructionPlot):

        size = construction_plot.size
        short_side = min(size)
        # At the moment, only one outline width, might change in the future
        outline_width = 2

        # Let's say minimal house indoor size is 3x3
        min_indoor_size = 3
        # If there is a profession, we need 5x5 to fit the profession module
        if profession != 'none':
            min_indoor_size = 5


        # Check validity
        min_house_size = min_indoor_size + 2 * outline_width
        if short_side < min_house_size:
            raise Exception(f'Not enough space ({size}) ! (min : {min_house_size})')


        # define corners size

        # Define this depending on available corners modules sizes
        max_available_corner_size = 4

        max_corner_size = (short_side - min_indoor_size) // 2
        max_corner_size = min(max_corner_size, max_available_corner_size)
        corner_size = random.randint(outline_width, max_corner_size)


        # define wall sequence
        # explanation of length_needed
        # + 2 because of each corners having one intersecting point with the wall
        """Long explanation for the + 2
        our pattern joins elements (corners/walls) by having on all of them the same extremities and superposing them.

        So, for example, a wall of size 4 has : [extremity , block , block , extremity]
        and if we add another wall of size 4 we obtain : [extremity , block , block , extremity , block , block , extremity]
        which would be a wall of size 7

        Since our corners make up for 2 intersections, we add + 2 to the length needed
        """
        if size[0] != size[1]:
            sides = []
            for side in size:
                length_needed = side - (2 * corner_size) + 2
                sides.append((side, self.get_wall_sequence(length_needed)))
        else:
            length_needed = size[0] - (2 * corner_size) + 2
            wall_sq = self.get_wall_sequence(length_needed)
            sides = [(size[0], wall_sq), (size[1], wall_sq)]


        construction_plot.build_foundation(construction_plot.build_start.y)

        print(f'wall sequence : {sides[0][1]}')

        # first side
        x_shift = 0

        for b in random.choice(self.corners[(corner_size, corner_size)]).get_blocks_for(construction_plot):

            INTF.placeBlock(*b.coordinates.shift(x_shift, 1, 0), b.name)
        x_shift += corner_size - 1

        for wall in sides[0][1]:
            for b in random.choice(self.walls[(wall, outline_width)]).get_blocks_for(construction_plot):

                INTF.placeBlock(*b.coordinates.shift(x_shift, 1, 0), b.name)
            x_shift += wall - 1


        z_shift = 0
        for b in random.choice(self.corners[(corner_size, corner_size)]).get_blocks_for(construction_plot):
            INTF.placeBlock(*b.coordinates.shift(0, 1, z_shift), b.name)
        z_shift += corner_size - 1

        for wall in sides[1][1]:
            for b in random.choice(self.walls[(wall, outline_width)]).get_blocks_for(construction_plot):
                INTF.placeBlock(*b.coordinates.shift(0, 1, z_shift), b.name)
            z_shift += wall - 1





    @staticmethod
    def get_wall_sequence(length_needed: int):
        """Return a wall sequence for a needed length"""

        # Defined by modules
        max_available_wall = 7
        min_available_wall = 2
        even_walls = [2, 4, 6]
        odd_walls = [3, 5, 7]
        all_walls = even_walls + odd_walls

        wall_sequence = []
        # We divide the length needed by 2 because we want our wall sequence to be symmetrical
        # So we make a distinction between odd and even length_needed
        if length_needed % 2 == 0:
            length_needed //= 2
            filtered_walls = list(filter(lambda w: w <= length_needed, even_walls))
            middle_wall = random.choices(*HouseGenerator.generate_values_and_weights(filtered_walls), k=1)[0]

        else:
            length_needed //= 2
            filtered_walls = list(filter(lambda w: w <= length_needed, odd_walls))
            middle_wall = random.choices(*HouseGenerator.generate_values_and_weights(filtered_walls), k=1)[0]
        length_needed -= (middle_wall // 2)

        # Now for the remaining length
        while length_needed > 0:
            filtered_walls = list(filter(lambda w: w <= length_needed + 1, all_walls))
            chose_wall = random.choices(*HouseGenerator.generate_values_and_weights(filtered_walls), k=1)[0]
            # - 1 because of superposition point
            length_needed -= (chose_wall - 1)
            wall_sequence.append(chose_wall)

        random.shuffle(wall_sequence)
        wall_sequence = wall_sequence + [middle_wall] + wall_sequence[::-1]

        return wall_sequence

    @staticmethod
    def generate_values_and_weights(values: List, pow_factor: int = 3):
        values.sort()
        powered_values = sorted(map(lambda v: v ** pow_factor, values))
        values_sum = sum(powered_values)
        weights = sorted(map(lambda v: v / values_sum, powered_values))
        return values, weights



if __name__ == "__main__":
    print("TESTING HOUSE GENERATOR")


    print(Direction.EAST.get_rotated_direction(90))

    # print('rotation coordinate test')
    #
    # center = Coordinates(10, 0, 0)
    #
    # point = Coordinates(1000, 0, 3000)
    #
    # print(point)
    # print(point.rotate(270, center))

    # print("wall sequence test")
    #
    # values = list(range(8, 20))
    #
    # for v in values:
    #     for i in range(5):
    #         print(f'{v} : {HouseGenerator.get_wall_sequence(v)}')
    #     print()
