# Vitrine

Skill pour Claude Code qui conçoit ou refait une interface web en cinq étapes. Chaque
étape est finie et montrée avant de passer à la suivante, pour que tu puisses corriger
la direction tôt plutôt que de découvrir une page entière qui ne te plaît pas.

## Les cinq étapes

1. **Direction** : à qui s'adresse la page, ce qu'on doit y trouver tout de suite,
   l'action principale, le ton. Si le projet a déjà une source de design (`DESIGN.md`,
   un fichier de tokens, le thème CSS ou Tailwind, une charte), c'est elle qui décide.
   Sinon, la skill propose une palette, deux polices, des espacements et une idée
   propre au produit.
2. **Référence visuelle** : une maquette HTML statique de l'écran principal, avec le
   vrai texte, vue en largeur bureau et à 375 px. Tu la valides avant qu'une ligne du
   vrai code ne change.
3. **Implémentation** : les tokens d'abord, puis les composants, dans la pile déjà en
   place. Tous les états sont prévus (survol, focus, chargement, erreur, vide).
4. **Vérification dans un navigateur** : captures en 1440 px et en 375 px, lecture de
   la console, corrections, nouvelles captures. Elle utilise Playwright CLI s'il est
   installé, sinon les outils de navigateur de la session. Si aucun navigateur n'est
   disponible, elle le dit au lieu de faire comme si.
5. **Audit** : clavier, focus visible, contraste calculé, taille des cibles tactiles,
   formulaires, animations, et les bases avant la mise en ligne (titre, description,
   favicon, page 404, mentions légales, bannière de cookies).

À la fin, tu as la liste des fichiers modifiés, les deux captures et un tableau d'audit
avec ce qui reste à faire.

## Utilisation

```
/vitrine page d'accueil d'une appli de covoiturage pour étudiants
/vitrine redesign src/pages/tarifs.tsx
/vitrine audit http://localhost:3000
```

Le mode `audit` ne fait que les étapes 4 et 5 sur une page qui existe déjà.

## Installation

```bash
git clone https://github.com/adambrai/Claude_Skills.git
mkdir -p ~/.claude/skills/vitrine
cp Claude_Skills/Vitrine/SKILL.md ~/.claude/skills/vitrine/
```

Pour les captures en ligne de commande, Playwright est optionnel :

```bash
npm install -D playwright && npx playwright install chromium
```

## Licence

MIT, voir [LICENSE](../LICENSE).
