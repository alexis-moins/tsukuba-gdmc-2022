from typing import Any

import yaml


def load_file(file_name: str) -> Any:
    """Load the given yaml file and return its content"""
    with open(f'resources/{file_name}', 'r') as data:
        return yaml.safe_load(data)


# Wether the simulation runs in debug mode or not
DEBUG = False

# The mapping material -> (replacement, keepProperties)
BUILDING_MATERIALS: dict[str, tuple[str, bool]] = dict()

# The mapping of relations between structures to compute the score at each turn
RELATIONS: dict[str, dict[str, int]] = load_file('relations.yaml')
