# Intallez llama_cpp (https://github.com/ggerganov/llama.cpp)
from llama_cpp import Llama


# Téléchargez le modèle Zephyr-7B (https://huggingface.co/TheBloke/zephyr-7B-alpha-GGUF)
# La version zephyr-7b-alpha.Q5_K_M.gguf est recommandée pour s'exécuter avec 8 Go de RAM
# Le téléchargement pèse 5 Go environ, voici le lien direct :
#       https://huggingface.co/TheBloke/zephyr-7B-alpha-GGUF/resolve/main/zephyr-7b-alpha.Q5_K_M.gguf?download=true
# Créez un sous-répertoire "models/Zephyr-7B" dans le répertoire où se trouve ce fichier,
# et déposez-y le fichier téléchargé.
MODEL_PATH = "./models/Zephyr-7B/zephyr-7b-alpha.Q5_K_M.gguf"
MODEL_START_TOKEN = "<|im_start|>system\n"
MODEL_STOP_TOKEN = "<|im_end|>\n"


# Chargez le modèle
llm = Llama(model_path=MODEL_PATH, verbose=False)


# Construisez votre question et appelez le LLM
# La "temperature" permet de doser l'aléa :
#  - proche de 0 la réponse du modèle sera plus déterministe
#  - proche de 1 la réponse du modèle sera plus aléatoire
input_text = MODEL_START_TOKEN + "What are you ? Answer in less than 3 phrases." + MODEL_STOP_TOKEN
output = llm(input_text, max_tokens=None, temperature=0.1)


# Affichez le résultat
output_text = output["choices"][0]["text"]
print(output_text)
