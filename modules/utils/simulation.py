import random
from enum import Enum

from modules.blocks.collections.block_list import BlockList
from modules.blocks.structure import Structure
from modules.plots.plot import Plot
from modules.utils import loader
from modules.utils.coordinates import Coordinates
from modules.utils.criteria import Criteria


class Event:
    def __init__(self, name):
        self.name = name


class Building:
    def __init__(self, structure, name, profession, bed_amount, productivity, food):
        self.structure = structure
        self.name = name
        self.profession = profession
        self.bed_amount = bed_amount
        self.work_productivity = productivity
        self.food_productivity = food

    def __str__(self):
        return self.name


class City:
    def __init__(self, plot):
        self.plot = plot
        self.buildings = [Building(loader.structures['house1'], "Town hall", None, 5, 5, 5)]
        self.professions = {}
        self.population = 5
        self.productivity_available = 5
        self.food_available = 5

    def add_building(self, building: Building, coord: Coordinates, rotation: int):
        padding = 3
        structure = building.structure
        size = structure.get_size(rotation)
        plot = Plot(*coord, size=size)

        area_with_padding = BlockList(
            list(map(lambda coord: self.plot.get_blocks(Criteria.MOTION_BLOCKING_NO_LEAVES).find(coord),
                     filter(lambda coord: coord in self.plot, plot.surface(padding)))))
        plot.remove_trees(area_with_padding)

        plot.build_foundation()
        structure.build(coord, rotation=rotation)

        self.buildings.append(building)

    @property
    def bed_amount(self):
        return sum(b.bed_amount for b in self.buildings)

    @property
    def work_production(self):
        return sum(b.work_productivity for b in self.buildings)

    @property
    def food_production(self):
        return sum(b.food_productivity for b in self.buildings)

    def update(self):
        self.productivity_available += max(0, min(self.work_production, self.population))
        self.food_available += self.food_production

        # Increase population if enough food
        if self.food_available >= self.population:
            self.food_available -= self.population

            if self.bed_amount >= self.population:
                max_children_amount = min(int(self.population // 2), self.bed_amount - self.population)

                # add extra value if you don't want to go out of food immediately
                food_for_children = self.food_available - self.population
                self.population += max(0, min(food_for_children, max_children_amount))

        # Decrease population else
        else:
            # Feed with the remaining food and compute the missing food
            self.food_available -= self.population
            # Remove extra population
            self.population += self.food_available
            # reset food
            self.food_available = 0

    def __str__(self) -> str:
        return f'population : {self.population}/{self.bed_amount}' \
               f'\nFood : {self.food_available} (var: {self.food_production})' \
               f'\nWork : {self.productivity_available} (var : {max(0, min(self.work_production, self.population))})' \
               f'\nBuildings : {len(self.buildings)}' \
               f'\n{" - ".join(str(b) for b in self.buildings)}'


class DecisionMaker:
    def __init__(self):
        pass

    def get_action(self, possible_actions):
        act = random.choice(possible_actions)
        print(f'Possible actions [{", ".join(str(a) for a in possible_actions)}] :: Chose {act}')
        return act

    def get_coordinates(self, plot) -> Coordinates:
        return random.choice(plot.get_blocks(Criteria.MOTION_BLOCKING_NO_TREES)).coordinates

    def get_rotation(self) -> int:
        orientation = [0, 90, 180, 270]
        return random.choice(orientation)


class HumanPlayer(DecisionMaker):
    def __init__(self):
        super().__init__()

    def get_action(self, possible_actions):

        action_chose = None
        while action_chose is None:
            print('You have to choose an action')
            for i, act in enumerate(possible_actions):
                print(f'{i} - {act}')

            try:
                action_chose = possible_actions[int(input('Selected : '))]
            except IndexError:
                print('Your answer is incorrect')
            except ValueError:
                print('Your answer is incorrect')
        return action_chose

    def get_coordinates(self, plot):
        print(f"Choose coordinates between {plot.start} and {plot.end}")
        coord = None
        while coord is None:
            answer = input("Coordinates for the building X Z: ").split()
            try:
                x, z = int(answer[0]), int(answer[1])
                coord = Coordinates(x, 0, z)
                coord = plot.get_blocks(Criteria.MOTION_BLOCKING_NO_TREES).find(coord).coordinates
            except Exception:
                print("Something went wrong with your coordinate")

            if coord and coord not in plot:
                print(f"Coord {coord} not in plot !")
                coord = None
        return coord

    def get_rotation(self):
        angles = [0, 90, 180, 270]
        print(f"Choose rotation between {angles}")
        rotation = None
        while rotation is None:
            for i, ang in enumerate(angles):
                print(f'{i} - {ang}')
            try:
                rotation = angles[int(input('Selected : '))]
            except IndexError:
                print('Your answer is incorrect')
            except ValueError:
                print('Your answer is incorrect')
        return rotation


class Buildings(Enum):
    HOUSE = (30, Building(loader.structures['house2'], 'House', None, 5, 0, 0))
    FARM = (30, Building(loader.structures['house3'], 'Farm', 'Farmer', 0, 1, 5))
    FACTORY = (50, Building(loader.structures['house3'], 'Factory', None, 0, 20, 0))


class Simulation:
    def __init__(self, plot: Plot, friendliness: float, field_productivity: float, humidity: float,
                 decision_maker: DecisionMaker):
        self.decision_maker = decision_maker
        self.humidity = humidity
        self.field_productivity = field_productivity
        self.friendliness = friendliness
        self.plot = plot
        self.duration = 30

        self.city = None
        self.events = []
        self.actions = []

    def start(self):
        year = 0

        # If you have multiple cities, just give a subplot here
        self.city = City(self.plot)

        while year < self.duration:

            # Update city
            self.city.update()

            action = self.decision_maker.get_action(self.get_available_actions())

            # Execute action
            for building in Buildings:
                cost, build = building.value
                if action == build:
                    if self.city.productivity_available >= cost:
                        self.city.productivity_available -= cost
                        self.city.add_building(build,
                                               self.decision_maker.get_coordinates(Plot(*self.city.plot.start, size=self.city.plot.size - build.structure.size)),
                                               self.decision_maker.get_rotation())
                        print(f'Added building {build}')
                    else:
                        print(f'Not enough productivity available for this ! {self.city.productivity_available}/{cost}')
                    break

            # Get event
            print('No event this year')

            # Update city
            # self.update_city()

            # End turn
            print(f'End of year {year}, current stats : {self.city}')
            # input('Enter to go to next year')
            year += 1

            # input('Enter to go to next year')

    def get_available_actions(self):
        actions = ['Nothing']
        for b in Buildings:
            if b.value[0] <= self.city.productivity_available:
                actions.append(b.value[1])
        return actions
