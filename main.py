import datetime as dt

from humeur import (
    Player, Day, Activity,
    ActivityType, Category, MoodState, MentalState,
    focus_score, happiness_score, afficher_bilan,
)


def main():
    joueur = Player(name="Emmanuel", origin="Sherbrooke", level=3)

    # Journée 1 : plutôt bonne
    lundi = Day(
        player=joueur,
        date=dt.date(2026, 11, 9),
        sleep_time=7.5,
        mood=MoodState.GOOD,
        mental_state=MentalState.MOTIVATED,
        stress_level=3,
    )
    lundi.add_activity(Activity("Révision AVL", ActivityType.OK, Category.STUDY, dt.timedelta(hours=2)))
    lundi.add_activity(Activity("Basket", ActivityType.FUN, Category.SPORT, dt.timedelta(hours=1, minutes=30)))
    lundi.add_activity(Activity("Souper entre amis", ActivityType.FUN, Category.SOCIAL, dt.timedelta(hours=2)))
    lundi.add_activity(Activity("YouTube", ActivityType.OK, Category.SCREEN, dt.timedelta(hours=1)))

    # Journée 2 : plus difficile
    mardi = Day(
        player=joueur,
        date=dt.date(2026, 11, 10),
        sleep_time=5,
        mood=MoodState.NOT_GREAT,
        mental_state=MentalState.STRESSED,
        stress_level=8,
    )
    mardi.add_activity(Activity("Devoir de C++", ActivityType.BORING, Category.STUDY, dt.timedelta(hours=1)))
    mardi.add_activity(Activity("TikTok", ActivityType.TRASH, Category.SCREEN, dt.timedelta(hours=4)))

    # Bilan de chaque jour (afficher_bilan appelle decrire_journee + scores + suggestions)
    semaine = [lundi, mardi]
    for jour in semaine:
        afficher_bilan(jour)

    # Moyenne de la semaine
    moy_focus = sum(focus_score(j) for j in semaine) / len(semaine)
    moy_bonheur = sum(happiness_score(j) for j in semaine) / len(semaine)
    print(f"Moyenne sur {len(semaine)} jours : concentration {moy_focus:.1f}, bonheur {moy_bonheur:.1f}")


if __name__ == "__main__":
    main()