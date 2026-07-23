import os
import random
from atproto import Client

# 1. Liste de phrases que le bot peut choisir au hasard
PHRASES = [
    "Bonjour ! Ceci est un message automatique.",
    "Un petit coucou depuis mon script Python !",
    "La citation du jour : Il fait toujours beau quelque part.",
    "Ceci est un test de publication automatique sur Bluesky."
]

# 2. Récupération des identifiants secrets
HANDLE = os.environ.get("BSKY_HANDLE")
PASSWORD = os.environ.get("BSKY_PASSWORD")

# 3. Connexion à Bluesky et envoi du message
client = Client()
client.login(HANDLE, PASSWORD)

phrase_choisie = random.choice(PHRASES)
client.send_post(text=phrase_choisie)

print("Message envoyé avec succès !")
