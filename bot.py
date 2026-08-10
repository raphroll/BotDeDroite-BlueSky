import os
import json
import random
from atproto import Client
from PIL import Image, ImageDraw, ImageFont

# 1. Charger les données depuis le fichier JSON
with open('donnees.json', 'r', encoding='utf-8') as f:
    donnees = json.load(f)

# 2. Probabilités de tirage
PROBA_OBS_COMPO = 0.3
PROBA_OBS_NOM = 0.3
PROBA_SUJET_NEO = 0.25
PROBA_ADJ = 0.75


def tirer_obsessions(donnees):
    """Tire obs1, obs2, obs3 selon les règles composé / nom."""
    obs1_est_compo = random.random() < PROBA_OBS_COMPO
    obs3_est_nom = random.random() < PROBA_OBS_NOM

    if obs1_est_compo:
        obs1 = random.choice(donnees["obsessions-compo"])
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

def calculer_taille_police_deuxieme(texte):
    """Réduit la taille de police si le texte est long, l'augmente s'il est court.
    Formule linéaire simple, bornée entre 55 (mini) et 80 (maxi)."""
    taille = 90 - len(texte)
    return max(55, min(80, taille))

def generer_image(premiere_ligne, deuxieme_ligne):
    """Génère l'image façon 'couverture d'hebdo' avec le texte incrusté.
    Cette fonction ne publie rien : elle sauvegarde juste un fichier .jpg
    en local, que le workflow GitHub Actions rendra téléchargeable."""
    image = Image.open("une-vierge2.png").convert("RGBA")
    largeur, hauteur = image.size

    marge_gauche = 250
    marge_droite = 250
    marge_haut = 360
    marge_bas = 130

    x_gauche = marge_gauche
    largeur_utile = largeur - marge_gauche - marge_droite
    largeur_utile_premiere = largeur_utile * 0.6  # % de la largeur normale, pour forcer le retour à la ligne
    y = marge_haut

    calque_texte = Image.new("RGBA", image.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(calque_texte)

    police_premiere = ImageFont.truetype("Oswald-Regular.ttf", 38)
    taille_police_deuxieme = calculer_taille_police_deuxieme(deuxieme_ligne)
    police_deuxieme = ImageFont.truetype("Anton-Regular.ttf", taille_police_deuxieme)

    couleur_blanc = (255, 255, 255, 255)
    couleur_jaune = (255, 210, 0, 255)
    couleur_ombre = (0, 0, 0, 160)
    decalage_ombre = (4, 4)

    def dessiner_avec_ombre(x, y, texte, police, couleur):
        draw.text((x + decalage_ombre[0], y + decalage_ombre[1]), texte, font=police, fill=couleur_ombre)
        draw.text((x, y), texte, font=police, fill=couleur)

    lignes_premiere = decouper_selon_largeur(draw, premiere_ligne, police_premiere, largeur_utile_premiere)
    for ligne in lignes_premiere:
        dessiner_avec_ombre(x_gauche, y, ligne, police_premiere, couleur_blanc)
        y += 38 + 15

    y += 46

    lignes_deuxieme = decouper_selon_largeur(draw, deuxieme_ligne, police_deuxieme, largeur_utile)
    for ligne in lignes_deuxieme:
        largeur_ligne = draw.textlength(ligne, font=police_deuxieme)
        x_centre = x_gauche + (largeur_utile - largeur_ligne) / 2
        dessiner_avec_ombre(x_centre, y, ligne, police_deuxieme, couleur_jaune)
        y += taille_police_deuxieme + 23

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

# 4. Génération de l'image
chemin_image = generer_image(premiere_ligne, deuxieme_ligne)

# 5. Connexion et publication sur Bluesky (texte + image ensemble)
HANDLE = os.environ.get("BSKY_HANDLE")
PASSWORD = os.environ.get("BSKY_PASSWORD")

client = Client()
client.login(HANDLE, PASSWORD)

with open(chemin_image, "rb") as f:
    donnees_image = f.read()

client.send_image(
    text=texte_du_post,
    image=donnees_image,
    image_alt=texte_du_post
)

print("Post (texte + image) publié avec succès !")
