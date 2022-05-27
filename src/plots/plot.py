from __future__ import annotations

import math
import random
import time
import timeit
from collections import defaultdict
from typing import Generator

import networkx as nx
import numpy as np
from gdpc import interface as INTF
from gdpc import lookup
from numpy import ndarray

from src import env
from src.blocks.block import Block
from src.blocks.collections.block_list import BlockList
from src.simulation.buildings.building_type import BuildingType
from src.utils import math_utils
from src.utils.coordinates import Coordinates
from src.utils.coordinates import Size
from src.utils.criteria import Criteria
from src.utils.direction import Direction


class Plot:
    """Class representing a plot"""

    def __init__(self, x: int, y: int, z: int, size: Size) -> None:
        """Parameterised constructor creating a new plot inside the build area"""
        self.start = Coordinates(x, y, z)
        self.end = Coordinates(x + size.x, 255, z + size.z)
        self.size = size

        self.occupied_coordinates: set[Coordinates] = set()
        self.construction_coordinates: set[Coordinates] = set()

        self.surface_blocks: dict[Criteria, BlockList] = {}
        self.valid_terrain_blocks: dict[Size, list[Coordinates]] = {}
        self.offset = self.start - env.BUILD_AREA.start, self.end - env.BUILD_AREA.start

        # TODO change center into coordinates
        self.center = self.start.x + self.size.x // 2, self.start.z + self.size.z // 2

        self.steep_factor = 2
        self.steep_map = None
        self.priority_blocks: BlockList | None = None

        self.graph = None

        self.all_roads: set[Coordinates] = set()
        self.roads_infos: dict[str, defaultdict[Coordinates, int]] = {'INNER': defaultdict(int),
                                                                      'MIDDLE': defaultdict(int),
                                                                      'OUTER': defaultdict(int)}
        self.__recently_added_roads = None
        self.roads_y = None

        self.water_mode = 'water' in self.get_blocks(Criteria.MOTION_BLOCKING_NO_TREES).most_common

    def fill_graph(self):
        start = time.time()
        self.graph = nx.Graph()
        if self.steep_map is None:
            self.compute_steep_map()

        for block in self.get_blocks(Criteria.MOTION_BLOCKING_NO_TREES):
            self.graph.add_node(block.coordinates)

        for coordinates in self.graph.nodes.keys():
            for coord in coordinates.neighbours():
                if coord in self.graph.nodes.keys():
                    # self.graph.add_edge(coordinates, coord, weight=100 + abs(coord.y - coordinates.y) * 10)
                    malus = self.get_steep_map_value(coord)
                    if malus > 15:
                        malus = min(malus * 100, 100_000)
                    self.graph.add_edge(coordinates, coord, weight=100 + malus * 10)

        if env.SHOW_TIME:
            time_took = time.time() - start
            print(f'Computed graph in {time_took:.2f} s.')

    def equalize_roads(self):
        if len(self.all_roads) < 1:
            return
        self.roads_y = dict()

        for road in self.all_roads:
            neighbors_blocks = map(lambda coord: self.get_blocks(Criteria.MOTION_BLOCKING_NO_TREES).find(coord),
                                   filter(lambda r: r.as_2D() in self.all_roads, road.around_2d(5)))

            neighbors_y = list(map(lambda block: block.coordinates.y, filter(lambda block: block, neighbors_blocks)))

            # Maybe use median if you implement marching cube like technic for placing stairs
            # median_y = statistics.median_grouped(neighbors_y)
            average_y = sum(neighbors_y) / max(len(neighbors_y), 1)

            self.roads_y[road.as_2D()] = average_y

    def build_roads(self, floor_pattern: dict[str, dict[str, float]], slab_pattern=None):
        self.equalize_roads()

        roads = []

        # clean above roads
        for road in self.all_roads:
            for i in range(1, 20):
                coordinates = road.with_points(y=int(self.roads_y[road]) + i)

                if coordinates in self and coordinates.as_2D() not in self.construction_coordinates:
                    roads.append(self.get_blocks(Criteria.MOTION_BLOCKING_NO_LEAVES).find(coordinates))
                    INTF.placeBlock(*coordinates, 'air')

        self.remove_trees(BlockList(roads))

        # place blocks
        for key in self.roads_infos.keys():
            for road in self.roads_infos[key]:
                if road not in self:
                    continue
                # Default : place a block
                chose_pattern = floor_pattern
                shift = 0

                # If the average block y is near half :
                if slab_pattern and 0.5 < self.roads_y[road] - int(self.roads_y[road]):
                    # place a slab
                    chose_pattern = slab_pattern
                    shift = 1
                    if road.as_2D() in self.construction_coordinates:
                        continue

                x, y, z = (road.with_points(y=int(self.roads_y[road]) + shift))
                if road.as_2D() in self.construction_coordinates:
                    if not self.get_block_at(x, y, z).is_one_of(('air', 'grass', 'snow', 'sand', 'stone')):
                        continue

                the_blocks = random.choices(list(chose_pattern[key].keys()),
                                            k=1, weights=list(chose_pattern[key].values()))

                if the_blocks[0] in ('minecraft:shroomlight', 'minecraft:sea_lantern',
                                     'minecraft:glowstone', 'minecraft:redstone_lamp[lit=true]'):
                    INTF.placeBlock(x, y - 1, z, the_blocks)
                    INTF.placeBlock(x, y, z, 'minecraft:white_stained_glass')
                else:
                    if Coordinates(x, 0, z) in self.construction_coordinates:
                        continue

                    if 'note_block' in the_blocks[0]:
                        INTF.placeBlock(x, y + 1, z, random.choice(list(slab_pattern['OUTER'].keys())))

                    INTF.placeBlock(x, y, z, the_blocks)

        INTF.sendBlocks()

    def __add_road_block(self, coordinates: Coordinates, placement: str):

        road_coord = coordinates.as_2D()

        delete = False
        for key in self.roads_infos:
            if key == placement:
                if road_coord not in self.__recently_added_roads[placement]:
                    self.roads_infos[key][road_coord] += 1
                delete = True
            else:
                if road_coord in self.roads_infos[key]:
                    if delete:
                        self.roads_infos[key].pop(road_coord)
                    else:
                        return

        self.__recently_added_roads[placement].add(road_coord)
        self.all_roads.add(road_coord)
        self.occupied_coordinates.add(road_coord)

    def compute_roads(self, start: Coordinates, end: Coordinates) -> bool:
        time_start = time.time()
        if self.graph is None:
            self.fill_graph()

        start = b.coordinates if (b := self.get_blocks(Criteria.MOTION_BLOCKING_NO_TREES).find(start)) else start
        end = b.coordinates if (b := self.get_blocks(Criteria.MOTION_BLOCKING_NO_TREES).find(end)) else end

        try:
            path = nx.dijkstra_path(self.graph, start, end)
        except nx.NetworkXException:
            return False

        self.__recently_added_roads = {'INNER': set(), 'MIDDLE': set(), 'OUTER': set()}
        for coord in path:
            # INNER PART
            self.__add_road_block(coord, 'INNER')

            # MIDDLE PART
            self.__add_road_block(coord.shift(x=1), 'MIDDLE')
            self.__add_road_block(coord.shift(x=-1), 'MIDDLE')
            self.__add_road_block(coord.shift(z=1), 'MIDDLE')
            self.__add_road_block(coord.shift(z=-1), 'MIDDLE')

            # OUTER PART
            self.__add_road_block(coord.shift(x=1, z=1), 'OUTER')
            self.__add_road_block(coord.shift(x=-1, z=1), 'OUTER')
            self.__add_road_block(coord.shift(x=1, z=-1), 'OUTER')
            self.__add_road_block(coord.shift(x=-1, z=-1), 'OUTER')
            self.__add_road_block(coord.shift(x=2), 'OUTER')
            self.__add_road_block(coord.shift(x=-2), 'OUTER')
            self.__add_road_block(coord.shift(z=2), 'OUTER')
            self.__add_road_block(coord.shift(z=-2), 'OUTER')

        # Update weights to use the roads
        for c1, c2 in zip(path[:-2], path[1:]):
            if self.graph.has_edge(c1, c2):
                self.graph[c1][c2]['weight'] = 10

        if env.SHOW_TIME:
            time_took = time.time() - time_start
            print(f'Computed road from {start} to {end} in {time_took:.2f} s.')

        return True

    def add_roads_signs(self, amount: int, buildings: list):
        if not self.roads_y:
            self.equalize_roads()

        max_sign_height = min(5, len(buildings))
        min_sign_height = 2
        if len(buildings) <= min_sign_height:
            return
        for block in random.sample(self.all_roads, amount):
            block = block.with_points(y=round(self.roads_y[block]) + 1)
            for i, build in enumerate(random.sample(buildings, random.randint(min_sign_height, max_sign_height))):
                distance = block.distance(build.plot.start)

                angle = block.angle(build.plot.start)

                block.shift(y=i).place_sign(f"<------------  {distance} m           {build.get_display_name()}",
                                            replace_block=True,
                                            rotation=math_utils.radian_to_orientation(angle, shift=math.pi))

    def remove_lava(self):
        checked = set()
        lava_blocks = list(self.get_blocks(criteria=Criteria.MOTION_BLOCKING_NO_TREES).filter('lava'))
        while lava_blocks:
            block = lava_blocks.pop()
            checked.add(block)
            INTF.placeBlock(*block.coordinates, 'obsidian')  # water to cancel the lava

            # Check for neighbors
            for coord_neighbor in block.neighbouring_coordinates():
                neighbor = self.get_block_at(*coord_neighbor)
                if neighbor and 'lava' in neighbor.name and neighbor not in checked and coord_neighbor in self:
                    lava_blocks.append(neighbor)

        INTF.sendBlocks()

    @staticmethod
    def from_coordinates(start: Coordinates, end: Coordinates) -> Plot:
        """Return a new plot created from the given start and end coordinates"""
        return Plot(*start, Size.from_coordinates(start, end))

    def update(self) -> None:
        """Update the env.WORLD slice and most importantly the heightmaps"""
        env.get_world_slice()
        self.surface_blocks.clear()

    @staticmethod
    def _delta_sum(values: list, base: int) -> int:
        return sum(abs(base - v) for v in values)

    def flat_heightmap_to_plot_block(self, index: int) -> Block | None:
        surface = self.get_blocks(Criteria.MOTION_BLOCKING_NO_TREES)

        span = self.steep_factor

        side_length = self.size.x - 2 * span
        x = index // side_length
        z = index - side_length * x

        return surface.find(self.start.shift(x + span, 0, z + span))

    def compute_steep_map(self):
        span = self.steep_factor

        heightmap: np.ndarray = self.get_heightmap(Criteria.MOTION_BLOCKING_NO_TREES)
        water_value = 100_000_000 if not self.water_mode else 10
        steep = np.empty(shape=(self.size.x - 2 * span, self.size.z - 2 * span))
        for i in range(span, self.size.x - span):
            for j in range(span, self.size.z - span):
                block = self.get_blocks(Criteria.MOTION_BLOCKING_NO_TREES).find(self.start.shift(i, 0, j))
                if block.is_one_of(('water',)):
                    steep[i - span, j - span] = water_value
                else:
                    steep[i - span, j - span] = self._delta_sum(
                        heightmap[i - span: i + 1 + span, j - span: j + 1 + span].flatten(), heightmap[i, j])

        self.steep_map = steep.flatten()

        amount_of_prio = int((10 / 100) * self.steep_map.size)

        prio = np.argpartition(self.steep_map, amount_of_prio)[:amount_of_prio]
        blocks = []
        for p in prio:
            block = self.flat_heightmap_to_plot_block(p)
            if block and block not in self.occupied_coordinates:
                blocks.append(block)
        self.priority_blocks = BlockList(blocks)

    def visualize_roads(self, y_offset: int = 0):
        colors = ('lime', 'white', 'pink', 'yellow', 'orange', 'red', 'magenta', 'purple', 'black')
        materials = ('concrete', 'wool', 'stained_glass')
        self.equalize_roads()
        for i, key in enumerate(self.roads_infos):
            for road in self.roads_infos[key]:
                block = self.get_blocks(Criteria.MOTION_BLOCKING_NO_TREES).find(
                    road)  # to be sure that we are in the plot
                if block:
                    INTF.placeBlock(*(road.with_points(y=self.roads_y[road] + y_offset)),
                                    colors[min(self.roads_infos[key][road], len(colors)) - 1] + '_' + materials[i])

        INTF.sendBlocks()

    def visualize_occupied_area(self):
        for coord in self.occupied_coordinates:
            block = self.get_blocks(Criteria.MOTION_BLOCKING_NO_TREES).find(coord)
            if block:
                INTF.placeBlock(*(block.coordinates.shift(y=1)), 'red_stained_glass')
        INTF.sendBlocks()

    def visualize_graph(self):
        colors = ('lime', 'white', 'pink', 'yellow', 'orange', 'red', 'magenta', 'purple', 'black')
        for coord in self.graph.nodes():
            weights = list(map(lambda edge: self.graph[edge[0]][edge[1]]['weight'], self.graph.edges(coord)))
            if len(weights) == 0:
                chose_color = 'blue'
            else:
                coord_access_value = min(weights)
                chose_color = 'black'
                if coord_access_value < 50:
                    chose_color = colors[0]
                elif coord_access_value < 110:
                    continue  # 'default' value, don't show
                elif coord_access_value < 150:
                    chose_color = colors[2]
            INTF.placeBlock(*(coord.shift(y=1)), chose_color + '_stained_glass')
        INTF.sendBlocks()

    def visualize_steep_map(self):
        span = self.steep_factor
        colors = ('lime', 'white', 'pink', 'yellow', 'orange', 'red', 'magenta', 'purple', 'black')
        for i, value in enumerate(self.steep_map):
            block = self.flat_heightmap_to_plot_block(i, span)
            if block:
                INTF.placeBlock(*block.coordinates, colors[min(int(value // span), 8)] + '_stained_glass')
        INTF.sendBlocks()

    def visualize(self, ground: str = 'orange_wool', criteria: Criteria = Criteria.MOTION_BLOCKING_NO_TREES) -> None:
        """Change the blocks at the surface of the plot to visualize it"""
        for block in self.get_blocks(criteria):
            INTF.placeBlock(*block.coordinates, ground)
        INTF.sendBlocks()

    def get_block_at(self, x: int, y: int, z: int) -> Block:
        """Return the block found at the given x, y, z coordinates in the env.WORLD"""
        try:
            name = env.WORLD.getBlockAt(x, y, z)
            return Block.deserialize(name, Coordinates(x, y, z))
        except IndexError:
            return Block('out of bound', None)

    def get_heightmap(self, criteria: Criteria) -> ndarray:
        """Return the desired heightmap of the given type"""
        # Add our custom
        if Criteria.MOTION_BLOCKING_NO_TREES not in env.WORLD.heightmaps:
            env.WORLD.heightmaps[Criteria.MOTION_BLOCKING_NO_TREES.name] = self.__get_heightmap_no_trees()

        if criteria.name in env.WORLD.heightmaps.keys():
            return env.WORLD.heightmaps[criteria.name][self.offset[0].x:self.offset[1].x,
                   self.offset[0].z:self.offset[1].z]

        raise Exception(f'Invalid criteria: {criteria}')

    def get_blocks(self, criteria: Criteria) -> BlockList:
        """Return a list of the blocks at the surface of the plot, using the given criteria"""

        if criteria in self.surface_blocks.keys():
            return self.surface_blocks[criteria]

        surface = []
        heightmap = self.get_heightmap(criteria)

        for x, rest in enumerate(heightmap):
            for z, h in enumerate(rest):
                coordinates = Coordinates(self.start.x + x, h - 1, self.start.z + z)
                surface.append(self.get_block_at(*coordinates))

        self.surface_blocks[criteria] = BlockList(surface)
        return self.surface_blocks[criteria]

    def __get_heightmap_no_trees(self) -> np.ndarray:
        """Return a list of block representing a heightmap without trees

        It is not perfect as sometimes, there can be flower or grass or other blocks between the ground and the '
        floating' logs, but it is good enough for our use"""
        heightmap = np.copy(env.WORLD.heightmaps[Criteria.MOTION_BLOCKING_NO_LEAVES.name])

        for x, rest in enumerate(heightmap):
            for z, h in enumerate(rest):
                base_coord = Coordinates(env.BUILD_AREA.start.x + x, h - 1, env.BUILD_AREA.start.z + z)

                ground_coord = None
                # To get to the last block until the ground
                for ground_coord in self.__yield_until_ground(base_coord):
                    pass
                if ground_coord:
                    heightmap[x, z] = ground_coord.y

        return heightmap

    def get_subplot(self, building, rotation: int, padding: int = 5, city_buildings: list = None) -> Plot | None:
        """Return the best coordinates to place a building of a certain size, minimizing its score"""
        start = time.time()

        size = building.get_size(rotation)

        shift = building.get_entrance_shift(rotation)

        if self.graph is None:
            self.fill_graph()

        # TODO add .lower_than(max_height=200)

        if self.priority_blocks is None:
            self.compute_steep_map()
            if env.DEBUG:
                self.visualize_steep_map()
        block_checked = 0
        best_coords = None
        best_score = -1
        blocks_to_check = self.get_valid_coords(size, shift)
        coord_check_start = time.time()
        for block in blocks_to_check:
            score = self.__get_score(block.coordinates, building, size, shift, city_buildings)
            block_checked += 1
            INTF.placeBlock(*block.coordinates, 'red_wool')
            INTF.sendBlocks()
            if score > best_score:
                best_coords = block.coordinates

        if env.SHOW_TIME:
            time_took = time.time() - coord_check_start
            print(f'Check {block_checked} in {time_took} s, average : {block_checked / time_took if time_took != 0 else 1 :.2f} blocks per seconds.')

        if best_coords is None:
            return None

        sub_plot = Plot(*(best_coords - shift), size=size)

        # self.visualize_occupied_area()
        # sub_plot.visualize()
        # for x in range(size.x):
        #     for z in range(size.z):
        #         current_coord = sub_plot.start.shift(x - shift.x, 10, z - shift.z)
        #         INTF.placeBlock(*current_coord, 'blue_stained_glass')
        # for x in range(size.x):
        #     for z in range(size.z):
        #         current_coord = sub_plot.start.shift(x, 11, z)
        #         INTF.placeBlock(*current_coord, 'orange_stained_glass')
        # INTF.sendBlocks()
        # input('Enter to continue')

        coord = best_coords - shift
        if env.DEBUG:
            print(f"shift {shift}")
            print(best_coords in map(lambda b: b.coordinates, self.get_blocks(Criteria.MOTION_BLOCKING_NO_TREES)))
            print(best_coords)
            print(coord in map(lambda b: b.coordinates, self.get_blocks(Criteria.MOTION_BLOCKING_NO_TREES)))

        if building.properties.building_type is BuildingType.FARM:
            padding = 8

        if building.properties.building_type is BuildingType.DECORATION:
            padding = 2

        self.occupy_coords(padding, sub_plot)

        if env.DEBUG:
            self.visualize_roads(10)
            self.visualize_graph()

        if env.SHOW_TIME:
            time_took = time.time() - start
            print(f'Found plot for building {building.name} in {time_took:.2f} s.')

        return sub_plot

    def occupy_coords(self, padding, sub_plot):
        for coordinates in sub_plot.surface(padding):

            self.occupied_coordinates.add(coordinates.as_2D())

            block = self.get_blocks(Criteria.MOTION_BLOCKING_NO_TREES).find(coordinates)
            if block and block.coordinates.as_2D() not in self.all_roads:
                for edges in self.graph.edges(block.coordinates):
                    self.graph.add_edge(*edges, weight=100_000_000)
        for coordinates in sub_plot.surface():
            self.construction_coordinates.add(coordinates.as_2D())

    def build_valid_coords_terrain_wise(self, coord_to_check, accepted_score, surface, size, shift):
        blocks_scores = []
        blocks = []
        for block in coord_to_check:
            block_score = self.get_terrain_score(coordinates=block.coordinates, surface=surface, size=size, shift=shift)
            if block_score <= accepted_score:
                blocks_scores.append(block_score)
                blocks.append(block)

        k = min(round(0.05 * self.size.area), len(blocks) - 1)
        idx_of_bests = np.argpartition(blocks_scores, k)

        best_block = [blocks[i] for i in idx_of_bests]
        return best_block

    def fetch_valid_coord(self, size: Size):
        valid_coord = []
        for s, coords in self.valid_terrain_blocks.items():
            if size <= s:
                valid_coord += coords
        return valid_coord

    def build_coords_to_check(self):

        surface = self.get_blocks(Criteria.MOTION_BLOCKING_NO_TREES)
        excluded = ('water', 'lava')
        if self.water_mode:
            excluded = ('lava',)
        surface = surface.without(excluded).not_inside(self.occupied_coordinates)
        random_blocks = min(int(len(surface) * (20 / 100)), 5000)  # more than 5000 should be overkill, our
        # average plot area should like 60k blocks

        blocks_to_check = surface.random_elements(random_blocks)
        # Take 10 % of the best coordinates + a % of the rest, randomly
        blocks_to_check = self.priority_blocks.random_elements(
            max(1, int(len(self.priority_blocks) * 1 / 10))) + blocks_to_check

        return blocks_to_check, surface

    def get_valid_coords(self, size: Size, shift: Coordinates, bonus_tolerance: float = 0):
        valid_terrain_coords = self.fetch_valid_coord(size)
        print(f'Fetched coords : {len(valid_terrain_coords)}')
        if not valid_terrain_coords:
            print('Building valid terrain coords')
            start = time.time()
            max_score = size.area * (1 + bonus_tolerance)
            print(f'Step 1 : {time.time() - start:.2f} s')
            start = time.time()
            coords_to_check, surface = self.build_coords_to_check()
            print(f'Step 2 : {time.time() - start:.2f} s')
            start = time.time()
            valid_terrain_coords = self.build_valid_coords_terrain_wise(coords_to_check, max_score, surface, size,
                                                                        shift)
            print(f'Step 3 : {time.time() - start:.2f} s')
            self.valid_terrain_blocks[size] = valid_terrain_coords
        return valid_terrain_coords

    def get_terrain_score(self, coordinates: Coordinates, surface: BlockList, size: Size, shift: Coordinates):
        terrain_score = 0
        # Score = sum of difference between the first point's altitude and the other
        for x in range(size.x):
            for z in range(size.z):
                current_coord = coordinates.shift(x - shift.x, 0 - shift.y, z - shift.z)
                current_block = surface.find(current_coord)

                if not current_block or current_block.coordinates in self.occupied_coordinates:
                    return 100_000_000

                if current_block.is_one_of('water'):
                    # little malus to push it to generate on land
                    terrain_score += .5

                # putting foundation isn't a problem compared to digging in the terrain, so we apply a
                # worsening factor to digging
                to_add = coordinates.y - current_block.coordinates.y
                # placing foundation
                if to_add > 0:
                    terrain_score += int(to_add * .8)
                # digging (bad)
                else:
                    terrain_score += abs(to_add) * 3

        return terrain_score

    def __get_score(self, coordinates: Coordinates, building, size: Size, shift,
                    city_buildings: list = None) -> float:
        """Return a score evaluating the fitness of a building in an area.
            The lower the score, the better it fits

            Score is calculated as follows :
            malus depending on the distance from the center of the area +
            Sum of all differences in the y coordinate
            """

        for x in range(size.x):
            for z in range(size.z):
                current_coord = coordinates.shift(x - shift.x, 0, z - shift.z)
                if current_coord.as_2D() in self.occupied_coordinates or current_coord not in self:
                    return -100

        # apply malus to score depending on the distance to the 'center'
        #
        # center = Coordinates(self.center[0], 0, self.center[1])
        # score = coordinates.as_2D().distance(center) * .1

        special_score = 0
        road_score = 0
        relation_score = 0

        special_time = time.time()

        # For mines : Try to place them up a cave
        if building.properties.building_type == BuildingType.MINING:
            # we shift 10 blocs into the ground and search for air, because that would be a cave.
            # y - 30 to not go too deep
            # x and z shift to get to the center
            for down in coordinates.shift(x=round(size.x / 2), y=-10, z=round(size.z / 2)).line(coordinates.y - 30,
                                                                                                Direction.DOWN):
                if self.get_block_at(*down).is_one_of('air'):
                    depth = coordinates.y - down.y
                    special_score += 5
                    building.depth = (depth // 5) + 1
                    break
            # apply malus, the idea is that the bonus will compensate for it, so mine without bonus should be less frequent

        # For tower : place them as high as possible
        elif building.name == 'Tower':
            if coordinates.y > 200:
                special_score += 5
            elif coordinates.y > 100:
                special_score += 3

        # if env.SHOW_TIME:
        #     time_took = time.time() - special_time
        #     print(f'Special took {time_took} s')

        # add malus due to bad road connectivity
        if city_buildings:
            # road_time = time.time()
            # try:
            #     path = nx.dijkstra_path(self.graph, city_buildings[0].entrances[0].coordinates, coordinates)
            #     road_score = 3
            # except nx.NetworkXException:
            #     pass
            #
            # if env.SHOW_TIME:
            #     time_took = time.time() - road_time
            #     print(f'Road took {time_took} s')

            # connectivity check
            connectivity_time = time.time()
            horizontal_directions = (Direction.SOUTH, Direction.WEST, Direction.NORTH, Direction.SOUTH)
            for _dir in horizontal_directions:
                line = list(coordinates.line(3, _dir))
                for u, v in zip(line[:-2], line[1:]):
                    if not self.graph.has_edge(u, v):
                        return -5

            # if env.SHOW_TIME:
            #     time_took = time.time() - connectivity_time
            #     print(f'Connectivity took {time_took} s')

        # And now modifications for specials buildings
        relation_time = time.time()
        relation = env.RELATIONS.get_building_relation(building.name)

        if relation and city_buildings:
            relation_score = sum(list(map(lambda build: relation.get_building_value(build.name), filter(
                lambda b: b.plot.start.distance(coordinates) < 50, city_buildings))) + [0])

        # if env.SHOW_TIME:
        #     time_took = time.time() - relation_time
        #     print(f'Relation took {time_took} s')

        return special_score + road_score + relation_score

    def remove_trees(self, surface: BlockList = None) -> None:
        """Remove all plants at the surface of the current plot"""
        pattern = ('log', 'bush', 'mushroom', 'bamboo')

        if surface is None:
            surface = self.get_blocks(Criteria.MOTION_BLOCKING_NO_LEAVES)

        amount = 0
        unwanted_blocks = surface.filter(pattern).to_set()

        if env.DEBUG:
            print(f'\n=> Removing trees on plot at {self.start} with size {self.size}')

        while unwanted_blocks:
            block = unwanted_blocks.pop()
            for coord in self.__yield_until_ground(block.coordinates):
                INTF.placeBlock(*coord, 'minecraft:air')
                amount += 1

        INTF.sendBlocks()
        if env.DEBUG:
            print(f'=> Deleted {amount} blocs\n')
        # self.update()

    def __yield_until_ground(self, coordinates: Coordinates):
        """Yield the coordinates """
        current_coord: Coordinates = coordinates

        while self.get_block_at(*current_coord).is_one_of(('air', 'leaves', 'log', 'vine', 'bamboo')):
            yield current_coord
            current_coord = current_coord.shift(0, -1, 0)

    def build_foundation(self, build_area: Plot) -> None:
        """Build the foundations under the house"""
        if not self.water_mode:
            blocks = ('stone_bricks', 'diorite', 'cobblestone')
            weights = (75, 15, 10)

            for coord in self.__iterate_over_air(self.start.y):
                block = random.choices(blocks, weights)
                INTF.placeBlock(*coord, block)
        else:

            # INSIDE
            for coord in self.surface():
                INTF.placeBlock(*coord, "oak_planks")

            # OUTER FRAME
            for coord in self.start.shift(x=-3, z=-1).line(self.size.x + 4, Direction.EAST):
                if coord in build_area:
                    INTF.placeBlock(*coord, "oak_log[axis=x]")
                c = coord.shift(z=self.size.z + 1)
                if c in build_area:
                    INTF.placeBlock(*c, "oak_log[axis=x]")
            for coord in self.start.shift(x=-1, z=-3).line(self.size.z + 4, Direction.SOUTH):
                if coord in build_area:
                    INTF.placeBlock(*coord, "oak_log[axis=z]")
                c = coord.shift(x=self.size.x + 1)
                if c in build_area:
                    INTF.placeBlock(*c, "oak_log[axis=z]")

            # PILLARS
            for coord in self.start.shift(x=-1, y=2, z=-1).line(50, Direction.DOWN):
                if coord in build_area:
                    INTF.placeBlock(*coord, "oak_log[axis=y]")
                c = coord.shift(x=self.size.x + 1)
                if c in build_area:
                    INTF.placeBlock(*c, "oak_log[axis=y]")
                c = coord.shift(x=self.size.x + 1, z=self.size.z + 1)
                if c in build_area:
                    INTF.placeBlock(*c, "oak_log[axis=y]")
                c = coord.shift(z=self.size.z + 1)
                if c in build_area:
                    INTF.placeBlock(*c, "oak_log[axis=y]")

        INTF.sendBlocks()

    def __iterate_over_air(self, max_y: int) -> Coordinates:
        """"""
        for block in self.get_blocks(Criteria.MOTION_BLOCKING_NO_TREES):
            for new_y in range(block.coordinates.y, max_y):
                yield block.coordinates.with_points(y=new_y)

    def __contains__(self, coordinates: Coordinates) -> bool:
        """Return true if the current plot contains the given coordinates"""
        return self.start.x <= coordinates.x < self.end.x and \
               self.start.y <= coordinates.y <= self.end.y and \
               self.start.z <= coordinates.z < self.end.z

    def surface(self, padding: int = 0) -> Generator[Coordinates]:
        """Return a generator over the coordinates of the current plot"""
        for x in range(-padding, self.size.x + padding):
            for z in range(-padding, self.size.z + padding):
                yield self.start.shift(x, 0, z)

    def get_steep_map_value(self, coord: Coordinates) -> int:
        if self.steep_map is None:
            self.compute_steep_map()

        steep_map_size = self.size.x - self.steep_factor * 2, self.size.z - self.steep_factor * 2
        i, j = (coord - self.start).xz
        i = min(max(i - self.steep_factor, 0), steep_map_size[0] - 1)
        j = min(max(j - self.steep_factor, 0), steep_map_size[1] - 1)
        return self.steep_map[j + i * steep_map_size[1]]
