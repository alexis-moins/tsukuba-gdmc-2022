from __future__ import annotations
"""
Manage events used in the simulation. Provides:
- a get_event function to randomly return an event (with a 1/4 chance)
- an Event abstract base class you can use to define your own custom events
- a register decorator to use your custom events
"""

import random
from typing import Any, Callable
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from src import env, view
from src.simulation.settlement import Settlement
from src.simulation.buildings.building import Blueprint, Graveyard, WeddingTotem


@dataclass(kw_only=True, slots=True)
class Event(ABC):
    """
    Represents any generic abstract event
    """
    _description: str
    year: int = 0
    replacements: dict[str, list[str]] = field(default_factory=dict)

    @staticmethod
    def deserialize(data: dict[str, Any]) -> Event:
        """Return a new Event created using the given [data]"""
        _description = data.pop('description')
        handler = data.pop('handler')

        constructor = _handlers[handler]
        return constructor(_description=_description, **data)

    @abstractmethod
    def resolve(self, settlement: Settlement, year: int) -> str:
        """
        Resolve this event, producing effects on the given |settlement| and
        return the formatted description of the event. Note that you are
        strongly encouraged to use the provided |description| method to to
        so
        """
        pass

    @property
    def description(self) -> str:
        """
        Return the formatted description of the event. You should not call
        this property yourself but rather call the resolve method of an event
        subclass which wraps it into another layer of logic, by adding the
        missing replacements for instance
        """
        replacements = {key: random.choice(value)
                        if type(value) is list else value
                        for key, value in self.replacements.items()}

        return self._description.format(**replacements)

    def _get_victims(self, settlement: Settlement, maximum: int) -> int:
        """Return the number of victims between 1 and [maximum], considering the
        population of the given [settlement]"""

        # Reduce the number of victims if at least 1 watch tower has been
        # built in the given settlement
        modificator = -2 if 'Watch tower' in settlement else 0

        # Maximum number of villagers that can be killed so that it remains
        # at least 2 villagers alive in the settlement
        true_maximum = min(settlement.population - 2, maximum)

        return max(1, true_maximum + modificator)

    def _kill_villagers(self, settlement: Settlement, number: int,
                        year: int, cause: str) -> None:
        """
        Kill [number] villager in the given [settlement] on year [year]
        from [cause]
        """
        graveyard: list[Graveyard] | None = settlement.get('Graveyard', None)
        view.print_kills(number, cause)

        for villager in random.sample(settlement.inhabitants, k=number):
            villager.die(year, cause)
            settlement.inhabitants.remove(villager)

            if graveyard:
                graveyard[0].add_tomb(villager, year, cause)


# Dictionary mapping tags to their Event class. The is used to match
# tags from the events.yaml file to the corresponding Event class.
_handlers: dict[str, Event] = dict()


def register(tag: str) -> Callable[..., Event]:
    """Add the given [tag] to the 'handlers' dictionary as key and map it to
    the decorated class. This is the way to go if you want to define new events
    and use them in the handler field of the events.yaml configuration file"""
    def decorator(constructor: Event) -> Event:
        _handlers[tag] = constructor

        return constructor
    return decorator


@register('pillager-attack')
@dataclass(kw_only=True)
class PillagerAttack(Event):
    """Represents a hord of pillagers attacking the settlement"""

    def resolve(self, settlement: Settlement, year: int) -> str:
        """Resolve this event, producing effects on the given [settlement] and
        return the formatted description of the event. Note that you are strongly
        encouraged to use the provided description property to to so"""
        victims = self._get_victims(settlement, random.randint(4, 6))

        self._kill_villagers(settlement, victims, year, cause='an attack of pillagers')
        self.replacements['victims'] = victims

        if 'tower' in self._description:

            data = env.BUILDINGS['watch-tower']
            for _ in range(random.randint(2, 5)):

                tower = Blueprint.deserialize(data)
                added = settlement.add_building(tower)

                if added:
                    position = tower.entrance

                    for _ in range(random.randint(3, 10)):
                        env.summon('minecraft:iron_golem', position.shift(y=10), name='Watcher Guard')

        if 'Watch tower' not in settlement:
            self._description += 'Unfortunately, we did not find a place to build it'

        return self.description


@register('wolf-attack')
@dataclass(kw_only=True)
class WolfAttack(Event):
    """Represents a pack of wolves attacking the settlement"""

    def resolve(self, settlement: Settlement, year: int) -> str:
        """Resolve this event, producing effects on the given [settlement] and
        return the formatted description of the event. Note that you are strongly
        encouraged to use the provided description property to to so"""
        victims = self._get_victims(settlement, random.randint(2, 4))

        self._kill_villagers(settlement, victims, year, 'a wolf attack')
        self.replacements['victims'] = victims

        position = random.choice(settlement.chronology).entrance

        for _ in range(random.randint(5, 20)):
            env.summon('minecraft:wolf', position.shift(y=1),
                       name=random.choice(env.WOLF_NAMES). capitalize())

        return self.description


@register('fire')
@dataclass(kw_only=True)
class Fire(Event):
    """Represents a fire starting in the settlement, burning buildings and killing
    villagers"""

    def resolve(self, settlement: Settlement, year: int) -> str:
        """Resolve this event, producing effects on the given [settlement] and
        return the formatted description of the event. Note that you are strongly
        encouraged to use the provided description property to to so"""
        victims = self._get_victims(settlement, random.randint(2, 4))

        self._kill_villagers(settlement, victims, year, 'a fire')

        building = random.choice(settlement.chronology)
        building.history.append(
            f'Year {year}\nThis building caught fire unexpectedly, killing {victims} villagers that were here at the moment!')

        self.replacements['building'] = building.name.lower()
        self.replacements['victims'] = victims

        amount = random.randint(65, 80)
        building.set_on_fire(amount)

        return self.description


@register('wedding')
@dataclass(kw_only=True)
class Wedding(Event):
    """Represents a wedding between two villagers of the settlement"""

    def resolve(self, settlement: Settlement, year: int) -> str:
        """Resolve this event, producing effects on the given [settlement] and
        return the formatted description of the event. Note that you are strongly
        encouraged to use the provided 'description' method to to so"""
        husband, wife = random.sample(settlement.inhabitants, 2)
        self.replacements['husband'] = husband.name
        self.replacements['wife'] = wife.name

        if 'Wedding totem' in settlement:
            totem: WeddingTotem = settlement['Wedding totem'][0]
            totem.add_wedding()

            totem.history.append(f'Year {year}\nCongratulations to {husband.name} and {wife.name} for their wonderfull wedding!')

        return self.description


# List of the different events available in the simulation. Please note that
# once again, you should not directly take events from this list but rather use
# the get_event function provided below
_events = [Event.deserialize(event) for event in env.get_content('events.yaml')]


def get_event(current_year: int) -> Event | None:
    """Get a randomly selected event from a list of available events, if the
    event's minimal year is <= to the [current year]. There is a 25% chance to
    trigger an event and 75% to get no events at all"""
    if random.randint(1, 4) == 4 and _events:
        event = random.choice(_events)

        if current_year >= event.year:
            _events.remove(event)
            return event

    return None
