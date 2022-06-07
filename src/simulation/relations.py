"""TODO write module doc here"""

from src import env
from collections import defaultdict
# from src.simulation.buildings.building import Building
from src.simulation.buildings.utils.building_type import BuildingType


#
Relation = dict[str, dict[str, int]]

#
_relations: dict[str, Relation] = env.get_content('relations.yaml')

#
_cached_relations: dict[tuple[str, str], Relation] = dict()


def parse_relation(key: str) -> Relation:
    """"""
    relation = _relations.get(key, {})
    return defaultdict(dict, relation)


def _gather_relation(target_name: str, target_type: BuildingType) -> Relation:
    """"""
    building_name = parse_relation(target_name)
    building_type = parse_relation(target_type.name)

    return {
        'buildings': building_name['buildings'] | building_type['buildings'],
        'types': building_name['types'] | building_type['types']
    }


def _get_relation(target_name: str, target_type: BuildingType) -> Relation:
    """"""
    identity = (target_name, target_type)

    if identity in _cached_relations:
        return _cached_relations[identity]

    relation = _gather_relation(target_name, target_type)
    _cached_relations[identity] = relation

    return relation


def get_priorities(target, buildings: list) -> list:
    """"""
    relation = _get_relation(target.name, target.properties.type)

    input(relation)

    priorities = []
    modificators = []

    for building in buildings:
        if building.name in relation['buildings']:
            priorities.append(building)
            modificators.append(relation['buildings'][building.name])
        elif building.properties.type.name in relation['types']:
            priorities.append(building)
            modificators.append(relation['types'][building.properties.type.name])

    a = sorted(priorities, key=lambda item: modificators[priorities.index(item)])
    input(a)

    return a
