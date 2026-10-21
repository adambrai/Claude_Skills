---
name: revision
description: >-
  Build the user's own exam-prep course for a subject from their material
  (lectures, slides, TD/TP, past exams, quizzes/interros, corrections, notes).
  Analyses what has already come up in exams and what is likely to come up,
  ranks every topic by exam weight, then writes a dense revision course that
  keeps every essential fact (definitions, formulas, methods, traps, typical
  questions with model answers) while cutting everything that does not help
  score points, so the student is not overloaded. Also makes active-recall
  quizzes, a one-page last-day sheet, and updates everything when a new exam
  or quiz is added. Use when the user types /revision, wants to revise for an
  exam, make a "fiche de révision", analyse annales, or predict exam questions.
argument-hint: "[dossier ou fichiers de la matière] [quiz | veille | maj | exam-blanc]"
---

# revision

Construire **notre propre cours**, taillé pour l'examen : tout ce qui est tombé, tout ce
qui peut tomber, rien qui ne serve pas à gagner des points. Dense, jamais saturant.

Ce que l'utilisateur a tapé après `/revision` : `$ARGUMENTS`

Langue : celle des documents de la matière (français par défaut). Tutoiement.

## Modes

| argument | ce que ça fait |
|---|---|
| *(chemin seul ou rien)* | parcours complet : étapes 1 à 6 |
| `quiz` | quiz de rappel actif sur un chapitre ou tout (étape 5), interactif |
| `veille` | seulement la fiche d'une page de la veille (étape 6) |
| `maj <fichier>` | intègre une nouvelle interro/examen/cours, met à jour les priorités et le cours |
| `exam-blanc` | génère un sujet type examen (durée, barème) dans le style des annales, puis corrige ce que l'utilisateur répond |

Si aucun chemin n'est donné : chercher un dossier de la matière dans le répertoire
courant ; sinon demander où sont les documents (une seule question).

## Règles de densité (s'appliquent à tout ce qui est écrit)

Le but : **le maximum d'info utile par ligne**. Chaque ligne doit pouvoir rapporter
des points ou éviter d'en perdre.

- Phrases courtes, listes, tableaux. Pas d'introduction, pas de transition, pas de
  « il est important de noter que ».
- Une notion = sa définition exacte (mot pour mot si le prof la formule ainsi, c'est
  ce qui est attendu), puis l'intuition en une ligne si elle aide.
- Une méthode = des étapes numérotées, applicables telles quelles en examen.
- **Un** exemple par méthode, le plus proche des annales. Pas trois.
- Formules dans des blocs, avec la signification de chaque symbole et les conditions
  d'application.
- Ce qui n'est jamais tombé et ne sert pas à comprendre ce qui tombe : une ligne au
  plus, ou supprimé. Le dire dans la carte (« hors radar »), pour que l'utilisateur
  sache que c'est un choix.
- **Ne jamais couper l'essentiel pour faire court.** Test : chaque question des
  annales doit pouvoir être résolue avec le cours écrit seul. Si non, il manque
  quelque chose, on l'ajoute.
- Rien d'inventé. Toute info vient des documents. Si un complément extérieur est
  indispensable (prérequis manquant), le marquer `(hors docs)`.

## 1. Inventaire des sources

Lister et lire tous les fichiers fournis (PDF, images, slides, .docx, notes). Pour un
PDF long, lire par plages de pages. Pour un scan illisible, utiliser l'OCR (skill
`pdf` si disponible) ou le signaler.

Classer chaque source dans un petit tableau :

| fichier | type | année / date | corrigé ? |
|---|---|---|---|

Types : `cours`, `TD`, `TP`, `interro`, `examen`, `rattrapage`, `corrigé`, `notes`,
`consignes prof` (ce que le prof a dit : « ça tombe », « pas au programme »).
Les consignes du prof priment sur tout le reste.

## 2. Analyse des annales (ce qui est tombé)

Pour chaque interro / examen, découper en questions. Pour chaque question noter :
chapitre, notion, type (cours / définition / calcul / exercice / analyse de code /
QCM / démonstration / schéma), points au barème, année.

Puis produire la **carte des sujets** :

| notion | tombé (années) | fréquence | points moyens | type de question | priorité |
|---|---|---|---|---|---|

Priorité :
- `★★★` tombé plusieurs fois ou annoncé par le prof → **à maîtriser par cœur**
- `★★` tombé une fois, ou gros chapitre du cours/TD jamais encore interrogé → **probable**
- `★` notion secondaire, utile pour comprendre un ★★★ → **à connaître en surface**
- `—` jamais tombé, marginal → **hors radar** (une ligne au plus dans le cours)

Ensuite repérer les **schémas récurrents** : questions qui reviennent presque à
l'identique, exercices dont seules les valeurs changent, structure fixe du sujet
(ex. « toujours 1 question de cours + 2 exos »), pièges récurrents dans les corrigés.

**Ce qui peut tomber** : chapitres traités en cours/TD mais pas encore interrogés,
variantes plausibles des questions déjà posées, chapitre le plus récent du cours.
Le dire avec une justification courte, sans prétendre à la certitude.

S'il n'y a aucune annale : le dire, et prioriser d'après le poids dans le cours, les
TD (ce qu'on fait en TD tombe souvent) et les consignes du prof.

## 2 bis. Tri : blabla ou essentiel

Les cours (surtout les slides) sont pleins de remplissage. Passer chaque slide /
paragraphe au tri suivant, **avant** d'écrire quoi que ce soit.

**Essentiel (garder, formulation exacte du prof) :**
- définitions (« un X est… »), surtout quand le prof les met en gras ou les répète
- définitions formelles : n-uplets, notations, syntaxe (ex. `A = <Q, A, E, I, F>`)
- classifications et « types de » (ex. sûreté vs vivacité), différences entre deux notions
- composants d'une chose (« une technique formelle = 1… 2… 3… »)
- méthodes, algorithmes, règles, formules, et leurs conditions
- avantages / limites / « ce que ça permet / ne permet pas » : questions de cours
  classiques, à garder **en mots-clés**
- tout ce qui est apparu dans une annale, un TD ou une interro, même si ça a l'air
  anecdotique

**Blabla (supprimer ou réduire à une ligne) :**
- étymologie, historique, citations, « le terme vient du grec… »
- slides de motivation (« les systèmes sont de plus en plus complexes… ») : garder
  l'idée en une ligne si elle répond à « pourquoi X ? »
- longues listes d'exemples industriels ou d'applications : 2–3 exemples marquants
  au plus, sauf si les annales en demandent
- exemples hors sujet (modèle météo, économique…) : un mot au plus
- répétitions : la même idée reformulée sur plusieurs slides, le même schéma repris
  et complété de slide en slide (garder seulement la version finale)
- en-têtes, pieds de page, numéros, titres de cours répétés, texte de schéma éclaté
  par l'extraction PDF (le reconstruire en un schéma propre ou une ligne)

**Règle de prudence :** le blabla d'un cours peut être une question d'examen
(« citez les apports des méthodes formelles »). On **compresse** (liste de mots-clés)
plutôt qu'on supprime, dès qu'une liste répond à une question qu'on pourrait poser.
On supprime seulement ce qui ne répond à aucune question plausible.

Pour chaque document de cours, donner à la fin le ratio : « 57 slides → 2 pages ».

## 3. Le cours de révision

Un fichier par matière, ordonné par chapitre, chaque chapitre ainsi :

```
## <Chapitre> ★★★

**Tombé :** 2023 Q2 (4 pts), 2024 interro Q1 · **Peut tomber :** <variante>

### L'essentiel
- définitions exactes, propriétés, formules (avec conditions)

### Méthodes
1. étapes pour le type d'exercice qui tombe

### Pièges
- erreurs fréquentes / ce qui fait perdre des points dans les corrigés

### Question type
> énoncé court dans le style des annales
**Réponse attendue :** la réponse modèle, au niveau de détail qui donne tous les points
```

Budget : un chapitre ★★★ peut prendre de la place ; un ★ tient en quelques lignes ;
un `—` tient en une ligne ou disparaît. Un tableau comparatif vaut mieux que deux
paragraphes (ex. « X vs Y » quand les annales demandent des différences).

Ajouter en tête du fichier : la carte des sujets (étape 2), la structure habituelle du
sujet et le barème typique.

## 4. Vérification de couverture

Avant de rendre, repasser **chaque question de chaque annale** et vérifier qu'elle est
couverte par le cours écrit. Lister ce qui manquait et l'ajouter. Puis relire pour
couper ce qui est redondant. Donner à l'utilisateur le résultat en une ligne :
« N questions d'annales, N couvertes ».

## 5. Quiz de rappel actif

Fichier de questions courtes, réponses cachées dans des `<details>` :

```
**Q.** Définition de … ?
<details><summary>réponse</summary>…</details>
```

En priorité les ★★★, puis ★★. Mélanger définitions, « pourquoi », mini-calculs,
pièges. En mode `quiz` interactif : poser une question à la fois, attendre la
réponse, corriger en une ou deux lignes, noter les ratés, et reposer les ratés à la
fin.

## 6. Fiche de la veille

Une page, pas plus : formules et définitions ★★★, les étapes des méthodes qui
tombent, les pièges, la structure du sujet et la gestion du temps. C'est ce qu'on
relit le matin de l'examen.

## Fichiers produits

Dans `revision/<matiere>/` (dans le dossier de la matière ou le répertoire courant) :

| fichier | contenu |
|---|---|
| `cours.md` | carte des sujets + cours de révision (étapes 2–4) |
| `annales.md` | chaque question d'annale classée, avec la réponse modèle |
| `quiz.md` | questions de rappel actif |
| `veille.md` | la fiche d'une page |

Si l'utilisateur veut un PDF, convertir ensuite (skill `pdf` ou pandoc si présent).

## Mode `maj`

Lire le nouveau document, l'ajouter à l'inventaire, mettre à jour la carte des sujets
(fréquences, priorités), ajouter ou corriger les chapitres concernés, relancer la
vérification de couverture, et résumer ce qui a changé en quelques lignes.

## Fin

Terminer par un récap court : nombre de sources, la carte des sujets ★★★ (une
ligne chacun), le résultat de couverture, et ce qui manque éventuellement (un
corrigé absent, un scan illisible, un chapitre sans support).
