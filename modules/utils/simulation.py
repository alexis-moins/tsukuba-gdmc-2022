import random
from enum import Enum

from modules.plots.plot import Plot
from modules.utils.criteria import Criteria


class Event:
    def __init__(self, name):
        self.name = name


class Building:
    def __init__(self, name, profession, bed_amount, productivity, food):
        self.name = name
        self.profession = profession
        self.bed_amount = bed_amount
        self.work_productivity = productivity
        self.food_productivity = food

    def __str__(self):
        return self.name


class City:
    def __init__(self):
        self.buildings = [Building("Town hall", None, 5, 5, 5)]
        self.professions = {}
        self.population = 5
        self.productivity_available = 5
        self.food_available = 5

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

    def get_location(self, plot):
        return random.choice(plot.get_blocks(Criteria.MOTION_BLOCKING_NO_TREES)).coordinates


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

    def get_location(self, plot):
        pass


class Buildings(Enum):
    HOUSE = (30, Building('House', None, 5, 0, 0))
    FARM = (30, Building('Farm', 'Farmer', 0, 1, 5))
    FACTORY = (50, Building('Factory', None, 0, 20, 0))


class Simulation:
    def __init__(self, plot: Plot, friendliness, field_productivity, humidity, decision_maker):
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

        self.city = City()

        while year < self.duration:

            # Update city
            self.city.update()

            action = self.decision_maker.get_action(self.get_available_actions())

            # Execute action
            for building in Buildings:
                cost, house = building.value
                if action == house:
                    if self.city.productivity_available >= cost:
                        self.city.productivity_available -= cost
                        self.city.buildings.append(house)
                        print(f'Added building {house}')
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


