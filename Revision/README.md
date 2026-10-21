# Revision

Skill pour Claude Code qui construit **ton propre cours de révision** à partir de tes
documents : cours, slides, TD, TP, interros, examens, corrigés, notes.

Ce n'est pas un résumé. La skill **trie et analyse** : elle relève toutes les notions
du cours, enlève seulement le bruit, garde la méthode et les notations du prof, étudie
ce qui est tombé et ce qui peut tomber, et surtout **comment le prof veut qu'on
réponde**.

## Le processus

1. **Inventaire** : chaque fichier est classé (cours, TD, TP, interro, examen, corrigé,
   consignes du prof).
2. **Registre** : toutes les notions du cours, slide par slide, avec leur source.
3. **Tri** : chaque notion devient « à savoir », « à comprendre », « exemple » ou
   « bruit ». Seul le bruit disparaît ; les répétitions sont fusionnées, pas perdues.
4. **Annales** : chaque question est découpée et rattachée à une notion. On obtient la
   carte des sujets (tombé, fréquence, points, ce qui peut tomber).
5. **Façon de répondre** : d'après les corrigés et les barèmes, la structure attendue,
   les notations, le niveau de détail, ce qui rapporte ou fait perdre des points, et un
   gabarit de réponse par type de question.
6. **Cours** : le plan du prof, sa méthode, ses notations, et pour chaque chapitre une
   question type avec la réponse modèle au format attendu.
7. **Double vérification** : aucune notion du registre n'est perdue, et chaque question
   d'annale est couverte, au bon format.
8. **Quiz et fiche de la veille.**

## Priorités

| | sens |
|---|---|
| ★★★ | tombé plusieurs fois ou annoncé par le prof |
| ★★ | tombé une fois, ou chapitre important jamais interrogé (probable) |
| ★ | nécessaire pour comprendre un ★★★ |
| ○ | secondaire : gardé, mais à réviser en dernier |

La priorité dit dans quel ordre réviser. Elle ne supprime rien.

## Ce que ça produit

Dans `revision/<matiere>/` :

| fichier | contenu |
|---|---|
| `registre.md` | toutes les notions du cours, avec source, statut et « tombé » |
| `examen.md` | annales découpées, carte des sujets, façon de répondre, gabarits |
| `cours.md` | le cours de révision |
| `quiz.md` | rappel actif, réponses cachées |
| `veille.md` | une page pour le matin de l'examen |

## Le PDF

Ajoute `pdf` à la commande (ou écris « etudes pdf », « en pdf ») : la skill met tout le
cours en page dans un PDF sobre, inspiré d'Apple. Il n'y a pas de page de titre ni de
sommaire, et aucune page n'est perdue : le contenu commence en haut de la page 1. Un
encadré coloré par type d'information (définition, pour comprendre, piège, méthode du
prof, comment répondre), avec des schémas propres et des réponses modèles.

Il faut Google Chrome (ou Chromium / Edge / Brave) pour l'impression. Les scripts
n'utilisent que la bibliothèque standard de Python.

## Utilisation

```
/revision
/revision ~/Documents/S3/Reseaux
/revision ~/Documents/S3/Reseaux pdf
/revision quiz
/revision veille
/revision maj interro2.pdf
/revision exam-blanc
```

Sans chemin, la skill lit **tout** le dossier où tu es, sous-dossiers compris. Elle liste
chaque fichier dans `sources.md` et le coche une fois lu en entier : aucun fichier n'est
sauté. Mets tout ce que tu as dans un dossier par matière, même en vrac : elle classe les
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
cp -R Claude_Skills/Revision/. ~/.claude/skills/revision/
```

Il faut Claude Code et Python 3. Chrome sert seulement pour le PDF.

## Fichiers

| fichier | rôle |
|---|---|
| `SKILL.md` | les étapes que suit Claude Code |
| `scripts/inventaire.py` | liste tous les fichiers du dossier, pour n'en sauter aucun |
| `scripts/build_pdf.py` | transforme le cours HTML en PDF avec Chrome |
| `assets/template.html` | modèle du PDF, avec chaque type d'encadré |
| `assets/cours.css` | le style du PDF |

## Licence

MIT, voir [LICENSE](../LICENSE).
