from enum import Enum

class Rarity(Enum):
    COMMON = (1.0, "\033[37m", "Common", 10)      # White
    UNCOMMON = (1.5, "\033[92m", "Uncommon", 25)  # Green
    RARE = (2.0, "\033[94m", "Rare", 50)          # Blue
    EPIC = (3.0, "\033[95m", "Epic", 100)         # Magenta

    def __init__(self, multiplier, color, display_name, base_price):
        self.multiplier = multiplier
        self.color = color
        self.display_name = display_name
        self.base_price = base_price

class TileType(Enum):
    WALL = '#'
    FLOOR = '.'
    DOOR = '+'
    PLAYER = '@'
    ENEMY = 'E'
    CHEST = 'C'
    STAIRS_DOWN = '>'
    STAIRS_UP = '<'
    POTION = 'p'
    WEAPON = 'w'
    ARMOR = 'a'

class EnemyType(Enum):
    GOBLIN = ("Goblin", 20, 3, 1, 15, 'G', "\033[33m", 5)      # Yellow
    ORC = ("Orc", 35, 5, 2, 30, 'O', "\033[91m", 10)            # Red
    TROLL = ("Troll", 50, 7, 3, 50, 'T', "\033[31m", 20)        # Dark Red
    DRAGON = ("Dragon", 100, 12, 5, 150, 'D', "\033[35m", 50)   # Purple
    DEMON = ("Knight", 75, 10, 4, 100, 'K', "\033[90m", 30)      # Dark Gray

    def __init__(self, display_name, hp, atk, defense, xp, symbol, color, gold):
        self.display_name = display_name
        self.base_hp = hp
        self.base_atk = atk
        self.base_def = defense
        self.xp_reward = xp
        self.symbol = symbol
        self.color = color
        self.gold_reward = gold
