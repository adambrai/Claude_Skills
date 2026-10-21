---
name: revision
description: >-
  Build the user's own exam-prep course for a subject, aiming for 20/20. Reads
  every file of the current folder (or the folder the user names) recursively:
  lectures, slides, TD/TP, past exams, quizzes/interros, corrections, notes.
  Extracts every notion into a register so nothing is lost, sorts real content
  from filler, analyses what came up in exams, what can come up, and how the
  professor expects answers (structure, notation, method, what earns points).
  Writes a course that truly explains, in the professor's own method, with
  model answers in the expected format; checks that no notion was lost and
  that every past exam question can be answered; adds quizzes and a last-day
  sheet. With "pdf" (e.g. "etudes pdf", "en pdf") it also renders a clean
  Apple-style PDF. Use when the user types /revision, wants to revise for an
  exam, make a "fiche de révision", analyse annales, or predict exam questions.
argument-hint: "[dossier] [pdf] [quiz | veille | maj <fichier> | exam-blanc]"
---

# revision

Construire **notre propre cours**, fait pour avoir 20/20. Ce n'est pas un résumé : on
lit **tout**, on **trie** et on **analyse**. On ne perd aucune information, on enlève
seulement le bruit, on garde la méthode du prof, on apprend à répondre comme il
l'attend, et on explique assez bien pour que tout soit compris, pas seulement appris.

Ce que l'utilisateur a tapé après `/revision` : `$ARGUMENTS`

Les scripts et le gabarit sont dans le dossier de ce fichier SKILL.md (en général
`~/.claude/skills/revision/`) : `scripts/inventaire.py`, `scripts/build_pdf.py`,
`assets/template.html`, `assets/cours.css`.

Langue : celle des documents de la matière (français par défaut). Tutoiement.

## Lire la demande

| l'utilisateur écrit | ce que ça veut dire |
|---|---|
| rien, ou seulement `pdf` | la matière = **le dossier courant**, en entier |
| un chemin, ou un nom de dossier | la matière = ce dossier, en entier |
| `pdf`, `etudes pdf`, `études pdf`, « en pdf », « fais-moi le pdf » | processus complet **+ PDF** (étape 9) |
| `quiz` | quiz interactif (étape 8) |
| `veille` | seulement la fiche de la veille |
| `maj <fichier>` | intègre un nouveau document et met tout à jour |
| `exam-blanc` | sujet dans le style et au barème des annales, puis correction comme le prof |

Les mots se combinent : `/revision ~/Documents/etudes/S3/MSC pdf`.

Si le dossier contient **plusieurs matières** (sous-dossiers par module, ou des
centaines de fichiers sans lien), ne pas tout mélanger : lister les matières trouvées
et demander laquelle traiter (une seule question). On peut aussi traiter chaque
matière séparément, l'une après l'autre.

## Le niveau visé : 20/20

Tout ce qui suit sert ce but. Chaque fois qu'il faut choisir, choisir ce qui fait
gagner des points à l'examen.

1. **Aucune perte d'information.** Condenser veut dire enlever des mots, jamais des
   faits. Une info répétée sur 5 slides est fusionnée en une, dans sa version la plus
   complète.
2. **La méthode du prof, telle quelle.** Ses définitions mot pour mot, ses notations,
   ses étapes, son vocabulaire, l'ordre de son plan. Ne jamais remplacer sa méthode
   par une autre, même plus simple : c'est la sienne qui est notée.
3. **Faire comprendre, pas seulement lister.** Écrire pour un étudiant qui a raté le
   cours et doit pouvoir répondre à tout avec ce seul document (voir « Écrire pour
   faire comprendre »).
4. **L'examen est la référence.** Ce qui est tombé, ce qui peut tomber et la façon dont
   il faut y répondre guident l'ordre, l'insistance et les exemples.
5. **Rien d'inventé.** Tout vient des documents. Une explication ajoutée pour aider à
   comprendre est permise, mais elle ne contredit jamais le prof. Un fait venu
   d'ailleurs est marqué `(hors docs)`.
6. **Lisible sans saturer.** Listes, tableaux, étapes numérotées, encadrés ; pas
   d'introduction ni de transition creuse. Mais la longueur suit la matière : un
   chapitre dense reste dense.

## 1. Inventaire : lire absolument tout

Lancer l'inventaire, qui liste récursivement chaque fichier (dossiers cachés et
`revision/` exclus) :

```bash
python3 ~/.claude/skills/revision/scripts/inventaire.py "<dossier>" "<dossier>/revision/<matiere>/sources.md"
```

Puis lire **chaque fichier en entier** et cocher sa ligne dans `sources.md` :
- PDF : toutes les pages, par plages de 20 si c'est long. Ne jamais s'arrêter aux
  premières pages.
- Slides (.pptx/.key) et .docx : extraire le texte (skills `pptx` / `docx` si
  présentes), sinon le dire.
- Images, scans, photos de copies : les regarder ; OCR (skill `pdf`) si c'est du texte.
- Code de TP : le lire ; il montre la méthode attendue.
- Archives (.zip) : en lister le contenu, et demander avant d'extraire.

Pour chaque fichier, remplir la colonne type : `cours`, `TD`, `TP`, `interro`,
`examen`, `rattrapage`, `corrigé`, `barème`, `notes`, `consignes prof` (« ça tombe »,
« pas au programme », « je veux tel format »). Les consignes du prof priment sur tout.
Un fichier hors sujet (autre matière, administratif) est marqué `hors matière`, sans
disparaître de la liste.

**Aucun fichier n'est sauté en silence.** Un fichier illisible ou impossible à ouvrir
est noté comme tel et signalé à la fin.

## 2. Registre des notions (extraction exhaustive)

Parcourir chaque document de cours, TD et TP, slide par slide, et relever **tout** ce
qu'il contient d'informatif dans `registre.md` :

| # | notion | nature | source | statut | tombé |
|---|---|---|---|---|---|

- **nature** : définition, propriété, théorème, notation, classification, méthode,
  algorithme, formule, schéma, exemple, avantage/limite, comparaison, remarque du prof
- **source** : fichier + slide/page, pour retourner au cours
- **statut** : rempli à l'étape 3 · **tombé** : rempli à l'étape 4

Le texte extrait des PDF de slides est souvent éclaté (schémas cassés, lignes
mélangées, en-têtes répétés au milieu des phrases) : reconstituer le sens à partir du
contexte, et regarder la page en image quand un schéma compte. Signaler un schéma qui
reste incompréhensible.

## 3. Tri

Donner un statut à chaque ligne du registre :

| statut | quoi | traitement dans le cours |
|---|---|---|
| **À savoir** | définitions, notations formelles, classifications, méthodes, formules, théorèmes, comparaisons, tout ce qui est tombé | en entier, formulation du prof |
| **À comprendre** | explications, intuitions, liens entre notions, justifications (« pourquoi X ») | gardé et expliqué clairement, sans perte de sens |
| **Exemple** | exemples du prof, exercices résolus, cas d'application | gardés quand ils illustrent une méthode ou ressemblent aux annales ; les autres sont cités en une ligne |
| **Bruit** | étymologie, répétitions, en-têtes et pieds de page, slides de transition, phrases sans contenu | supprimé (les doublons sont fusionnés, pas perdus) |

Pièges du tri :
- Une liste d'avantages, de limites ou d'exemples d'application n'est **pas** du bruit :
  c'est souvent une question de cours (« citez… »). On la garde entière.
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
- `○` jamais tombé, secondaire (gardé dans le cours, à réviser en dernier)

La priorité dit **dans quel ordre réviser et où insister**. Elle ne supprime rien.

Repérer aussi :
- les **questions récurrentes** (identiques ou presque d'une année à l'autre)
- les **exercices types** dont seules les données changent
- la **structure du sujet** (parties, cours/exos, durée, barème)
- **ce qui peut tomber** : chapitres traités en cours ou en TD mais pas encore
  interrogés, variantes des questions passées, derniers chapitres vus. Justifier en
  une ligne, sans prétendre à la certitude.

Sans annale : le dire, et se baser sur les TD (ce qu'on fait en TD tombe souvent), le
poids des chapitres et les consignes du prof.

## 5. Analyse de la façon de répondre

Savoir **comment** le prof veut qu'on réponde, pas seulement quoi. Sources, par ordre
de fiabilité : barèmes et corrigés d'examens, corrections de TD/TP, exemples résolus du
cours, consignes notées.

Pour chaque **type de question** rencontré, établir :
- **structure attendue** : définition puis exemple ? tableau comparatif ? étapes
  numérotées ? schéma obligatoire ? justification à chaque étape ?
- **notations et vocabulaire** du prof à reprendre tels quels
- **niveau de détail** qui donne tous les points (d'après le barème : où vont les points)
- **ce qui fait perdre des points** d'après les corrigés : condition oubliée, mauvaise
  notation, réponse sans justification, confusion classique
- **gabarit de réponse** : le squelette à remplir le jour de l'examen

Le tout va dans `examen.md`. Sans corrigé : déduire des corrections de TD et des
exemples du cours, et le dire.

## 6. Écrire le cours

`cours.md`, en suivant **le plan du prof** (mêmes chapitres, même ordre). En tête : la
carte des sujets et la structure habituelle du sujet. Puis, pour chaque chapitre :

```
## <Chapitre du prof> ★★★

**Tombé :** 2023 Q2 (4 pts), interro 2024 Q1 · **Peut tomber :** <variante, pourquoi>

<fil rouge : 2-3 lignes, à quelle question ce chapitre répond, comment il se relie au précédent>

### <Section du prof>
> **Définition (prof)** : mot pour mot
explication claire en une ou deux phrases, puis un exemple

| comparaison entre notions proches | … |

> **Pour comprendre** : le pourquoi, l'intuition, le lien
> **Piège** : la confusion classique
> **Méthode du prof** : ses étapes, avec ses notations, puis un exemple déroulé
> **Comment répondre** : gabarit, ce qui rapporte, ce qui coûte

### Question type
> énoncé dans le style des annales (points)
**Réponse modèle :** rédigée exactement comme attendu (structure, notations, détail)
```

### Écrire pour faire comprendre

- Chaque notion **À savoir** suit l'ordre : définition exacte du prof → ce qu'elle veut
  dire en mots simples → pourquoi elle existe (quel problème elle résout) → un exemple
  → comment on l'interroge à l'examen.
- Chaque **méthode** a un exemple déroulé en entier, chaque étape justifiée, avec les
  notations du prof. Pas d'étape sautée « parce qu'elle est évidente ».
- Les **notions proches** sont comparées dans un tableau (c'est là que se font les
  confusions, et les questions « différence entre »).
- Les **liens** entre notions et entre chapitres sont dits explicitement (« on a besoin
  de X pour Y »).
- Un **schéma** vaut mieux qu'un paragraphe pour une architecture, un automate, un
  flux ou un protocole : le reproduire proprement (SVG dans le PDF, liste ou tableau
  dans le markdown).
- Phrases courtes, un fait par phrase. Les mots techniques du prof sont gardés et
  expliqués la première fois.

## 7. Vérifications (obligatoires avant de rendre)

1. **Sources** : chaque ligne de `sources.md` est cochée, ou marquée illisible.
2. **Rien de perdu** : chaque ligne du registre qui n'est pas du Bruit apparaît dans
   `cours.md`. Lister ce qui manquait et l'ajouter.
3. **Méthode respectée** : définitions, notations et étapes identiques à celles du prof.
4. **Test du 20/20** : pour chaque annale (ou, sans annale, une dizaine de questions
   plausibles écrites d'après le cours), répondre **avec `cours.md` seul**, au format
   attendu, puis comparer au corrigé ou au barème. Si l'outil Agent est disponible,
   confier les réponses à un sous-agent qui n'a que `cours.md` et le sujet (pas le
   corrigé). Chaque point perdu révèle un trou : compléter le cours, puis refaire.
5. **Relecture de correcteur exigeant** : définitions exactes, aucune contradiction
   avec le prof, aucune explication fausse, exemples justes.

Annoncer le résultat : « sources : N/N lues · registre : N notions, N reprises ·
annales : N questions, N couvertes · test : N/20 ».

## 8. Quiz et fiche de la veille

`quiz.md` : questions courtes, réponses cachées dans des `<details>`. D'abord ★★★,
puis ★★. Mélanger définitions, « pourquoi », comparaisons, mini-exercices, pièges.

Mode `quiz` interactif : une question à la fois, attendre la réponse, corriger comme le
prof (barème, format attendu), noter les ratés, les reposer à la fin.

`veille.md` : une à deux pages, pour le matin de l'examen. Définitions et notations
★★★, les gabarits de réponse, les pièges, la structure du sujet et la gestion du
temps. C'est le seul fichier volontairement court ; il renvoie au cours pour le reste.

## 9. PDF (quand la demande contient « pdf »)

Le PDF reprend **tout** `cours.md` (même contenu, rien de coupé), mis en page sobre
dans l'esprit Apple : police système, hiérarchie nette, un encadré coloré par type
d'information.

**Zéro page perdue.** Pas de page de titre, pas de sommaire, pas de page blanche, pas
de saut de page entre les chapitres. Un bandeau d'une ligne (matière, prof, légende),
et le contenu commence tout de suite en haut de la page 1. C'est un document qu'on lit
la veille : chaque centimètre doit servir.

1. Copier `assets/template.html` vers `revision/<matiere>/cours.html`. Garder la
   structure et les classes ; remplacer tout le contenu d'exemple.
2. Remplir :
   - le **bandeau** (`.head`) : matière à gauche ; niveau, prof et légende des
     priorités à droite, en une ligne ;
   - un `<section class="chapter">` par chapitre, avec un `<h2>` (badge
     `<span class="prio p3">★★★</span>`), la ligne `.examline`, le fil rouge `.thread`,
     des `<h3>` par section ;
   - les encadrés : `.box.def` (définition, avec `.verbatim` pour le mot à mot du prof),
     `.box.why` (pour comprendre), `.box.trap` (piège), `.box.method` (méthode du
     prof), `.box.exam` (comment répondre), `.box.example` ;
   - `.formula` pour les formules et notations, avec `.legend` dessous ; `<table>`
     pour les comparaisons ; `<figure>` avec un SVG simple pour les schémas ;
   - `.qa` (`.q` avec `.pts`, puis `.a`) pour chaque question type ;
   - à la fin, un chapitre `quiz` avec les réponses dans `.answers`, puis la fiche de
     la veille comme dernier chapitre.
3. Construire :
   ```bash
   python3 ~/.claude/skills/revision/scripts/build_pdf.py revision/<matiere>/cours.html revision/<matiere>/<Matiere>.pdf
   ```
   Le script ajoute le style et les numéros de page, puis imprime avec Chrome en mode
   headless.
4. **Vérifier le rendu** : ouvrir le PDF (Read, par pages) et regarder la page 1, une
   page dense et un schéma. Corriger les débordements de tableau, les schémas
   illisibles, les encadrés coupés et tout espace vide inutile (une page à moitié
   blanche est un défaut), puis reconstruire.
5. Vérifier que le PDF contient bien tous les chapitres et toutes les sections de
   `cours.md` (comparer les titres).

Sans Chrome : le dire, et proposer d'ouvrir `cours.html` dans un navigateur puis
Imprimer > Enregistrer en PDF.

## Fichiers produits

Dans `revision/<matiere>/`, à l'intérieur du dossier de la matière :

| fichier | contenu |
|---|---|
| `sources.md` | tous les fichiers du dossier, cochés une fois lus |
| `registre.md` | toutes les notions, avec source, statut et « tombé » |
| `examen.md` | annales découpées, carte des sujets, façon de répondre, gabarits |
| `cours.md` | le cours de révision |
| `quiz.md` | rappel actif |
| `veille.md` | la fiche de la veille |
| `<Matiere>.pdf` | avec « pdf » : le cours complet mis en page |

## Mode `maj`

Lire le nouveau document et l'ajouter à `sources.md`. Si c'est du cours : l'ajouter au
registre puis le trier. Si c'est une annale : la découper, mettre à jour la carte et
les priorités, et affiner `examen.md`. Mettre à jour les chapitres concernés de
`cours.md`, refaire les vérifications (et le PDF s'il existe), et résumer ce qui a
changé en quelques lignes.

## Fin

Un récap court :
- les sources (N/N lues, et ce qui est illisible) ;
- les ★★★, une ligne chacun ;
- le résultat des vérifications et du test du 20/20 ;
- ce qui manque : un corrigé absent, un scan illisible, un chapitre sans support ;
- le chemin du PDF, s'il a été produit.
