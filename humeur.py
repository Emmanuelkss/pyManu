from enum import Enum
from dataclasses import dataclass, field
import datetime as dt


# ---------- Énumérations (définies AVANT les classes qui les utilisent) ----------

class ActivityType(Enum):
    FUN = 0
    OK = 1
    NOT_GREAT = 2
    BORING = 3
    TRASH = 4


class Category(Enum):
    STUDY = "étude"
    SOCIAL = "social"
    SPORT = "sport"
    SCREEN = "écran"
    OTHER = "autre"


class MoodState(Enum):
    GOOD = 1
    FINE = 2
    NOT_GREAT = 3
    BAD = 4


class MentalState(Enum):
    EXHAUSTED = 1
    STRESSED = 2
    NEUTRAL = 3
    CALM = 4
    MOTIVATED = 5


MOOD_POINTS = {
    MoodState.GOOD: 35,
    MoodState.FINE: 25,
    MoodState.NOT_GREAT: 10,
    MoodState.BAD: 0,
}

MENTAL_POINTS = {
    MentalState.EXHAUSTED: 0,
    MentalState.STRESSED: 10,
    MentalState.NEUTRAL: 20,
    MentalState.CALM: 30,
    MentalState.MOTIVATED: 35,
}

SEUIL = 60


# ---------- Classes ----------

@dataclass
class Player:
    name: str
    origin: str
    level: int


@dataclass
class Activity:
    name: str
    activity_type: ActivityType
    category: Category
    duration: dt.timedelta

    @property
    def hours(self) -> float:
        return self.duration.total_seconds() / 3600


@dataclass
class Day:
    player: Player
    date: dt.date
    sleep_time: float
    mood: MoodState
    mental_state: MentalState
    stress_level: int
    activities: list[Activity] = field(default_factory=list)

    def __post_init__(self):
        if not 0 <= self.stress_level <= 10:
            raise ValueError("stress_level doit être entre 0 et 10")
        if self.sleep_time < 0:
            raise ValueError("sleep_time doit être positif")

    def add_activity(self, activity: Activity):
        self.activities.append(activity)

    def time_in(self, category: Category) -> float:
        return sum(a.hours for a in self.activities if a.category == category)

    def did_something_fun(self) -> bool:
        return any(a.activity_type == ActivityType.FUN for a in self.activities)


# ---------- Scores (0 à 100) ----------

def focus_score(day: Day) -> float:
    if day.mental_state == MentalState.EXHAUSTED:
        return 0  # deal-breaker
    score = MENTAL_POINTS[day.mental_state]
    score += min(day.sleep_time / 8, 1) * 35
    score += max(1 - day.time_in(Category.SCREEN) / 6, 0) * 20
    score += min(day.time_in(Category.STUDY) / 2, 1) * 10
    return score


def happiness_score(day: Day) -> float:
    if day.mood == MoodState.BAD:
        return 0
    score = MOOD_POINTS[day.mood]
    score += min(day.time_in(Category.SOCIAL) / 2, 1) * 25
    score += (10 - day.stress_level) / 10 * 25
    score += 15 if day.did_something_fun() else 0
    return score


def is_focused(day: Day) -> bool:
    return focus_score(day) >= SEUIL


def is_happy(day: Day) -> bool:
    return happiness_score(day) >= SEUIL


def suggestions(day: Day) -> list[str]:
    conseils = []
    if day.sleep_time < 7:
        conseils.append(f"Dors plus : {day.sleep_time:.1f} h, vise 7-8 h.")
    if day.time_in(Category.SCREEN) > 3:
        conseils.append("Réduis le temps d'écran (plus de 3 h aujourd'hui).")
    if day.time_in(Category.SOCIAL) < 1:
        conseils.append("Prends un moment avec des amis ou la famille.")
    if not day.did_something_fun():
        conseils.append("Fais au moins une activité que tu aimes.")
    if day.stress_level >= 7:
        conseils.append("Stress élevé : une pause ou du sport peut aider.")
    return conseils


# ---------- Description de la journée ----------

def formater_duree(heures: float) -> str:
    h = int(heures)
    m = round((heures - h) * 60)
    if h and m:
        return f"{h} h {m:02d}"
    return f"{h} h" if h else f"{m} min"


def decrire_journee(day: Day) -> str:
    """Retourne un résumé en phrases de ce que le joueur a fait."""
    if not day.activities:
        return f"{day.player.name} n'a enregistré aucune activité le {day.date}."

    lignes = [f"Le {day.date}, {day.player.name} a fait {len(day.activities)} activité(s) :"]

    # Ordre chronologique d'ajout, avec une phrase par activité
    for a in day.activities:
        lignes.append(f"  - {a.name} ({a.category.value}) pendant {formater_duree(a.hours)}"
                      f", ressenti : {a.activity_type.name.lower().replace('_', ' ')}")

    # Temps total par catégorie
    totaux = {c: day.time_in(c) for c in Category if day.time_in(c) > 0}
    total = sum(totaux.values())
    lignes.append(f"Temps total : {formater_duree(total)}, dont "
                  + ", ".join(f"{formater_duree(t)} en {c.value}" for c, t in totaux.items()) + ".")

    # Activité principale, meilleure et pire
    principale = max(day.activities, key=lambda a: a.hours)
    meilleure = min(day.activities, key=lambda a: a.activity_type.value)
    pire = max(day.activities, key=lambda a: a.activity_type.value)
    lignes.append(f"Ce qui a pris le plus de temps : {principale.name}.")
    if meilleure is not pire:
        lignes.append(f"Meilleur moment : {meilleure.name}. Moins bon : {pire.name}.")

    lignes.append(f"Nuit de {formater_duree(day.sleep_time)}, humeur {day.mood.name.lower().replace('_', ' ')}, "
                  f"état mental {day.mental_state.name.lower()}, stress {day.stress_level}/10.")
    return "\n".join(lignes)


# ---------- Affichage ----------

def afficher_bilan(day: Day):
    print(f"=== Bilan de {day.player.name} - {day.date} ===")
    print(decrire_journee(day))

    f, h = focus_score(day), happiness_score(day)
    print(f"Concentration : {f:5.1f}/100 -> {'concentré' if is_focused(day) else 'pas concentré'}")
    print(f"Bonheur       : {h:5.1f}/100 -> {'heureux' if is_happy(day) else 'pas heureux'}")

    conseils = suggestions(day)
    if conseils:
        print("Suggestions :")
        for c in conseils:
            print(f"  * {c}")
    print()