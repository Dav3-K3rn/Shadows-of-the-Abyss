from enums import EnemyType

class Enemy:
    def __init__(self, enemy_type: EnemyType, level: int):
        self.type = enemy_type
        self.name = enemy_type.display_name
        self.level = level
        self.max_hp = enemy_type.base_hp + (level - 1) * 5
        self.hp = self.max_hp
        self.attack = enemy_type.base_atk + (level - 1) * 2
        self.defense = enemy_type.base_def + (level - 1)
        self.xp_reward = enemy_type.xp_reward + (level - 1) * 10
        self.gold_reward = enemy_type.gold_reward + (level - 1) * 5
        self.symbol = enemy_type.symbol
        self.color = enemy_type.color

    def is_alive(self):
        return self.hp > 0
