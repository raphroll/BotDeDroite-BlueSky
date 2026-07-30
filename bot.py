import os
import json
import random
from atproto import Client

# 1. Charger les données depuis le fichier JSON
with open('donnees.json', 'r', encoding='utf-8') as f:
    donnees = json.load(f)

# 2. Probabilités de tirage (regroupées en haut, faciles à ajuster)
PROBA_OBS_COMPO = 0.3         # 1ère obsession composée originale
PROBA_OBS_NOM = 0.3         # 3e obsession = nom de personne
PROBA_SUJET_NEO = 0.25  # le sujet vient de "sujets-neo" plutôt que "sujets"
PROBA_ADJ = 0.8        # (uniquement si sujet normal) l'adjectif est présent


def tirer_obsessions(donnees):
    """Tire obs1, obs2, obs3 selon les règles néologisme / nom."""
    obs1_est_compo = random.random() < PROBA_OBS_COMPO
    obs3_est_nom = random.random() < PROBA_OBS_NOM

    if obs1_est_compo:
        obs1 = random.choice(donnees["obsessions-neo"])
        if obs3_est_nom:
            obs2 = random.choice(donnees["obsessions"])
            obs3 = random.choice(donnees["obsessions-noms"])
        else:
            obs2, obs3 = random.sample(donnees["obsessions"], 2)
    else:
        if obs3_est_nom:
            obs1, obs2 = random.sample(donnees["obsessions"], 2)
            obs3 = random.choice(donnees["obsessions-noms"])
        else:
            obs1, obs2, obs3 = random.sample(donnees["obsessions"], 3)

    return obs1, obs2, obs3


def construire_deuxieme_ligne(donnees):
    """
    Construit la 2e ligne de la phrase ("{sujet} ...").
    Deux grandes familles de résultat :
    - sujet "néo" (mot inventé) -> phrase courte, 2 variantes possibles
    - sujet "normal" -> phrase classique, avec adjectif optionnel
    """
    sujet_est_neo = random.random() < PROBA_SUJET_NEO

    if sujet_est_neo:
        sujet = random.choice(donnees["sujets-neo"])
        verbe = random.choice(donnees["verbes"])
        comp = random.choice(donnees["complements"])
        adj = random.choice(donnees["adjectifs"])

        # Deux scénarios possibles à 50/50 pour varier la structure courte
        if random.random() < 0.5:
            return f"{sujet} {verbe} {comp}"
        else:
            return f"{sujet} {adj}"

    else:
        sujet = random.choice(donnees["sujets"])
        verbe = random.choice(donnees["verbes"])
        comp = random.choice(donnees["complements"])
        adj = random.choice(donnees["adjectifs"])

        # L'adjectif est optionnel, uniquement dans ce cas "normal"
        if random.random() < PROBA_ADJ:
            return f"{sujet} {adj} {verbe} {comp}"
        else:
            return f"{sujet} {verbe} {comp}"


# 3. Construction du texte final
obs1, obs2, obs3 = tirer_obsessions(donnees)
premiere_ligne = f"{obs1}, {obs2}, {obs3}"
deuxieme_ligne = construire_deuxieme_ligne(donnees)

texte_du_post = f"{premiere_ligne}\n{deuxieme_ligne}"

print("Message généré :")
print(texte_du_post)

# 4. Connexion et publication sur Bluesky
HANDLE = os.environ.get("BSKY_HANDLE")
PASSWORD = os.environ.get("BSKY_PASSWORD")

client = Client()
client.login(HANDLE, PASSWORD)
client.send_post(text=texte_du_post)

print("Message publié avec succès !")
