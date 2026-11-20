"""
Meilleurs scores, gardés entre les parties dans un fichier JSON.

Comme moteur.py, ce fichier n'importe pas pygame.
"""

import datetime as dt
import json
from dataclasses import dataclass, asdict
from pathlib import Path

FICHIER_SCORES = Path(__file__).with_name("scores.json")
NB_MEILLEURS = 5


@dataclass
class Score:
    nom: str
    niveau: int
    xp: int
    rang: str
    date: str  # format AAAA-MM-JJ


def charger(fichier: Path = FICHIER_SCORES) -> list[Score]:
    """Lit les scores. Un fichier absent ou abîmé donne une liste vide."""
    try:
        donnees = json.loads(fichier.read_text(encoding="utf-8"))
        return [Score(**d) for d in donnees]
    except (OSError, ValueError, TypeError):
        return []


def sauvegarder(scores: list[Score], fichier: Path = FICHIER_SCORES):
    try:
        fichier.write_text(json.dumps([asdict(s) for s in scores], ensure_ascii=False, indent=2),
                           encoding="utf-8")
    except OSError:
        pass  # pas grave : le jeu continue sans sauvegarde


def ajouter(score: Score, fichier: Path = FICHIER_SCORES) -> tuple[list[Score], int | None]:
    """Ajoute le score et garde les meilleurs.

    Retourne (meilleurs scores, place du nouveau score à partir de 1),
    la place est None si le score n'entre pas dans le classement.
    """
    scores = charger(fichier)
    scores.append(score)
    scores.sort(key=lambda s: s.xp, reverse=True)  # tri stable : à égalité, l'ancien reste devant
    scores = scores[:NB_MEILLEURS]
    sauvegarder(scores, fichier)
    place = next((i for i, s in enumerate(scores, start=1) if s is score), None)
    return scores, place


def score_de_partie(partie) -> Score:
    """Construit le score d'une partie terminée (objet Partie de moteur.py)."""
    p = partie.perso
    return Score(
        nom=p.joueur.name,
        niveau=p.niveau,
        xp=p.xp,
        rang=partie.rang_final(),
        date=dt.date.today().isoformat(),
    )
