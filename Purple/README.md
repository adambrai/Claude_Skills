# Purple

Skill pour Claude Code qui durcit la sécurité d'un projet qui t'appartient, en boucle,
jusqu'à ce que les attaques automatiques ne trouvent plus rien.

On lance `/purple` sur un dossier de code. Des agents « rouges » cherchent des failles
concrètes et atteignables, un juge confirme chacune et note sa gravité, des agents
« bleus » réécrivent les fichiers touchés pour corriger la cause, et un juge vérifie que
chaque faille est bien fermée sans rien casser. Au tour suivant, les rouges attaquent le
code déjà corrigé, y compris les correctifs. Ça s'arrête quand un tour entier ne trouve
plus de faille confirmée, ou au nombre de tours maximum.

Tout se passe en local, sur une **copie** du projet. Aucune requête réseau, rien de
destructeur, et ton projet d'origine n'est jamais modifié.

## Déroulement d'un tour

1. **Rouges** : plusieurs agents, chacun sous un angle différent (injection, contrôle
   d'accès, authentification, SSRF et fichiers, désérialisation, secrets, logique et
   concurrence, dépendances). Chaque faille est décrite précisément : fichier et ligne,
   l'entrée qui l'atteint, l'impact, et une idée de preuve locale.
2. **Vérification** : un juge ouvre le code, confirme ou écarte chaque faille, retire les
   doublons, note la gravité (critique, haute, moyenne, basse) et écrit une petite preuve
   locale quand c'est possible.
3. **Bleus** : pour chaque fichier concerné, un agent le réécrit en corrigeant la cause
   avec les bonnes pratiques actuelles de la techno (requêtes paramétrées, allowlist,
   vérification d'accès du framework, encodage de sortie, comparaison en temps constant,
   secrets déplacés hors du code…).
4. **Confirmation** : un juge vérifie que chaque faille est fermée, relance les tests du
   projet pour détecter une régression, et écrit un test qui empêchera la faille de
   revenir.

## Ce que tu obtiens

- Le **code durci** dans le dossier de travail, et le **diff complet** par rapport à
  l'original. Rien n'est appliqué à ton projet sans que tu voies le diff et donnes ton
  accord.
- Un **test de non-régression** par faille corrigée.
- Un **rapport** : les failles trouvées, leur gravité, comment elles ont été corrigées,
  et ce qui reste ouvert ou partiel. Les secrets sont masqués.

## Installation

Dans Claude Code :

```
https://github.com/adambrai/Claude_Skills
Installe la skill Purple de ce dépôt dans ~/.claude/skills/purple, puis vérifie que /purple marche.
```

Ou à la main :

```bash
git clone https://github.com/adambrai/Claude_Skills.git
mkdir -p ~/.claude/skills/purple
cp Claude_Skills/Purple/{SKILL.md,purple.py,templates.md,rubric.md,angles.json} ~/.claude/skills/purple/
```

Il faut Claude Code et Python 3.8 ou plus récent. Pas de dépendance à installer.

## Utilisation

```
/purple --project .
/purple --eco --project ~/mon-appli
/purple --max --project ~/mon-pfe --test-cmd "npm test"
```

| option | effet |
|---|---|
| `--project <chemin>` | le dossier à durcir (obligatoire). Une copie est faite. |
| `--eco` | 3 rouges, 2 tours. Le plus rapide. |
| (aucune) | 4 rouges, 3 tours. Réglage par défaut. |
| `--max` | 6 rouges, 5 tours. Passe approfondie. |
| `--rounds N` | limiter le nombre de tours. |
| `--test-cmd "..."` | la commande qui lance les tests du projet, pour vérifier qu'aucun correctif ne casse quelque chose. Détectée automatiquement quand c'est possible. |

Pense à passer en mode « accept edits » (Shift+Tab) avant de lancer, sinon chaque
fichier écrit par un agent demande une validation.

## Coût

La skill est gratuite, mais chaque agent consomme des tokens de ton abonnement, environ
60 000 par appel. Une passe `--eco` fait autour d'une quinzaine d'appels, une passe par
défaut plusieurs dizaines. `python3 purple.py plan --mode std` affiche le détail avant de
commencer, et la boucle s'arrête tôt si un tour ne trouve plus rien.

## Exemple

Test sur une petite API volontairement vulnérable (injection SQL, injection de commande,
accès non contrôlé, secret en dur), en mode `--eco`, 2 tours :

- tour 1 : 7 failles confirmées (dont 2 critiques et 3 hautes), toutes corrigées, les
  tests du projet passent toujours ;
- tour 2 : les rouges attaquent le code corrigé et ne trouvent plus que du renforcement
  de second niveau ; un correctif a introduit un effet de bord, que le juge a détecté
  avec son propre test de non-régression et signalé comme partiel ;
- le code final compile, le secret et l'appel shell dangereux ont disparu, et chaque
  correctif est protégé par un test.

Les tests du moteur simulent des cycles complets :

```bash
cd Purple && python3 -m unittest discover -s tests -v
```

## Ce que ce n'est pas

C'est un durcissement de code source par des agents, qui s'améliore tour après tour. Ce
n'est pas un test d'intrusion complet ni une garantie d'absence de faille. La logique
métier, l'infrastructure, la configuration déployée, le fournisseur d'authentification et
les services tiers demandent encore une vérification humaine et des tests en conditions
réelles. « Plus de faille trouvée » veut dire que ces agents ne trouvent plus rien, pas
que le code est invulnérable. Le rapport le dit clairement.

## Fichiers

| fichier | rôle |
|---|---|
| `SKILL.md` | les étapes que suit Claude Code |
| `purple.py` | le moteur qui gère la boucle (Python, bibliothèque standard) |
| `templates.md` | les consignes données à chaque rôle |
| `angles.json` | les angles d'attaque des agents rouges |
| `rubric.md` | la grille de gravité et de confirmation |
| `tests/` | les tests |

## Licence

MIT, voir [LICENSE](../LICENSE).
