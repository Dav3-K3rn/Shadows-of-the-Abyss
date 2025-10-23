import random
import json
import os
import sys
import time
import pickle
from collections import defaultdict
from typing import List, Tuple, Optional, Dict

from enums import Rarity, TileType, EnemyType
from dataclasses import Item, Character, asdict
from dungeon_generator import DungeonGenerator, Room
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

    # -------------------------
    # Class selection
    # -------------------------
    def choose_class(self):
        os.system('clear' if os.name != 'nt' else 'cls')
        print("Choose your class:\n")
        names = list(CLASS_DEFS.keys())
        for i, name in enumerate(names, start=1):
            c = CLASS_DEFS[name]
            print(f"{i}. {name}")
            print(f"   HP: {c['hp']} | ATK: {c['atk']} | DEF: {c['def']}")
            print(f"   Crit: {int(c['crit'])}% | Crit DMG: {c['crit_dmg']}x")
            print(f"   Starting Weapon: {c['weapon_name']} (+{c['weapon_bonus']} ATK)")
            print(f"   Playstyle: {c['playstyle']}\n")

        while True:
            choice = input("Enter the number of your class: ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(names):
                chosen_name = names[int(choice) - 1]
                break
            print("Invalid selection. Try again.")

        stats = CLASS_DEFS[chosen_name]
        # Create player Character using class stats (player.attack is base attack WITHOUT weapon)
        self.player = Character(
            name="Hero",
            hp=stats["hp"],
            max_hp=stats["hp"],
            attack=stats["atk"],
            defense=stats["def"],
            level=1,
            xp=0,
            xp_to_next=100,
            gold=100,
            crit_chance=stats["crit"],
            crit_damage=stats["crit_dmg"],
            character_class=chosen_name
        )

        # Equip starting weapon (kept as an Item so code that expects Item works)
        weapon_item = Item(
            name=stats["weapon_name"],
            item_type='attack',
            value=stats["weapon_bonus"],
            description=f"Starting weapon: {stats['weapon_name']}",
            rarity=Rarity.COMMON
        )
        self.weapon = weapon_item
        self.add_message(f"Selected class: {chosen_name}. Equipped {weapon_item.name} (+{weapon_item.value} ATK)")

    # -------------------------
    # Level generation, items, enemies...
    # -------------------------
    def generate_level(self):
        # Check if this is a shop level (every 5 levels)
        if self.dungeon_level % 5 == 0:
            self.in_shop = True
            self.add_message(f"Welcome to the shop! Floor {self.dungeon_level}")
            return

        self.in_shop = False
        gen = DungeonGenerator(self.width, self.height)
        self.grid, rooms = gen.generate(random.randint(6, 10))

        # Place player in first room (center)
        self.player_pos = rooms[0].center

        # Place stairs in last room
        self.stairs_pos = rooms[-1].center

        # Place enemies and items
        self.enemies.clear()
        self.items.clear()

        for room in rooms[1:-1]:  # Skip first and last room
            # Enemies
            if random.random() < 0.7:
                enemy_x = random.randint(room.x + 1, room.x + room.width - 2)
                enemy_y = random.randint(room.y + 1, room.y + room.height - 2)
                enemy_type = random.choice(list(EnemyType))
                self.enemies[(enemy_x, enemy_y)] = Enemy(enemy_type, self.dungeon_level)

            # Items
            if random.random() < 0.4:
                item_x = random.randint(room.x + 1, room.x + room.width - 2)
                item_y = random.randint(room.y + 1, room.y + room.height - 2)
                self.items[(item_x, item_y)] = self._generate_item()

        self.add_message(f"Entered dungeon level {self.dungeon_level}")

    def _generate_item(self) -> Item:
        # First, determine if we should drop money instead of an item
        money_chance = 0.3  # 30% chance to find money instead of an item
        if random.random() < money_chance:
            # Generate money drop
            gold_amount = random.randint(5, 20) + (self.dungeon_level * 2)
            return Item("Gold Pouch", 'gold', gold_amount, f"A pouch containing {gold_amount} gold", Rarity.COMMON)

        item_type = random.choice(['weapon', 'armor', 'amulet', 'potion'])
        
        # Reduce potion frequency by adjusting weights
        item_weights = {
            'weapon': 0.3,
            'armor': 0.3,
            'amulet': 0.25,
            'potion': 0.15  # Reduced from equal chance
        }
        
        item_type = random.choices(
            list(item_weights.keys()),
            weights=list(item_weights.values())
        )[0]

        # Determine rarity with weighted probabilities
        rarity_roll = random.random()
        if rarity_roll < 0.5:
            rarity = Rarity.COMMON
        elif rarity_roll < 0.8:
            rarity = Rarity.UNCOMMON
        elif rarity_roll < 0.95:
            rarity = Rarity.RARE
        else:
            rarity = Rarity.EPIC

        base_value = random.randint(2, 5) + self.dungeon_level
        actual_value = int(base_value * rarity.multiplier)

        if item_type == 'weapon':
            weapons = ['Sword', 'Axe', 'Mace', 'Spear', 'Dagger']
            name = random.choice(weapons)
            return Item(name, 'attack', actual_value, f"A deadly {name.lower()}", rarity)
        elif item_type == 'armor':
            armors = ['Leather Armor', 'Chain Mail', 'Plate Armor', 'Shield']
            name = random.choice(armors)
            return Item(name, 'defense', actual_value, f"Protective {name.lower()}", rarity)
        elif item_type == 'amulet':
            amulet_type = random.choice(['crit_chance', 'crit_damage'])
            if amulet_type == 'crit_chance':
                value = random.randint(2, 5) * rarity.multiplier
                return Item('Amulet of Precision', 'crit_chance', int(value), 'Increases critical hit chance', rarity)
            else:
                value = random.randint(10, 25) * (rarity.multiplier / 10)
                return Item('Amulet of Power', 'crit_damage', int(value * 10), 'Increases critical damage', rarity)
        else:
            # Health potion - reduced frequency due to the weights above
            heal_amount = 30 + (self.dungeon_level * 5)  # Scale potion healing with dungeon level
            return Item('Health Potion', 'heal', heal_amount, f'Restores {heal_amount} HP', Rarity.COMMON)

    # -------------------------
    # Movement & combat
    # -------------------------
    def move_player(self, dx: int, dy: int):
        if self.in_shop:
            return

        new_x = self.player_pos[0] + dx
        new_y = self.player_pos[1] + dy

        if not (0 <= new_x < self.width and 0 <= new_y < self.height):
            return

        if self.grid[new_y][new_x] == TileType.WALL:
            return

        # Check for enemy
        if (new_x, new_y) in self.enemies:
            self._combat(self.enemies[(new_x, new_y)])
            return

        # Check for item
        if (new_x, new_y) in self.items:
            item = self.items.pop((new_x, new_y))
            
            if item.item_type == 'gold':
                # Handle money pickup
                self.player.gold += item.value
                self.add_message(f"Found {item.value} gold!")
            else:
                # Handle regular item pickup
                self.inventory.append(item)
                self.add_message(f"Picked up {item.rarity.display_name} {item.name}")

        # Check for stairs
        if (new_x, new_y) == self.stairs_pos:
            self.dungeon_level += 1
            self.generate_level()
            return

        self.player_pos = (new_x, new_y)

        # Enemy turns
        self._enemy_turns()

    def _combat(self, enemy: Enemy):
        # Calculate crit (crit_chance stored as percent)
        crit_chance = self.player.crit_chance + (self.amulet.value / 100 if self.amulet and self.amulet.item_type == 'crit_chance' else 0)
        crit_dmg_bonus = self.player.crit_damage + (self.amulet.value / 100 if self.amulet and self.amulet.item_type == 'crit_damage' else 0)

        is_crit = random.random() * 100 < crit_chance

        base_dmg = max(1, self.player.attack + (self.weapon.value if self.weapon else 0) - enemy.defense)
        player_dmg = int(base_dmg * crit_dmg_bonus) if is_crit else base_dmg

        enemy.hp -= player_dmg
        if is_crit:
            self.add_message(f"CRIT! Hit {enemy.name} for {player_dmg} damage!")
        else:
            self.add_message(f"Hit {enemy.name} for {player_dmg} damage!")

        if enemy.hp <= 0:
            self.add_message(f"Defeated {enemy.name}! +{enemy.xp_reward} XP, +{enemy.gold_reward} gold")
            self.player.xp += enemy.xp_reward
            self.player.gold += enemy.gold_reward

            # Remove enemy
            for pos, e in list(self.enemies.items()):
                if e is enemy:
                    del self.enemies[pos]
                    break

            self._check_level_up()
        else:
            enemy_dmg = max(1, enemy.attack - (self.player.defense + (self.armor.value if self.armor else 0)))
            self.player.hp -= enemy_dmg
            self.add_message(f"{enemy.name} hit you for {enemy_dmg} damage!")

            if self.player.hp <= 0:
                self.game_over = True
                self.add_message("You died! Game Over.")

    def _enemy_turns(self):
        for pos, enemy in list(self.enemies.items()):
            # Simple AI: move towards player if in range
            dx = self.player_pos[0] - pos[0]
            dy = self.player_pos[1] - pos[1]
            distance = abs(dx) + abs(dy)

            if distance <= 5:
                move_x = 1 if dx > 0 else -1 if dx < 0 else 0
                move_y = 1 if dy > 0 else -1 if dy < 0 else 0

                new_x = pos[0] + move_x
                new_y = pos[1] + move_y

                if (new_x, new_y) == self.player_pos:
                    # Attack player
                    enemy_dmg = random.randint(1, 15)
                    self.player.hp -= enemy_dmg
                    self.add_message(f"{enemy.name} hit you for {enemy_dmg} damage!")

                    if self.player.hp <= 0:
                        self.game_over = True
                        self.add_message("You died! Game Over.")
                elif (0 <= new_x < self.width and 0 <= new_y < self.height and
                      self.grid[new_y][new_x] == TileType.FLOOR and
                      (new_x, new_y) not in self.enemies):
                    del self.enemies[pos]
                    self.enemies[(new_x, new_y)] = enemy

    def _check_level_up(self):
        while self.player.xp >= self.player.xp_to_next:
            self.player.level += 1
            self.player.xp -= self.player.xp_to_next
            self.player.xp_to_next = int(self.player.xp_to_next * 1.5)

            self.player.max_hp += 20
            self.player.hp = self.player.max_hp
            self.player.attack += 2
            self.player.defense += 1

            self.add_message(f"Level Up! Now level {self.player.level}")

    # -------------------------
    # Items / Inventory
    # -------------------------
    def use_item(self, index: int):
        if 0 <= index < len(self.inventory):
            item = self.inventory[index]

            if item.item_type == 'heal':
                self.player.hp = min(self.player.max_hp, self.player.hp + item.value)
                self.add_message(f"Used {item.name}, restored {item.value} HP")
                self.inventory.pop(index)
                self._enemy_turns()
            elif item.item_type == 'attack':
                if self.weapon:
                    self.inventory.append(self.weapon)
                self.weapon = self.inventory.pop(index)
                self.add_message(f"Equipped {item.name}")
            elif item.item_type == 'defense':
                if self.armor:
                    self.inventory.append(self.armor)
                self.armor = self.inventory.pop(index)
                self.add_message(f"Equipped {item.name}")
            elif item.item_type in ['crit_chance', 'crit_damage']:
                if self.amulet:
                    self.inventory.append(self.amulet)
                self.amulet = self.inventory.pop(index)
                self.add_message(f"Equipped {item.name}")

    def combine_items(self, idx1: int, idx2: int):
        if not (0 <= idx1 < len(self.inventory) and 0 <= idx2 < len(self.inventory)):
            self.add_message("Invalid item indices")
            return

        if idx1 == idx2:
            self.add_message("Cannot combine an item with itself")
            return

        item1 = self.inventory[idx1]
        item2 = self.inventory[idx2]

        # Check if items can be combined (same name and type)
        if item1.name != item2.name or item1.item_type != item2.item_type:
            self.add_message(f"Cannot combine {item1.name} with {item2.name}")
            return

        # Cannot combine healing potions
        if item1.item_type == 'heal':
            self.add_message("Cannot combine potions")
            return

        # Combine items - add the values and use higher rarity
        new_value = item1.value + item2.value
        new_rarity = item1.rarity if item1.rarity.multiplier > item2.rarity.multiplier else item2.rarity
        combined_item = Item(item1.name, item1.item_type, new_value, item1.description, new_rarity)

        # Remove both items and add the combined one
        higher_idx = max(idx1, idx2)
        lower_idx = min(idx1, idx2)

        self.inventory.pop(higher_idx)
        self.inventory.pop(lower_idx)
        self.inventory.append(combined_item)

        self.add_message(f"Combined into {new_rarity.display_name} {combined_item.name} (+{new_value})!")

    # -------------------------
    # Shop
    # -------------------------
    def show_shop(self):
        shop_items = []
        # Generate shop inventory
        for _ in range(8):
            item_type = random.choice(['weapon', 'armor', 'amulet'])
            rarity = random.choices(
                [Rarity.COMMON, Rarity.UNCOMMON, Rarity.RARE],
                weights=[0.5, 0.35, 0.15]
            )[0]

            base_value = random.randint(3, 7) + self.dungeon_level // 2
            actual_value = int(base_value * rarity.multiplier)

            if item_type == 'weapon':
                weapons = ['Sword', 'Axe', 'Mace', 'Spear', 'Dagger', 'Halberd']
                name = random.choice(weapons)
                shop_items.append(Item(name, 'attack', actual_value, f"A deadly {name.lower()}", rarity))
            elif item_type == 'armor':
                armors = ['Leather Armor', 'Chain Mail', 'Plate Armor', 'Shield', 'Helmet']
                name = random.choice(armors)
                shop_items.append(Item(name, 'defense', actual_value, f"Protective {name.lower()}", rarity))
            else:
                amulet_type = random.choice(['crit_chance', 'crit_damage'])
                if amulet_type == 'crit_chance':
                    value = random.randint(2, 5) * rarity.multiplier
                    shop_items.append(Item('Amulet of Precision', 'crit_chance', int(value), 'Increases critical hit chance', rarity))
                else:
                    value = random.randint(10, 25) * (rarity.multiplier / 10)
                    shop_items.append(Item('Amulet of Power', 'crit_damage', int(value * 10), 'Increases critical damage', rarity))

        # Add health potions (reduced quantity)
        for _ in range(2):  # Reduced from 3 to 2
            heal_amount = 30 + (self.dungeon_level * 5)
            shop_items.append(Item('Health Potion', 'heal', heal_amount, f'Restores {heal_amount} HP', Rarity.COMMON))

        while True:
            os.system('clear' if os.name != 'nt' else 'cls')
            print("=" * 80)
            print(f"{'SHOP - FLOOR ' + str(self.dungeon_level):^80}")
            print("=" * 80)
            print(f"Your Gold: {self.player.gold}")
            print("\n=== SHOP INVENTORY ===")

            for i, item in enumerate(shop_items):
                print(f"{i+1}. {item.colored_repr()} - {item.get_price()} gold")

            print("\n=== YOUR INVENTORY ===")
            if not self.inventory:
                print("Empty")
            else:
                for i, item in enumerate(self.inventory):
                    print(f"s{i+1}. {item.colored_repr()} - Sell for {item.get_sell_price()} gold")

            print("\nType number to buy, 's' + number to sell (e.g., 's3'), 'leave' to continue")

            choice = input("> ").strip().lower()

            if choice == 'leave':
                self.dungeon_level += 1
                self.generate_level()
                break
            elif choice.startswith('s') and len(choice) > 1:
                try:
                    idx = int(choice[1:]) - 1
                    if 0 <= idx < len(self.inventory):
                        item = self.inventory.pop(idx)
                        sell_price = item.get_sell_price()
                        self.player.gold += sell_price
                        self.add_message(f"Sold {item.name} for {sell_price} gold")
                except ValueError:
                    self.add_message("Invalid sell command")
            elif choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(shop_items):
                    item = shop_items[idx]
                    price = item.get_price()
                    if self.player.gold >= price:
                        self.player.gold -= price
                        self.inventory.append(item)
                        self.add_message(f"Bought {item.name} for {price} gold")
                    else:
                        self.add_message(f"Not enough gold! Need {price}, have {self.player.gold}")

    # -------------------------
    # Rendering & UI
    # -------------------------
    def render(self):
        os.system('clear' if os.name != 'nt' else 'cls')

        if self.in_shop:
            self.show_shop()
            return

        # Draw dungeon
        for y in range(self.height):
            row = []
            for x in range(self.width):
                if (x, y) == self.player_pos:
                    row.append('\033[93m@\033[0m')  # Yellow player
                elif (x, y) in self.enemies:
                    enemy = self.enemies[(x, y)]
                    row.append(f'{enemy.color}{enemy.symbol}\033[0m')
                elif (x, y) in self.items:
                    # Different color for gold items
                    item = self.items[(x, y)]
                    if item.item_type == 'gold':
                        row.append('\033[33m$\033[0m')  # Gold color for money
                    else:
                        row.append('\033[92mi\033[0m')  # Green for regular items
                elif (hasattr(self, 'stairs_pos') and (x, y) == self.stairs_pos):
                    row.append('\033[96m>\033[0m')  # Cyan stairs
                else:
                    tile = self.grid[y][x]
                    row.append(tile.value)
            print(''.join(row))

        # Status bar
        print("=" * self.width)
        print(f"Class: {self.player.character_class} | HP: {self.player.hp}/{self.player.max_hp} | "
              f"Gold: {self.player.gold} | "
              f"Lvl: {self.player.level} | XP: {self.player.xp}/{self.player.xp_to_next} | "
              f"Depth: {self.dungeon_level}")

        weapon_bonus = self.weapon.value if self.weapon else 0
        armor_bonus = self.armor.value if self.armor else 0
        crit_chance_bonus = self.amulet.value if self.amulet and self.amulet.item_type == 'crit_chance' else 0
        crit_dmg_bonus = self.amulet.value if self.amulet and self.amulet.item_type == 'crit_damage' else 0

        total_atk = self.player.attack + weapon_bonus
        total_def = self.player.defense + armor_bonus
        total_crit_chance = self.player.crit_chance + crit_chance_bonus
        total_crit_dmg = self.player.crit_damage + (crit_dmg_bonus / 100)

        print(f"ATK: {total_atk} | "
              f"DEF: {total_def} | "
              f"Crit: {total_crit_chance:.1f}% | "
              f"CritDMG: {total_crit_dmg:.2f}x")

        if self.weapon:
            print(f"Weapon: {self.weapon.name} (+{self.weapon.value} ATK) [{self.weapon.rarity.display_name}]")
        if self.armor:
            print(f"Armor: {self.armor.name} (+{self.armor.value} DEF) [{self.armor.rarity.display_name}]")
        if self.amulet:
            bonus_type = "Crit%" if self.amulet.item_type == 'crit_chance' else "CritDMG"
            print(f"Amulet: {self.amulet.name} (+{self.amulet.value} {bonus_type}) [{self.amulet.rarity.display_name}]")
        print("\nMessages:")
        for msg in self.message_log:
            print(f"  {msg}")

        print("\nEnemies: g=Goblin o=Orc T=Troll D=Dragon d=Demon")
        print("Items: i=Item $=Gold")
        print("Controls: [wasd] move (prefix with number like '5w') | [i] inventory | [save] save | [q] quit")

    # -------------------------
    # Inventory UI
    # -------------------------
    def show_inventory(self):
        while True:
            os.system('clear' if os.name != 'nt' else 'cls')
            print("=== INVENTORY ===")

            if not self.inventory:
                print("Empty")
            else:
                for i, item in enumerate(self.inventory):
                    print(f"{i+1}. {item.colored_repr()}")

            print("\nPress number to use/equip item")
            print("Press 'c' followed by two numbers to combine items")
            print("Press [b] to go back")

            choice = input("> ").strip().lower()

            if choice == 'b':
                break
            elif choice.startswith('c'):
                # Combine items - extract numbers after 'c'
                try:
                    nums_str = choice[1:].strip()
                    if ' ' in nums_str:
                        parts = nums_str.split()
                        idx1 = int(parts[0]) - 1
                        idx2 = int(parts[1]) - 1
                    else:
                        if len(nums_str) == 2:
                            idx1 = int(nums_str[0]) - 1
                            idx2 = int(nums_str[1]) - 1
                        elif len(nums_str) == 3:
                            try:
                                idx1 = int(nums_str[0]) - 1
                                idx2 = int(nums_str[1:]) - 1
                            except:
                                idx1 = int(nums_str[:2]) - 1
                                idx2 = int(nums_str[2]) - 1
                        elif len(nums_str) == 4:
                            idx1 = int(nums_str[:2]) - 1
                            idx2 = int(nums_str[2:]) - 1
                        else:
                            raise ValueError("Invalid format")

                    self.combine_items(idx1, idx2)
                except (ValueError, IndexError):
                    self.add_message("Invalid combination command. Use format: c 3 5")
            elif choice.isdigit():
                self.use_item(int(choice) - 1)
                if not self.inventory or all(item.item_type != 'heal' for item in self.inventory):
                    continue

    # -------------------------
    # Save / Load
    # -------------------------
    def save_game(self, filename="game_save.sav"):
        save_data = {
            'player': asdict(self.player),
            'player_pos': self.player_pos,
            'dungeon_level': self.dungeon_level,
            'in_shop': self.in_shop,
            'inventory': [(asdict(item), item.rarity.name) for item in self.inventory],
            'weapon': (asdict(self.weapon), self.weapon.rarity.name) if self.weapon else None,
            'armor': (asdict(self.armor), self.armor.rarity.name) if self.armor else None,
            'amulet': (asdict(self.amulet), self.amulet.rarity.name) if self.amulet else None,
            'message_log': self.message_log,
            'grid': [[tile.name for tile in row] for row in self.grid] if not self.in_shop else None,
            'stairs_pos': self.stairs_pos if not self.in_shop else None,
            'enemies': {str(pos): {'type': e.type.name, 'level': e.level, 'hp': e.hp}
                       for pos, e in self.enemies.items()},
            'items': {str(pos): (asdict(item), item.rarity.name)
                     for pos, item in self.items.items()}
        }

        with open(filename, 'wb') as f:
            pickle.dump(save_data, f)

        self.add_message(f"Game saved to {filename}")

    def load_game(self, filename="game_save.sav"):
        with open(filename, 'rb') as f:
            save_data = pickle.load(f)

        # ensure character_class exists in saved player dict
        player_dict = save_data['player']
        if 'character_class' not in player_dict:
            player_dict['character_class'] = "Adventurer"
        self.player = Character(**player_dict)
        self.player_pos = tuple(save_data['player_pos'])
        self.dungeon_level = save_data['dungeon_level']
        self.in_shop = save_data.get('in_shop', False)

        # Load inventory
        self.inventory = []
        for item_dict, rarity_name in save_data.get('inventory', []):
            item_dict['rarity'] = Rarity[rarity_name]
            self.inventory.append(Item(**item_dict))

        # Load equipment
        if save_data.get('weapon'):
            weapon_dict, rarity_name = save_data['weapon']
            weapon_dict['rarity'] = Rarity[rarity_name]
            self.weapon = Item(**weapon_dict)
        else:
            self.weapon = None

        if save_data.get('armor'):
            armor_dict, rarity_name = save_data['armor']
            armor_dict['rarity'] = Rarity[rarity_name]
            self.armor = Item(**armor_dict)
        else:
            self.armor = None

        if save_data.get('amulet'):
            amulet_dict, rarity_name = save_data['amulet']
            amulet_dict['rarity'] = Rarity[rarity_name]
            self.amulet = Item(**amulet_dict)
        else:
            self.amulet = None

        self.message_log = save_data.get('message_log', [])

        if not self.in_shop and save_data.get('grid'):
            # Load grid
            self.grid = [[TileType[tile_name] for tile_name in row]
                        for row in save_data['grid']]

            self.stairs_pos = tuple(save_data['stairs_pos'])

            # Load enemies
            self.enemies = {}
            for pos_str, enemy_data in save_data.get('enemies', {}).items():
                pos = eval(pos_str)
                enemy_type = EnemyType[enemy_data['type']]
                enemy = Enemy(enemy_type, enemy_data['level'])
                enemy.hp = enemy_data['hp']
                self.enemies[pos] = enemy

            # Load items
            self.items = {}
            for pos_str, (item_dict, rarity_name) in save_data.get('items', {}).items():
                pos = eval(pos_str)
                item_dict['rarity'] = Rarity[rarity_name]
                self.items[pos] = Item(**item_dict)

        self.add_message("Game loaded successfully!")

    # -------------------------
    # Main loop
    # -------------------------
    def run(self):
        while not self.game_over:
            self.render()

            if self.in_shop:
                continue

            cmd = input("> ").strip().lower()

            if cmd == 'save':
                self.save_game()
                continue

            # Parse command for number prefix (e.g., "5w" means move 5 spaces up)
            steps = 1
            direction = cmd

            if len(cmd) > 1 and cmd[0].isdigit():
                num_str = ''
                for i, char in enumerate(cmd):
                    if char.isdigit():
                        num_str += char
                    else:
                        direction = cmd[i:]
                        break
                steps = int(num_str) if num_str else 1

            if direction == 'w':
                for _ in range(steps):
                    if self.game_over:
                        break
                    self.move_player(0, -1)
            elif direction == 's':
                for _ in range(steps):
                    if self.game_over:
                        break
                    self.move_player(0, 1)
            elif direction == 'a':
                for _ in range(steps):
                    if self.game_over:
                        break
                    self.move_player(-1, 0)
            elif direction == 'd':
                for _ in range(steps):
                    if self.game_over:
                        break
                    self.move_player(1, 0)
            elif direction == 'i':
                self.show_inventory()
            elif direction == 'q':
                print("Thanks for playing!")
                break

        if self.game_over:
            self.render()
            print("\nFinal Score:")
            print(f"  Level: {self.player.level}")
            print(f"  Dungeon Depth: {self.dungeon_level}")
            print(f"  Gold Earned: {self.player.gold}")
