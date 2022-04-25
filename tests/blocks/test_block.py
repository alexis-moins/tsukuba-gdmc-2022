from modules.blocks.block import Block

from modules.utils.direction import Direction
from modules.utils.coordinates import Coordinates


def test_deserialize() -> None:
    """Test to ensure the deserialization of a block works"""
    name = 'minecraft:glowstone'
    coordinates = Coordinates(1, 2, 3)
    block = Block.deserialize(name, coordinates)

    assert block.name == name
    assert block.coordinates == coordinates

    name = 'minecraft:oak_stairs[facing=east]'
    block = Block.deserialize(name, coordinates)

    assert block.name == 'minecraft:oak_stairs'
    assert 'facing' in block.properties.keys()
    assert block.properties['facing'] == Direction.EAST
    assert block.properties == {'facing': Direction.EAST}
    assert block.coordinates == coordinates
