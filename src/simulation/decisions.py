import random
from typing import Callable

from src.utils.action_type import ResourceType

from src.simulation.settlement import Settlement
from src.simulation.buildings.building import Building


# Type alias for functions in charge of the building selection logic
# Functions given to the Simulation constructor as building_selection must all
# follow the prototype below, which is:
# - arguments: Settlement, list[Building]
# - return value: Building | None
DecisionMaking = Callable[[Settlement, list[Building]], Building | None]


def choose_building(settlement: Settlement, buildings: list[Building]) -> Building | None:
    """Return a building chosen from the given [buildings] Selection is
    made by looking at the resource the settlement needs the most and
    randomly selecting a building from them"""
    if len(buildings) == 1:
        return buildings[0]

    main_resource = _choose_resource_type(settlement)

    selected_buildings = list(filter(lambda building: building.properties.resource in (
        main_resource, ResourceType.UTILITY), buildings))

    if not selected_buildings:
        return None

    return random.choice(selected_buildings)


def _choose_resource_type(settlement: Settlement) -> ResourceType:
    """Return the ResourceType on which the settlement should be focusing on.

    The optimal resource is selected based on the following criteriae:
    - [FOOD] if the settlement is lacking food to feed everyone
    - [WORK] if there are: no available jobs but unemployed villagers
    - [BED]  if there are: no available jobs and no free beds
    - [NONE] if there are: no available jobs, no unemployment and no free beds
    - [BED]  if there are available jobs"""
    if settlement.food_production <= settlement.population:
        return ResourceType.FOOD

    if settlement.worker_number == settlement.total_worker_slots:

        if settlement.inactive_villagers:
            return ResourceType.WORK

        if settlement.number_of_beds == settlement.population:
            return ResourceType.BED

        return ResourceType.NONE

    return ResourceType.BED
