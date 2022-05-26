from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
import random

from src.simulation.settlement import Settlement

from src import env


_descriptions: dict[str, list] = env.get_content('descriptions.yaml')


def get_data(event: str) -> dict:
    """"""
    choice: dict = random.choice(_descriptions[event.lower()])
    _descriptions[event.lower()].remove(choice)

    if len(_descriptions[event.lower()]) == 0:
        del _descriptions[event.lower()]

    return choice


# [Event('Wedding'), Event('Wandering trader'), Event('Town Celebration'),
#  Event('Fire', is_dangerous=True, kills=(1, 2)),
#  Event('Pillager attack', is_dangerous=True, kills=(2, 4)),
#  Event('Wolf attack', is_dangerous=True, kills=(4, 4))]

#
_events: set[Event] = list()  # _parse_events()


def get_event(current_year: int) -> Event | None:
    """Get a randomly selected event from the list of available events, if the
    event's minimal year is <= to the [current year]. There is a 25% chance to
    trigger an event and 75% to get no events at all"""
    if random.randint(1, 4) == 4:
        event = random.choice(_events)

        if current_year >= event.year:
            _events.remove(event)
            return event

    return None


@dataclass(kw_only=True, frozen=True)
class Event(ABC):
    """Represents an abstract event"""
    name: str
    year: int

    @abstractmethod
    def resolve(self, settlement: Settlement, year: int) -> str:
        """"""
        pass

        if self.is_dangerous and year >= 10:

            # special effect depending on event
            if self.name == 'Wolf attack':
                dog_names = ["MAX", "KOBE", "OSCAR", "COOPER", "OAKLEY", "MAC", "CHARLIE", "REX ", "RUDY", "TEDDY ",
                             "BAILEY", "CHIP", "BEAR ", "CASH ", "WALTER", "MILO ", "JASPER", "BLAZE", "BENTLEY", "BO",
                             "OZZY", "Bella", "Luna", "Lucy", "Daisy", "Zoe", "Lily", "Lola", "Bailey", "Stella",
                             "Molly", "Coco", "Maggie", "Penny"]
                x, y, z = random.choice(settlement.buildings).entrance
                y += 1
                for i in range(random.randint(5, 20)):
                    interface.runCommand(
                        f'summon minecraft:wolf {x} {y} {z} {{CustomName:"\\"{random.choice(dog_names).capitalize()}\\""}}')

            mod = 0
            for building in settlement.buildings:
                if building.name == 'Watch Tower':
                    print('The tower is protecting us')
                    mod = -2
                    break

            kills = max(1, min(random.randint(*self.kills), max(len(settlement.inhabitants) - 2 + mod, 2)))
            print(
                f'=> The {Fore.RED}{self.name.lower()}{Fore.WHITE} killed {Fore.RED}[{kills}]{Fore.WHITE} villagers this year')

            for v in random.sample(settlement.inhabitants, kills):
                settlement.villager_die(v, year, self.name.lower())

            data = get_data(self.name)
            description = data.pop('description').format(
                victims=kills, **{key: random.choice(value) for key, value in data.items()})

            if self.name == 'Pillager attack':

                if 'tower' in description:

                    towers_built = 0
                    for _ in range(random.randint(2, 5)):
                        building = deepcopy(env.BUILDINGS['Watch Tower'])
                        rotation = random.choice([0, 90, 180, 270])
                        plot = settlement.plot.get_subplot(building, rotation, city_buildings=settlement.buildings)
                        if plot:
                            settlement.build(building, plot, rotation)
                            x, y, z = building.get_entrance()
                            y += 10
                            for i in range(random.randint(3, 10)):
                                interface.runCommand(f'summon minecraft:iron_golem {x} {y} {z}')

                        towers_built += 1

                    if towers_built == 0:
                        description += "Unfortunately, we did not find a place to build it."

            if self.name == 'Fire':
                building = random.choice(settlement.buildings)
                building.set_on_fire(random.randint(65, 80))
                # TODO add to building history

            if self.name.lower() not in _descriptions:
                _events.remove(self)

            return f'Year {year}\n{description}'

        else:
            print(
                f'=> This year we celebrate {Fore.CYAN}{self.name.lower()}{Fore.WHITE}')

            if self.name == 'Wedding':
                settlement.wedding()

            return f'Year {year}\nen event'


@dataclass(kw_only=True, frozen=True)
class WolfAttack(Event):
    """"""

    def resolve(self, settlement: Settlement, year: int) -> str:
        """"""
