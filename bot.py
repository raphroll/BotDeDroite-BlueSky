import os
import json
import random
from atproto import Client

# 1. Charger les données depuis le fichier JSON
with open('donnees.json', 'r', encoding='utf-8') as f:
    donnees = json.load(f)

# 2. Tirer au sort les variables
PROBA_NEO = 0.3  # probabilité que la 1ère obsession soit un néologisme
PROBA_NOM = 0.3   # probabilité que la 3e obsession soit un nom

pool12 = donnees["obsessions12"]

obs1_est_neo = random.random() < PROBA_NEO
obs3_est_nom = random.random() < PROBA_NOM

if obs1_est_neo:
    obs1 = random.choice(donnees["neologismes"])
    if obs3_est_nom:
        obs2 = random.choice(pool12)
        obs3 = random.choice(donnees["obsessions3"])
    else:
        obs2, obs3 = random.sample(pool12, 2)
else:
    if obs3_est_nom:
        obs1, obs2 = random.sample(pool12, 2)
        obs3 = random.choice(donnees["obsessions3"])
    else:
        obs1, obs2, obs3 = random.sample(pool12, 3)

sujet = random.choice(donnees["sujets"])
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
