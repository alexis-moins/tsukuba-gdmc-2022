import random
from typing import Any, Callable

from gdpc import interface as INTERFACE

from src.simulation.settlement import Settlement


# Type alias for functions in charge of the event resolution logic
# Functions given to the Event constructor as 'resolve' must all
# follow the prototype below, which is:
# - arguments: Event, Settlement
# - return value: None
EventHandler = Callable[[Event, Settlement, int], None]


# Dictionary mapping tags to their EventHandler function. The is used to match
# tags from the events.yaml file to the corresponding EventHandler function.
# You should not call the EventHandler functions yourself but call the resolve
# method from an Event object which wraps it around another layer of logic
_handlers: dict[str, EventHandler] = dict()


def add(tag: str) -> None:
    """Add the given [tag] to the 'handlers' dictionary as key and map it to
    the decorated function"""
    def decorator(function: EventHandler) -> None:
        _handlers[tag] = function

        return function
    return decorator


def _get_victims(settlement: Settlement, maximum: int) -> int:
    """Return the number of victims between 1 and [maximum], considering the population
    of the given [settlement]"""

    # Reduce the number of victims if at least 1 watch tower has been
    # built in the given settlement
    modificator = 0
    # modificator = -2 if 'watch tower' in settlement else 0

    # Maximum number of villagers that can be killed so that it remains
    # at least 2 villagers alive in the settlement
    true_maximum = min(settlement.population - 2, maximum)

    return max(1, true_maximum + modificator)


def _kill_villagers(settlement: Settlement, number: int) -> None:
    """Kill [number] villager in the given [settlement]"""
    for villager in random.sample(settlement.inhabitants, k=number):
        settlement.villager_die(villager)


@add('pillager-attack')
def pillager_attack(event: dict[str, Any], settlement: Settlement) -> None:
    """"""
    victims = _get_victims(settlement, random.randint(4, 6))
    event['description.format(victims=victims)

    _kill_villagers(victims)

    if 'tower' in event.description:

        for _ in range(random.randint(2, 5)):
            tower= Building.deserialize(env.BUILDINGS['Tower'])

            settlement.add_building('Tower', tower)

            x, y, z= tower.entrance
            y += 10

            for _ in range(random.randint(3, 10)):
                interface.runCommand(f'summon minecraft:iron_golem {x} {y} {z}')

        if 'Tower' not in settlement:
            event.description += 'Unfortunately, we did not find a place to build it'


_wolf_names= env.get_content('wolf-names.txt', YAML=False)


@ add('wolf-attack')
def wolf_attack(event: dict[str, Any], settlement: Settlement) -> None:
    """"""
    victims= _get_victims(settlement, random.randint(2, 4))
    event.description.format(victims=victims)

    _kill_villagers(victims)

    x, y, z= random.choice(settlement.buildings).entrance
    y += 1

    for i in range(random.randint(5, 20)):
        interface.runCommand(
            f'summon minecraft:wolf {x} {y} {z} {{CustomName:"\\"{random.choice(_wolf_names).capitalize()}\\""}}')


@ add('fire')
def fire(event: dict[str, Any], settlement: Settlement) -> None:
    """"""
    victims= _get_victims(settlement, random.randint(2, 4))

    _kill_villagers(victims)

    building= random.choice(settlement.buildings)
    event.description.format(victims=victims, building=building)

    amount= random.randint(65, 80)
    building.set_on_fire(amount)


@ add('wedding')
def wedding(event: dict[str, Any], settlement: Settlement) -> None:
    """"""
    settlement.wedding()
