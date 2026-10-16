# Rouage

Skill pour Claude Code qui explique comment marche une application en lisant son code ou
son build. Tu poses une question précise (comment le jeu choisit la prochaine tuile, où
le score est enregistré, ce qui se passe quand on clique sur Rechercher), elle répond avec
les lignes de code qui le prouvent, puis résume en quelques phrases simples.

Pour les builds, les bundles JavaScript, les applis Electron, le .NET ou les binaires
natifs, elle utilise REA, un outil libre (licence MIT), s'il est installé. Pour du code
source ordinaire, elle lit directement les fichiers.

## Pour quels logiciels

Uniquement tes propres logiciels, du code open source, ou un logiciel que tu as le droit
d'examiner (l'appli d'un client avec son accord, un exercice de cours). Pas de
contournement de licence, d'activation, de protection anticopie ou d'anti-triche, pas de
copie piratée. La skill pose ce cadre au début, et propose une version légitime si une
demande en sort.

L'analyse se fait sur ta machine. L'analyse statique lit les fichiers sans lancer le
programme.

## Ce que tu obtiens

- Des réponses avec la preuve : le fichier, la fonction et les lignes qui décident.
- Ce qu'elle n'a pas pu voir (noms minifiés, logique côté serveur), dit clairement.
- Un résumé en langage simple.
- En option, une version à toi de la fonctionnalité, écrite à neuf dans ton projet, avec
  une amélioration de ton choix.

## Installer REA (pour les builds et binaires)

```bash
node --version                 # 22.19 ou plus récent
npx rea-agents setup           # coche Claude Code avec la barre d'espace, puis Entrée
```

Redémarre Claude Code, puis vérifie que REA apparaît avec `/mcp`. Pour les binaires
natifs, il faut aussi Ghidra (gratuit) ou un outil comme IDA ou Hopper, installé avec une
licence valide.

## Installer la skill

```bash
git clone https://github.com/adambrai/Claude_Skills.git
mkdir -p ~/.claude/skills/rouage
cp Claude_Skills/Rouage/SKILL.md ~/.claude/skills/rouage/
```

## Utilisation

```
/rouage ~/jeux/2048 comment le jeu choisit la valeur et la place des nouvelles tuiles ?
/rouage ./mon-appli où et comment la recherche filtre les résultats ?
```

## Licence

MIT, voir [LICENSE](../LICENSE).
