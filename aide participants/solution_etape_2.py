from llama_cpp import Llama
import json

# Définition du modèle et chargement
MODEL_PATH = "./models/Zephyr-7B/zephyr-7b-alpha.Q5_K_M.gguf"
MODEL_START_TOKEN = "<|im_start|>system\n"
MODEL_STOP_TOKEN = "<|im_end|>\n"
TEMPERATURE = 0.1
llm = Llama(model_path=MODEL_PATH, verbose=False)


def vote(llm, player_name, other_players):
    # Construire le texte d'appel pour le LLM
    # Expliquez ce que vous attendez du LLM
    # Notez que l'on demande au LLM de répondre avec un JSON respectant un certain format
    # Cela facilite la réutilisation du résultat du LLM
    input_text = MODEL_START_TOKEN
    input_text += "Your name is " + player_name + ". You live in a village and people die every night to the werewolves.\n"
    input_text += "You are a villager and you have to vote to kill who you suspect is a werewolf.\n"
    input_text += "Here is the list of players :\n"
    for p in other_players:
        input_text += p + "\n"
    input_text += "It's your turn to vote, who do you vote to kill ? Think step by step. Answer with a JSON following : \
         ( why : 'make a short explanation of your choice here', \
           who : 'name the player you vote to kill or None if you don't vote', \
         ) Answer with the JSON and nothing else before of after."
    input_text += MODEL_STOP_TOKEN
    
    # Appel du LLM
    #print("DEBUG : Calling LLM with input : " + input_text + "\n")
    output = llm(input_text, max_tokens=None, temperature=TEMPERATURE)
    #print("DEBUG : Ouput is : " + str(output) + "\n")

    # Extraire le JSON de la réponse
    llm_output = output["choices"][0]["text"]

    # Récupérer le JSON, en verifiant qu'il est bien au format attendu
    try:
        llm_output = json.loads(llm_output)
    except ValueError as e:
        print("ERROR : no valid JSON found in answer")
    # Si le JSON est valide alors récupérer les variables
    if "who" in llm_output:
        player_to_kill = str(llm_output["who"])
    else:
        player_to_kill = None
    if "why" in llm_output:
        why = str(llm_output["why"])
    else:
        why = None
    
    # Contrôler que le joueur à tuer est bien dans la liste des autres joueurs
    if player_to_kill not in other_players:
        print("ERROR : LLM output contains an invalid player name")
        player_to_kill = None

    return player_to_kill, why


# Appel de la méthode de vote
player_name = "Bernard"
player_to_kill, why = vote(llm, player_name, ["Valérie", "Sylvie", "Nicolas", "Alexandre"])

# Afficher le resultat
output_text = player_name + " voted to kill " + player_to_kill + " because " + why
print(output_text)
