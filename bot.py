import os
import json
import random
from atproto import Client
from PIL import Image, ImageDraw, ImageFont

# ============================================================
# 1. CHARGEMENT DES DONNÉES
# ============================================================
with open('donnees.json', 'r', encoding='utf-8') as f:
    donnees = json.load(f)


# ============================================================
# 2. PROBABILITÉS DE TIRAGE DU TEXTE
# ============================================================
PROBA_OBS_COMPO = 0.3
PROBA_OBS_NOM = 0.3
PROBA_SUJET_NEO = 0.25
PROBA_ADJ = 0.75


# ============================================================
# 3. PARAMÈTRES VISUELS DE L'IMAGE
# ============================================================

# --- Image de fond ---
FICHIER_IMAGE_FOND = "une-vierge2.png"

# --- Marges (zone de texte autorisée sur l'image) ---
MARGE_GAUCHE = 250
MARGE_DROITE = 250
MARGE_HAUT = 360
MARGE_BAS = 130

# --- Phrase 1 (les 3 obsessions), en haut, alignée à gauche ---
FICHIER_POLICE_PHRASE1 = "Oswald-Regular.ttf"
COULEUR_PHRASE1 = (255, 255, 255, 255)  # blanc
TAILLE_PHRASE1 = 38
INTERLIGNE_PHRASE1 = 15
RATIO_LARGEUR_PHRASE1 = 0.66  # réduit la largeur dispo pour forcer le retour à la ligne plus tôt

# --- Phrase 2 (sujet + verbe + complément), centrée ---
FICHIER_POLICE_PHRASE2 = "Anton-Regular.ttf"
COULEUR_PHRASE2 = (255, 210, 0, 255)  # jaune
INTERLIGNE_PHRASE2 = 23
TAILLE_PHRASE2_BASE = 98        # valeur de départ avant réduction
TAILLE_PHRASE2_MIN = 60
TAILLE_PHRASE2_MAX = 92
TAILLE_PHRASE2_COEF_REDUCTION = 0.5  # points perdus par caractère

# --- Espacement entre les deux blocs de texte ---
ESPACE_ENTRE_PHRASES = 46

# --- Ombrage (appliqué aux deux phrases) ---
COULEUR_OMBRE = (0, 0, 0, 160)
DECALAGE_OMBRE = (4, 4)


# ============================================================
# 4. FONCTIONS DE GÉNÉRATION DU TEXTE
# ============================================================

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


# ============================================================
# 5. FONCTIONS DE GÉNÉRATION DE L'IMAGE
# ============================================================

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


def calculer_taille_police_phrase2(texte):
    """Réduit la taille de police si le texte est long, l'augmente s'il est court.
    Formule linéaire simple, bornée entre TAILLE_PHRASE2_MIN et TAILLE_PHRASE2_MAX."""
    taille = TAILLE_PHRASE2_BASE - len(texte) * TAILLE_PHRASE2_COEF_REDUCTION
    return max(TAILLE_PHRASE2_MIN, min(TAILLE_PHRASE2_MAX, taille))


def generer_image(premiere_ligne, deuxieme_ligne):
    """Génère l'image façon 'couverture d'hebdo' avec le texte incrusté.
    Cette fonction ne publie rien : elle sauvegarde juste un fichier .jpg en local."""
    image = Image.open(FICHIER_IMAGE_FOND).convert("RGBA")
    largeur, hauteur = image.size

    x_gauche = MARGE_GAUCHE
    largeur_utile = largeur - MARGE_GAUCHE - MARGE_DROITE
    largeur_utile_premiere = largeur_utile * RATIO_LARGEUR_PHRASE1
    y = MARGE_HAUT

    calque_texte = Image.new("RGBA", image.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(calque_texte)

    police_premiere = ImageFont.truetype(FICHIER_POLICE_PHRASE1, TAILLE_PHRASE1)
    taille_police_deuxieme = calculer_taille_police_phrase2(deuxieme_ligne)
    police_deuxieme = ImageFont.truetype(FICHIER_POLICE_PHRASE2, taille_police_deuxieme)

    def dessiner_avec_ombre(x, y, texte, police, couleur):
        draw.text((x + DECALAGE_OMBRE[0], y + DECALAGE_OMBRE[1]), texte, font=police, fill=COULEUR_OMBRE)
        draw.text((x, y), texte, font=police, fill=couleur)

    # --- Phrase 1 : alignée à gauche ---
    lignes_premiere = decouper_selon_largeur(draw, premiere_ligne, police_premiere, largeur_utile_premiere)
    for ligne in lignes_premiere:
        dessiner_avec_ombre(x_gauche, y, ligne, police_premiere, COULEUR_PHRASE1)
        y += TAILLE_PHRASE1 + INTERLIGNE_PHRASE1

    y += ESPACE_ENTRE_PHRASES

    # --- Phrase 2 : centrée ---
    lignes_deuxieme = decouper_selon_largeur(draw, deuxieme_ligne, police_deuxieme, largeur_utile)
    for ligne in lignes_deuxieme:
        largeur_ligne = draw.textlength(ligne, font=police_deuxieme)
        x_centre = x_gauche + (largeur_utile - largeur_ligne) / 2
        dessiner_avec_ombre(x_centre, y, ligne, police_deuxieme, COULEUR_PHRASE2)
        y += taille_police_deuxieme + INTERLIGNE_PHRASE2

    resultat = Image.alpha_composite(image, calque_texte).convert("RGB")
    resultat.save("post_genere.jpg", quality=95)
    return "post_genere.jpg"


# ============================================================
# 6. CONSTRUCTION DU TEXTE DU POST
# ============================================================
obs1, obs2, obs3 = tirer_obsessions(donnees)
premiere_ligne = f"{obs1}, {obs2}, {obs3}"
deuxieme_ligne = construire_deuxieme_ligne(donnees)
texte_du_post = f"{premiere_ligne}\n{deuxieme_ligne}"

print("Message généré :")
print(texte_du_post)


# ============================================================
# 7. GÉNÉRATION DE L'IMAGE
# ============================================================
chemin_image = generer_image(premiere_ligne, deuxieme_ligne)


# ============================================================
# 8. PUBLICATION SUR BLUESKY (texte + image ensemble)
# ============================================================
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
