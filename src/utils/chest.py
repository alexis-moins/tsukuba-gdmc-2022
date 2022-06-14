import random


def get_filled_chest_data(prio_items, table, fill_amount: int = None):
    if fill_amount is None:
        fill_amount = random.randint(5, 20)
    slots = random.sample(range(27), k=fill_amount + 1)  # + 1 if we need slot for prio item
    item_data = [item.to_minecraft_data(slot) for slot, item in zip(slots, list(table.get_items(fill_amount)))]
    # Add prio item
    if prio_items:
        item_data.append(random.choice(prio_items).to_minecraft_data(slots[-1]))
    chest_data = f'{{Items:[{",".join(item_data)}]}}'
    return chest_data
