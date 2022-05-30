import random
from src import env


class Villager:
    """"""

    def __init__(self, birth_year: int = 0) -> None:
        """"""
        self.__first_name = random.choice(env.FIRST_NAMES)
        self.__last_name = random.choice(env.LAST_NAMES)

        self.productivity = 1
        self.house = None
        self.work_place = None
        self.birth_year = birth_year

    @property
    def name(self) -> str:
        """Return the name of the villager"""
        return f'{self.__first_name} {self.__last_name}'

    def die(self, year: int, cause: str):
        """"""
        if self.work_place:
            self.work_place.workers.remove(self)
            self.work_place.history.append(f'{self.name} died at {year} of {cause}')

        if self.house:
            self.house.inhabitants.remove(self)
            self.house.history.append(f'{self.name} died at {year} of {cause}')
