import os
import json
import random
from atproto import Client

# 1. Charger les données depuis le fichier JSON
with open('donnees.json', 'r', encoding='utf-8') as f:
    donnees = json.load(f)

# 2. Tirer au sort les variables
    # Probabilité que la 3e obsession soit un nom (issu de obsessions3)
    PROBA_NOM = 0.3  # ajuste selon ta préférence (0.3 = 30% des posts)

    if random.random() < PROBA_NOM:
    # Cas "nom" : obs1 et obs2 viennent du pool général, obs3 est un nom
    obs1, obs2 = random.sample(donnees["obsessions12"], 2)
    obs3 = random.choice(donnees["obsessions3"])
    else:
    # Cas "classique" : les 3 viennent du pool général, sans doublon
    obs1, obs2, obs3 = random.sample(donnees["obsessions12"], 3)

nom = random.choice(donnees["noms"])
adj = random.choice(donnees["adjectifs"])
verbe = random.choice(donnees["verbes"])
comp = random.choice(donnees["complements"])

# 3. Construire le texte avec le saut de ligne
texte_du_post = f"{obs1}, {obs2}, {obs3}\n{nom} {adj} {verbe} {comp}"

print("Message généré :")
print(texte_du_post)

# 4. Connexion et publication sur Bluesky
HANDLE = os.environ.get("BSKY_HANDLE")
PASSWORD = os.environ.get("BSKY_PASSWORD")

client = Client()
client.login(HANDLE, PASSWORD)
client.send_post(text=texte_du_post)

print("Message publié avec succès !")
