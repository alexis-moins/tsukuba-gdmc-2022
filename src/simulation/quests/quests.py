import random

from gdpc import lookup

from src import env

creatures = env.get_content('creatures.txt', YAML=False)


class Quest:
    def __init__(self, task, reward, danger_level):
        self.danger_level = danger_level
        self.reward = reward
        self.task = task

    def __str__(self):
        return f'{self.task} {self.danger_level} {self.reward}'


def get_quests(amount: int):
    for i in range(amount):

        danger_level = random.choice(['Peaceful', 'No Danger', 'Be careful', 'Dangerous', 'Very Dangerous'])
        reward = f'{random.choice(range(1, 99))} {random.choice(lookup.BLOCKS).replace("minecraft:", "")}'

        task = get_getter_task() if bool(random.getrandbits(1)) else get_hunt_task()

        yield Quest(task, reward, danger_level)


def get_getter_task():
    return f'Collect {random.choice(range(1, 15))} {random.choice(lookup.BLOCKS).replace("minecraft:", "")}'


def get_hunt_task():
    return f'{random.choice(["Hunt", "Capture"])} {random.choice(range(2, 15))} {random.choice(creatures)}'
