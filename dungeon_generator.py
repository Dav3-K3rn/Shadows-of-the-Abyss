import random
from typing import List, Tuple
from enums import TileType

class Room:
    def __init__(self, x: int, y: int, width: int, height: int):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.center = (x + width // 2, y + height // 2)

    def intersects(self, other: 'Room') -> bool:
        return (self.x < other.x + other.width and
                self.x + self.width > other.x and
                self.y < other.y + other.height and
                self.y + self.height > other.y)

class DungeonGenerator:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.grid = [[TileType.WALL for _ in range(width)] for _ in range(height)]
        self.rooms: List[Room] = []

    def generate(self, num_rooms: int) -> Tuple[List[List[TileType]], List[Room]]:
        attempts = 0
        max_attempts = 100

        while len(self.rooms) < num_rooms and attempts < max_attempts:
            w = random.randint(5, 9)
            h = random.randint(4, 7)
            x = random.randint(1, self.width - w - 1)
            y = random.randint(1, self.height - h - 1)

            new_room = Room(x, y, w, h)

            if not any(new_room.intersects(room) for room in self.rooms):
                self._carve_room(new_room)

                if self.rooms:
                    prev_center = self.rooms[-1].center
                    new_center = new_room.center

                    # Check if tunnel would be too long
                    h_dist = abs(new_center[0] - prev_center[0])
                    v_dist = abs(new_center[1] - prev_center[1])

                    if h_dist > 20 or v_dist > 20:
                        attempts += 1
                        continue

                    if random.random() < 0.5:
                        self._carve_h_tunnel(prev_center[0], new_center[0], prev_center[1])
                        self._carve_v_tunnel(prev_center[1], new_center[1], new_center[0])
                    else:
                        self._carve_v_tunnel(prev_center[1], new_center[1], prev_center[0])
                        self._carve_h_tunnel(prev_center[0], new_center[0], new_center[1])

                self.rooms.append(new_room)

            attempts += 1

        # ensure at least one room exists
        if not self.rooms:
            fallback = Room(2, 2, 6, 5)
            self._carve_room(fallback)
            self.rooms.append(fallback)

        return self.grid, self.rooms

    def _carve_room(self, room: Room):
        for y in range(room.y, room.y + room.height):
            for x in range(room.x, room.x + room.width):
                if 0 <= x < self.width and 0 <= y < self.height:
                    self.grid[y][x] = TileType.FLOOR

    def _carve_h_tunnel(self, x1: int, x2: int, y: int):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            if 0 <= x < self.width and 0 <= y < self.height:
                self.grid[y][x] = TileType.FLOOR

    def _carve_v_tunnel(self, y1: int, y2: int, x: int):
        for y in range(min(y1, y2), max(y1, y2) + 1):
            if 0 <= x < self.width and 0 <= y < self.height:
                self.grid[y][x] = TileType.FLOOR
