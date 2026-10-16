# Rabot

Skill pour Claude Code qui relit un texte et enlève ce qui l'alourdit : formules toutes
faites, tirets à rallonge, gras partout, puces en émoji, précautions inutiles,
paragraphes tous de la même taille. Le sens, les faits et ton ton restent les mêmes.

Elle sert pour un README, un post, un mail, un rapport, ou le texte d'un site avant de
le publier.

## Le vérificateur

La skill vient avec `slopcheck.py`, un petit script qui donne une note sur 100 à un
texte (100 = rien à signaler) et liste chaque tic avec sa ligne. Il marche en français et
en anglais, ignore les blocs de code, et ne demande aucune dépendance.

```bash
python3 slopcheck.py mon-texte.md
python3 slopcheck.py --json README.md
cat brouillon.txt | python3 slopcheck.py -
python3 slopcheck.py --min 80 docs/*.md     # code de sortie 1 si un fichier est sous 80
python3 slopcheck.py --fix-suggestions mon-texte.md   # un remplacement simple par signal
```

L'option `--min` permet de l'utiliser dans une CI ou un hook de commit.

Avec `--fix-suggestions`, chaque signal est suivi d'une ligne qui dit par quoi le remplacer :
une virgule ou un point à la place d'un tiret long, un mot simple à la place d'un mot de
remplissage, la suppression d'une phrase d'ouverture. Avec `--json`, la même information
arrive dans le champ `suggestion` de chaque signal.

Ce que le script repère :

- le tiret long au milieu d'une phrase. En français, tous ceux qui sont à l'intérieur d'une
  ligne comptent et pèsent plus lourd. Un tiret qui commence une ligne (dialogue) est laissé
  tranquille ;
- la tournure `ce n'est pas X, c'est Y` et `pas seulement X, mais Y` ;
- les émojis en début de puce ou dans un titre ;
- trop de gras, du gras sur des mots isolés, un texte presque entièrement en puces ;
- les énumérations par trois qui reviennent à chaque phrase ;
- les précautions en série : `il est possible que`, `potentiellement`, `dans certains cas`,
  `il semblerait que` ;
- les paragraphes qui font tous presque la même longueur ;
- la première phrase qui reformule la question, complimente ou annonce la suite
  (`tu veux savoir`, `ta question porte sur`, `voici un aperçu`, `let's dive`) ;
- le vocabulaire de remplissage : `explorons`, `plongeons`, `il convient de noter`, `paysage` au
  sens figuré, `au cœur de`, `robuste`, `incontournable`, et en anglais `delve`, `tapestry`,
  `seamless`, `leverage` ;
- les guillemets et apostrophes courbes dans un texte anglais tapé simplement, quand rien
  d'autre ne montre de soin typographique. En français, les guillemets « » et l'apostrophe
  ’ sont normaux et ne sont jamais signalés.

La langue (français ou anglais) est devinée à partir du texte. Aucun de ces signes n'est une
faute à lui seul : c'est leur accumulation qui se remarque. Quand cinq familles de signes
sur dix ou plus sont présentes, le rapport le dit.

## Utilisation

```
/rabot mon-texte.md
/rabot <colle ton texte>
/rabot site ./mon-site
```

En mode texte, la skill note le texte, le réécrit, le note à nouveau et te montre la
nouvelle version avec les deux scores. Elle ne modifie le fichier que si tu le demandes.
Tes idées et tes exemples restent en place : seule la forme change. Elle te donne aussi la
liste de ce qu'elle a retiré ou modifié, et pourquoi (par exemple « trois tirets longs
remplacés par des virgules », « gras réduit de quatorze passages à deux », « première phrase
qui reformulait la question supprimée »).

En mode site, elle passe en revue un projet de site avant sa mise en ligne : le texte des
pages, les choix visuels faits par défaut, les éléments de base (favicon, titres et
descriptions, page 404, mentions légales réelles, version mobile à 375 px, bannière de
cookies avec un vrai refus) et les points de sécurité de base. Elle liste ce qui manque
avec le fichier à changer, et ne touche à rien sans ton accord.

Le mode site avance en quatre passes :

1. Vingt signes d'un site que personne n'a regardé : adresse de déploiement gardée telle
   quelle, dégradé violet, photos visiblement générées, faux témoignages, boutons qui ne font
   rien, animations au défilement partout, tout sur une seule page, logo réduit à un nom,
   pas de favicon, titre en couleurs animées, politique de confidentialité ou conditions
   générales vides, faux compteurs de visiteurs ou de clients, chiffres inventés, émojis à la
   place d'icônes, titre qui ne dit rien, police manuscrite, badge du générateur dans le pied
   de page, tirets longs dans les textes.
2. Les vingt-quatre réflexes de design, jugés par une seule question : choisi pour ce
   produit, ou là par défaut ? La liste est dans la section 2 de la charte.
3. Vingt éléments qui manquent souvent avant le lancement : page 404 avec un retour, appel à
   l'action visible sans défiler, titre et description propres à chaque page, image de
   partage, jeu de favicons complet, robots.txt, sitemap, texte alternatif, version mobile
   testée à 375 px, bouton d'action fixe sur mobile, états de chargement, messages d'erreur de
   formulaire, page de confirmation, vraie politique de confidentialité, vraies conditions,
   bandeau cookies avec un vrai refus, mesure d'audience, adresse de contact réelle, images
   compressées. Pour chaque élément, la skill dit s'il est présent ou absent, dans quel
   fichier, et comment le corriger, du plus urgent au moins urgent.
4. Vingt points de sécurité, lus dans le code. Pour chacun : l'état, le fichier et la ligne,
   ce qu'un attaquant pourrait faire, et le correctif, classés par gravité réelle. Les deux
   premiers : le contrôle d'accès au niveau des lignes sur chaque table, et aucune clé dans
   l'historique Git. Pour un vrai audit, la skill renvoie vers `/purple`.

## La charte

La charte a son propre dépôt : [Garde-fou](https://github.com/adambrai/Garde-fou). Ce sont
des règles courtes à garder en permanence : comment écrire, quels choix éviter sur un site,
et les règles de sécurité de base pour le code. Avec `/rabot charte`, la skill récupère la
dernière version, te la montre et l'ajoute à ton `CLAUDE.md` si tu es d'accord. Tu peux aussi la coller
dans les préférences personnelles de Claude, pour qu'elle s'applique à toutes tes
conversations.

## Ce que ce n'est pas

C'est un outil de relecture. Il ne sert pas à cacher qu'une IA a aidé à écrire un texte :
si ton école, ton client ou ton journal demande de le dire, c'est à toi de le faire.

## Installation

```bash
git clone https://github.com/adambrai/Claude_Skills.git
mkdir -p ~/.claude/skills/rabot
cp Claude_Skills/Rabot/{SKILL.md,slopcheck.py} ~/.claude/skills/rabot/
```

## Tests

```bash
cd Rabot && python3 -m unittest discover -s tests -v
```

## Licence

MIT, voir [LICENSE](../LICENSE).
