import pygame
import math
import ptext

BLACK = (0, 0, 0)


class TextBox:
    def __init__(self, text, x : int, y : int, width : int, height : int, bg_color=BLACK, text_color="white"):
        self.text = text.split("\n")
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.bg_color = bg_color
        self.text_color = text_color
        self.index = 0

    def set_text(self, text : str):
        # Store as a list of strings
        self.text = text.split("\n")
        n_lines = len(self.text)
        self.index = min(self.index, n_lines - 3)

    def draw(self, screen):
        pygame.draw.rect(screen, self.bg_color, (self.x, self.y, self.width, self.height))
        displayed_text = "\n".join(self.text[self.index:])
        ptext.draw(displayed_text, (self.x + 5, self.y + 5), width=self.width - 10, color=self.text_color)

    def collidepoint(self, x : int, y : int):
        return self.x <= x <= self.x + self.width and self.y <= y <= self.y + self.height

    def manage_event(self, event):
        if event.type == pygame.MOUSEWHEEL:
            if event.y > 0:
                self.index = max((self.index - 1), 0)
            elif event.y < 0:
                n_lines = len(self.text)
                self.index = min((self.index + 1), n_lines - 3)


class Table():
    def __init__(self, players_zone_width : int, players_zone_height : int):
        self.TABLE_COLOR = (100, 100, 100)
        self.TABLE_RADIUS = 80
        self.DISTANCE_TO_TABLE = 70
        self.players_zone_width = players_zone_width
        self.players_zone_height = players_zone_height
        self.x = self.players_zone_width // 2
        self.y = self.players_zone_height // 2
        self.game_context = ""
    
    def set_position(self, x, y):
        self.x = x
        self.y = y

    def get_players_position(self, num_players):
        # Calculate the position of each player
        result = []
        for i in range(num_players):
            angle = 2 * math.pi * i / num_players
            table_distance = self.TABLE_RADIUS + self.DISTANCE_TO_TABLE
            x = self.x + int(table_distance * math.cos(angle))
            y = self.y + int(table_distance * math.sin(angle))
            result.append((x, y))
        return result

    def draw(self, screen):
        pygame.draw.circle(screen, self.TABLE_COLOR, (self.x, self.y), self.TABLE_RADIUS)

    def collidepoint(self, x, y):
        return self.x - self.TABLE_RADIUS <= x <= self.x + self.TABLE_RADIUS and self.y - self.TABLE_RADIUS <= y <= self.y + self.TABLE_RADIUS

    def add_game_context(self, context : str):
        self.game_context += context

    def get_game_context(self):
        return self.game_context