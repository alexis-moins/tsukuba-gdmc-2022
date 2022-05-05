import random

from gdpc import toolbox, interface

from src import env
from src.plots.plot import Plot
from src.simulation.buildings.building import Building
from src.simulation.city import City
from src.simulation.decisions.decision_maker import DecisionMaker


class Event:
    def __init__(self, name):
        self.name = name


events = (Event('Wedding'), Event('Fire'), Event('Wolves attack'), Event('Wandering trader'),
          Event('Barbarian attack'), Event('Town Celebration'))


class Simulation:
    """"""

    def __init__(self, plot: Plot, decision_maker: DecisionMaker, years: int, friendliness: float = 1, field_productivity: float = 1, humidity: float = 1):
        """"""
        self.decision_maker = decision_maker
        self.humidity = humidity
        self.field_productivity = field_productivity
        self.friendliness = friendliness
        self.plot = plot
        self.years = years

        self.city: City = None
        self.events = []
        self.actions = []

    def start(self):
        year = 0

        # If you have multiple cities, just give a subplot here
        self.city = City(self.plot)
        self.decision_maker.city = self.city

        history = []

        print('Starting Game !!')
        print('Give a rotation and a location for the Town hall')

        town_hall = env.BUILDINGS['TOWN_HALL']
        rotation = self.decision_maker.get_rotation()

        size = town_hall.get_size(rotation)
        plot = self.city.plot.get_subplot(size)
        self.city.add_building(town_hall, plot, rotation)

        while year < self.years:
            print(f'\n=> Start of year {year}:')

            self.city.update()
            buildings = self.get_constructible_buildings()

            if buildings:
                rotation = self.decision_maker.get_rotation()
                choice, plot = self.decision_maker.choose_building(buildings, rotation)

                if choice is not None and plot is not None:
                    self.city.add_building(choice, plot, rotation)

            # Get event

            if random.randint(0, 1):
                event = random.choice(events)
                print(event.name)
                history.append((year, event))
            else:
                print('=> No event this year')

            # Update city
            # self.update_city()

            # End turn
            print(f'=> End of year {year}')
            print('==== Summary ====')
            self.city.display()
            # input('Enter to go to next year')
            year += 1
            # input('Enter to go to next year')


        history_string = "\n".join(f'year {year} : {event.name}' for year, event in history)
        print(f'City history : {history_string}')

        # make a book
        book_data = toolbox.writeBook(history_string, title='City history', author='No one')
        lectern_list = self.city.buildings[0].blocks.filter('lectern')
        if len(lectern_list):
            x, y, z = lectern_list[0].coordinates
            command = (f'data merge block {x} {y} {z} '
                       f'{{Book: {{id: "minecraft:written_book", '
                       f'Count: 1b, tag: {book_data}'
                       '}, Page: 0}')

            interface.runCommand(command)
            print(f'placed history book at {x}, {y}, {z}')



    def get_constructible_buildings(self) -> list[Building]:
        """Return the available buildings for the year"""
        actions = [building for building in env.BUILDINGS.values()
                   if building.properties.cost <= self.city.productivity]

        # TODO Change ActionType enum to be NOTHING, CONSTUCTION, REPARATION, etc
        return actions
