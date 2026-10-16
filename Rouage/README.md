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

Le programme d'installation propose une liste d'outils : place-toi sur Claude Code, appuie
sur Espace pour le cocher, puis sur Entrée. Entrée seule n'installe rien pour Claude Code.
Il ajoute REA comme serveur MCP avec ses instructions, sauvegarde ta configuration et
montre les changements avant de les appliquer.

Redémarre Claude Code (dans VS Code : « Developer: Reload Window »), puis vérifie que REA
apparaît avec `/mcp`. Pour contrôler que tout est prêt :

```bash
npx rea-agents@latest doctor
```

Cette commande lit ta machine et ta configuration sans rien modifier. Un résultat
« non sain » en général ne bloque pas l'analyse JavaScript.

Ce qu'il faut selon la cible :

- JavaScript, applis web, Electron, .NET : rien de plus.
- Binaires natifs (.exe) : Ghidra (gratuit, avec la variable `GHIDRA_INSTALL_DIR` qui
  pointe vers son dossier) ou IDA, installé avec une licence valide. Hopper existe
  seulement sous macOS et Linux.
- Les outils de capture réseau et de comportement d'un processus ne marchent que sous
  Linux et macOS. L'analyse de JavaScript marche partout.

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

## Exemple pas à pas : le jeu 2048

1. Télécharge le dépôt officiel du jeu 2048 (code libre) et ouvre Claude Code dans le
   dossier.
2. Demande : « Analyse ce jeu avec REA et donne le code exact comme preuve pour trois
   questions : comment la valeur d'une nouvelle tuile (2 ou 4) est choisie et avec quelles
   chances ; où elle apparaît et si le placement est déjà choisi pour gêner le joueur ; où
   sont enregistrés le meilleur score et la partie en cours. »
3. Termine par : « Résume en cinq lignes pour quelqu'un qui ne programme pas. »

Ce que tu dois retrouver : la fonction `addRandomTile` tire `Math.random() < 0.9 ? 2 : 4`,
soit 90 % de 2 et 10 % de 4. `randomAvailableCell` prend une case vide au hasard, donc le
placement ne cherche jamais à te piéger. Les scores sont gardés dans le `localStorage` du
navigateur. Si le code que tu as sous les yeux dit autre chose, c'est lui qui a raison.

### Sans le serveur MCP

Pour une appli JavaScript ou Electron, tu peux lancer l'analyse à la main et garder le
résultat dans un fichier :

```bash
npx -y rea-agents@latest analyze-javascript-application "/chemin/vers/appli" --json > evidence.json
```

Le résultat peut peser plusieurs centaines de Mo : enregistre-le toujours dans un fichier
au lieu de l'afficher, puis demande à Claude de le lire par morceaux.

## Et ensuite

- Refaire le jeu en un seul fichier, avec ton propre design et un bouton « annuler ».
- Étudier le jeu du dinosaure de Chrome (code libre dans Chromium) : comment la vitesse
  augmente, à partir de quand les oiseaux arrivent.
- Prendre la recherche de ta propre appli, comprendre son fonctionnement preuves à
  l'appui, puis construire une fonction du même genre.
- Regarder un site web, seulement si c'est le tien ou celui d'un client qui t'a donné son
  accord. La commande de REA pour les bundles web est `analyze-web-bundle` (voir son
  `--help`). Jamais sur un site que tu n'as pas le droit d'examiner.

## Format des réponses

Pour chaque question : la réponse en une phrase, le fichier et la fonction avec les lignes
citées, l'explication pas à pas, le niveau de certitude, puis une liste « Inconnues » avec
ce qui n'a pas pu être vu (code minifié, partie serveur, fichier de configuration absent)
et où regarder ensuite.

## En cas de problème

| Problème | Solution |
|---|---|
| Node trop ancien (moins de 22.19) | Installe la dernière version de Node.js |
| REA n'apparaît pas dans `/mcp` | Redémarre Claude Code, lance `npx rea-agents@latest doctor`, refais l'installation en cochant bien Claude Code |
| `capability_unavailable` sur un .exe | Installe Ghidra ou IDA, puis vérifie avec `doctor` |
| Capture réseau ou processus indisponible | Ces outils n'existent que sous Linux et macOS |
| Résultat énorme | Enregistre-le dans un fichier avec `--json > fichier` |

## Licence

MIT, voir [LICENSE](../LICENSE).
