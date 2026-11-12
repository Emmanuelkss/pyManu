# pyManu - Une semaine dans ma vie

Un petit jeu en Python où tes activités affectent ton personnage.

Chaque jour, tu as 16 heures à remplir : étudier, voir des amis, faire du sport, les écrans ou te reposer. Chaque activité change l'énergie, le bonheur, le stress, la forme et le savoir de ton personnage, et son visage réagit. Le soir, tu choisis combien d'heures dormir, puis tu reçois un bilan de ta journée et de l'XP. Le but est de finir la semaine au plus haut niveau possible.

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

Le jeu utilise **pygame-ce**, qui fonctionne avec Python 3.14.

## Lancer

| Commande | Ce que ça fait |
|---|---|
| `python jeu.py` | Lance le jeu avec l'interface |
| `python main.py` | Affiche deux journées d'exemple dans le terminal |

## Comment jouer

1. Entre le nom de ton personnage.
2. Choisis une durée (boutons 1 h à 4 h, ou - et +), puis clique sur une activité. Les touches **1 à 5** marchent aussi.
3. Clique sur **Finir la journée** quand tu veux, puis choisis tes heures de sommeil. 7 à 9 h, c'est l'idéal.
4. Lis ton bilan et passe au jour suivant.

Attention : un événement aléatoire peut arriver au début de chaque journée (examen surprise, invitation, mal de tête...), et si l'énergie tombe à 0 avec un stress très élevé, c'est le burnout.

## Organisation du code

| Fichier | Rôle |
|---|---|
| `humeur.py` | Classes `Player`, `Activity`, `Day`, scores de concentration et de bonheur, description de la journée |
| `moteur.py` | Logique du jeu, sans interface : personnage, effets des activités, événements, XP, partie de 7 jours |
| `jeu.py` | Interface pygame : écrans, boutons, avatar |
| `main.py` | Exemple dans le terminal |

Pour équilibrer le jeu, modifie le dictionnaire `EFFETS` et les constantes en haut de `moteur.py`.
