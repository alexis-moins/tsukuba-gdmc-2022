import textwrap
from colorama import Fore

from src.simulation.settlement import Settlement
from src.simulation.buildings.building import Building


def print_kills(number: int, cause: str) -> None:
    """Display the [number] of killed villagers and the [cause] of their death"""
    print(f'{Fore.RED}[{number}]{Fore.WHITE} villagers died in {cause}')


def display_constructible_buildings(buildings: list[Building]) -> None:
    """"""
    formatted = textwrap.fill(", ".join(str(building) for building in buildings), width=80, subsequent_indent=' ' * 26)
    print(f'Constructible buildings: [{formatted}]')


def display_settlement(settlement: Settlement) -> None:
    """Display a summary of the given [settlement] at the end of the current year"""
    print('==== Summary ====')
    print(
        f'\n   Population: {Fore.GREEN}{settlement.population}/{settlement.number_of_beds}{Fore.WHITE}')
    print(f'   Food: {Fore.GREEN}{settlement.food_available}{Fore.WHITE} ({Fore.GREEN}{settlement.food_production}{Fore.WHITE} / year)')
    print(f'   Work: {Fore.GREEN}{settlement.worker_number}/{settlement.total_worker_slots}{Fore.WHITE}')

    print(f'\n   Buildings {Fore.GREEN}[{len(settlement._buildings)}]{Fore.WHITE}')

    buildings = textwrap.fill(
        ", ".join([f"{building.name}: {Fore.GREEN}{settlement._counter[building.name]}/{building.properties.maximum}{Fore.WHITE}" for building in settlement.chronology]), subsequent_indent=' ' * 6)
    print(f'\n      {buildings}')
