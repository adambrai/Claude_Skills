# Vitrine

Skill pour Claude Code qui conçoit ou refait une interface web en cinq étapes. Chaque
étape est finie et montrée avant de passer à la suivante, pour que tu puisses corriger
la direction tôt plutôt que de découvrir une page entière qui ne te plaît pas.

## Les cinq étapes

1. **Direction** : à qui s'adresse la page, ce qu'on doit y trouver tout de suite,
   l'action principale, le ton. Si le projet a déjà une source de design (`DESIGN.md`,
   un fichier de tokens, le thème CSS ou Tailwind, une charte), c'est elle qui décide.
   Sinon, la skill propose une palette, deux polices, des espacements et une idée
   propre au produit.
2. **Référence visuelle** : une maquette HTML statique de l'écran principal, avec le
   vrai texte, vue en largeur bureau et à 375 px. Tu la valides avant qu'une ligne du
   vrai code ne change.
3. **Implémentation** : les tokens d'abord, puis les composants, dans la pile déjà en
   place. Tous les états sont prévus (survol, focus, chargement, erreur, vide).
4. **Vérification dans un navigateur** : captures en 1440 px et en 375 px, lecture de
   la console, corrections, nouvelles captures. Elle utilise Playwright CLI s'il est
   installé, sinon les outils de navigateur de la session. Si aucun navigateur n'est
   disponible, elle le dit au lieu de faire comme si.
5. **Audit** : clavier, focus visible, contraste calculé, taille des cibles tactiles,
   formulaires, animations, et les bases avant la mise en ligne (titre, description,
   favicon, page 404, mentions légales, bannière de cookies).

## Pourquoi les pages générées se ressemblent

Un modèle écrit ce qui est le plus courant : fond blanc, cartes arrondies, dégradé
violet vers bleu, une seule police sans empattement. Lui demander « quelque chose de
moderne » n'y change rien. Ce qui change le résultat, ce sont des contraintes qui
viennent de l'extérieur. La skill en utilise cinq : une direction choisie (étape 1),
une liste de contrôle (étape 5), un système de design (étape 1), une référence à
regarder avant de coder (étape 2) et des captures réelles après chaque changement
(étape 4).

## Ce que la skill ajoute au fil des étapes

- **Styles proposés en option** à l'étape 1 : refonte d'un projet existant, « tout
  finir » (aucune section vide, aucun TODO, aucun bouton qui ne mène nulle part),
  minimaliste, doux, brutaliste. Aucun n'est imposé.
- **Systèmes de design** : celui du projet passe toujours en premier. Si tu utilises une
  bibliothèque de systèmes, chacun vient avec un fichier `SKILL.md` (jetons, règles de
  composants, contraintes d'accessibilité) et un fichier `DESIGN.md` (l'intention et ses
  raisons). Elle les prévisualise avant de choisir, parce que les noms trompent. Si deux
  systèmes se font concurrence, le `DESIGN.md` du projet l'emporte.
- **Image vers code** : soit tu apportes une référence (capture, export Figma, photo
  d'un site) et elle est reproduite fidèlement, soit la skill en propose une, te la
  montre, puis code à partir d'elle.
- **Journal des décisions** : un petit tableau (quoi, pourquoi, source, étape) pour que
  les corrections tardives ne défassent pas les choix du début.
- **Réflexes par défaut** : le fichier `reflexes.md` liste une quarantaine de tics
  (dégradés violets, ombres partout, trois cartes, trois tarifs, fausses
  recommandations, aucune démo réelle du produit...). Pour chacun, la question est :
  choisi ou par défaut ? Elle est posée au début et à la fin.
- **Navigateur** : en plus des captures en 1440 px et 375 px, la skill vérifie les
  boutons qui débordent, les grilles cassées, le texte illisible et les états de
  survol manquants, puis recommence après chaque correction. Pour une page derrière un
  identifiant, elle prend une page publique ou une route de démonstration avec des
  données d'exemple, et elle lit elle-même les captures.
- **Audit** : lancé aussi quand tu dis « vérifie l'interface » ou « audite
  l'accessibilité ». Si un style trop pâle échoue au contraste, on fonce seulement le
  texte courant et les libellés d'action ; le gris clair reste pour la décoration.
- **Test final** : quelqu'un qui arrive pour la première fois trouve-t-il ce qu'il
  cherche en trois secondes ?

## Erreurs courantes

- Tout changer d'un coup : impossible de savoir ce qui a produit quoi.
- Choisir un système de design sur son nom.
- Croire qu'un outil prend les décisions de produit. Le public, le but et l'ordre des
  informations restent les tiens.

## Par où commencer

Ajoute les contraintes une par une : la direction, puis l'audit, puis un système de
design, puis la référence visuelle, puis la vérification dans le navigateur. Essaie
chacune sur une petite page avant une grande. Pour lancer tout le parcours :

```
/vitrine <page>. Cinq étapes : direction, référence visuelle, code, vérification
navigateur en 1440 et 375 px, audit. Montre chaque résultat et ne passe pas à
l'étape suivante avant que la précédente soit terminée.
```

À la fin, tu as la liste des fichiers modifiés, les deux captures et un tableau d'audit
avec ce qui reste à faire.

## Utilisation

```
/vitrine page d'accueil d'une appli de covoiturage pour étudiants
/vitrine redesign src/pages/tarifs.tsx
/vitrine audit http://localhost:3000
```

Le mode `audit` ne fait que les étapes 4 et 5 sur une page qui existe déjà.

## Installation

```bash
git clone https://github.com/adambrai/Claude_Skills.git
mkdir -p ~/.claude/skills/vitrine
cp Claude_Skills/Vitrine/SKILL.md Claude_Skills/Vitrine/reflexes.md ~/.claude/skills/vitrine/
```

Pour les captures en ligne de commande, Playwright est optionnel :

```bash
npm install -D playwright && npx playwright install chromium
```

Une version pensée pour les agents, qui consomme bien moins de contexte qu'un serveur
MCP de navigateur (à garder pour les automatisations exploratoires complexes) :

```bash
npm i -g @playwright/cli@latest
playwright-cli install-browser
playwright-cli install --skills
```

La dernière commande est indispensable : sans elle, l'agent ne sait pas que l'outil
existe. La skill demande ton accord avant d'installer quoi que ce soit.

## Licence

MIT, voir [LICENSE](../LICENSE).
