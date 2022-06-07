import random
from typing import Iterator

from src import env


class MinecraftItem:
    def __init__(self, name: str, tag_data: str = None):
        self.tag_data = tag_data
        self.name = name

    def to_minecraft_data(self, slot: int, count: int = 1):
        if self.tag_data is None:
            return f'{{Slot:{slot}b,id:"{self._mc_name()}",Count:{count}}}'
        else:
            return f'{{Slot:{slot}b,id:"{self._mc_name()}",Count:{count},tag:{{{self.tag_data}}}}}'

    def _mc_name(self):
        if 'minecraft:' in self.name:
            return self.name
        else:
            return 'minecraft:' + self.name


class ItemLoot(MinecraftItem):
    def __init__(self, name: str, max_amount: int, chance: float, repetition: int = 1):
        super().__init__(name)
        self.repetition = repetition
        self.chance = chance
        self.max_amount = max_amount

    @staticmethod
    def deserialize(data: dict[str, str]):
        return ItemLoot(data['item'], int(data['max_amount']), float(data['chance']), int(data['repetition']))

    def to_minecraft_data(self, slot: int, count=None):
        count = random.randint(1, self.max_amount)
        return super().to_minecraft_data(slot, count)


class LootTable:
    def __init__(self, items: list[ItemLoot]):
        self.items: list[ItemLoot] = items

    def get_items(self, max_slot_amount: int) -> Iterator[tuple[str, int]]:
        amount = 0
        for item in self.items:
            if amount >= max_slot_amount:
                break
            for i in range(item.repetition):
                if item.chance * 100 >= random.randint(0, 100):
                    yield item
                    amount += 1

    @staticmethod
    def deserialize(data: list[dict[str, str]]):
        return LootTable([ItemLoot.deserialize(item_data) for item_data in data])


LOOT_TABLES = {name: LootTable.deserialize(content)
               for name, content in env.get_content('loot_table.yaml').items()}
