import random

from modules.plots.plot import Plot


class Agent:
    def __init__(self):
        self.name = 'name'
        self.age = 1
        self.profession = None


class Event:
    def __init__(self, name):
        self.name = name


class Simulation:
    def __init__(self, plot: Plot):
        self.plot = plot

        self.agents = [Agent() for _ in range(random.randint(1, 3))]


