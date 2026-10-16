# Rabot

Skill pour Claude Code qui relit un texte et enlève ce qui l'alourdit : formules toutes
faites, tirets à rallonge, gras partout, puces en émoji, précautions inutiles,
paragraphes tous de la même taille. Le sens, les faits et ton ton restent les mêmes.

Elle sert pour un README, un post, un mail, un rapport, ou le texte d'un site avant de
le publier.

## Le vérificateur

La skill vient avec `slopcheck.py`, un petit script qui donne une note sur 100 à un
texte (100 = rien à signaler) et liste chaque tic avec sa ligne. Il marche en français et
en anglais, ignore les blocs de code, et ne demande aucune dépendance.

```bash
python3 slopcheck.py mon-texte.md
python3 slopcheck.py --json README.md
cat brouillon.txt | python3 slopcheck.py -
python3 slopcheck.py --min 80 docs/*.md     # code de sortie 1 si un fichier est sous 80
```

L'option `--min` permet de l'utiliser dans une CI ou un hook de commit.

## Utilisation

```
/rabot mon-texte.md
/rabot <colle ton texte>
/rabot site ./mon-site
```

En mode texte, la skill note le texte, le réécrit, le note à nouveau et te montre la
nouvelle version avec les deux scores. Elle ne modifie le fichier que si tu le demandes.

En mode site, elle passe en revue un projet de site avant sa mise en ligne : le texte des
pages, les choix visuels faits par défaut, les éléments de base (favicon, titres et
descriptions, page 404, mentions légales réelles, version mobile à 375 px, bannière de
cookies avec un vrai refus) et les points de sécurité de base. Elle liste ce qui manque
avec le fichier à changer, et ne touche à rien sans ton accord.

## Ce que ce n'est pas

C'est un outil de relecture. Il ne sert pas à cacher qu'une IA a aidé à écrire un texte :
si ton école, ton client ou ton journal demande de le dire, c'est à toi de le faire.

## Installation

```bash
git clone https://github.com/adambrai/Claud_Skills.git
mkdir -p ~/.claude/skills/rabot
cp Claud_Skills/Rabot/{SKILL.md,slopcheck.py} ~/.claude/skills/rabot/
```

## Tests

```bash
cd Rabot && python3 -m unittest discover -s tests -v
```

## Licence

MIT, voir [LICENSE](../LICENSE).
