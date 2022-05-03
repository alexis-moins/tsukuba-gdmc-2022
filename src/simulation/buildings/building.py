from __future__ import annotations

from enum import Enum

from src.plots.plot import Plot
from src.simulation.buildings.building_types import BuildingTypes
from src.utils import loader


class Building:
    """Class representing a list of blocks (structure) on a given plot"""

    def __init__(self, structure, name, profession, bed_amount, productivity, food,
                 build_type: BuildingTypes = BuildingTypes.NONE):
        self.structure = structure
        self.name = name
        self.profession = profession
        self.bed_amount = bed_amount
        self.work_productivity = productivity
        self.food_productivity = food
        self.build_type = build_type
        self.plot: Plot = None

    def __str__(self):
        return self.name


class Buildings(Enum):
    HOUSE = (10, Building(loader.structures['house2'], 'house2', None, 5, 0, 0, BuildingTypes.HOUSING))
    FARM = (10, Building(loader.structures['farm'], 'farm', 'Farmer', 0, 1, 5, BuildingTypes.FARM))
    WHEAT_PACK_1 = (
        20, Building(loader.structures['extensions/farm_wheat_1'], 'farm_wheat_1', 'Farmer', 0, 0, 5, BuildingTypes.FARM))
    WHEAT_PACK_2 = (
        20, Building(loader.structures['extensions/farm_wheat_2'], 'farm_wheat_2', 'Farmer', 0, 0, 5, BuildingTypes.FARM))
    ORE_PACK = (50, Building(loader.structures['extensions/forge_ore_pack'],
                'forge_ore_pack', None, 0, 5, 0, BuildingTypes.FORGING))
    FORGE = (20, Building(loader.structures['forge'], 'forge', None, 0, 20, 0, BuildingTypes.FORGING))
    SAWMILL = (20, Building(loader.structures['sawmill'], 'sawmill', None, 0, 10, 0, BuildingTypes.WOODCUTTING))
    WOOD_STACK = (10, Building(loader.structures['extensions/sawmill2'],
                  'sawmill2', None, 0, 5, 0, BuildingTypes.WOODCUTTING))
    CUT_TREE = (50, Building(loader.structures['extensions/sawmill1'],
                'sawmill1', None, 0, 20, 0, BuildingTypes.WOODCUTTING))
