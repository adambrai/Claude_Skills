# Douane

Skill pour Claude Code qui inspecte une skill trouvée ailleurs (sur GitHub, dans un
zip, envoyée par quelqu'un) avant que tu l'installes. Une skill peut contenir des
scripts et des consignes que l'agent suivra sur ta machine : ça vaut la peine de les
lire avant.

La règle de base : elle lit les fichiers, elle ne les exécute jamais.

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

Le script marche aussi seul :

```bash
python3 -I audit_skill.py ~/Downloads/une-skill
python3 -I audit_skill.py ~/Downloads/une-skill --json
```

Le code de sortie vaut 1 s'il y a au moins un point élevé, ce qui permet de l'utiliser
dans un script.

Si tu lances Douane sur son propre dossier, elle relève beaucoup de points : ses fichiers
contiennent justement les motifs qu'elle cherche.

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
