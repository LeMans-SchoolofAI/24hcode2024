from llama_cpp import Llama
import json
import os
import random

# Debug mode
DEBUG = True

# Model selection
MODEL_FOLDER = os.path.join(os.path.dirname(__file__), "../models/")
TEMPERATURE = 0.3
model = "Mistral-7B-Instruct"
if model == "Zephyr-7B":
    MODEL_PATH = MODEL_FOLDER + "Zephyr-7B/zephyr-7b-alpha.Q5_K_M.gguf"
    MODEL_START_TOKEN = "<|im_start|>system\n"
    MODEL_STOP_TOKEN = "<|im_end|>"
elif model == "OpenChat-7B":
    MODEL_PATH = MODEL_FOLDER + "OpenChat-7B/openchat_3.5.Q5_K_M.gguf"
    MODEL_START_TOKEN = "GPT4 Correct user: "
    MODEL_STOP_TOKEN = "<|end_of_turn|>GPT4 Correct Assistant:"
elif model == "CapybaraHermes-7B":
    MODEL_PATH = MODEL_FOLDER + "CapybaraHermes-7B/capybarahermes-2.5-mistral-7b.Q5_K_M.gguf"
    MODEL_START_TOKEN = "<|im_start|>system\n<|im_end|>\n<|im_start|>user\n"
    MODEL_STOP_TOKEN = "<|im_end|>\n<|im_start|>assistant\n"
elif model == "Mistral-7B-Instruct":
    MODEL_PATH = MODEL_FOLDER + "Mistral-7B-Instruct/mistral-7b-instruct-v0.1.Q5_K_M.gguf"
    MODEL_START_TOKEN = "<s>[INST] "
    MODEL_STOP_TOKEN = " [/INST]"
else:
    raise ValueError("Model not found")
LLM = Llama(model_path=MODEL_PATH, n_gpu_layers=-1, n_threads=7, seed=-1, n_ctx=4096, verbose=False)

class IA_Player:
    start_context = "You are playing a werewolf game."
    day_discussion_context = \
        """It's your turn to play, you want to convince everyone to kill who you think is dangerous.
           Think step by step. Answer with a JSON following :
         ( why : 'make a short explanation of who you propose to kill and why',
         ) Answer with the JSON and nothing else before of after."""
    vote_context = \
        """It's your turn to vote, who do you vote to kill ? Think step by step. Answer with a JSON following :
         ( who : 'name the player you vote to kill or None if you don't vote',
         ) Answer with the JSON and nothing else before of after."""
    night_discussion_context = \
        """It's your turn to play, you want to convince your fellows werewolves to kill who you think is dangerous to the werewolves.
           Think step by step. Answer with a JSON following :
         ( why : 'make a short explanation of who you propose to kill and why',
         ) Answer with the JSON and nothing else before of after."""

    def __init__(self, name = None, role = None, names_to_avoid = []):
        if name is None:
            # Pick a random name
            llm_output = self.process(MODEL_START_TOKEN + "Provide a random name and only that with no comment." +
                                      "Do not pick a name from this list : " + ", ".join(names_to_avoid) + "\n" +
                                      MODEL_STOP_TOKEN,
                                      max_tokens=10, temperature=TEMPERATURE)
            llm_output = llm_output.strip()
            self.name = llm_output
        else:
            self.name = name
        if role is None:
            # Pick a random role
            role = random.choice(["villager", "werewolf"])
        elif role not in ["villager", "werewolf"]:
            raise ValueError("role must be 'villager' or 'werewolf'")
        else:
            self.role = role
        self.state = "alive"
        self.think = ""
        self.thinking = False

    def is_alive(self):
        return self.state == "alive"

    def process(self, input_text : str, max_tokens=None, temperature=TEMPERATURE) -> str:
        if DEBUG:
            self.thinking = True
        output = LLM(input_text, max_tokens=max_tokens, temperature=temperature)
        # Extract JSON from output
        llm_output = output["choices"][0]["text"]
        self.thinking = False
        return llm_output

    def play_day_discussion(self, other_players_names, alive_werewolves_names, game_history = "", turn_history = "") -> str:
        if game_history == "":
            game_history = "The game just started, this is the first round."
        list_players_str = "Here are the names of the others players still alive : " + ", ".join(other_players_names)
        if self.role == "villager":
            player_role = "You are a villager. You are trying to kill a werewolf."
        elif self.role == "werewolf":
            if alive_werewolves_names == []:
                player_role = "You are the only werewolf alive in the game. You must avoid to be killed."
            else:
                player_role = "You are a werewolf, the other werewolves are : " + ", ".join(alive_werewolves_names) + ". " + \
                              "They are your friends and you must choose a villager to kill to protect your pack."
        input_text = MODEL_START_TOKEN + self.start_context + "\n" + game_history + "\n" + list_players_str + "\n" + \
                     player_role + "\n" + turn_history + "\n" + self.day_discussion_context + MODEL_STOP_TOKEN

        llm_output = self.process(input_text)

        # If in DEBUG mode the print the input text for the LLM
        if DEBUG:
            print("\nDEBUG - " + self.name + " : \n" + input_text + "\n\n" + llm_output + "\n\n")
            
        # Check if the answer contain a valid JSON
        try:
            llm_output = json.loads(llm_output)
        except ValueError as e:
            print("ERROR - " + self.name + " : no valid JSON found in answer")
            print("ERROR -    Result was : " + str(llm_output))
            return ("")
        if "why" in llm_output:
            why = str(llm_output["why"])
        else:
            why = ""
        return (why)

    def play_day_vote(self, other_players_names, alive_werewolves_names, game_history = "", turn_history = "") -> str:
        if game_history == "":
            game_history = "The game just started, this is the first round."
        list_players_str = "Here are the names of the other players who are still alive : " + ", ".join(other_players_names)
        if self.role == "villager":
            player_role = "You are a villager. You must vote to try to kill the werewolves."
        elif self.role == "werewolf":
            if alive_werewolves_names == []:
                player_role = "You are the only werewolf alive in the game. You must avoid to be killed."
            else:
                player_role = "You are a werewolf, the other werewolves are : " + ", ".join(alive_werewolves_names) + ". " + \
                              "They are your friends and you must choose a villager to kill to protect your pack."
        input_text = MODEL_START_TOKEN + self.start_context + "\n" + game_history + "\n" + list_players_str + "\n" + \
                     player_role + "\n" + turn_history + "\n" + self.vote_context + MODEL_STOP_TOKEN

        llm_output = self.process(input_text)

        # If in DEBUG mode the print the input text for the LLM
        if DEBUG:
            print("\nDEBUG - " + self.name + " : \n" + input_text + "\n\n" + llm_output + "\n\n")
            
        # Check if the answer contain a valid JSON
        try:
            llm_output = json.loads(llm_output)
        except ValueError as e:
            print("ERROR - " + self.name + " : no valid JSON found in answer")
            print("ERROR -    Result was : " + str(llm_output))
            return (None, "")

        # Check if the anwser contain a player name for the vote
        if "who" in llm_output:
            return (llm_output["who"])
        else:
            return (None)

    def play_night_discussion(self, alive_villagers_names, alive_werewolves_names, game_history = "", turn_history = "") -> str:
        if self.role == "villager":
            raise ValueError("Villagers do not play at night")
            return("")
        if game_history == "":
            game_history = "The game just started, this is the first round."
        list_players_str = "Here are the names of the villagers still alive : " + ", ".join(alive_villagers_names)
        if alive_werewolves_names == []:
            player_role = "You are the only werewolf alive in the game. You must avoid to be killed."
        else:
            player_role = "The other werewolves are : " + ", ".join(alive_werewolves_names) + ". " + \
                          "They are your friends and you must choose a villager to kill together this night."
        input_text = MODEL_START_TOKEN + self.start_context + "\n" + game_history + "\n" + list_players_str + "\n" + \
                     player_role + "\n" + turn_history + "\n" + self.night_discussion_context + MODEL_STOP_TOKEN
        
        llm_output = self.process(input_text)
        # If in DEBUG mode then print the input text for the LLM
        if DEBUG:
            print("\nDEBUG - " + self.name + " : \n" + input_text + "\n\n" + llm_output + "\n\n")
        
        try:
            llm_output = json.loads(llm_output)
        except ValueError as e:
            print("ERROR - " + self.name + " : no valid JSON found in answer")
            print("ERROR -    Result was : " + str(llm_output))
            return ("")
        # Check if the anwser contain a player name to kill
        if "why" in llm_output:
            why = str(llm_output["why"])
        else:
            why = ""
        return (why)

    def play_night_vote(self, alive_villagers_names, alive_werewolves_names, game_history = "", turn_history = "") -> str:
        if self.role == "villager":
            raise ValueError("Villagers do not play at night")
            return(None)
        if game_history == "":
            game_history = "The game just started, this is the first round."
        list_players_str = "Here are the names of the villagers still alive : " + ", ".join(alive_villagers_names)

        if alive_werewolves_names == []:
            player_role = "You are the only werewolf alive in the game. You must avoid to be killed."
        else:
            player_role = "The other werewolves are : " + ", ".join(alive_werewolves_names) + ". " + \
                          "They are your friends and you must choose a villager to kill together this night."
        input_text = MODEL_START_TOKEN + self.start_context + "\n" + game_history + "\n" + list_players_str + "\n" + \
                        player_role + "\n" + turn_history + "\n" + self.vote_context + MODEL_STOP_TOKEN

        llm_output = self.process(input_text)

        # If in DEBUG mode then print the input text for the LLM
        if DEBUG:
            print("\nDEBUG - " + self.name + " : \n" + input_text + "\n\n" + llm_output + "\n\n")
        
        try:
            llm_output = json.loads(llm_output)
        except ValueError as e:
            print("ERROR - " + self.name + " : no valid JSON found in answer")
            print("ERROR -    Result was : " + str(llm_output))
            return (None)
        # Check if the anwser contain a player name to kill
        if "who" in llm_output:
            return (llm_output["who"])
        else:
            return (None)

    def set_dead(self):
        self.state = "dead"
