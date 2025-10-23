import random
import json
import os
import sys
import time
import pickle
from collections import defaultdict
from typing import List, Tuple, Optional, Dict

from enums import Rarity, TileType, EnemyType
from dataclasses import Item, Character
from dungeon_generator import DungeonGenerator
from enemy import Enemy
from config import CLASS_DEFS

class Game:
    def __init__(self, skip_class_select: bool = False):
        self.width = 80
        self.height = 24
        self.player_pos = (0, 0)
        self.dungeon_level = 1
        self.enemies: Dict[Tuple[int, int], Enemy] = {}
        self.items: Dict[Tuple[int, int], Item] = {}
        # placeholders; will be set by class selection or by load_game
        # Provide a safe default Character to avoid __init__ issues when loading.
        self.player = Character("Hero", 100, 100, 10, 5, 1, 0, 100, 0, 5.0, 1.5, "Adventurer")
        self.inventory: List[Item] = []
        self.weapon: Optional[Item] = None
        self.armor: Optional[Item] = None
        self.amulet: Optional[Item] = None
        self.message_log: List[str] = []
        self.game_over = False
        self.in_shop = False

        # Only ask the player for class selection for brand-new games
        if not skip_class_select:
            self.choose_class()

        # generate starting level (or will be replaced by load_game)
        self.generate_level()

    def add_message(self, msg: str):
        self.message_log.append(msg)
        if len(self.message_log) > 5:
            self.message_log.pop(0)

    # ... (rest of the Game class methods remain the same)
    # All the methods from choose_class() to run() go here
    # I'm truncating for brevity since you already have the complete code
