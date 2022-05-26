import random
import textwrap
import time
from collections import Counter
from typing import Any

from colorama import Fore
from gdpc import interface
from gdpc import lookup

from src import env
from src.blocks.collections.block_list import BlockList
from src.plots.plot import Plot
from src.simulation.buildings.building import Building
from src.simulation.buildings.building import Graveyard
from src.simulation.buildings.building import WeddingTotem
from src.simulation.buildings.utils.building_type import BuildingType
from src.utils.criteria import Criteria


with open('resources/first-names.txt', 'r') as file:
    _first_names = file.read().splitlines()

with open('resources/last-names.txt', 'r') as file:
    _last_names = file.read().splitlines()


class Villager:
    """"""

    def __init__(self, birth_year: int = 0) -> None:
        """"""
        self.name = f'{random.choice(_first_names)} {random.choice(_last_names)}'
        self.productivity = 1
        self.house: Building = None
        self.work_place: Building = None
        self.birth_year = birth_year

    def die(self, year: int, cause: str):
        if self.work_place:
            self.work_place.workers.remove(self)
            self.work_place.history.append(f'{self.name} died at {year} of {cause}')
        if self.house:
            self.house.inhabitants.remove(self)
            self.house.history.append(f'{self.name} died at {year} of {cause}')


class Settlement:
    """Represents a settlement, with villagers and buildings"""

    def __init__(self, plot: Plot):
        """Creates a new settlement on the given [plot]. The settlement starts with a
        default population of 5 and a default food stock of 5."""
        self.plot = plot

        # TODO change into a dict str, Building
        self.buildings: list[Building] = []

        self.deserialized_buildings = {}

        # TODO get rid of this
        self.graveyard: Graveyard | None = None
        self.wedding_totem: WeddingTotem | None = None

        self.counter = Counter()

        self.inhabitants = [Villager() for _ in range(5)]

        self.food_available = 5

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
        return sum(building.properties.number_of_beds for building in self.buildings)

    @property
    def worker_number(self) -> int:
        """Return the total number of workers in the settlement, that is to say
        of villagers with a job"""
        return sum(len(building.workers) for building in self.buildings)

    @property
    def total_worker_slots(self) -> int:
        """Return the maximum number of workers that can work in the settlement"""
        return sum(building.properties.workers for building in self.buildings)

    @property
    def food_production(self):
        return sum(building.properties.food_production for building in self.buildings)

    def get_constructible_buildings(self) -> list[Building]:
        """Return the available buildings of the year in the form of a list of Building objects

        Constructible buildings are selected based on the following criteriae:
        - its cost (in production points) is <= to the current production points of the city
        - its type is not one of DECORATION
        - the city has not reached the maximum number for this buildings"""
        return [Building.deserialize(name, data) for name, data in env.BUILDINGS.items()
                if self.is_building_constructible(name, data)]

    def is_building_constructible(self, name: str, data: dict[str, Any]) -> bool:
        """Return true if the building is constructible, false if it is not. The building is formed
        by the given [name] associated with the given [data]"""
        return data.get('cost', 0) <= self.worker_number and data['type'] != 'DECORATION' \
            and self.counter[name] < data.get('maximum', 1)

    def add_building(self, building: Building, max_score: int = None) -> bool:
        """Add the given [building] to this settlement. If no available plot is found, the function
        returns false and the building is not built. Return true upon successful construction of the
        building. Additionally, a [max score] parameter may tell the inner logic after what score it
        should give the current plot up when looking for a decent spot on the map"""
        plot = self.plot.get_subplot(building, building.rotation,
                                     max_score, city_buildings=self.buildings)

        if plot is None:
            return False

        self.build(building, plot)
        self.counter[building.name] += 1
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
        time.sleep(2)

        plot.build_foundation(self.plot)

        print(f'{building} added to the settlement')

        building.build(plot, self.plot)
        self.buildings.append(building)

        if len(self.buildings) > 1 and not self.buildings[-1].properties.is_extension:
            if env.DEBUG:
                print(f'building road from {self.buildings[0]} to {self.buildings[1]}')

            road_done = False
            i = 0
            max_i = len(self.buildings) - 1
            while not road_done and i < max_i:
                end = self.buildings[i].entrance
                start = self.buildings[-1].entrance

                road_done = self.plot.compute_roads(start, end)
                i += 1

    def update(self, year: int) -> None:
        """Update the city's indicators"""
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

                print(f'=> {Fore.CYAN}[{k}]{Fore.WHITE} new villager(s) born this year')
                self.inhabitants.extend([Villager(year) for _ in range(k)])

        # Decrease population else
        else:
            # Feed with the remaining food and compute the missing food
            self.food_available -= self.population
            # Remove extra population
            print(f'======= Check wether the population is decreased or notm it should ======')
            self.inhabitants.extend([Villager(year) for _ in range(self.food_available)])
            # reset food
            self.food_available = 0

        # Attributing villagers to buildings
        # First, give every homeless villager a house (if possible)
        available_houses = [building for building in self.buildings if building.has_empty_beds]

        for villager in self.homeless_villagers:
            if not available_houses:
                break

            house = available_houses.pop()
            house.add_inhabitant(villager, year)

            if house.has_empty_beds:
                available_houses.append(house)

        # Then, give every inactive villager a place to work at (if possible)
        available_work_places = [building for building in self.buildings if building.can_offer_work]

        for villager in self.inactive_villagers:
            if not available_work_places:
                break

            work_place = available_work_places.pop()
            work_place.add_worker(villager, year)

            if work_place.can_offer_work:
                available_work_places.append(work_place)

    def display(self) -> None:
        """Display a summary of the city at the end of the current year"""
        print('==== Summary ====')
        print(
            f'\n   Population: {Fore.GREEN}{self.population}/{self.number_of_beds}{Fore.WHITE} ({Fore.GREEN}{len(self.inactive_villagers)}{Fore.WHITE} inactive)')
        print(f'   Food: {Fore.GREEN}{self.food_available}{Fore.WHITE} ({Fore.GREEN}{self.food_production}{Fore.WHITE} per year)')
        print(f'   Work: {Fore.GREEN}{self.worker_number}/{self.total_worker_slots}{Fore.WHITE}')

        print(f'\n   Buildings {Fore.GREEN}[{len(self.buildings)}]{Fore.WHITE}\n')

        buildings = "\n      ".join(textwrap.wrap(
            ", ".join([f"{building.name}: {Fore.GREEN}{self.counter[building.name]}/{building.properties.maximum}{Fore.WHITE}" for building in self.buildings])))
        print(f'\n      {buildings}')

    def wedding(self):
        if self.wedding_totem:
            self.wedding_totem.add_wedding()

    def villager_die(self, villager: Villager, year: int, cause: str):
        if self.graveyard:
            self.graveyard.add_tomb(villager, year, cause)

        villager.die(year, cause)
        self.inhabitants.remove(villager)

    def spawn_villagers_and_guards(self):
        x, y, z = self.buildings[0].entrance[0].coordinates
        for villager in self.inhabitants:
            interface.runCommand(f'summon villager {x} {y + 1} {z} {{CustomName:"\\"{villager.name}\\""}}')
        for i in range(random.randint(5, 15)):
            interface.runCommand(f'summon iron_golem {x} {y + 1} {z} {{CustomName:"\\"Town Guard\\""}}')

    def end_simulation(self):
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
        self.plot.add_roads_signs(10, self.buildings)
