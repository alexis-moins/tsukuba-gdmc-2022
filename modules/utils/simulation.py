import random

from modules.plots.plot import Plot


class Agent:
    def __init__(self, name):
        self.name = name
        self.age = 1
        self.profession = None


    def act(self):
        return 1


class Event:
    def __init__(self, name):
        self.name = name


class Building:
    def __init__(self, profession, bed_amount):
        self.profession = profession
        self.bed_amount = bed_amount


class City:
    def __init__(self):
        self.buildings = [Building(None, 3)]
        self.professions = {}
        self.work_points = 0

    @property
    def bed_amount(self):
        return sum(b.bed_amount for b in self.buildings)


class Simulation:
    def __init__(self, plot: Plot):
        self.plot = plot
        self.duration = 30

        self.agents = [Agent(str(i)) for i in range(1)]
        self.city = City()
        self.events = []
        self.actions = []

    def start(self):
        year = 0

        building_cost = 10

        while year < self.duration:
            for agent in self.agents:
                self.city.work_points += agent.act()

            if self.city.work_points > building_cost:
                self.city.work_points -= building_cost
                print(f'Creating a building for cost 10')
                self.city.buildings.append(Building(None, 1))

            agent_amount = len(self.agents)
            if agent_amount < self.city.bed_amount:
                self.agents.append(Agent(str(agent_amount)))

            print(f'End of year {year}, current city work : {self.city.work_points}, current inhabitants : {agent_amount}')
            year += 1

            # input('Enter to go to next year')



