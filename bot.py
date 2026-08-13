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

# --- Marges du texte (zone autorisée sur l'image) ---
MARGE_GAUCHE = 250
MARGE_DROITE = 250
MARGE_HAUT = 360
MARGE_BAS = 130

# --- Phrase 1 (les 3 obsessions), en haut, alignée à gauche ---
FICHIER_POLICE_PHRASE1 = "Oswald-Regular.ttf"
COULEUR_PHRASE1 = (255, 255, 255, 255)  # blanc
TAILLE_PHRASE1 = 38
INTERLIGNE_PHRASE1 = 15
RATIO_LARGEUR_PHRASE1 = 0.66

# --- Phrase 2 (sujet + verbe + complément), centrée ---
FICHIER_POLICE_PHRASE2 = "Anton-Regular.ttf"
COULEUR_PHRASE2 = (255, 210, 0, 255)  # jaune
INTERLIGNE_PHRASE2 = 23
TAILLE_PHRASE2_BASE = 98
TAILLE_PHRASE2_MIN = 60
TAILLE_PHRASE2_MAX = 92
TAILLE_PHRASE2_COEF_REDUCTION = 0.5

# --- Espacement entre les deux blocs de texte ---
ESPACE_ENTRE_PHRASES = 46

# --- Ombrage (texte) ---
COULEUR_OMBRE = (0, 0, 0, 160)
DECALAGE_OMBRE = (4, 4)

# --- Géométrie de l'encadré noir (mesurée sur l'image de fond) ---
X_GAUCHE_ENCADRE = 200
LARGEUR_ENCADRE = 807
Y_BAS_ENCADRE = 1131

# --- Illustrations dans l'encadré ---
DOSSIER_IMAGES = "images"
HAUTEUR_ZONE_BASSE = 500
SUFFIXE_SANS_ESPACE_VERTICAL = "_en-bas"
MARQUEUR_SUPERPOSE = "_superpose"
ESPACEMENT_H_MAX = 100
ESPACEMENT_H_MIN_SUPERPOSE = -100


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
# 5. FONCTIONS D'ILLUSTRATION (images dans l'encadré)
# ============================================================

def lister_images_disponibles():
    """Liste les images PNG du dossier images/, avec leurs dimensions réelles."""
    if not os.path.isdir(DOSSIER_IMAGES):
        return []

    images_disponibles = []
    for nom_fichier in os.listdir(DOSSIER_IMAGES):
        if not nom_fichier.lower().endswith(".png"):
            continue
        chemin = os.path.join(DOSSIER_IMAGES, nom_fichier)
        largeur, hauteur = Image.open(chemin).size
        images_disponibles.append({
            "nom_fichier": nom_fichier,
            "chemin": chemin,
            "largeur": largeur,
            "hauteur": hauteur,
        })
    return images_disponibles


def calculer_y_image(hauteur_image, nom_fichier):
    """Calcule la position verticale (haut de l'image), selon la règle
    de la zone basse de l'encadré, sauf exception '_en-bas' sans espacement."""
    if nom_fichier.endswith(f"{SUFFIXE_SANS_ESPACE_VERTICAL}.png"):
        espacement_vertical = 0
    else:
        marge_max = max(0, HAUTEUR_ZONE_BASSE - hauteur_image)
        espacement_vertical = random.randint(0, marge_max)

    y_bas_image = Y_BAS_ENCADRE - espacement_vertical
    y_haut_image = y_bas_image - hauteur_image
    return y_haut_image


def determiner_espacement_min(nom_fichier, est_premiere):
    """L'espacement minimal est -100 uniquement si l'image autorise la
    superposition ET qu'elle n'est pas la première (rien à superposer avant elle)."""
    if not est_premiere and MARQUEUR_SUPERPOSE in nom_fichier:
        return ESPACEMENT_H_MIN_SUPERPOSE
    return 0


def choisir_emplacements_illustrations(images_disponibles):
    """Construit la liste des illustrations à intégrer, de gauche à droite.
    Pour chaque étape : on choisit d'abord une image qui tient dans l'espace
    restant, puis on tire l'espacement à sa gauche selon l'espace qu'il reste."""
    x_courant = X_GAUCHE_ENCADRE
    espace_restant = LARGEUR_ENCADRE
    emplacements = []
    est_premiere = True

    while True:
        candidats = [img for img in images_disponibles if img["largeur"] <= espace_restant]
        if not candidats:
            break

        image_choisie = random.choice(candidats)

        espacement_min = determiner_espacement_min(image_choisie["nom_fichier"], est_premiere)
        espacement_max = min(ESPACEMENT_H_MAX, espace_restant - image_choisie["largeur"])
        espacement = random.randint(espacement_min, espacement_max)

        x_courant += espacement
        y_haut = calculer_y_image(image_choisie["hauteur"], image_choisie["nom_fichier"])

        emplacements.append({
            "chemin": image_choisie["chemin"],
            "x": x_courant,
            "y": y_haut,
        })

        x_courant += image_choisie["largeur"]
        espace_restant -= (espacement + image_choisie["largeur"])
        est_premiere = False

    return emplacements


def integrer_illustrations(image):
    """Colle les illustrations choisies sur l'image de fond, avant le texte."""
    images_disponibles = lister_images_disponibles()
    emplacements = choisir_emplacements_illustrations(images_disponibles)

    for emplacement in emplacements:
        illustration = Image.open(emplacement["chemin"]).convert("RGBA")
        image.alpha_composite(illustration, (emplacement["x"], emplacement["y"]))

    return image


# ============================================================
# 6. FONCTIONS DE GÉNÉRATION DE L'IMAGE (texte)
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
    """Réduit la taille de police si le texte est long, l'augmente s'il est court."""
    taille = TAILLE_PHRASE2_BASE - len(texte) * TAILLE_PHRASE2_COEF_REDUCTION
    return max(TAILLE_PHRASE2_MIN, min(TAILLE_PHRASE2_MAX, taille))


def generer_image(premiere_ligne, deuxieme_ligne):
    """Génère l'image façon 'couverture d'hebdo' : fond + illustrations + texte."""
    image = Image.open(FICHIER_IMAGE_FOND).convert("RGBA")

    image = integrer_illustrations(image)

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

    lignes_premiere = decouper_selon_largeur(draw, premiere_ligne, police_premiere, largeur_utile_premiere)
    for ligne in lignes_premiere:
        dessiner_avec_ombre(x_gauche, y, ligne, police_premiere, COULEUR_PHRASE1)
        y += TAILLE_PHRASE1 + INTERLIGNE_PHRASE1

    y += ESPACE_ENTRE_PHRASES

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
# 7. CONSTRUCTION DU TEXTE DU POST
# ============================================================
obs1, obs2, obs3 = tirer_obsessions(donnees)
premiere_ligne = f"{obs1}, {obs2}, {obs3}"
deuxieme_ligne = construire_deuxieme_ligne(donnees)
texte_du_post = f"A la une aujourd'hui : {premiere_ligne}...\n{deuxieme_ligne}"

print("Message généré :")
print(texte_du_post)


# ============================================================
# 8. GÉNÉRATION DE L'IMAGE
# ============================================================
chemin_image = generer_image(premiere_ligne, deuxieme_ligne)


# ============================================================
# 9. PUBLICATION SUR BLUESKY
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
