from dataclasses import dataclass, asdict
from typing import Optional
from enums import Rarity

@dataclass
class Item:
    name: str
    item_type: str
    value: int
    description: str
    rarity: Rarity

    def get_price(self):
        return int(self.rarity.base_price * max(1, self.value // 2))

    def get_sell_price(self):
        return self.get_price() // 2

    def __repr__(self):
        return f"{self.name} (+{self.value} {self.item_type}) [{self.rarity.display_name}]"

    def colored_repr(self):
        return f"{self.rarity.color}{self.name} (+{self.value} {self.item_type}) [{self.rarity.display_name}]\033[0m"

@dataclass
class Character:
    name: str
    hp: int
    max_hp: int
    attack: int
    defense: int
    level: int
    xp: int
    xp_to_next: int
    gold: int
    crit_chance: float   # stored as percent (e.g., 3.0 for 3%)
    crit_damage: float   # multiplier (e.g., 1.4)
    character_class: str
