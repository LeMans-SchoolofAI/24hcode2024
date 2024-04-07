import pygame
import pygame_menu
import random
import threading
from typing import Optional, Union, List
import pygame_textinput
from player import Player
from ihm import Table, TextBox


# Initialize Pygame framework
pygame.init()

# Colors
BACKGROUND_COLOR = (255, 255, 255)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Screen config
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 768

# Debug mode
DEBUG = True


class Game:
    def __init__(self):
        # Set up the display
        self.screen_width = SCREEN_WIDTH
        self.screen_height = SCREEN_HEIGHT
        self.players_zone_width = min(SCREEN_WIDTH // 3 * 2, 700)
        self.players_zone_height = SCREEN_HEIGHT
        self.text_zone_position = (self.players_zone_width, 0)
        self.text_zone_width = SCREEN_WIDTH - self.players_zone_width
        self.text_zone_height = SCREEN_HEIGHT
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Loup-garou")

        # Define the table properties
        self.table = Table(self.players_zone_width, self.players_zone_height)

        # Define the text properties
        self.text_box = TextBox("", self.text_zone_position[0], self.text_zone_position[1], self.text_zone_width, self.text_zone_height)

        # Create the thread lock variable
        self.playing = False

        # Define the game properties
        self.day = 1
        # There are 3 phases : initial, night and day
        self.phase = "initial"
        self.players = []
        self.winners = None

        # Default values for menu
        self.number_of_ia_players = 6
        self.human_player = False
        self.human_player_name = "Human Player"
    
    def add_player(self, role, names_to_avoid = []):
        # Create a new player and annd it to the list
        player = Player(role = role, names_to_avoid = names_to_avoid)
        self.players.append(player)
        
        # Shuffle the player list
        random.shuffle(self.players)

        # Set the player position around the table
        players_pos = self.table.get_players_position(len(self.players))
        for player, pos in zip(self.players, players_pos):
            player.set_position(pos[0], pos[1])

    def display_table(self):
        self.table.draw(self.screen)

    def display_players(self):
        # Draw the players
        for player in self.players:
            player.draw(self.screen)

    def display_info_box(self):
        self.text_box.draw(self.screen)

    def display_all(self):
        # Clear the screen
        self.screen.fill(BACKGROUND_COLOR)
        # Display the table
        self.display_table()
        # Display the players
        self.display_players()
        # Display the info box
        self.display_info_box()
        # Add a play button on the top left
        if self.playing:
            Button_color = (255, 0, 0)
        elif self.winners is not None:
            Button_color = (0, 0, 255)
        else:
            Button_color = (0, 255, 0)
        play_button = pygame.draw.rect(self.screen, Button_color, (10, 10, 50, 20))
        pygame.display.flip()
        return play_button

    def find_player_by_name(self, player_name: str) -> Optional[Player]:
        """
        Finds a player in the list of players by their name.
        
        Args:
            player_name (str): The name of the player to search for.
        
        Returns:
            Player: The found player object, or None if the player is not found.
        """
        for player in self.players:
            if player.name == player_name:
                return player
        return None

    def check_player_vote_to_kill(self, voter_name: str, votee_name: str, list_of_exlusions: List[str] = []) -> Union[str, None]:
        """
        Check if a player's vote to kill is valid.

        Args:
            voter_name (str): The name of the player casting the vote.
            votee_name (str): The name of the player being voted to kill.
            list_of_exlusions (List[str], optional): A list of player names to exclude from the vote.

        Returns:
            Union[str, None]: The valid player name being voted to kill, or None if the vote is invalid.
        """
        if voter_name == votee_name:
            return None
        
        # Find the player being voted to kill
        votee = self.find_player_by_name(votee_name)
        if votee is None:
            return None
        elif votee.state == "dead":
            return None
        # Check that the vote is not on the exclusion list
        elif votee_name in list_of_exlusions:
            return None
        else:
            return votee_name

    def find_winner(self, votes) -> Optional[Player]:
        if len(votes) > 0:
            max_vote: int = max(votes.values())
            max_voted_players: List[str] = [name for name in votes if votes[name] == max_vote]
            if len(max_voted_players) == 1:
                player_name_to_kill: str = max_voted_players[0]
                player_to_kill: Optional[Player] = self.find_player_by_name(player_name_to_kill)
            else:
                player_to_kill = None
            return player_to_kill
        else:
            return None
            
    def get_players_names(self) -> List[str]:
        return [player.name for player in self.players]

    def get_alive_werewolves(self) -> List[Player]:
        return [player for player in self.players if player.is_alive() and player.role == "werewolf"]

    def get_alive_villagers(self) -> List[Player]:
        return [player for player in self.players if player.is_alive() and player.role != "werewolf"]

    def get_alive_players(self) -> List[Player]:
        return [player for player in self.players if player.is_alive()]

    def play_day(self) -> None:
        """
        Play a day phase.
        """
        if DEBUG:
            print("########## Start of the day phase ##########")
        turn_log: str = ""

        alive_werewolves = self.get_alive_werewolves()
        alive_players = self.get_alive_players()

        # First round : each player explain who he want to kill and why
        turn_log = ""
        for player in alive_players:
            other_werewolves_names = [werewolf.name for werewolf in alive_werewolves if werewolf != player]
            other_players_names = [other_player.name for other_player in alive_players if other_player != player]
            choice = player.play_day_discussion(other_players_names, other_werewolves_names, self.table.get_game_context(), turn_log)
            turn_log += player.name + " says : " + choice + ".\n"

        # Second round : now that each player has explained who he wants to kill, each player votes
        votes: Dict[str, int] = {player.name: 0 for player in alive_players}
        vote_log = ""
        for player in alive_players:
            # Play the player
            other_werewolves_names = [werewolf.name for werewolf in alive_werewolves if werewolf != player]
            other_players_names = [other_player.name for other_player in alive_players if other_player != player]
            votee_name = player.play_day_vote(other_players_names, other_werewolves_names, self.table.get_game_context(), turn_log)
            
            # Check if the vote is valid
            votee_name = self.check_player_vote_to_kill(player.name, str(votee_name))
            
            if votee_name is not None:
                # Store the vote
                votes[votee_name] += 1
                vote_log += player.name + " voted to kill " + votee_name + ".\n"
            else:
                vote_log += player.name + " did not vote to kill someone.\n"

        # Kill the player with the most votes
        player_to_kill: Optional[Player] = self.find_winner(votes)
        if player_to_kill is not None:
            player_to_kill.set_dead()
            vote_log += "Due to the votes, " + player_to_kill.name + " was killed on this day.\n"
        else:
            # This is a tie so no one will be killed
            vote_log += "There was a tie so no one was killed on this day.\n"

        # Update the table master game history
        self.table.add_game_context("*** Here is what was done on day " + str(self.day) + " ***\n")
        self.table.add_game_context(vote_log)
        self.table.add_game_context("*** This is the end of what was done on day " + str(self.day) + " ***\n\n")

        # Change the phase to "night"
        self.phase = "night"

        # Check if the game is over
        self.check_if_game_over()

        self.playing = False
        if DEBUG:
            print("########## Done playing on day " + str(self.day) + " ##########\n")

        return
            
    def play_night(self) -> None:
        """
        Play a night phase.
        """
        if DEBUG:
            print("########## Start of the night phase ##########")
        turn_log: str = ""

        alive_werewolves = self.get_alive_werewolves()
        alive_villagers = self.get_alive_villagers()
        villagers_names = [villager.name for villager in alive_villagers]

        # First round : each werewolf explain who he want to kill and why
        turn_log = ""
        for player in alive_werewolves:
            # Get the werewolf's choice
            other_werewolves_names = [werewolf.name for werewolf in alive_werewolves if werewolf != player]
            choice = player.play_night_discussion(villagers_names, other_werewolves_names, self.table.get_game_context(), turn_log)
            turn_log += player.name + " says : " + choice + ".\n"

        # Second round : now that each werewolf has explained who he wants to kill, each player votes
        votes: Dict[str, int] = {player.name: 0 for player in self.players if player.is_alive() and player.role != "werewolf"}
        for player in alive_werewolves:
            # Play the player
            other_werewolves_names = [werewolf.name for werewolf in alive_werewolves if werewolf != player]
            votee_name = player.play_night_vote(villagers_names, other_werewolves_names, self.table.get_game_context(), turn_log)
            
            # Check if the vote is valid
            votee_name = self.check_player_vote_to_kill(player.name, str(votee_name))
            
            if votee_name is not None:
                # Store the vote
                votes[votee_name] += 1

        # Kill the player with the most votes
        player_to_kill: Optional[Player] = self.find_winner(votes)
        if player_to_kill is not None:
            player_to_kill.set_dead()
            vote_log = player_to_kill.name + " was found dead.\n"
        else:
            vote_log = "Everyone survived the night.\n"
        
        # Update the table master game history
        self.table.add_game_context("*** Here is what happened on night " + str(self.day) + " ***\n")
        self.table.add_game_context(vote_log)
        self.table.add_game_context("*** This is the end of what was done on day " + str(self.day) + " ***\n\n")

        # Change the phase to "day" and increment the day number
        self.phase = "day"
        self.day += 1

        # Check if the game is over
        self.check_if_game_over()

        self.playing = False
        if DEBUG:
            print("########## Done playing on night " + str(self.day) + " ##########\n")

        return
    
    def play_initial(self) -> None:
        if DEBUG:
            print("########## Start of the initial phase ##########")
        turn_log: str = ""

        # If there is a thief then allow him to change his role with someone
        #TODO

        # If there is a cupidon then define the two lovers
        #TODO

        # Then the next turn is the night phase
        if DEBUG:
            print("########## Done playing on initial phase ##########\n")
        self.phase = "night"
        self.play_night()
        return    

    def check_if_game_over(self):
        # Check if there is a werewolf left ?
        if len([player for player in self.players if player.role == "werewolf" and player.state != "dead"]) == 0:
            self.winners = "villagers"
        # Check if there is a villager left ?
        if len([player for player in self.players if player.role == "villager" and player.state != "dead"]) == 0:
            self.winners = "werewolves"


    def check_collided_players(self, x, y) -> Player:
        for player in self.players:
            if player.collidepoint(x, y):
                return player
        return None

    def play_game(self):
        if DEBUG:
            print("Number of ia players : " + str(self.number_of_ia_players))
            print("Name of human player : " + str(self.human_player_name))
            print("Is there a human player : " + str(self.human_player))

        # Create a new screen
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Loup-garou")

        # Add players
        if self.number_of_ia_players > 11:
            number_of_werewolves = 3
        else:
            number_of_werewolves = 2
        for i in range(number_of_werewolves):
            self.add_player(role = "werewolf", names_to_avoid = self.get_players_names())
        for i in range(self.number_of_ia_players - 2):
            self.add_player(role = "villager", names_to_avoid = self.get_players_names())
                        
        # Set up the game loop
        running = True
        clock = pygame.time.Clock()
        while running:
            # Draw the screen
            play_button = self.display_all()
            
            # Limit frame rate
            clock.tick(60)  # 60 frames per second

            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                elif event.type == pygame.MOUSEWHEEL:
                    # Get the mouse position
                    x, y = pygame.mouse.get_pos()
                    if self.text_box.collidepoint(x, y):
                        self.text_box.manage_event(event)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    # Check if the user clicked on the play button
                    if play_button.collidepoint(event.pos) and not self.playing:
                        if self.winners is not None:
                            self.text_box.set_text(self.winners + " won the game !\nGame is over.")
                        else:
                            # Start the current phase
                            if self.phase == "day":
                                target = self.play_day
                            elif self.phase == "night":
                                target = self.play_night
                            else:
                                target = self.play_initial
                            self.playing = True
                            play = threading.Thread(target=target)
                            play.start()
                    # Check if the user clicked on a player
                    clicked_player = self.check_collided_players(event.pos[0], event.pos[1])
                    if clicked_player is not None:
                        self.text_box.set_text(clicked_player.get_info())
                    # Check if the user clicked on the table
                    elif self.table.collidepoint(event.pos[0], event.pos[1]):
                        self.text_box.set_text(self.table.get_game_context())
        
        # Empty player list
        self.players = []

    def set_human_player(self, human_player, **kwargs):
        self.human_player = human_player

    def set_human_player_name(self, human_player_name, **kwargs):
        self.human_player_name = human_player_name

    def set_ia_players(self, number_of_ia_players, **kwargs):
        self.number_of_ia_players = number_of_ia_players

    def start_menu(self):
        # Menu
        menu = pygame_menu.Menu('Welcome', 600, 600, theme=pygame_menu.themes.THEME_BLUE)
        menu.add.range_slider("Number of IA players : ", 6, (6, 12), 1, onchange=self.set_ia_players)
        menu.add.toggle_switch('Human player : ', False, onchange=self.set_human_player)
        menu.add.text_input('Human player name : ', default=self.human_player_name, onchange=self.set_human_player_name)
        menu.add.button('Play', self.play_game)
        menu.add.button('Quit', pygame_menu.events.EXIT)

        # Start the game
        menu.mainloop(self.screen)

game = Game()
game.start_menu()
