# Claud_Skills

Une collection de **skills pour [Claude Code](https://claude.com/claude-code)**.

Une skill est un dossier d'instructions (et parfois de scripts) que Claude Code charge
automatiquement : elle lui apprend à faire une tâche précise, de la même façon à chaque fois.
Chaque dossier de ce dépôt est une skill indépendante, avec son propre README, prête à être
installée.

*English: a collection of Claude Code skills. Each folder is a standalone skill with its own
README.*

## Les skills

| dossier | commande | en bref |
|---|---|---|
| [`Debat/`](Debat/) | `/debat` | Fait débattre plusieurs agents Claude jusqu'à obtenir la meilleure réponse possible. |

### [Débat](Debat/) — `/debat`

Plusieurs agents traitent la même tâche, chacun avec une façon de raisonner différente. Les
réponses sont triées, s'affrontent en duels, puis les finalistes se corrigent entre eux
jusqu'à ce que le résultat ne progresse plus. La version finale regroupe le meilleur de
chacune et passe une dernière relecture.

Trois modes (`--eco`, par défaut, `--max`). Le débat est enregistré sur le disque et peut être
repris s'il est interrompu.

[Documentation de Débat](Debat/README.md)

## Installer une skill

Le plus simple, dans Claude Code :

```
https://github.com/adambrai/Claud_Skills
Installe la skill Debat de ce dépôt, puis vérifie qu'elle marche.
```

À la main : copie le dossier de la skill dans `~/.claude/skills/<nom>/` (pour toutes tes
sessions) ou dans `.claude/skills/<nom>/` d'un projet (pour ce projet seulement). Le README
de chaque skill donne la commande exacte.

## Licence

MIT, voir [LICENSE](LICENSE).
