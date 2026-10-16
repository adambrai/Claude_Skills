# Fourmi

Skill pour Claude Code qui aide à dépenser moins de tokens sur un projet, sans perdre en
qualité. Elle mesure d'abord ce qui est chargé à chaque message, explique où part le
contexte, puis propose des changements. Rien n'est écrit sans ton accord, fichier par
fichier.

## Ce qu'elle fait

1. **Mesure** avec `audit_context.py` : les CLAUDE.md chargés à chaque message (global,
   projet, local) et leurs `@imports`, ceux des sous-dossiers, la taille des descriptions
   de skills, les serveurs MCP (seulement leurs noms, jamais leurs réglages), les plugins
   activés, les gros fichiers que l'agent pourrait lire par erreur, et les règles
   `permissions.deny` déjà en place. Les chiffres sont des estimations (environ
   4 caractères par token).
2. **Explique** le résultat : ce qui pèse le plus, ce qu'il vaut la peine d'alléger en
   premier, et ce qui peut rester.
3. **Fusionne un bloc court dans le CLAUDE.md du projet** : quel modèle pour quel type de
   tâche, quand lancer un sous-agent, et quelques habitudes de lecture. Tu vois le diff
   avant. S'il y a déjà un bloc Fourmi, il est remplacé ; le reste du fichier ne bouge pas.
   Le bloc existe en français et en anglais. Il va à la racine du projet : on règle un
   projet sans toucher aux règles globales.
4. **Propose un petit sous-agent**, `ouvriere`, qui tourne sur Haiku avec les outils
   Read, Grep, Glob, Bash et Edit. Il s'occupe des corvées (chercher et lister des
   fichiers, lire des logs, renommer, faire une petite modification précise, résumer un
   fichier) et rend la main dès qu'il faut réfléchir. S'il est installé, une ligne dans
   `~/.claude/CLAUDE.md` dit à l'agent principal quand lui confier ces tâches (section
   « Répartition des tâches ») et ce qu'il garde pour lui : la planification, les choix
   importants et les bugs difficiles.
5. **Mesure à nouveau** à la fin et compare avec la mesure du début : les chiffres
   avant et après s'affichent côte à côte.

## Le bloc du CLAUDE.md

Choix du modèle selon la difficulté :

- Haiku : recherches rapides, inventaires, résumés, vérification de liens.
- Sonnet : modifications simples, tests, documentation, SEO technique, accessibilité,
  commits.
- Opus : implémentation complexe, changements sur plusieurs fichiers, refactors.
- Le niveau au-dessus d'Opus (architecture, stratégie floue, bug très difficile, revue
  finale) n'est utilisé que si tu le demandes, parce qu'il peut être facturé en crédits
  supplémentaires. Sinon Opus fait ce travail.
- Le paramètre `model` est indiqué à chaque lancement de sous-agent.

Quand utiliser un sous-agent :

- Pour isoler un travail qui demande beaucoup de lecture, ou pour des tâches vraiment
  indépendantes menées en parallèle.
- Pas pour une modification simple, des étapes qui se suivent, ou une tâche qui a besoin
  d'un seul contexte partagé : l'agent principal les fait lui-même.
- L'agent principal fait le plan avant de déléguer, puis garde le plan, les décisions
  finales et l'intégration.
- Jamais deux modifications en parallèle sur les mêmes fichiers.
- Quand une décision dépend d'un fichier source, l'agent principal le relit lui-même. Le
  rapport d'un sous-agent résume un travail isolé ; il ne remplace pas le matériau
  essentiel.

## Projets de site web

Pour un site, un bloc supplémentaire (`claude-md-web.md`, aussi en anglais) répartit le
travail :

- une seule validation de direction au départ (références, plan des pages, assets,
  décisions clés), pas une par section ;
- Haiku pour l'inventaire des assets, la recherche de références et la vérification des
  liens ;
- Sonnet pour le SEO et l'accessibilité ;
- Opus pour l'implémentation de plusieurs pages ;
- le niveau au-dessus d'Opus, seulement sur demande, pour le système de design et la
  revue finale ;
- des sous-agents pour les inventaires d'assets, les recherches de références et les
  audits SEO ;
- la direction créative reste dans le contexte principal.

## Utilisation

```
/fourmi
/fourmi audit
/fourmi ~/code/mon-projet
```

`audit` mesure et explique sans rien changer.

Les scripts marchent aussi seuls :

```bash
python3 audit_context.py ~/code/mon-projet
python3 audit_context.py ~/code/mon-projet --json
python3 audit_context.py ~/code/mon-projet --save avant.json       # garde la mesure du début
python3 audit_context.py ~/code/mon-projet --compare avant.json    # compare après changement
python3 merge_block.py ~/code/mon-projet/CLAUDE.md claude-md-block.md           # aperçu
python3 merge_block.py ~/code/mon-projet/CLAUDE.md claude-md-block.md --write   # écrit
```

## Vérifier que le sous-agent est installé

Un sous-agent défini par un fichier dans `~/.claude/agents/` est une fonction officielle
de Claude Code. Pour vérifier :

1. Redémarre Claude Code si une session était déjà ouverte.
2. Tape `/agents` et cherche `ouvriere` dans la liste des agents utilisateur.
3. Demande une corvée, par exemple « liste les fichiers Python du projet » : le nom de
   l'agent s'affiche pendant qu'il travaille.
4. Tu peux aussi l'appeler toi-même : « utilise l'agent ouvriere pour lister les fichiers
   Python ».

Pour le retirer, supprime `~/.claude/agents/ouvriere.md` et le bloc `fourmi-agent` de
`~/.claude/CLAUDE.md`.

## Limites

- Haiku est un modèle moins fort. Si une réponse de `ouvriere` paraît mince, repose la
  question sans l'agent.
- Les chiffres de l'audit sont des estimations. Le bloc ajoute quelques centaines de
  tokens au CLAUDE.md ; le gain vient des modèles moins chers pour les corvées et d'un
  contexte moins relu, ce qu'un simple comptage ne montre pas.
- Le coût par modèle sur un abonnement n'est pas publié. Les prix de l'API ne servent
  qu'à illustrer l'idée : un petit modèle coûte une fraction d'un grand.

## Fichiers

- `SKILL.md` : les consignes pour Claude Code.
- `audit_context.py` : la mesure.
- `merge_block.py` : fusionne un bloc ou copie un fichier, en montrant le diff d'abord.
- `claude-md-block.md` et `claude-md-block.en.md` : le bloc pour le CLAUDE.md du projet,
  en français et en anglais.
- `claude-md-web.md` et `claude-md-web.en.md` : le bloc en plus pour les projets de site.
- `agent-ouvriere.md` : le sous-agent.
- `delegation-line.md` et `delegation-line.en.md` : la section « Répartition des tâches »
  pour `~/.claude/CLAUDE.md`.

## Installation

```bash
git clone https://github.com/adambrai/Claude_Skills.git
mkdir -p ~/.claude/skills/fourmi
cp Claude_Skills/Fourmi/{SKILL.md,audit_context.py,merge_block.py,agent-ouvriere.md,claude-md-block.md,claude-md-block.en.md,claude-md-web.md,claude-md-web.en.md,delegation-line.md,delegation-line.en.md} ~/.claude/skills/fourmi/
```

## Tests

```bash
cd Fourmi && python3 -m unittest discover -s tests -v
```

## Licence

MIT, voir [LICENSE](../LICENSE).
