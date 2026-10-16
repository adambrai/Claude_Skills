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
4. **Propose un petit sous-agent**, `ouvriere`, qui tourne sur Haiku avec les outils
   Read, Grep, Glob, Bash et Edit. Il s'occupe des corvées (chercher et lister des
   fichiers, lire des logs, renommer, faire une petite modification précise, résumer un
   fichier) et rend la main dès qu'il faut réfléchir. S'il est installé, une ligne dans
   `~/.claude/CLAUDE.md` dit à l'agent principal quand lui confier ces tâches.

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
python3 merge_block.py ~/code/mon-projet/CLAUDE.md claude-md-block.md           # aperçu
python3 merge_block.py ~/code/mon-projet/CLAUDE.md claude-md-block.md --write   # écrit
```

## Vérifier que le sous-agent est installé

Ouvre une nouvelle session Claude Code, tape `/agents` et cherche `ouvriere` dans la
liste des agents utilisateur. Pour le retirer, supprime `~/.claude/agents/ouvriere.md` et
le bloc `fourmi-agent` de `~/.claude/CLAUDE.md`.

## Fichiers

- `SKILL.md` : les consignes pour Claude Code.
- `audit_context.py` : la mesure.
- `merge_block.py` : fusionne un bloc ou copie un fichier, en montrant le diff d'abord.
- `claude-md-block.md` : le bloc pour le CLAUDE.md du projet.
- `agent-ouvriere.md` : le sous-agent.
- `delegation-line.md` : la ligne pour `~/.claude/CLAUDE.md`.

## Installation

```bash
git clone https://github.com/adambrai/Claude_Skills.git
mkdir -p ~/.claude/skills/fourmi
cp Claude_Skills/Fourmi/{SKILL.md,audit_context.py,merge_block.py,claude-md-block.md,agent-ouvriere.md,delegation-line.md} ~/.claude/skills/fourmi/
```

## Tests

```bash
cd Fourmi && python3 -m unittest discover -s tests -v
```

## Licence

MIT, voir [LICENSE](../LICENSE).
