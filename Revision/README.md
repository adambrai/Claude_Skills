# Revision

Skill pour Claude Code qui construit **ton propre cours de révision** à partir de tes
documents : cours, slides, TD, TP, interros, examens, corrigés, notes.

Elle regarde d'abord ce qui est déjà tombé, en déduit ce qui peut tomber, classe chaque
notion par priorité, puis écrit un cours dense : toutes les infos essentielles
(définitions, formules, méthodes, pièges, questions types avec la réponse attendue), et
rien qui ne serve pas à gagner des points. Le but est de tout savoir sans saturer.

## Blabla ou essentiel

Avant d'écrire, la skill trie chaque slide. Elle garde les définitions exactes, les
notations formelles, les classifications, les méthodes, et ce qui est tombé. Elle
enlève l'étymologie, les slides de motivation, les répétitions, les longues listes
d'exemples. Une liste qui pourrait faire une question de cours (« citez les apports
de… ») est compressée en mots-clés plutôt que supprimée.

## Ce que ça produit

Dans `revision/<matiere>/` :

| fichier | contenu |
|---|---|
| `cours.md` | la carte des sujets (tombé / probable / hors radar) puis le cours, chapitre par chapitre |
| `annales.md` | chaque question d'interro ou d'examen, classée, avec la réponse modèle |
| `quiz.md` | questions de rappel actif, réponses cachées |
| `veille.md` | une page à relire le matin de l'examen |

Avant de rendre, la skill vérifie que **chaque question des annales** peut être résolue
avec le cours écrit. Si ce n'est pas le cas, elle complète.

## Priorités

| | sens |
|---|---|
| ★★★ | tombé plusieurs fois ou annoncé par le prof : à maîtriser par cœur |
| ★★ | tombé une fois, ou gros chapitre jamais interrogé : probable |
| ★ | utile pour comprendre un ★★★ : en surface |
| — | jamais tombé, marginal : une ligne au plus |

## Utilisation

```
/revision ~/Documents/S3/Reseaux
/revision quiz
/revision veille
/revision maj interro2.pdf
/revision exam-blanc
```

Mets tout ce que tu as dans un dossier par matière, même en vrac : la skill classe les
fichiers elle-même. Si le prof a dit « ça tombe » ou « pas au programme », écris-le dans
un fichier texte du dossier, ça passe avant le reste.

## Installation

Dans Claude Code :

```
https://github.com/adambrai/Claude_Skills
Installe la skill Revision de ce dépôt dans ~/.claude/skills/revision, puis vérifie que /revision marche.
```

Ou à la main :

```bash
git clone https://github.com/adambrai/Claude_Skills.git
mkdir -p ~/.claude/skills/revision
cp Claude_Skills/Revision/SKILL.md ~/.claude/skills/revision/
```

Il faut Claude Code. La skill est un simple jeu d'instructions, sans script ni
dépendance.

## Fichiers

| fichier | rôle |
|---|---|
| `SKILL.md` | les étapes que suit Claude Code |

## Licence

MIT, voir [LICENSE](../LICENSE).
