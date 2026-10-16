<!-- fourmi:start -->
## Économie de contexte

### Choix du modèle (alias : ils suivent toujours la dernière version)
- `haiku` : recherches rapides, inventaires de fichiers, résumés, vérification de liens.
- `sonnet` : modifications simples, tests, documentation, SEO technique, accessibilité, commits.
- `opus` : implémentation complexe, changements sur plusieurs fichiers, refactors, bugs difficiles, architecture, revue finale.
- Niveau au-dessus d'opus (architecture, stratégie ambiguë, bug très difficile, revue finale) : seulement si on me le demande, car il peut être facturé en crédits supplémentaires. Sinon, opus s'en charge.
- Toujours passer le paramètre `model` quand je lance un sous-agent, sans exception.
- En cas de doute entre deux niveaux, prendre le moins cher, puis monter si le résultat est faible.

### Sous-agents
- Seulement pour isoler un travail qui produirait beaucoup de lecture, ou pour des tâches vraiment indépendantes en parallèle.
- Je travaille directement pour : une modification simple, des étapes qui se suivent, une tâche qui demande un seul contexte partagé.
- Je fais le plan avant de déléguer, et je garde le plan, les décisions et l'intégration.
- Jamais deux sous-agents sur les mêmes fichiers en même temps.
- Un sous-agent rend un résumé court de ce qu'il a fait en isolation, pas tout ce qu'il a lu, et son résumé ne remplace pas le matériau essentiel.
- Si une décision dépend d'un fichier source, je le relis moi-même (la partie utile) avant de trancher.

### Lecture
- Chercher avant de lire : Grep/Glob d'abord, puis seulement les lignes utiles d'un fichier.
- Ne pas relire un fichier déjà lu dans la conversation sauf s'il a changé.
- Sorties de commandes longues : filtrer (`| tail`, `| grep`) au lieu de tout afficher.
- Une seule validation de direction au début d'un gros travail, pas une par étape.
<!-- fourmi:end -->
