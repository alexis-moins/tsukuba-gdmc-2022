from src import env
from src.simulation.buildings.building import Building
from simulation.buildings.utils.building_type import BuildingType


class BuildingRelation:
    def __init__(self, building_relations: dict[str | BuildingType, int], block_relations: dict[str, int]):
        self.building_relations = building_relations
        self.bloc_relations = block_relations

    def get_building_value(self, other_building: str | BuildingType) -> int:
        """Return the bonus/malus corresponding to the given building/building type"""
        # print(f'type : {type(other_building)}, value : {other_building}')
        if isinstance(other_building, str):
            if other_building in self.building_relations:
                return self.building_relations[other_building]
            else:
                building_type = env.BUILDINGS[other_building].properties.building_type
        else:
            building_type = other_building

        if building_type in self.building_relations:
            return self.building_relations[building_type]
        else:
            return 0

    def get_block_values(self, block: str) -> int:
        """Return the bonus/malus corresponding to the given block"""
        if block in self.bloc_relations:
            return self.bloc_relations[block]
        else:
            return 0

    @staticmethod
    def deserialize(data: dict[str, any]):

        return BuildingRelation({BuildingType[k] if k in [bt.name for bt in BuildingType] else k: data['buildings'][k] for k in data['buildings']}, data['blocks'])


class RelationsHandler:
    def __init__(self, relation_data):
        self.relations: dict[str | BuildingType, BuildingRelation] = dict()

        for data in relation_data:
            if 'building' in data:
                self.relations[data['building']] = BuildingRelation.deserialize(data)
            else:
                self.relations[BuildingType[data['building_type']]] = BuildingRelation.deserialize(data)

    def get_building_relation(self, building: str | BuildingType) -> BuildingRelation:
        """"""
        if isinstance(building, str):
            if building in self.relations:
                return self.relations[building]
            else:
                building_type = env.BUILDINGS[building].properties.building_type
        else:
            building_type = building

        if building_type in self.relations:
            return self.relations[building_type]
        else:
            return None
