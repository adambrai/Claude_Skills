# Débat

Skill pour Claude Code qui fait travailler plusieurs agents sur la même tâche, les fait se
critiquer entre eux et garde la meilleure réponse.

On lance `/debat` avec une question ou une tâche. Chaque agent reçoit exactement la même
consigne, mais avec une façon de raisonner différente. Leurs réponses sont notées, comparées,
attaquées et corrigées pendant plusieurs tours. À la fin, on récupère une seule réponse, avec
un résumé de ce qui a été corrigé en cours de route.

## Déroulement

1. **Réponses de départ.** Chaque agent rédige sa réponse de son côté, avec une carte de
   stratégie qui lui est propre (un mode de raisonnement, une méthode, une priorité).
2. **Tri.** Des juges notent les réponses sans savoir qui les a écrites. Chaque réponse est
   notée deux fois. Les meilleures continuent, et les bonnes idées trouvées dans les autres
   sont mises de côté pour la suite.
3. **Duels.** Les réponses restantes s'affrontent deux par deux : chacune pointe les défauts
   de l'autre, puis corrige la sienne. Un juge tranche. Si l'écart est faible, un deuxième
   juge relit le match dans l'autre sens.
4. **Tour de table final.** Les finalistes se relisent et se corrigent mutuellement, plusieurs
   fois de suite. On s'arrête quand il ne reste plus de problème sérieux et que les notes ne
   montent plus.
5. **Version finale.** Un agent assemble la meilleure réponse avec les apports des autres, un
   relecteur extérieur cherche ce qui cloche, la réponse est corrigée, puis un juge vérifie
   qu'elle est bien meilleure que celle du leader.
6. **Comparaison (optionnelle).** Si on part d'une réponse qui ne convenait pas, la version
   finale lui est comparée à la fin.

Quelques règles qui s'appliquent partout :

- tous les agents reçoivent la même consigne, mot pour mot ;
- les notes suivent une grille écrite dans `rubric.md` (exactitude, respect des exigences,
  solidité, précision, clarté) ;
- une réponse avec une erreur grave vérifiée ne peut pas gagner contre une réponse correcte ;
- tout est enregistré dans le dossier `.debat/`, ce qui permet de reprendre un débat
  interrompu ;
- la skill ne modifie pas ton projet : si la réponse contient du code, elle te le propose et
  te demande avant de l'appliquer.

## Installation

Dans Claude Code :

```
https://github.com/adambrai/Claud_Skills
Installe la skill Debat de ce dépôt dans ~/.claude/skills/debat, puis vérifie que /debat marche.
```

Ou à la main :

```bash
git clone https://github.com/adambrai/Claud_Skills.git
mkdir -p ~/.claude/skills/debat
cp Claud_Skills/Debat/{SKILL.md,debat.py,templates.md,cards.json,rubric.md} ~/.claude/skills/debat/
```

Il faut Claude Code et Python 3.8 ou plus récent. Pas de dépendance à installer.

## Utilisation

```
/debat quelle base de données choisir pour mon projet : PostgreSQL, MongoDB ou Firebase ?
/debat --eco écris le résumé de mon rapport de stage
/debat --max trouve et corrige la fuite mémoire dans src/worker.py
/debat --agents 20 --seed 7 propose l'architecture de mon API
/debat
```

Sans texte, `/debat` reprend ta dernière demande et essaie de faire mieux que la réponse
précédente.

| option | effet |
|---|---|
| `--eco` | 6 agents, conseil limité à 2 tours. Le moins cher. |
| (aucune) | 12 agents. Réglage par défaut. |
| `--max` | 32 agents, jusqu'à 6 tours de conseil. Pour les questions importantes. |
| `--agents N` | choisir le nombre d'agents. |
| `--seed S` | refaire un débat avec les mêmes cartes et les mêmes duels. |
| `--ext codex,opus,antigravity` | ajouter des réponses d'autres outils via la skill `multi-agents` (optionnel). |

Les modèles sont désignés par leur gamme (`sonnet`, `opus`, `haiku`), donc la skill utilise
toujours la dernière version disponible.

Pense à passer en mode « accept edits » (Shift+Tab) avant de lancer, sinon Claude Code te
demandera une validation pour chaque fichier écrit par un agent.

## Coût

La skill est gratuite, mais chaque agent consomme des tokens de ton abonnement, environ
60 000 par appel.

| mode | appels | ordre de grandeur |
|---|---|---|
| `--eco` | environ 30 | 2 millions de tokens |
| par défaut | 60 à 85 | 4 à 5 millions |
| `--max` | 90 à 130 | 6 à 8 millions |

`python3 debat.py plan --mode std` affiche le détail avant de commencer. Le tour de table
s'arrête dès que les réponses ne progressent plus, donc on reste souvent dans le bas de la
fourchette.

## Exemple

Test en mode `--eco` avec 4 agents sur une fonction `slugify()` (accents français, longueur
maximale sans couper de mot, au moins 8 tests) :

- 31 appels au total ;
- la version finale a obtenu 90,5/100 contre 81 pour la meilleure réponse individuelle ; elle
  gérait un cas particulier que les autres avaient manqué ;
- le code final passe ses 17 tests, par exemple `"Œuvre complète — été 2026 !"` donne
  `oeuvre-complete-ete-2026`.

Les tests du moteur simulent des débats complets de 2 à 100 agents :

```bash
cd Debat && python3 -m unittest discover -s tests -v
```

## Fichiers

| fichier | rôle |
|---|---|
| `SKILL.md` | les étapes que suit Claude Code |
| `debat.py` | le moteur qui gère le débat (Python, bibliothèque standard) |
| `templates.md` | les consignes données à chaque rôle |
| `cards.json` | les cartes de stratégie, modifiables |
| `rubric.md` | la grille de notation |
| `tests/` | les tests |

## Licence

MIT, voir [LICENSE](../LICENSE).
