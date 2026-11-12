"""
Moteur du jeu : toute la logique, sans aucune interface.

Ton personnage vit une semaine. Chaque jour il a 16 heures éveillé à remplir
avec des activités qui changent ses stats. Le soir il dort, puis le jeu fait
le bilan de la journée avec humeur.py et donne de l'XP.

Ce fichier n'importe pas pygame : on peut le tester ou le réutiliser avec
n'importe quelle interface (terminal, pygame, web...).
"""

import datetime as dt
import random
from dataclasses import dataclass, field

from humeur import (
    Player, Day, Activity,
    ActivityType, Category, MoodState, MentalState,
    focus_score, happiness_score, suggestions, decrire_journee,
)

HEURES_EVEILLE = 16
NB_JOURS = 7
XP_PAR_NIVEAU = 80
STATS = ("energie", "bonheur", "stress", "forme")


# ---------- Activités ----------

# Effet de chaque catégorie, PAR HEURE
EFFETS = {
    Category.STUDY:  {"energie": -8,  "stress": +4, "savoir": +10},
    Category.SOCIAL: {"energie": -3,  "stress": -5, "bonheur": +10},
    Category.SPORT:  {"energie": -12, "stress": -8, "bonheur": +4, "forme": +10},
    Category.SCREEN: {"energie": -2,  "stress": +2, "bonheur": +3, "forme": -2},
    Category.OTHER:  {"energie": +4,  "stress": -3},
}

# Plus l'activité est appréciée, plus elle rapporte de bonheur
BONUS_RESSENTI = {
    ActivityType.FUN: 1.3,
    ActivityType.OK: 1.0,
    ActivityType.NOT_GREAT: 0.7,
    ActivityType.BORING: 0.6,
    ActivityType.TRASH: 0.4,
}


@dataclass(frozen=True)
class ChoixActivite:
    nom: str
    categorie: Category
    resume: str      # texte court affiché dans l'interface


ACTIVITES = [
    ChoixActivite("Étudier", Category.STUDY, "+savoir  -énergie  +stress"),
    ChoixActivite("Voir des amis", Category.SOCIAL, "+bonheur  -stress"),
    ChoixActivite("Faire du sport", Category.SPORT, "+forme  -stress  --énergie"),
    ChoixActivite("Écrans", Category.SCREEN, "+bonheur  -forme  +stress"),
    ChoixActivite("Se reposer", Category.OTHER, "+énergie  -stress"),
]


# ---------- Personnage ----------

@dataclass
class Personnage:
    joueur: Player
    energie: float = 80
    bonheur: float = 60
    stress: float = 30
    forme: float = 50
    savoir: float = 0
    xp: int = 0

    def borner(self):
        """Garde énergie, bonheur, stress et forme entre 0 et 100."""
        for stat in STATS:
            setattr(self, stat, max(0.0, min(100.0, getattr(self, stat))))
        self.savoir = max(0.0, self.savoir)

    def appliquer(self, effets: dict, facteur: float = 1.0):
        for stat, valeur in effets.items():
            setattr(self, stat, getattr(self, stat) + valeur * facteur)
        self.borner()

    def instantane(self) -> dict:
        """Copie des stats, pour calculer ce qui a changé après une action."""
        return {s: getattr(self, s) for s in (*STATS, "savoir")}

    def ressenti(self, categorie: Category, heures_ecran: float) -> ActivityType:
        """Le ressenti dépend de l'état du personnage, pas juste de l'activité."""
        if self.energie < 20 and categorie != Category.OTHER:
            return ActivityType.NOT_GREAT
        if categorie == Category.STUDY:
            return ActivityType.BORING if self.stress > 70 else ActivityType.OK
        if categorie in (Category.SOCIAL, Category.SPORT):
            return ActivityType.FUN
        if categorie == Category.SCREEN:
            return ActivityType.TRASH if heures_ecran >= 3 else ActivityType.OK
        return ActivityType.OK

    def humeur(self) -> MoodState:
        if self.bonheur >= 70:
            return MoodState.GOOD
        if self.bonheur >= 45:
            return MoodState.FINE
        if self.bonheur >= 20:
            return MoodState.NOT_GREAT
        return MoodState.BAD

    def etat_mental(self) -> MentalState:
        if self.energie < 15:
            return MentalState.EXHAUSTED
        if self.stress > 70:
            return MentalState.STRESSED
        if self.energie > 60 and self.stress < 30:
            return MentalState.MOTIVATED
        if self.stress < 40:
            return MentalState.CALM
        return MentalState.NEUTRAL

    def en_burnout(self) -> bool:
        return self.energie <= 0 and self.stress >= 90

    @property
    def niveau(self) -> int:
        return 1 + self.xp // XP_PAR_NIVEAU

    @property
    def xp_dans_niveau(self) -> int:
        return self.xp % XP_PAR_NIVEAU


# ---------- Événements aléatoires ----------

@dataclass
class Evenement:
    titre: str
    description: str
    effets: dict


def tirer_evenement(p: Personnage, rng: random.Random, chance: float = 0.45) -> Evenement | None:
    """Un événement a `chance` d'arriver au début de chaque journée."""
    if rng.random() > chance:
        return None

    possibles = [
        lambda: (Evenement("Examen surprise !", "Tu avais assez étudié, ça s'est bien passé.",
                           {"bonheur": +12, "stress": +5})
                 if p.savoir >= 40 else
                 Evenement("Examen surprise !", "Tu n'avais pas assez étudié... Le stress monte.",
                           {"stress": +20, "bonheur": -10})),
        lambda: Evenement("Invitation", "Un ami t'invite à dîner. Ça fait du bien.",
                          {"bonheur": +10, "stress": -5}),
        lambda: Evenement("Mal de tête", "Tu te réveilles avec un mal de tête.",
                          {"energie": -15, "bonheur": -5}),
        lambda: Evenement("Il fait beau", "Grand soleil aujourd'hui, tu te sens d'attaque.",
                          {"energie": +10, "bonheur": +5}),
        lambda: Evenement("Travail d'équipe", "Ton coéquipier n'a pas fait sa partie du projet.",
                          {"stress": +15}),
        lambda: (Evenement("Bonne note !", "Tes efforts payent : excellente note.",
                           {"bonheur": +15, "stress": -10})
                 if p.savoir >= 60 else
                 Evenement("Note décevante", "La note n'est pas celle que tu espérais.",
                           {"bonheur": -8, "stress": +8})),
        lambda: (Evenement("En pleine forme", "Le sport commence à payer, tu as plus d'énergie.",
                           {"energie": +15})
                 if p.forme >= 70 else
                 Evenement("Courbatures", "Tu manques de forme, tout est un peu plus dur.",
                           {"energie": -8})),
    ]
    return rng.choice(possibles)()


# ---------- Bilan d'une journée ----------

@dataclass
class BilanJour:
    day: Day
    description: str
    focus: float
    bonheur: float
    xp_gagne: int
    niveau_monte: bool
    conseils: list[str]
    messages_nuit: list[str] = field(default_factory=list)


# ---------- La partie ----------

class Partie:
    def __init__(self, nom: str, seed: int | None = None, date_debut: dt.date | None = None):
        self.rng = random.Random(seed)
        self.perso = Personnage(Player(name=nom or "Joueur", origin="Sherbrooke", level=1))
        self.date_debut = date_debut or dt.date.today()
        self.jour = 1
        self.historique: list[BilanJour] = []
        self._nouvelle_journee()

    # --- Journée en cours ---

    def _nouvelle_journee(self):
        self.activites: list[Activity] = []
        self.heures_restantes = float(HEURES_EVEILLE)
        self.heures_ecran = 0.0
        self.burnout = False
        self.evenement = tirer_evenement(self.perso, self.rng)
        if self.evenement:
            self.perso.appliquer(self.evenement.effets)
        self.stress_max = self.perso.stress

    @property
    def date(self) -> dt.date:
        return self.date_debut + dt.timedelta(days=self.jour - 1)

    @property
    def journee_terminee(self) -> bool:
        return self.heures_restantes <= 0 or self.burnout

    @property
    def finie(self) -> bool:
        return self.jour > NB_JOURS

    def faire_activite(self, choix: ChoixActivite, heures: float) -> tuple[Activity, dict]:
        """Fait l'activité et retourne (activité, changements des stats)."""
        if self.journee_terminee:
            raise ValueError("La journée est terminée.")
        if not 0 < heures <= self.heures_restantes:
            raise ValueError(f"Durée invalide : {heures} h (il reste {self.heures_restantes} h).")

        avant = self.perso.instantane()
        ressenti = self.perso.ressenti(choix.categorie, self.heures_ecran)

        effets = dict(EFFETS[choix.categorie])
        if "bonheur" in effets:
            effets["bonheur"] *= BONUS_RESSENTI[ressenti]
        self.perso.appliquer(effets, heures)

        activite = Activity(choix.nom, ressenti, choix.categorie, dt.timedelta(hours=heures))
        self.activites.append(activite)
        self.heures_restantes -= heures
        if choix.categorie == Category.SCREEN:
            self.heures_ecran += heures
        self.stress_max = max(self.stress_max, self.perso.stress)

        if self.perso.en_burnout():
            self.burnout = True

        apres = self.perso.instantane()
        changements = {s: apres[s] - avant[s] for s in apres if abs(apres[s] - avant[s]) >= 0.05}
        return activite, changements

    def terminer_journee(self, sommeil: float) -> BilanJour:
        """Fin de journée : bilan avec humeur.py, XP, puis effets de la nuit."""
        if not 0 <= sommeil <= 12:
            raise ValueError("Le sommeil doit être entre 0 et 12 h.")
        p = self.perso

        day = Day(
            player=p.joueur,
            date=self.date,
            sleep_time=sommeil,
            mood=p.humeur(),
            mental_state=p.etat_mental(),
            stress_level=round(self.stress_max / 10),
            activities=list(self.activites),
        )
        focus, bonheur = focus_score(day), happiness_score(day)

        xp = round((focus + bonheur) / 4 + min(p.savoir, 300) * 0.02)
        if self.burnout:
            xp //= 2
        ancien_niveau = p.niveau
        p.xp += xp
        p.joueur.level = p.niveau

        bilan = BilanJour(
            day=day,
            description=decrire_journee(day),
            focus=focus,
            bonheur=bonheur,
            xp_gagne=xp,
            niveau_monte=p.niveau > ancien_niveau,
            conseils=suggestions(day),
        )

        # La nuit : on récupère moins bien quand on manque de forme
        recup = 0.6 + 0.4 * p.forme / 100
        p.appliquer({"energie": +10 * recup, "stress": -2}, sommeil)
        if sommeil < 6:
            p.appliquer({"bonheur": -10, "forme": -5})
            bilan.messages_nuit.append("Nuit trop courte : -10 bonheur, -5 forme.")
        elif sommeil > 10:
            p.appliquer({"forme": -3})
            bilan.messages_nuit.append("Tu as trop dormi : -3 forme.")
        if self.burnout:
            bilan.messages_nuit.append("Burnout : XP divisée par 2.")

        self.historique.append(bilan)
        return bilan

    def jour_suivant(self):
        self.jour += 1
        if not self.finie:
            self._nouvelle_journee()

    # --- Fin de partie ---

    def rang_final(self) -> str:
        n = self.perso.niveau
        if n >= 6:
            return "Légende de l'équilibre"
        if n >= 5:
            return "Étudiant modèle"
        if n >= 4:
            return "Bien dans ses baskets"
        if n >= 2:
            return "Peut mieux faire"
        return "Semaine difficile"
