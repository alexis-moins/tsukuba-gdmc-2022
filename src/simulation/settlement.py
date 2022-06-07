import math
import random
from collections import Counter, defaultdict
from typing import Any, DefaultDict, Iterator, MutableMapping

from colorama import Fore
from gdpc import interface, lookup

from src import env
from src.plots.plot import Plot, CityPlot
from src.utils import chest, loot_table
from src.utils.criteria import Criteria
from src.simulation.villager import Villager
from src.blocks.collections.block_list import BlockList
from src.simulation.buildings.building import Building, Graveyard, WeddingTotem
from src.utils.loot_table import MinecraftItem


class Settlement(MutableMapping):
    """Represents a settlement, with villagers and buildings. This object behaves like
        a dictionary (keys, valyes, etc...) while also providing a chronology of the buildings
        added to the settlement"""

    def __init__(self, plot: CityPlot, *, population: int = 5, food: int = 5):
        """Creates a new settlement on the given [plot]. The settlement starts with a
        default [population] of 5 and a default [food] stock of 5"""
        self.plot = plot

        self.is_running = True
        self._consecutive_years_without_build = 0

        self.chronology: list[Building] = []
        self._buildings: dict[str, list[Building]] = dict()

        self._buildings_cache = {}

        self._counter = Counter()

        self.inhabitants = [Villager() for _ in range(population)]

        self.food_available = food

        self.possible_light_blocks = ('minecraft:shroomlight', 'minecraft:sea_lantern',
                                      'minecraft:glowstone')

        self.road_light = random.choice(self.possible_light_blocks)

    @property
    def population(self) -> int:
        """Return the number of inhabitants in the city"""
        return len(self.inhabitants)

    @property
    def inactive_villagers(self) -> list[Villager]:
        """Return the list of all villagers that don't have a job"""
        return [villager for villager in self.inhabitants if villager.work_place is None]

    @property
    def homeless_villagers(self) -> list[Villager]:
        """Return the list of all villagers that don't have a house"""
        return [villager for villager in self.inhabitants if villager.house is None]

    @property
    def number_of_beds(self) -> int:
        """Return the total number of beds in the city"""
        return sum(building.properties.number_of_beds for building in self.chronology)

    @property
    def worker_number(self) -> int:
        """Return the total number of workers in the settlement, that is to say
        of villagers with a job"""
        return sum(len(building.workers) for building in self.chronology)

    @property
    def total_worker_slots(self) -> int:
        """Return the maximum number of workers that can work in the settlement"""
        return sum(building.properties.workers for building in self.chronology)

    @property
    def food_production(self):
        """Return the number of food produced in the settlement this year"""
        return sum(building.properties.food_production for building in self.chronology)

    def get_constructible_buildings(self) -> list[Building]:
        """Return the available buildings of the year in the form of a list of Building objects

        Constructible buildings are selected based on the following criteriae:
        - its cost (in production points) is <= to the current production points of the city
        - its type is not one of DECORATION
        - the city has not reached the maximum number for this buildings"""
        buildings = []
        for data in env.BUILDINGS.values():
            if self.is_building_constructible(data):
                building = self._buildings_cache.pop(data['name'], None)

                if not building:
                    building = Building.deserialize(data)
                    self._buildings_cache[building.name] = building

                buildings.append(building)

        return buildings

    def is_building_constructible(self, data: dict[str, Any]) -> bool:
        """Return true if the building is constructible, false if it is not. The building is formed
        by the given [name] associated with the given [data]"""
        return data.get('cost', 0) <= self.worker_number and data['type'] != 'DECORATION' \
            and self._counter[data['name']] < data.get('maximum', 1)

    def __add_no_build(self) -> None:
        """TODO write documentation"""
        self._consecutive_years_without_build += 1
        self.is_running = (self._consecutive_years_without_build < 5)

    def add_building(self, building: Building | None, *, max_score: int = None) -> None:
        """Add the given [building] to this settlement. If no available plot is found, the function
        returns false and the building is not built. Return true upon successful construction of the
        building. Additionally, a [max score] parameter may tell the inner logic after what score it
        should give the current plot up when looking for a decent spot on the map"""
        if building is not None:
            return self.__add_building(building, max_score=max_score)

        self.__add_no_build()

    def deserialize_and_add_building(self, building: str, *, queue: list[str] = None, max_score: int = None) -> bool:
        """Deserialize the given [building] and try to add it to the settlement. If no available plot is
        found, deserialize the next building in the given [queue] until a building can be constructed in
        the settlement. Additionally, a [max score] parameter may tell the inner logic after what score
        it should give up the current plot when looking for a decent spot on the map. If no buildings have
        been placed at all (even from the queue), this function will return false. If one building has been
        placed, return true"""
        choice = Building.deserialize(env.BUILDINGS[building])
        done = self.__add_building(choice, max_score=max_score)

        while not done and queue:
            building = queue.pop(0)
            choice = Building.deserialize(env.BUILDINGS[building])
            done = self.__add_building(choice, max_score=max_score)

        return done

    def __add_building(self, building: Building, *, max_score: int = None) -> bool:
        """Add the given [building] to this settlement. If no available plot is found, the function
        returns false and the building is not built. Return true upon successful construction of the
        building. Additionally, a [max score] parameter may tell the inner logic after what score it
        should give the current plot up when looking for a decent spot on the map. Note that this
        method should not be called directly. You should use the wrapper method add_building instead."""
        if not self.is_running:
            return False

        plot = self.plot.get_subplot(building, building.rotation,
                                     max_score, city_buildings=self.chronology)

        if plot is None:
            self.__add_no_build()
            return False

        if building.name in self._buildings_cache:
            del self._buildings_cache[building.name]

        self.build(building, plot)

        self._counter[building.name] += 1
        self._consecutive_years_without_build = 0

        return True

    def build(self, building: Building, plot: Plot) -> None:
        """Build the given [building] on a [plot]. If you don't have a plot for your building yet,
        consider calling the add_building method instead"""

        if isinstance(building, Graveyard):
            self.graveyard = building
        elif isinstance(building, WeddingTotem):
            self.wedding_totem = building

        area_with_padding = BlockList(
            list(map(lambda coord: self.plot.get_blocks(Criteria.MOTION_BLOCKING_NO_LEAVES).find(coord),
                     filter(lambda coord: coord in self.plot, plot.surface(building.properties.padding)))))

        plot.remove_trees(area_with_padding)

        plot.build_foundation(self.plot)

        print(f'{building} added to the settlement')

        building.build(plot, self.plot)

        self.chronology.append(building)

        if building.name not in self._buildings_cache:
            self._buildings[building.name] = []

        self._buildings[building.name].append(building)

        if len(self._buildings) > 1 and not self.chronology[-1].properties.is_extension:
            if env.DEBUG:
                print(f'building road from {self.chronology[0]} to {self.chronology[1]}')

            road_done = False
            i = 0
            max_i = len(self._buildings) - 1
            while not road_done and i < max_i:
                end = self.chronology[i].entrance
                start = self.chronology[-1].entrance

                road_done = self.plot.compute_roads(start, end)
                i += 1

    def update(self, year: int) -> None:
        """Update the settlement's indicators"""
        self.food_available += self.food_production

        # Increase population if enough food
        if self.food_available >= self.population:
            # Feed everyone
            self.food_available -= self.population

            if self.number_of_beds >= self.population:
                max_children_amount = min(int(self.population // 2), self.number_of_beds - self.population)

                # add extra value if you don't want to go out of food immediately
                food_for_children = self.food_available - self.population
                k = max(0, min(food_for_children, max_children_amount))

                print(f'=> {Fore.CYAN}[{k}]{Fore.WHITE} new villager(s) are born')
                self.inhabitants.extend([Villager(year) for _ in range(k)])

        self.__fill_houses(year)
        self.__fill_work_places(year)

    def __fill_houses(self, year: int) -> None:
        """Attribute homeless villagers to available houses"""
        available_houses = [building for building in self.chronology
                            if building.has_empty_beds]

        for villager in self.homeless_villagers:
            if not available_houses:
                break

            house = available_houses.pop()
            house.add_inhabitant(villager, year)

            if house.has_empty_beds:
                available_houses.append(house)

    def __fill_work_places(self, year) -> None:
        # Then, give every inactive villager a place to work at (if possible)
        available_work_places = [building for building in self.chronology
                                 if building.can_offer_work]

        for villager in self.inactive_villagers:
            if not available_work_places:
                break

            work_place = available_work_places.pop()
            work_place.add_worker(villager, year)

            if work_place.can_offer_work:
                available_work_places.append(work_place)

    def grow_old(self, *, amount: float = 0.3) -> None:
        """"""
        k = amount * len(self.chronology)
        for building in random.sample(self.chronology, math.ceil(k)):
            building.grow_old(random.randint(65, 80))

    def spawn_villagers_and_guards(self):
        """"""
        x, y, z = self.chronology[0].entrance

        for villager in self.inhabitants:
            interface.runCommand(f'summon villager {x} {y + 1} {z} {{CustomName:"\\"{villager.name}\\""}}')

        for i in range(random.randint(5, 15)):
            interface.runCommand(f'summon iron_golem {x} {y + 1} {z} {{CustomName:"\\"Town Guard\\""}}')

    def build_roads(self):
        # Build roads
        road_pattern = {
            'INNER': {self.road_light: 100},
            'MIDDLE': {'oak_planks'.replace('oak', env.BUILDING_MATERIALS['oak'][
                0] if 'oak' in env.BUILDING_MATERIALS else 'oak'): 100},
            'OUTER': {'note_block': 100}
        }

        slab_pattern = {
            'INNER': {'oak_slab[waterlogged=false]'.replace('oak', env.BUILDING_MATERIALS['oak'][
                0] if 'oak' in env.BUILDING_MATERIALS else 'oak'): 100},
            'MIDDLE': {'oak_slab[waterlogged=false]'.replace('oak', env.BUILDING_MATERIALS['oak'][
                0] if 'oak' in env.BUILDING_MATERIALS else 'oak'): 100},
            'OUTER': {leave + '[persistent=true]': 20 for leave in lookup.LEAVES}
        }

        self.plot.build_roads(road_pattern, slab_pattern)

        # Spawn villagers
        self.spawn_villagers_and_guards()

        # Add roads signs
        self.plot.add_roads_signs(10, self.chronology)

        if self['Town Hall']:
            self['Town Hall'].fill_board()

        treasure_coords = self.generate_treasure()
        phrase = 'The treasure is located at'
        x_indicator = MinecraftItem('paper', f'display:{{Name:\'{{"text":"{phrase} X={treasure_coords.x}"}}\'}}')
        y_indicator = MinecraftItem('paper', f'display:{{Name:\'{{"text":"{phrase} Y={treasure_coords.y}"}}\'}}')
        z_indicator = MinecraftItem('paper', f'display:{{Name:\'{{"text":"{phrase} Z={treasure_coords.z}"}}\'}}')

        treasure_finders = [x_indicator, y_indicator, z_indicator]

        # Fill the buildings chests
        for type_of_building in self._buildings.values():
            for building in type_of_building:
                building.fill_chests(treasure_finders)

    def generate_treasure(self):
        coord = self.plot.random_coord_3d()
        chest_data = chest.get_filled_chest_data([], loot_table.LOOT_TABLES['TREASURE'], fill_amount=20)
        chest_string = f'minecraft:chest'
        interface.placeBlock(*coord, chest_string)
        print(f'Chest at {coord}')
        interface.sendBlocks()
        interface.runCommand(f'data merge block {coord.x} {coord.y} {coord.z} {chest_data}')
        return coord

    def __getitem__(self, key: str) -> list[Building]:
        """"""
        return self._buildings.__getitem__(key)

    def __setitem__(self, key: str, value: Building) -> None:
        """"""
        self._buildings.__setitem__(key, value)

    def __delitem__(self, key: Building) -> None:
        """"""
        self._buildings.__delitem__(key)

    def __iter__(self) -> Iterator[str]:
        """"""
        return self._buildings.__iter__()

    def __len__(self) -> int:
        """Return the number of properties"""
        return len(self._buildings)
