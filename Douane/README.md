# Douane

Skill pour Claude Code qui inspecte une skill trouvée ailleurs (sur GitHub, dans un
zip, envoyée par quelqu'un) avant que tu l'installes. Une skill peut contenir des
scripts et des consignes que l'agent suivra sur ta machine : ça vaut la peine de les
lire avant.

La règle de base : elle lit les fichiers, elle ne les exécute jamais.

Elle sert aussi de guichet pour tout le cycle de vie d'une skill : chercher, contrôler,
installer, lister, mettre à jour, supprimer, créer, et vérifier qu'un dépôt s'installe
avec `npx skills`. Le contrôle passe toujours avant l'installation ou la mise à jour.

## Ce qu'elle signale

Le script `audit_skill.py` passe sur chaque fichier et relève :

- les scripts et les fichiers exécutables, et les binaires (impossibles à relire) ;
- les commandes qui téléchargent du code puis le lancent (`curl … | sh`, `iwr … | iex`,
  `exec(urlopen(…))`, etc.), et les installations de paquets depuis une URL ;
- la lecture de fichiers d'identifiants : clés SSH, `~/.aws/credentials`, `.netrc`,
  `.npmrc`, trousseau macOS, données de navigateur, `.env`, variables de clés d'API ;
- les consignes qui demandent à l'agent d'agir sans te demander, de te cacher quelque
  chose ou d'ignorer ses consignes précédentes, en anglais et en français ;
- les caractères Unicode cachés (espaces de largeur nulle, contrôles de direction,
  caractères « tag ») qui peuvent dissimuler du texte ;
- les longs blocs encodés en base64 ou en hexadécimal ;
- les permissions d'outils trop larges dans `allowed-tools` ou un `settings.json` (tout
  le shell, tous les outils, `bypassPermissions`), et les hooks lancés automatiquement ;
- les commandes destructrices et les liens symboliques qui pointent hors du dossier.

Chaque point a un niveau (élevé, moyen, faible, info), avec le fichier et la ligne.

Un point relevé n'est pas une preuve : une skill de déploiement a de bonnes raisons
d'appeler `curl`. C'est pour ça que la skill relit ensuite chaque ligne signalée et te
donne son avis : attendu, suspect ou dangereux. Elle termine par un verdict (installer,
installer après une modification, ne pas installer). Elle n'installe rien sans que tu
le demandes.

## Utilisation

```
/douane ~/Downloads/une-skill
/douane https://github.com/quelquun/sa-skill
```

Les autres demandes se font en langage courant, par exemple : « cherche une skill pour
les tableaux », « installe-la en global », « liste mes skills », « mets à jour celles du
projet », « supprime telle skill », « crée une skill qui fait ceci », « vérifie que mon
dépôt s'installe avec npx skills ».

Le script marche aussi seul :

```bash
python3 -I audit_skill.py ~/Downloads/une-skill
python3 -I audit_skill.py ~/Downloads/une-skill --json
```

Le code de sortie vaut 1 s'il y a au moins un point élevé, ce qui permet de l'utiliser
dans un script.

Pour vérifier qu'un dépôt s'installe avec `npx skills` :

```bash
python3 -I audit_skill.py ~/mon-depot --check-install
python3 -I audit_skill.py ~/mon-depot --check-install --full-depth --json
```

Le code de sortie vaut 0 si le dépôt est installable, 1 s'il y a au moins une erreur,
2 si le dossier est introuvable. Voir plus bas ce qui est vérifié.

Si tu lances Douane sur son propre dossier, elle relève beaucoup de points : ses fichiers
contiennent justement les motifs qu'elle cherche.

## Chercher une skill

`npx skills find` ouvre une recherche interactive ; avec un mot-clé, il cherche par
sujet, et on peut se limiter à un propriétaire GitHub. Les skills sont aussi
consultables sur le site skills.sh. Un résultat de recherche n'est qu'un nom et une
adresse : rien n'est installé, et il faut encore passer par le contrôle.

## Sources acceptées

Douane récupère la skill dans un dossier temporaire vide, sans rien lancer :

- un dépôt GitHub, en forme courte (`proprietaire/depot`) ou en URL, y compris l'adresse
  d'un seul dossier de skill dans le dépôt ;
- GitLab, Azure Repos ou n'importe quelle URL Git ;
- un dossier local ;
- l'adresse directe d'un `SKILL.md` ou d'une archive (`.zip`, `.tar`, `.tgz`).

Pour une archive, les limites par défaut sont 10 Mio de téléchargement, 25 Mio une fois
extraite et 1000 fichiers. Les dépôts privés passent par les accès que tu as déjà
(`git`, `gh`, ssh) : Douane ne demande jamais de jeton.

## Installer

Après un verdict favorable, et seulement si tu le demandes. Deux voies :

- `npx skills add`, avec la télémétrie coupée (`DISABLE_TELEMETRY=1 DO_NOT_TRACK=1`).
  Douane installe depuis la copie qu'elle a relue, pas depuis la source distante, pour que
  ce qui arrive soit exactement ce qui a été lu.
- une copie à la main dans `~/.claude/skills/<nom>/`.

Options utiles de `add` :

| option | effet |
|---|---|
| `-g` | installation globale (`~/<agent>/skills/`) ; par défaut, c'est dans le projet (`./<agent>/skills/`) |
| `-a` | choisir les agents visés (Claude Code, Codex, Cursor, Gemini CLI, Copilot, Windsurf et d'autres, détectés automatiquement) |
| `-s` | n'installer que certaines skills d'un dépôt qui en contient plusieurs |
| `-l` | lister les skills du dépôt sans rien installer |
| `--copy` | copier les fichiers au lieu de faire des liens |
| `-y` | ne poser aucune question, à réserver au cas où tu as vu le rapport et la commande |
| `--all` | toutes les skills pour tous les agents |

En mode interactif, l'outil peut garder une seule copie de référence et la relier par des
liens symboliques à chaque agent (c'est le choix conseillé), ou copier. Les options
`allowed-tools`, `context: fork` et les hooks ne sont pas gérées de la même façon par
tous les agents : une skill peut donc faire moins, ou autre chose, ailleurs que dans Claude
Code.

`npx skills use` génère un prompt à partir d'une skill sans l'installer. Ce prompt reprend
le texte de la skill : le contrôle reste utile.

Une skill marquée `metadata.internal: true` est masquée, sauf si la variable
`INSTALL_INTERNAL_SKILLS=1` est définie.

## Lister, mettre à jour, supprimer

- `npx skills list` (ou `ls`) montre ce qui est installé, avec `-g` pour le global.
- Une mise à jour remplace des fichiers relus par des fichiers qui ne l'ont pas été. Douane
  récupère donc la nouvelle version à part, la compare à l'ancienne (`diff`), relance le
  contrôle sur ce qui a changé (nouveaux scripts, nouvelles permissions, nouveaux hooks)
  et ne met à jour (`npx skills update`, avec ou sans `-g`) qu'après ton accord, skill par
  skill.
- `npx skills remove` (ou `rm`) supprime : Douane te montre le dossier et attend ton oui.

## Créer une skill

`npx skills init <nom>` écrit un modèle de `SKILL.md`. Il faut au minimum un en-tête YAML
en tête de fichier, entre deux lignes `---`, avec :

- `name` : minuscules, chiffres et tirets, identique au nom du dossier ;
- `description` : ce que fait la skill et quand l'utiliser, car c'est ce texte qui décide
  de son déclenchement.

Douane relit ensuite la skill créée comme n'importe quelle autre.

## Vérifier qu'un dépôt s'installe

Avec `--check-install`, le script cherche les skills là où l'outil les cherche :

1. `SKILL.md` à la racine ;
2. `skills/`, `skills/.curated/` et les dossiers propres à chaque agent, jusqu'à 3
   niveaux de profondeur ;
3. les fichiers `.claude-plugin/marketplace.json` ou `plugin.json`, dont les chemins
   doivent rester dans le dépôt ;
4. à défaut, une recherche récursive ; `--full-depth` la fait sur tous les niveaux même
   si quelque chose a été trouvé.

Pour chaque skill, il contrôle l'en-tête YAML, `name`, `description`, la présence de
`metadata.internal` et les noms en double. Il ne lance rien.

## Télémétrie

`npx skills` envoie des statistiques anonymes. Douane les coupe à chaque appel avec
`DISABLE_TELEMETRY=1` (ou `DO_NOT_TRACK=1`). Note aussi que `npx` télécharge et lance
l'outil lui-même, qui est un programme tiers, à ne pas confondre avec la skill contrôlée.

## Installation

```bash
git clone https://github.com/adambrai/Claude_Skills.git
mkdir -p ~/.claude/skills/douane
cp Claude_Skills/Douane/{SKILL.md,audit_skill.py} ~/.claude/skills/douane/
```

## Tests

```bash
cd Douane && python3 -m unittest discover -s tests -v
```

## Licence

MIT, voir [LICENSE](../LICENSE).
