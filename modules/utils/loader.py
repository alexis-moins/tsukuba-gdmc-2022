from modules.blocks.structure import Structure

# Mapping of structure name -> Structure object
structures: dict[str, Structure] = {}

for file in ['house1', 'house2', 'house3']:
    __structure = Structure.parse_nbt_file(file)
    structures[file] = __structure
