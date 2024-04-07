from ia_player import IA_Player
import pygame

# Debug mode
DEBUG = True

class Player (IA_Player):
    def __init__(self, name = None, role = None, player_type = "IA", names_to_avoid = []):
        super().__init__(name, role, names_to_avoid=names_to_avoid)
        self.PLAYER_COLOR = (200, 200, 200)
        self.PLAYER_RADIUS = 30
        self.x = 0
        self.y = 0
        self.font = pygame.font.SysFont(None, 24)
        self.last_vote = None
        self.last_vote_reason = None
        self.player_type = player_type
    
    def set_position(self, x, y):
        self.x = x
        self.y = y

    def get_position(self):
        return (self.x, self.y)

    def get_color(self):
        if not self.is_alive():
            # Player is dead so color is red
            return (200, 0, 0)
        elif self.thinking:
            # Player is thinking so color is green
            return (0, 200, 0)
        # Player is alive and waiting so color is grey
        return (200, 200, 200)

    def draw(self, screen):
        player_color = self.get_color()
        pygame.draw.circle(screen, player_color, (self.x, self.y), self.PLAYER_RADIUS)
        # Draw the name
        text = self.font.render(self.name, True, (0, 0, 0))
        screen.blit(text, (self.x - text.get_width() // 2, self.y - text.get_height() // 2))

    def collidepoint(self, x, y):
        return (self.x - self.PLAYER_RADIUS) <= x <= (self.x + self.PLAYER_RADIUS) and (self.y - self.PLAYER_RADIUS) <= y <= (self.y + self.PLAYER_RADIUS)

    def play_day(self, players_name, alive_werewolves_names, game_history = "", turn_history = ""):
        if self.player_type == "IA":
            who, why = super().play_day(players_name, alive_werewolves_names, game_history, turn_history)
            self.last_vote = who
            self.last_vote_reason = why
            return (who, why)
        else:
            pass

    def get_info(self):
        context = self.name + '\n'
        context += "Status : " + self.state + '\n'
        if DEBUG:
            context += "Role : " + self.role + '\n'
            context += "Think : " + self.think + '\n'
        if self.last_vote is not None:
            context += "Last vote was to kill " + self.last_vote + "\n"
            if self.last_vote_reason is not None:
                context += "The reason was : " + self.last_vote_reason + "\n"
        return context