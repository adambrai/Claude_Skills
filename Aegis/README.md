# Aegis

Skill pour Claude Code qui cadre une session de travail en cybersécurité : périmètre,
autorisation, objectif défensif ou pédagogique. Elle est faite pour les gens qui
étudient la sécurité ou travaillent dessus : cours, CTF, lab autorisé, revue défensive,
préparation de certification.

On lance `/aegis` au début d'un travail de sécurité. La skill pose une courte charte (ce
qu'on vise, pourquoi c'est permis, dans quel but, avec quelles règles), puis le travail
technique avance avec un contexte clair : expliquer une classe de faille et sa
mécanique, analyser son propre code, raisonner sur un challenge, écrire des règles de
détection, réviser un sujet.

## Ce que ça fait, et ce que ça ne fait pas

Un sujet technique de sécurité passe sans friction quand le contexte est net : ton
code, ton lab, un CTF, un but défensif. Aegis met ce contexte en place au départ.

Ce n'est **pas** un outil de contournement. Il ne touche à aucun système de sécurité,
ne promet aucune liberté de tout dire, et ne fait pas passer une demande réellement
nuisible. Une charte décrit un travail ; elle ne « débloque » rien. Viser le système de
quelqu'un d'autre sans autorisation, ou demander une arme prête à l'emploi contre une
vraie cible, reste hors cadre, avec ou sans Aegis.

## La charte, en quatre points

1. **Cible et périmètre** : quoi exactement, et ce qui est dedans / dehors.
2. **Base d'autorisation** : ton code, ta machine, un CTF/lab prévu pour ça, une mission
   autorisée, ou un sujet théorique sans cible réelle.
3. **Objectif** : comprendre, détecter, corriger, apprendre. Défensif et pédagogique.
4. **Règles** : local ou lab uniquement, pas de système tiers réel, preuves minimales et
   non destructrices, secrets masqués.

Tu peux garder la charte dans un fichier `AEGIS.md` à la racine du projet.

## Installation

Dans Claude Code :

```
https://github.com/adambrai/Claude_Skills
Installe la skill Aegis de ce dépôt dans ~/.claude/skills/aegis, puis vérifie que /aegis marche.
```

Ou à la main :

```bash
git clone https://github.com/adambrai/Claude_Skills.git
mkdir -p ~/.claude/skills/aegis
cp Claude_Skills/Aegis/SKILL.md ~/.claude/skills/aegis/
```

Il faut Claude Code. La skill est un simple jeu d'instructions, sans script ni
dépendance.

## Utilisation

```
/aegis mon code dans ~/projet
/aegis ce challenge de CTF, lab local
/aegis je révise l'injection SQL pour ma certification
```

Une fois le cadre posé, la skill passe le relais aux skills plus profondes si elles sont
installées : [`/purple`](../Purple/) pour durcir son propre code en boucle,
[`/debat`](../Debat/) pour comparer plusieurs approches, et les skills de sécurité
dédiées de ta session pour une revue approfondie.

## Fichiers

| fichier | rôle |
|---|---|
| `SKILL.md` | les étapes que suit Claude Code |

## Licence

MIT, voir [LICENSE](../LICENSE).
