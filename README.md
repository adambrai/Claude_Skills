# Claude_Skills

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
| [`Purple/`](Purple/) | `/purple` | Durcit la sécurité d'un projet en boucle, jusqu'à ce que les attaques automatiques ne trouvent plus rien. |
| [`Rabot/`](Rabot/) | `/rabot` | Relit un texte et enlève ce qui l'alourdit, avec un vérificateur qui note le texte sur 100. |
| [`Gomme/`](Gomme/) | `/gomme` | Aide à réduire tes traces en ligne : trouver les pages, rédiger les demandes RGPD, suivre les délais. |
| [`Rouage/`](Rouage/) | `/rouage` | Explique comment marche une appli à partir de son code ou de son build, avec les lignes qui le prouvent. |
| [`Aegis/`](Aegis/) | `/aegis` | Cadre une session de sécurité (périmètre, autorisation, but défensif) pour étudier ou travailler proprement. |
| [`Vitrine/`](Vitrine/) | `/vitrine` | Conçoit une interface web en cinq étapes validées une à une, avec captures en bureau et à 375 px, puis un audit. |
| [`Fourmi/`](Fourmi/) | `/fourmi` | Mesure ce qu'un projet charge dans le contexte et propose de quoi dépenser moins de tokens. |
| [`Douane/`](Douane/) | `/douane` | Inspecte une skill trouvée ailleurs avant de l'installer, sans jamais exécuter ses fichiers. |

### [Débat](Debat/) : `/debat`

Plusieurs agents traitent la même tâche, chacun avec une façon de raisonner différente. Les
réponses sont triées, s'affrontent en duels, puis les finalistes se corrigent entre eux
jusqu'à ce que le résultat ne progresse plus. La version finale regroupe le meilleur de
chacune et passe une dernière relecture.

Trois modes (`--eco`, par défaut, `--max`). Le débat est enregistré sur le disque et peut être
repris s'il est interrompu.

[Documentation de Débat](Debat/README.md)

### [Purple](Purple/) : `/purple`

Du durcissement de sécurité en boucle sur un projet qui t'appartient. Des agents rouges
cherchent des failles atteignables, un juge les confirme et les note, des agents bleus
réécrivent le code pour les corriger, et un juge vérifie que chaque faille est fermée sans
casser les tests. Au tour suivant, les rouges attaquent le code corrigé. Ça s'arrête quand un
tour ne trouve plus rien.

Tout se passe en local, sur une copie du projet ; l'original n'est jamais modifié, et rien ne
sort sur le réseau. À la fin : le code durci, un test par faille corrigée, et un rapport.

[Documentation de Purple](Purple/README.md)

### [Aegis](Aegis/) : `/aegis`

Pose le cadre d'un travail de sécurité avant de commencer : la cible et son périmètre, la base
d'autorisation (ton code, ton lab, un CTF), l'objectif défensif ou pédagogique, et les règles.
Utile pour étudier, résoudre un CTF, réviser une certification ou préparer une revue. Elle ne
contourne aucun système de sécurité : elle décrit un travail légitime pour qu'il soit clair,
puis passe le relais aux skills plus profondes.

[Documentation d'Aegis](Aegis/README.md)

## Installer une skill

Le plus simple, dans Claude Code :

```
https://github.com/adambrai/Claude_Skills
Installe la skill Debat de ce dépôt, puis vérifie qu'elle marche.
```

À la main : copie le dossier de la skill dans `~/.claude/skills/<nom>/` (pour toutes tes
sessions) ou dans `.claude/skills/<nom>/` d'un projet (pour ce projet seulement). Le README
de chaque skill donne la commande exacte.

La charte de travail utilisée par `/rabot charte` est dans un dépôt à part :
[Garde-fou](https://github.com/adambrai/Garde-fou).

## Licence

MIT, voir [LICENSE](LICENSE).
