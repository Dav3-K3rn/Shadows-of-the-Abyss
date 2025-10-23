#!/usr/bin/env python3
"""
Shadows of the Abyss - A Terminal Dungeon Crawler RPG
A sophisticated roguelike with procedural generation, combat, and progression

This version adds Character Class selection (Warrior, Mage, Rogue, Archer),
and equips each class with its proper starting weapon and stats while keeping
The original game structure/logic intact.
"""

import os
import sys
from game import Game

if __name__ == "__main__":
    print("=== SHADOWS OF THE ABYSS ===")
    print("A Terminal Dungeon Crawler\n")

    # Check if save file is passed as argument
    save_file = None
    if len(sys.argv) > 1:
        save_file = sys.argv[1]
        if os.path.exists(save_file):
            print(f"Loading save file: {save_file}")
            game = Game(skip_class_select=True)
            game.load_game(save_file)
            game.run()
        else:
            print(f"Save file '{save_file}' not found. Starting new game.")
            print("Your quest: Descend into the abyss and survive!")
            print("\nPress Enter to begin...")
            input()
            game = Game()  # will prompt for class selection
            game.run()
    else:
        # Check for default save
        if os.path.exists("game_save.sav"):
            choice = input("Found existing save. Load it? (y/n): ").strip().lower()
            if choice == 'y':
                game = Game(skip_class_select=True)
                game.load_game()
                game.run()
            else:
                print("Your quest: Descend into the abyss and survive!")
                print("\nPress Enter to begin...")
                input()
                game = Game()
                game.run()
        else:
            print("Your quest: Descend into the abyss and survive!")
            print("\nPress Enter to begin...")
            input()
            game = Game()
            game.run()
