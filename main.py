from __future__ import annotations

import time
import random
from typing import Dict

from gdpc import toolbox as TB
from gdpc import geometry as GEO
from gdpc import interface as INTF

from plots import construction_plot
from plots.plot import Plot
from plots.suburb_plot import SuburbPlot
from utils.structure import Structure


def get_most_used_block_of_type(block_type: str, blocks: Dict[str, int]) -> str | None:
    """Return the block of the given type most represented in the given frequency dict"""
    iterator = filter(lambda k: block_type in k, blocks.keys())
    dicti = {key: blocks[key] for key in list(iterator)}

    if not dicti:
        return None

    return max(dicti, key=dicti.get)


if __name__ == '__main__':

    INTF.setBuffering(True)
    INTF.placeBlockFlags(doBlockUpdates=True, customFlags='0100011')

    try:
        # Retrieve the default build area
        build_area = Plot.get_build_area()

        command = f"tp @a {build_area.start.x} 110 {build_area.start.z}"
        INTF.runCommand(command)
        print(f'=> /{command}')

        most_used_wood = build_area.filter_most_used_blocks('log')

        if most_used_wood is None:
            most_used_wood = 'minecraft:oak_log (default)'

        print(f'=> Most used wood: {most_used_wood}')

        structures = dict()
        structures['house1'] = Structure.parse_nbt_file('house1')
        structures['house2'] = Structure.parse_nbt_file('house2')

        suburb = SuburbPlot(x=10 + build_area.start.x, z=10 + build_area.start.z, size=(50, 50))
        suburb.remove_trees()

        houses = [structures['house1'], structures['house2']]

        #  Move the following code into a method in SuburbPlot
        for i in range(5):
            iter_start = time.time()
            random.shuffle(houses)
            house = houses[0]

            area = (house.size[0], house.size[2])
            construction_plot = suburb.get_construction_plot(area)

            if construction_plot:
                construction_plot.build(house, replacement=most_used_wood)
                print(
                    f'\n=> Built structure {house.name} of size {house.size} at {construction_plot.build_start} in {time.time() - iter_start: .2f}s\n')

            print(f'=> Unable to find construction area for structure with size {house.size}')

        print('Done!')

    except KeyboardInterrupt:   # useful for aborting a run-away program
        print("Pressed Ctrl-C to kill program.")
