import os
import json
import random
from atproto import Client
from PIL import Image, ImageDraw, ImageFont

# 1. Charger les données depuis le fichier JSON
with open('donnees.json', 'r', encoding='utf-8') as f:
    donnees = json.load(f)

# 2. Probabilités de tirage
PROBA_NEO = 0.3
PROBA_NOM = 0.3
PROBA_SUJET_NEO = 0.25
PROBA_ADJ = 0.75


def tirer_obsessions(donnees):
    """Tire obs1, obs2, obs3 selon les règles néologisme / nom."""
    obs1_est_neo = random.random() < PROBA_NEO
    obs3_est_nom = random.random() < PROBA_NOM

    if obs1_est_neo:
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
    """Construit la 2e ligne de la phrase, selon sujet normal ou néo."""
    sujet_est_neo = random.random() < PROBA_SUJET_NEO

    if sujet_est_neo:
        sujet = random.choice(donnees["sujets-neo"])
        verbe = random.choice(donnees["verbes"])
        comp = random.choice(donnees["complements"])
        adj = random.choice(donnees["adjectifs"])

        if random.random() < 0.5:
            return f"{sujet} {verbe} {comp}"
        else:
            return f"{sujet} {adj}"

    else:
        sujet = random.choice(donnees["sujets"])
        verbe = random.choice(donnees["verbes"])
        comp = random.choice(donnees["complements"])
        adj = random.choice(donnees["adjectifs"])

        if random.random() < PROBA_ADJ:
            return f"{sujet} {adj} {verbe} {comp}"
        else:
            return f"{sujet} {verbe} {comp}"


def decouper_selon_largeur(draw, texte, police, largeur_max):
    """Découpe un texte en lignes qui tiennent dans largeur_max pixels."""
    mots = texte.split(" ")
    lignes = []
    ligne_actuelle = ""
    for mot in mots:
        essai = f"{ligne_actuelle} {mot}".strip()
        if draw.textlength(essai, font=police) <= largeur_max:
            ligne_actuelle = essai
        else:
            if ligne_actuelle:
                lignes.append(ligne_actuelle)
            ligne_actuelle = mot
    if ligne_actuelle:
        lignes.append(ligne_actuelle)
    return lignes


def generer_image(premiere_ligne, deuxieme_ligne):
    """Génère l'image façon 'couverture d'hebdo' avec le texte incrusté.
    Cette fonction ne publie rien : elle sauvegarde juste un fichier .jpg
    en local, que le workflow GitHub Actions rendra téléchargeable."""
    image = Image.open("une-vierge.png").convert("RGBA")
    largeur, hauteur = image.size

    marge_gauche = 70
    marge_droite = 70
    marge_haut = 130

    x_gauche = marge_gauche
    largeur_utile = largeur - marge_gauche - marge_droite
    largeur_utile_premiere = largeur_utile * 0.6  # 70% de la largeur normale, pour forcer le retour à la ligne
    y = marge_haut

    calque_texte = Image.new("RGBA", image.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(calque_texte)

    police_premiere = ImageFont.truetype("Oswald-Regular.ttf", 20)
    police_deuxieme = ImageFont.truetype("Anton-Regular.ttf", 38)

    couleur_blanc = (255, 255, 255, 255)
    couleur_jaune = (255, 210, 0, 255)
    couleur_ombre = (0, 0, 0, 160)
    decalage_ombre = (2, 2)

    def dessiner_avec_ombre(x, y, texte, police, couleur):
        draw.text((x + decalage_ombre[0], y + decalage_ombre[1]), texte, font=police, fill=couleur_ombre)
        draw.text((x, y), texte, font=police, fill=couleur)

    lignes_premiere = decouper_selon_largeur(draw, premiere_ligne, police_premiere, largeur_utile_premiere)
    for ligne in lignes_premiere:
        dessiner_avec_ombre(x_gauche, y, ligne, police_premiere, couleur_blanc)
        y += 20 + 8

    y += 24

    lignes_deuxieme = decouper_selon_largeur(draw, deuxieme_ligne, police_deuxieme, largeur_utile)
    for ligne in lignes_deuxieme:
        largeur_ligne = draw.textlength(ligne, font=police_deuxieme)
        x_centre = x_gauche + (largeur_utile - largeur_ligne) / 2
        dessiner_avec_ombre(x_centre, y, ligne, police_deuxieme, couleur_jaune)
        y += 38 + 14

    resultat = Image.alpha_composite(image, calque_texte).convert("RGB")
    resultat.save("post_genere.jpg", quality=95)
    return "post_genere.jpg"


# 3. Construction du texte
obs1, obs2, obs3 = tirer_obsessions(donnees)
premiere_ligne = f"{obs1}, {obs2}, {obs3}"
deuxieme_ligne = construire_deuxieme_ligne(donnees)
texte_du_post = f"{premiere_ligne}\n{deuxieme_ligne}"

print("Message généré :")
print(texte_du_post)

# 4. Connexion et publication du TEXTE sur Bluesky (comportement inchangé)
HANDLE = os.environ.get("BSKY_HANDLE")
PASSWORD = os.environ.get("BSKY_PASSWORD")

client = Client()
client.login(HANDLE, PASSWORD)
client.send_post(text=texte_du_post)

print("Message texte publié avec succès !")

# 5. Génération de l'image EN PLUS, à titre de test (pas publiée pour l'instant)
generer_image(premiere_ligne, deuxieme_ligne)
print("Image de test générée : post_genere.jpg (à consulter dans les artifacts du run)")
