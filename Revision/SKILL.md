---
name: revision
description: >-
  Build the user's own exam-prep course for a subject from their material
  (lectures, slides, TD/TP, past exams, quizzes/interros, corrections, notes).
  Extracts every notion from the course into a register so nothing is lost,
  sorts real content from filler, analyses what came up in past exams, what
  can come up, and how the professor expects answers to be written (structure,
  notation, method, what earns points). Then writes a revision course in the
  professor's own method and notation, with model answers in the expected
  format, checks that no notion was lost and that every past exam question is
  covered, and adds active-recall quizzes and a last-day sheet. Use when the
  user types /revision, wants to revise for an exam, make a "fiche de
  révision", analyse annales, or predict exam questions.
argument-hint: "[dossier ou fichiers de la matière] [quiz | veille | maj | exam-blanc]"
---

# revision

Construire **notre propre cours**, fait pour l'examen. Ce n'est pas un résumé : on
**trie** et on **analyse**. On ne perd aucune information, on enlève seulement le bruit,
on garde la méthode du prof, et on apprend à répondre comme il l'attend.

Ce que l'utilisateur a tapé après `/revision` : `$ARGUMENTS`

Langue : celle des documents de la matière (français par défaut). Tutoiement.

## Modes

| argument | ce que ça fait |
|---|---|
| *(chemin seul ou rien)* | processus complet : étapes 1 à 8 |
| `quiz` | quiz de rappel actif, interactif (étape 8) |
| `veille` | seulement la fiche de la veille (étape 8) |
| `maj <fichier>` | intègre une nouvelle interro / un examen / un chapitre et met tout à jour |
| `exam-blanc` | sujet dans le style et au barème des annales, puis correction selon les attentes du prof |

Si aucun chemin n'est donné : chercher un dossier de la matière dans le répertoire
courant ; sinon demander où sont les documents (une seule question).

## Principes

1. **Aucune perte d'information.** Condenser veut dire enlever des mots, jamais des
   faits. Une info répétée sur 5 slides est fusionnée en une, dans sa version la plus
   complète ; elle n'est pas supprimée.
2. **La méthode du prof, telle quelle.** Ses définitions mot pour mot, ses notations,
   ses étapes, son vocabulaire, l'ordre de son plan. Ne jamais remplacer sa méthode par
   une autre, même plus simple : c'est la sienne qui est notée.
3. **Trier n'est pas couper.** Chaque élément reçoit un statut (étape 3). Seul le bruit
   disparaît.
4. **L'examen est la référence.** Ce qui est tombé, ce qui peut tomber, et la façon dont
   il faut y répondre guident tout le reste.
5. **Rien d'inventé.** Tout vient des documents. Un complément extérieur indispensable
   est marqué `(hors docs)`.
6. **Lisible sans saturer.** Listes, tableaux, étapes numérotées ; pas d'introduction ni
   de transition. Mais la longueur suit la matière : un chapitre dense reste dense.

## 1. Inventaire des sources

Lire tous les fichiers fournis (PDF, images, slides, .docx, notes). Un PDF long se lit
par plages de pages ; un scan illisible passe par l'OCR (skill `pdf` si disponible) ou
est signalé.

| fichier | type | chapitre(s) | année / date | corrigé ? |
|---|---|---|---|---|

Types : `cours`, `TD`, `TP`, `interro`, `examen`, `rattrapage`, `corrigé`, `barème`,
`notes`, `consignes prof` (« ça tombe », « pas au programme », « je veux tel format »).
Les consignes du prof priment sur tout.

## 2. Registre des notions (extraction exhaustive)

Parcourir chaque document de cours, slide par slide, et relever **tout** ce qu'il
contient d'informatif dans `registre.md` :

| # | notion | nature | source | statut | tombé |
|---|---|---|---|---|---|

- **nature** : définition, propriété, théorème, notation, classification, méthode,
  algorithme, formule, schéma, exemple, avantage/limite, comparaison, remarque du prof
- **source** : fichier + slide/page, pour pouvoir retourner au cours
- **statut** : rempli à l'étape 3 · **tombé** : rempli à l'étape 4

Le texte extrait des PDF de slides est souvent éclaté (schémas cassés, lignes
mélangées) : reconstituer le sens à partir du contexte, et le signaler si un schéma
reste incompréhensible.

## 3. Tri

Donner un statut à chaque ligne du registre :

| statut | quoi | traitement dans le cours |
|---|---|---|
| **À savoir** | définitions, notations formelles, classifications, méthodes, formules, théorèmes, comparaisons, tout ce qui est tombé | en entier, formulation du prof |
| **À comprendre** | explications, intuitions, liens entre notions, justifications (« pourquoi X ») | gardé, reformulé court, sans perte de sens |
| **Exemple** | exemples du prof, exercices résolus, cas d'application | gardés quand ils illustrent une méthode ou ressemblent aux annales ; les autres sont listés en une ligne |
| **Bruit** | étymologie, répétitions, en-têtes et pieds de page, slides de transition, phrases sans contenu | supprimé (les doublons sont fusionnés, pas perdus) |

Pièges du tri :
- Une liste d'avantages, de limites ou d'exemples d'application n'est **pas** du bruit :
  c'est souvent une question de cours (« citez… »). On la garde entière, en liste.
- Une remarque du prof (« attention », « on confond souvent ») est **À savoir**.
- En cas de doute entre deux statuts, prendre le plus haut.

## 4. Analyse des annales : ce qui tombe

Découper chaque interro / examen en questions. Pour chacune : chapitre, notion (renvoi
au registre), type (définition, question de cours, calcul, exercice, modélisation,
analyse, QCM, démonstration, schéma), points, année.

Puis la **carte des sujets** :

| notion / chapitre | tombé (années) | fréquence | points | type de question | priorité |
|---|---|---|---|---|---|

- `★★★` tombé plusieurs fois ou annoncé par le prof
- `★★` tombé une fois, ou chapitre important du cours/TD jamais interrogé (probable)
- `★` jamais tombé, mais nécessaire pour comprendre un ★★★
- `○` jamais tombé, secondaire (gardé dans le cours, signalé comme moins prioritaire)

La priorité dit **dans quel ordre réviser**. Elle ne supprime rien.

Repérer aussi :
- les **questions récurrentes** (identiques ou presque d'une année à l'autre)
- les **exercices types** dont seuls les données changent
- la **structure du sujet** (nombre de parties, cours/exos, durée, barème)
- **ce qui peut tomber** : chapitres traités en cours ou en TD mais pas encore
  interrogés, variantes des questions passées, derniers chapitres vus. Justifier en une
  ligne, sans prétendre à la certitude.

Sans annale : le dire, et se baser sur les TD (ce qu'on fait en TD tombe souvent), le
poids des chapitres et les consignes du prof.

## 5. Analyse de la façon de répondre

Le but : savoir **comment** le prof veut qu'on réponde, pas seulement quoi. Sources, par
ordre de fiabilité : barèmes et corrigés d'examens, corrections de TD/TP, exemples
résolus du cours, consignes orales notées.

Pour chaque **type de question** rencontré, établir :
- **structure attendue** : définition puis exemple ? tableau comparatif ? étapes
  numérotées ? schéma obligatoire ? justification à chaque étape ?
- **notations et vocabulaire** du prof à reprendre (ex. `p –x→ q`, `a!` / `a?`, le
  n-uplet dans son ordre à lui)
- **niveau de détail** qui donne tous les points (d'après le barème : où vont les points)
- **ce qui fait perdre des points** d'après les corrigés : oubli d'une condition, mauvaise
  notation, réponse sans justification, confusion classique
- **gabarit de réponse** : le squelette à remplir le jour de l'examen

Écrire le résultat dans `examen.md`. Sans corrigé : déduire des corrections de TD et des
exemples du cours, et le dire.

## 6. Le cours de révision

`cours.md`, en suivant **le plan du prof** (mêmes chapitres, même ordre). En tête : la
carte des sujets et la structure habituelle du sujet. Puis, pour chaque chapitre :

```
## <Chapitre du prof> ★★★

**Tombé :** 2023 Q2 (4 pts), interro 2024 Q1 · **Peut tomber :** <variante, pourquoi>

### À savoir
- définitions exactes, notations, classifications, formules (avec conditions)

### À comprendre
- les explications et liens nécessaires, reformulés court

### Méthode du prof
1. ses étapes, dans son ordre, avec ses notations
   + un exemple du prof (ou de TD) déroulé

### Comment répondre à l'examen
- gabarit de réponse pour ce chapitre (renvoie à examen.md)
- ce qui rapporte les points / ce qui en fait perdre

### Question type
> énoncé dans le style des annales
**Réponse modèle :** rédigée exactement comme attendu (structure, notations, détail)
```

Un tableau vaut mieux que deux paragraphes quand le cours compare des notions.

## 7. Double vérification (obligatoire avant de rendre)

1. **Rien de perdu** : chaque ligne du registre qui n'est pas du Bruit apparaît dans
   `cours.md`. Lister ce qui manquait et l'ajouter.
2. **Annales couvertes** : chaque question d'annale peut être résolue avec `cours.md`
   seul, **au format attendu** (étape 5). Compléter sinon.
3. **Méthode respectée** : notations et étapes identiques à celles du prof.

Annoncer le résultat : « registre : N notions, N reprises · annales : N questions, N
couvertes ».

## 8. Quiz et fiche de la veille

`quiz.md` : questions courtes, réponses cachées dans des `<details>`. D'abord ★★★, puis
★★. Mélanger définitions, « pourquoi », comparaisons, mini-exercices, pièges.

```
**Q.** Définition de … ?
<details><summary>réponse</summary>…</details>
```

Mode `quiz` interactif : une question à la fois, attendre la réponse, corriger comme le
ferait le prof (barème, format attendu), noter les ratés, les reposer à la fin.

`veille.md` : une page, pour le matin de l'examen. Définitions et notations ★★★, les
gabarits de réponse, les pièges, la structure du sujet et la gestion du temps. C'est
le seul fichier volontairement court ; il renvoie au cours pour le reste.

## Fichiers produits

Dans `revision/<matiere>/` (dans le dossier de la matière ou le répertoire courant) :

| fichier | contenu |
|---|---|
| `registre.md` | toutes les notions du cours, avec source, statut et « tombé » |
| `examen.md` | annales découpées, carte des sujets, façon de répondre, gabarits |
| `cours.md` | le cours de révision |
| `quiz.md` | rappel actif |
| `veille.md` | la page de la veille |

Si l'utilisateur veut un PDF : convertir ensuite (skill `pdf`, ou pandoc s'il est
installé).

## Mode `maj`

Lire le nouveau document et l'ajouter à l'inventaire. Si c'est du cours : l'ajouter au
registre puis le trier. Si c'est une annale : la découper, mettre à jour la carte et les
priorités, et affiner `examen.md`. Mettre à jour les chapitres concernés de `cours.md`,
refaire la double vérification, et résumer ce qui a changé en quelques lignes.

## Fin

Un récap court : les sources utilisées, les ★★★ (une ligne chacun), le résultat de la
double vérification, et ce qui manque (corrigé absent, scan illisible, chapitre sans
support).
