from typing import Dict

from gdpc import toolbox as TB
from gdpc import interface as INTF
from gdpc import geometry as GEO

from build_area import Plot
from utils import Coordinates


def get_most_used_block_of_type(block_type: str, blocks: Dict[str, int]) -> str | None:
    """Return the block of the given type most represented in the given frequency dict"""
    iterator = filter(lambda k: block_type in k, blocks.keys())
    dicti = {key: blocks[key] for key in list(iterator)}

    if not dicti:
        return None

    return max(dicti, key=dicti.get)


def test_areas():

    plot1 = Plot(Coordinates(10, 0, 10), Coordinates(110, 255, 35))
    plot2 = Plot(Coordinates(10, 0, 40), Coordinates(110, 255, 75))
    plot3 = Plot(Coordinates(10, 0, 80), Coordinates(110, 255, 105))

    b1 = plot1.get_blocks_at_surface('MOTION_BLOCKING')
    for coordinates in b1.keys():
        INTF.placeBlock(*coordinates, 'lime_stained_glass')

    plot2.remove_trees()

    plot3.remove_trees()
    b1 = plot3.get_blocks_at_surface('MOTION_BLOCKING')
    for coordinates in b1.keys():
        INTF.placeBlock(*coordinates, 'orange_stained_glass')


if __name__ == '__main__':

    INTF.setBuffering(True)

    try:

        # Retreive the default build area
        build_area = Plot.get_build_area()

        command = f"tp @a {build_area.start.x} 110 {build_area.start.z}"
        INTF.runCommand(command)
        print(f'/{command}')

        build_area.remove_trees()

        plot1 = Plot(x=10, z=10, size=(10, 10))

        for coordinates in plot1.get_blocks_at_surface('MOTION_BLOCKING').keys():
            INTF.placeBlock(*coordinates, 'lime_stained_glass')
        INTF.sendBlocks()

        print("Done!")

    except KeyboardInterrupt:   # useful for aborting a run-away program
        print("Pressed Ctrl-C to kill program.")
