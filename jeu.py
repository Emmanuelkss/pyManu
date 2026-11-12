"""
Interface pygame du jeu.

Lancer :  python jeu.py
Installer pygame d'abord :  pip install -r requirements.txt

Toute la logique est dans moteur.py, ce fichier ne fait que l'affichage
et les clics.
"""

import math

import pygame

from humeur import MoodState
from moteur import (
    Partie, Personnage, Evenement, ACTIVITES, ChoixActivite,
    NB_JOURS, XP_PAR_NIVEAU,
)

LARGEUR, HAUTEUR = 1100, 700
FPS = 60

# ---------- Couleurs ----------
FOND = (24, 26, 38)
PANNEAU = (36, 40, 58)
PANNEAU_CLAIR = (50, 55, 78)
ACCENT = (110, 140, 255)
TEXTE = (235, 235, 245)
DISCRET = (150, 155, 175)
VERT = (90, 200, 120)
ROUGE = (235, 80, 80)
JAUNE = (250, 200, 60)
ROSE = (240, 110, 160)
PEAU = (240, 200, 160)

COULEURS_STATS = {
    "energie": ("Énergie", JAUNE),
    "bonheur": ("Bonheur", ROSE),
    "stress": ("Stress", ROUGE),
    "forme": ("Forme", VERT),
}

NOMS_HUMEUR = {
    MoodState.GOOD: "Super bien",
    MoodState.FINE: "Ça va",
    MoodState.NOT_GREAT: "Pas terrible",
    MoodState.BAD: "Au plus bas",
}


# ---------- Outils de dessin ----------

def couper_texte(texte: str, police: pygame.font.Font, largeur: int) -> list[str]:
    """Coupe un texte en lignes qui tiennent dans `largeur` pixels."""
    lignes = []
    for paragraphe in texte.split("\n"):
        mots = paragraphe.split(" ")
        ligne = ""
        for mot in mots:
            essai = f"{ligne} {mot}" if ligne else mot
            if police.size(essai)[0] <= largeur:
                ligne = essai
            else:
                if ligne:
                    lignes.append(ligne)
                ligne = mot
        lignes.append(ligne)
    return lignes


def ecrire(surf, texte, police, couleur, pos, largeur=None, interligne=4) -> int:
    """Écrit du texte (coupé si `largeur` est donné). Retourne la hauteur utilisée."""
    x, y = pos
    lignes = couper_texte(texte, police, largeur) if largeur else [texte]
    for ligne in lignes:
        surf.blit(police.render(ligne, True, couleur), (x, y))
        y += police.get_height() + interligne
    return y - pos[1]


def ecrire_centre(surf, texte, police, couleur, centre):
    image = police.render(texte, True, couleur)
    surf.blit(image, image.get_rect(center=centre))


def barre(surf, rect, valeur, couleur, maximum=100.0):
    pygame.draw.rect(surf, PANNEAU_CLAIR, rect, border_radius=6)
    plein = pygame.Rect(rect.x, rect.y, int(rect.w * max(0.0, min(1.0, valeur / maximum))), rect.h)
    if plein.w > 0:
        pygame.draw.rect(surf, couleur, plein, border_radius=6)


def melange(c1, c2, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


# ---------- Bouton ----------

class Bouton:
    def __init__(self, rect, texte, action, sous_texte="", couleur=ACCENT, actif=True):
        self.rect = pygame.Rect(rect)
        self.texte = texte
        self.action = action
        self.sous_texte = sous_texte
        self.couleur = couleur
        self.actif = actif

    def dessiner(self, surf, polices, souris):
        survol = self.actif and self.rect.collidepoint(souris)
        if not self.actif:
            fond = PANNEAU_CLAIR
        elif survol:
            fond = melange(self.couleur, (255, 255, 255), 0.25)
        else:
            fond = self.couleur
        pygame.draw.rect(surf, fond, self.rect, border_radius=10)
        couleur_texte = TEXTE if self.actif else DISCRET
        if self.sous_texte:
            ecrire_centre(surf, self.texte, polices["normal_gras"], couleur_texte,
                          (self.rect.centerx, self.rect.centery - 11))
            ecrire_centre(surf, self.sous_texte, polices["petit"], couleur_texte,
                          (self.rect.centerx, self.rect.centery + 13))
        else:
            ecrire_centre(surf, self.texte, polices["normal_gras"], couleur_texte, self.rect.center)

    def clic(self, pos) -> bool:
        if self.actif and self.rect.collidepoint(pos):
            self.action()
            return True
        return False


# ---------- Avatar ----------

def dessiner_avatar(surf, centre, p: Personnage, t: float, polices, echelle=1.0):
    """Le personnage change selon ses stats : sourire, yeux fatigués, sueur..."""
    cx, cy = centre
    cy += int(math.sin(t * 2) * 4 * echelle)          # petite respiration
    r = int(60 * echelle)

    # Corps : plus vert quand il est en forme
    couleur_corps = melange((120, 120, 140), VERT, p.forme / 100)
    corps = pygame.Rect(0, 0, int(110 * echelle), int(90 * echelle))
    corps.midtop = (cx, cy + r - int(10 * echelle))
    pygame.draw.rect(surf, couleur_corps, corps, border_radius=int(30 * echelle))

    # Tête : rougit avec le stress
    pygame.draw.circle(surf, melange(PEAU, (240, 150, 140), (p.stress - 50) / 50), (cx, cy), r)

    # Yeux
    ex, ey = int(22 * echelle), cy - int(12 * echelle)
    for dx in (-ex, ex):
        if p.energie < 25:                            # yeux mi-clos
            pygame.draw.line(surf, (40, 40, 50), (cx + dx - 9, ey), (cx + dx + 9, ey), 3)
        else:
            pygame.draw.circle(surf, (255, 255, 255), (cx + dx, ey), int(9 * echelle))
            pygame.draw.circle(surf, (40, 40, 50), (cx + dx, ey + 1), int(5 * echelle))

    # Bouche selon le bonheur
    bouche = pygame.Rect(0, 0, int(44 * echelle), int(26 * echelle))
    if p.bonheur >= 60:
        bouche.center = (cx, cy + int(14 * echelle))
        pygame.draw.arc(surf, (90, 40, 40), bouche, math.pi + 0.3, 2 * math.pi - 0.3, 4)
    elif p.bonheur >= 35:
        y = cy + int(26 * echelle)
        pygame.draw.line(surf, (90, 40, 40), (cx - 16, y), (cx + 16, y), 4)
    else:
        bouche.center = (cx, cy + int(36 * echelle))
        pygame.draw.arc(surf, (90, 40, 40), bouche, 0.3, math.pi - 0.3, 4)

    # Goutte de sueur si stressé
    if p.stress > 65:
        gx, gy = cx + r - 4, cy - r // 2
        pygame.draw.circle(surf, (120, 190, 255), (gx, gy + 6), 7)
        pygame.draw.polygon(surf, (120, 190, 255), [(gx - 6, gy + 4), (gx + 6, gy + 4), (gx, gy - 8)])

    # Zzz si épuisé
    if p.energie < 25:
        decalage = int((t * 20) % 20)
        ecrire(surf, "z Z", polices["normal_gras"], DISCRET, (cx + r - 10, cy - r - decalage))

    # Étoiles si très heureux
    if p.bonheur > 85:
        for i in range(3):
            angle = t * 1.5 + i * 2.1
            sx = cx + int(math.cos(angle) * (r + 25))
            sy = cy + int(math.sin(angle) * (r + 10)) - 10
            pygame.draw.circle(surf, JAUNE, (sx, sy), 4)


# ---------- Le jeu ----------

class Jeu:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("pyManu - Une semaine dans ma vie")
        self.ecran = pygame.display.set_mode((LARGEUR, HAUTEUR))
        self.horloge = pygame.time.Clock()
        polices = "segoeui,arial,dejavusans"
        self.polices = {
            "titre": pygame.font.SysFont(polices, 52, bold=True),
            "h1": pygame.font.SysFont(polices, 28, bold=True),
            "h2": pygame.font.SysFont(polices, 22, bold=True),
            "normal": pygame.font.SysFont(polices, 19),
            "normal_gras": pygame.font.SysFont(polices, 19, bold=True),
            "petit": pygame.font.SysFont(polices, 15),
        }
        self.en_cours = True
        self.scene = "titre"
        self.nom = ""
        self.partie: Partie | None = None
        self.duree = 1.0
        self.sommeil = 8.0
        self.bilan = None
        self.popup: Evenement | None = None
        self.flottants: list[dict] = []
        self.t = 0.0

    # ----- Boucle principale -----

    def lancer(self):
        while self.en_cours:
            dt = self.horloge.tick(FPS) / 1000
            for evenement in pygame.event.get():
                self.gerer(evenement)
            self.mettre_a_jour(dt)
            self.dessiner()
            pygame.display.flip()
        pygame.quit()

    def mettre_a_jour(self, dt):
        self.t += dt
        for f in self.flottants:
            f["age"] += dt
        self.flottants = [f for f in self.flottants if f["age"] < 2.2]

    # ----- Événements -----

    def gerer(self, e):
        if e.type == pygame.QUIT:
            self.en_cours = False
            return

        if self.scene == "titre" and not self.popup:
            if e.type == pygame.TEXTINPUT and len(self.nom) < 16:
                self.nom += e.text
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_BACKSPACE:
                    self.nom = self.nom[:-1]
                elif e.key == pygame.K_RETURN:
                    self.commencer()

        if e.type == pygame.KEYDOWN and self.scene == "jour" and not self.popup:
            touches = {pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2, pygame.K_4: 3, pygame.K_5: 4}
            if e.key in touches:
                self.faire(ACTIVITES[touches[e.key]])

        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for b in self.boutons():
                if b.clic(e.pos):
                    break

    # ----- Actions -----

    def commencer(self):
        self.partie = Partie(self.nom.strip() or "Joueur")
        self.debut_journee()

    def debut_journee(self):
        self.scene = "jour"
        self.duree = 1.0
        self.sommeil = 8.0
        self.popup = self.partie.evenement

    def faire(self, choix: ChoixActivite):
        p = self.partie
        if p.journee_terminee:
            return
        heures = min(self.duree, p.heures_restantes)
        _, changements = p.faire_activite(choix, heures)
        for i, (stat, delta) in enumerate(changements.items()):
            nom = COULEURS_STATS.get(stat, ("Savoir", ACCENT))[0]
            couleur = VERT if (delta > 0) != (stat == "stress") else ROUGE
            self.flottants.append({"texte": f"{delta:+.0f} {nom}", "couleur": couleur,
                                   "age": -i * 0.15})
        if p.journee_terminee:
            self.scene = "nuit"

    def changer_duree(self, delta):
        self.duree = max(0.5, min(self.partie.heures_restantes, self.duree + delta))

    def changer_sommeil(self, delta):
        self.sommeil = max(0.0, min(12.0, self.sommeil + delta))

    def dormir(self):
        self.bilan = self.partie.terminer_journee(self.sommeil)
        self.scene = "bilan"

    def suivant(self):
        self.partie.jour_suivant()
        if self.partie.finie:
            self.scene = "fin"
        else:
            self.debut_journee()

    def fermer_popup(self):
        self.popup = None

    def rejouer(self):
        self.partie = None
        self.bilan = None
        self.scene = "titre"

    def quitter(self):
        self.en_cours = False

    # ----- Boutons de chaque écran -----

    def boutons(self) -> list[Bouton]:
        if self.popup:
            return [Bouton((LARGEUR // 2 - 80, 430, 160, 46), "OK", self.fermer_popup)]
        return {
            "titre": self.boutons_titre,
            "jour": self.boutons_jour,
            "nuit": self.boutons_nuit,
            "bilan": self.boutons_bilan,
            "fin": self.boutons_fin,
        }[self.scene]()

    def boutons_titre(self):
        return [Bouton((LARGEUR // 2 - 120, 430, 240, 56), "Commencer", self.commencer)]

    def boutons_jour(self):
        p = self.partie
        liste = []
        for i, choix in enumerate(ACTIVITES):
            liste.append(Bouton((400, 140 + i * 82, 370, 70), f"{i + 1}. {choix.nom}",
                                lambda c=choix: self.faire(c), sous_texte=choix.resume,
                                actif=not p.journee_terminee))
        liste += [
            Bouton((800, 140, 50, 44), "-", lambda: self.changer_duree(-0.5), couleur=PANNEAU_CLAIR),
            Bouton((1030, 140, 50, 44), "+", lambda: self.changer_duree(+0.5), couleur=PANNEAU_CLAIR),
        ]
        for i, h in enumerate((1, 2, 3, 4)):
            liste.append(Bouton((800 + i * 71, 196, 63, 36), f"{h} h",
                                lambda h=h: self.changer_duree(h - self.duree),
                                couleur=PANNEAU_CLAIR, actif=h <= p.heures_restantes))
        liste.append(Bouton((800, 590, 280, 56), "Finir la journée", self.aller_nuit, couleur=(90, 80, 160)))
        return liste

    def aller_nuit(self):
        self.scene = "nuit"

    def boutons_nuit(self):
        return [
            Bouton((LARGEUR // 2 - 40, 330, 60, 50), "-", lambda: self.changer_sommeil(-0.5), couleur=PANNEAU_CLAIR),
            Bouton((LARGEUR // 2 + 200, 330, 60, 50), "+", lambda: self.changer_sommeil(+0.5), couleur=PANNEAU_CLAIR),
            Bouton((LARGEUR // 2 + 20, 470, 220, 56), "Dormir", self.dormir, couleur=(90, 80, 160)),
        ]

    def boutons_bilan(self):
        texte = "Voir le résultat" if self.partie.jour >= NB_JOURS else "Jour suivant"
        return [Bouton((LARGEUR - 280, HAUTEUR - 80, 250, 56), texte, self.suivant)]

    def boutons_fin(self):
        return [
            Bouton((LARGEUR - 560, HAUTEUR - 80, 250, 56), "Rejouer", self.rejouer),
            Bouton((LARGEUR - 280, HAUTEUR - 80, 250, 56), "Quitter", self.quitter, couleur=PANNEAU_CLAIR),
        ]

    # ----- Dessin -----

    def dessiner(self):
        self.ecran.fill(FOND)
        {
            "titre": self.dessiner_titre,
            "jour": self.dessiner_jour,
            "nuit": self.dessiner_nuit,
            "bilan": self.dessiner_bilan,
            "fin": self.dessiner_fin,
        }[self.scene]()

        souris = pygame.mouse.get_pos()
        if self.popup:
            self.dessiner_popup()
        for b in self.boutons():
            b.dessiner(self.ecran, self.polices, souris)

    def panneau(self, rect):
        pygame.draw.rect(self.ecran, PANNEAU, rect, border_radius=16)

    def dessiner_titre(self):
        P = self.polices
        ecrire_centre(self.ecran, "Une semaine dans ma vie", P["titre"], TEXTE, (LARGEUR // 2, 140))
        ecrire_centre(self.ecran, "Tes activités changent ton personnage. Trouve l'équilibre !",
                      P["normal"], DISCRET, (LARGEUR // 2, 200))

        ecrire_centre(self.ecran, "Nom de ton personnage :", P["h2"], TEXTE, (LARGEUR // 2, 300))
        champ = pygame.Rect(LARGEUR // 2 - 180, 330, 360, 54)
        pygame.draw.rect(self.ecran, PANNEAU, champ, border_radius=10)
        pygame.draw.rect(self.ecran, ACCENT, champ, 2, border_radius=10)
        curseur = "|" if int(self.t * 2) % 2 == 0 else ""
        ecrire_centre(self.ecran, self.nom + curseur, P["h2"], TEXTE, champ.center)

        regles = (f"{NB_JOURS} jours  •  16 h par jour  •  Choisis la durée puis l'activité  "
                  "•  Touches 1 à 5 pour aller plus vite")
        ecrire_centre(self.ecran, regles, P["petit"], DISCRET, (LARGEUR // 2, 540))

    def dessiner_entete(self):
        p = self.partie
        P = self.polices
        ecrire(self.ecran, f"Jour {p.jour}/{NB_JOURS}", P["h1"], TEXTE, (20, 18))
        ecrire(self.ecran, p.date.strftime("%d/%m/%Y"), P["normal"], DISCRET, (175, 26))
        texte = f"Il te reste {p.heures_restantes:g} h"
        ecrire_centre(self.ecran, texte, P["h2"], JAUNE, (LARGEUR // 2 + 40, 36))
        # Petite horloge : la journée qui se vide
        rect = pygame.Rect(LARGEUR - 300, 26, 280, 20)
        barre(self.ecran, rect, p.heures_restantes, ACCENT, maximum=16)

    def dessiner_perso(self, x=20, y=80):
        """Panneau de gauche : avatar + stats."""
        p = self.partie.perso
        P = self.polices
        self.panneau(pygame.Rect(x, y, 360, min(600, HAUTEUR - y - 20)))
        dessiner_avatar(self.ecran, (x + 180, y + 120), p, self.t, P)
        ecrire_centre(self.ecran, p.joueur.name, P["h2"], TEXTE, (x + 180, y + 275))
        ecrire_centre(self.ecran, f"{NOMS_HUMEUR[p.humeur()]}  •  {p.etat_mental().name.lower()}",
                      P["petit"], DISCRET, (x + 180, y + 302))

        yy = y + 330
        for stat, (nom, couleur) in COULEURS_STATS.items():
            valeur = getattr(p, stat)
            ecrire(self.ecran, nom, P["normal"], TEXTE, (x + 20, yy))
            ecrire(self.ecran, f"{valeur:.0f}", P["normal_gras"], TEXTE, (x + 300, yy))
            barre(self.ecran, pygame.Rect(x + 110, yy + 5, 180, 16), valeur, couleur)
            yy += 36
        ecrire(self.ecran, f"Savoir : {p.savoir:.0f}", P["normal"], TEXTE, (x + 20, yy))
        yy += 40
        ecrire(self.ecran, f"Niveau {p.niveau}", P["h2"], ACCENT, (x + 20, yy))
        ecrire(self.ecran, f"{p.xp_dans_niveau}/{XP_PAR_NIVEAU} XP", P["petit"], DISCRET, (x + 250, yy + 6))
        barre(self.ecran, pygame.Rect(x + 20, yy + 34, 320, 12), p.xp_dans_niveau, ACCENT, XP_PAR_NIVEAU)

        # Changements qui s'envolent au-dessus de l'avatar
        for i, f in enumerate(self.flottants):
            if f["age"] < 0:
                continue
            monte = int(f["age"] * 40)
            ecrire_centre(self.ecran, f["texte"], P["normal_gras"], f["couleur"],
                          (x + 290, y + 60 + i * 24 - monte))

    def dessiner_jour(self):
        P = self.polices
        p = self.partie
        self.dessiner_entete()
        self.dessiner_perso()

        ecrire(self.ecran, "Que fais-tu ?", P["h1"], TEXTE, (400, 90))

        # Durée choisie
        ecrire(self.ecran, "Durée", P["h2"], TEXTE, (800, 95))
        self.duree = max(0.5, min(p.heures_restantes, self.duree)) if p.heures_restantes > 0 else 0
        ecrire_centre(self.ecran, f"{self.duree:g} h", P["h1"], JAUNE, (940, 162))

        # Journal de la journée
        ecrire(self.ecran, "Aujourd'hui", P["h2"], TEXTE, (800, 255))
        yy = 290
        if not p.activites:
            ecrire(self.ecran, "Rien encore.", P["petit"], DISCRET, (800, yy))
        for a in p.activites[-10:]:
            ecrire(self.ecran, f"{a.name} - {a.hours:g} h ({a.activity_type.name.lower()})",
                   P["petit"], DISCRET, (800, yy))
            yy += 24
        if p.burnout:
            ecrire(self.ecran, "BURNOUT ! Ton personnage s'effondre.", P["normal_gras"], ROUGE,
                   (800, 550))

    def dessiner_nuit(self):
        P = self.polices
        self.dessiner_entete()
        self.dessiner_perso()
        self.panneau(pygame.Rect(400, 80, 680, 600))
        ecrire(self.ecran, "La nuit tombe...", P["h1"], TEXTE, (430, 110))
        ecrire(self.ecran, "Combien d'heures dors-tu ? 7 à 9 h, c'est l'idéal. "
                           "Moins de 6 h coûte du bonheur et de la forme, plus de 10 h un peu de forme.",
               P["normal"], DISCRET, (430, 160), largeur=620)

        couleur = VERT if 7 <= self.sommeil <= 9 else (JAUNE if 6 <= self.sommeil <= 10 else ROUGE)
        ecrire_centre(self.ecran, f"{self.sommeil:g} h", P["titre"], couleur, (LARGEUR // 2 + 130, 355))

        # Lune
        pygame.draw.circle(self.ecran, (230, 230, 200), (980, 140), 34)
        pygame.draw.circle(self.ecran, PANNEAU, (995, 128), 30)

    def dessiner_bilan(self):
        P = self.polices
        b = self.bilan
        p = self.partie
        ecrire(self.ecran, f"Bilan du jour {p.jour}", P["h1"], TEXTE, (30, 22))

        # Récit de la journée (decrire_journee de humeur.py)
        self.panneau(pygame.Rect(20, 80, 620, 520))
        ecrire(self.ecran, "Ta journée", P["h2"], TEXTE, (40, 98))
        ecrire(self.ecran, b.description, P["normal"], TEXTE, (40, 135), largeur=580, interligne=6)

        # Scores
        self.panneau(pygame.Rect(660, 80, 420, 520))
        yy = 100
        for nom, valeur, couleur in (("Concentration", b.focus, ACCENT), ("Bonheur", b.bonheur, ROSE)):
            ecrire(self.ecran, nom, P["h2"], TEXTE, (680, yy))
            ecrire(self.ecran, f"{valeur:.0f}/100", P["h2"], couleur, (980, yy))
            rect = pygame.Rect(680, yy + 36, 380, 18)
            barre(self.ecran, rect, valeur, couleur)
            seuil_x = rect.x + int(rect.w * 0.6)        # seuil de 60
            pygame.draw.line(self.ecran, TEXTE, (seuil_x, rect.y - 4), (seuil_x, rect.bottom + 4), 2)
            yy += 80

        ecrire(self.ecran, f"+{b.xp_gagne} XP", P["h1"], VERT, (680, yy))
        if b.niveau_monte:
            ecrire(self.ecran, f"NIVEAU {p.perso.niveau} !", P["h1"], JAUNE, (840, yy))
        yy += 50
        for m in b.messages_nuit:
            yy += ecrire(self.ecran, m, P["petit"], ROUGE, (680, yy), largeur=380)
        if b.conseils:
            yy += 8
            ecrire(self.ecran, "Conseils", P["h2"], TEXTE, (680, yy))
            yy += 32
            for c in b.conseils:
                yy += ecrire(self.ecran, f"• {c}", P["petit"], DISCRET, (680, yy), largeur=380) + 2

    def dessiner_fin(self):
        P = self.polices
        p = self.partie
        ecrire_centre(self.ecran, "Fin de la semaine !", P["titre"], TEXTE, (LARGEUR // 2, 60))
        self.dessiner_perso(x=20, y=110)

        self.panneau(pygame.Rect(400, 110, 680, 480))
        ecrire(self.ecran, p.rang_final(), P["h1"], JAUNE, (430, 130))
        ecrire(self.ecran, f"Niveau {p.perso.niveau}  •  {p.perso.xp} XP au total",
               P["h2"], TEXTE, (430, 175))

        # Tableau des jours
        yy = 230
        for x, titre in ((430, "Jour"), (540, "Concentration"), (720, "Bonheur"), (880, "XP")):
            ecrire(self.ecran, titre, P["normal_gras"], DISCRET, (x, yy))
        yy += 34
        for i, b in enumerate(p.historique, start=1):
            ecrire(self.ecran, str(i), P["normal"], TEXTE, (430, yy))
            barre(self.ecran, pygame.Rect(540, yy + 4, 140, 14), b.focus, ACCENT)
            barre(self.ecran, pygame.Rect(720, yy + 4, 140, 14), b.bonheur, ROSE)
            ecrire(self.ecran, f"+{b.xp_gagne}", P["normal"], VERT, (880, yy))
            yy += 36

    def dessiner_popup(self):
        voile = pygame.Surface((LARGEUR, HAUTEUR), pygame.SRCALPHA)
        voile.fill((0, 0, 0, 150))
        self.ecran.blit(voile, (0, 0))
        cadre = pygame.Rect(LARGEUR // 2 - 260, 200, 520, 300)
        pygame.draw.rect(self.ecran, PANNEAU, cadre, border_radius=16)
        pygame.draw.rect(self.ecran, ACCENT, cadre, 2, border_radius=16)
        P = self.polices
        ecrire_centre(self.ecran, "Événement du jour", P["petit"], DISCRET, (cadre.centerx, cadre.y + 30))
        ecrire_centre(self.ecran, self.popup.titre, P["h1"], TEXTE, (cadre.centerx, cadre.y + 70))
        ecrire(self.ecran, self.popup.description, P["normal"], TEXTE, (cadre.x + 30, cadre.y + 110),
               largeur=cadre.w - 60)
        effets = "   ".join(f"{v:+d} {COULEURS_STATS.get(k, ('Savoir', ACCENT))[0]}"
                            for k, v in self.popup.effets.items())
        ecrire_centre(self.ecran, effets, P["normal_gras"], JAUNE, (cadre.centerx, cadre.y + 195))


def main():
    Jeu().lancer()


if __name__ == "__main__":
    main()
