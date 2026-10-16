"""Tests for slopcheck.py. Run from the Rabot folder:
python3 -m unittest discover -s tests -v
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import slopcheck  # noqa: E402

FORMULAIC = """Excellente question ! Plongeons dans le sujet.

## 🚀 Pourquoi c'est important

Dans un monde où tout va vite, l'outil n'est pas seulement pratique, mais un **véritable levier**. Il est important de noter que cette solution **robuste** va **révolutionner** ton travail — sans effort.

- ✅ **Rapide**, **simple** et **efficace**
- ✅ Un atout majeur
- ✅ Potentiellement utile

En conclusion, n'hésitez pas à booster votre productivité. J'espère que cela vous aide !
"""

PLAIN = """J'ai testé la fonction sur trois cas qui posaient problème : un nom avec un accent, une chaîne vide et un titre trop long.

Les deux premiers passent. Le troisième coupe encore au milieu d'un mot. J'ai ajouté un test pour ce cas et je corrige demain.
"""


class SlopcheckTests(unittest.TestCase):
    def kinds(self, text):
        return {f["kind"] for f in slopcheck.analyse(text)["findings"]}

    def test_formulaic_scores_low(self):
        r = slopcheck.analyse(FORMULAIC)
        self.assertLess(r["score"], 40)
        for k in ("marker", "contrast", "opener", "emoji", "bold", "dash", "hedge"):
            self.assertIn(k, self.kinds(FORMULAIC), k)

    def test_plain_scores_high(self):
        self.assertGreaterEqual(slopcheck.analyse(PLAIN)["score"], 95)

    def test_code_blocks_are_ignored(self):
        text = "Voici le code :\n\n```python\n# robuste, révolutionner, en conclusion — delve\nx = 1\n```\n"
        self.assertNotIn("marker", self.kinds(text))

    def test_english_markers(self):
        self.assertIn("marker", self.kinds("We will delve into the landscape of tools. I hope this helps."))

    def test_line_numbers(self):
        r = slopcheck.analyse("ligne simple\nEn conclusion, voilà.\n")
        self.assertTrue(any(f["line"] == 2 for f in r["findings"]))

    def test_cli_exit_code_with_min(self):
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write(FORMULAIC)
        try:
            self.assertEqual(slopcheck.main([f.name, "--min", "80"]), 1)
            self.assertEqual(slopcheck.main([f.name, "--min", "0"]), 0)
        finally:
            os.unlink(f.name)


    # --- checks added later ---

    def test_french_dash_flagged_strictly(self):
        self.assertIn("dash", self.kinds("Le fichier est prêt—il manque le test pour la suite de ce travail."))
        self.assertIn("dash", self.kinds("Le fichier est prêt et il manque le test pour la suite. Voilà —\nfin de la phrase."))

    def test_french_dialogue_dash_at_line_start_is_left_alone(self):
        self.assertNotIn("dash", self.kinds("— Tu viens avec nous ce soir, dans la salle ?\n— Oui, je viens avec vous."))

    def test_french_dash_weighs_more_than_english(self):
        fr = slopcheck.analyse("Le test est écrit — et il passe sur la machine de Paul pour une fois.")
        en = slopcheck.analyse("The test is written \u2014 and it passes on the machine that Paul has for once.")
        self.assertLess(fr["score"], en["score"])

    def test_restating_question_openers(self):
        for t in ("Tu veux savoir comment lancer les tests ? Lance la commande.",
                  "Votre question porte sur le déploiement. Voici la réponse.",
                  "You want to know how to run the tests. Run the command.",
                  "Pour répondre à ta question, il faut lire le fichier.",
                  "Voici un aperçu des options disponibles."):
            self.assertIn("opener", self.kinds(t), t)

    def test_opener_skips_leading_heading_and_reports_line(self):
        r = slopcheck.analyse("# Titre\n\nBonne question ! Voici.\n")
        self.assertEqual([f["line"] for f in r["findings"] if f["kind"] == "opener"], [3])

    def test_plain_opener_is_not_flagged(self):
        self.assertNotIn("opener", self.kinds("Lance `make test`. Les trois cas passent."))

    def test_new_marker_words(self):
        self.assertIn("marker", self.kinds("Explorons ensemble le sujet du jour."))
        self.assertIn("marker", self.kinds("Le paysage des outils change vite."))

    def test_new_hedges(self):
        self.assertIn("hedge", self.kinds("Cela pourrait potentiellement casser le build."))
        self.assertIn("hedge", self.kinds("Il semblerait que le test échoue."))

    def test_curly_quotes_in_plain_english_flagged(self):
        t = "He said \u201cstop\u201d and left. It\u2019s done, and we do not need more."
        self.assertIn("curly", self.kinds(t))

    def test_curly_quotes_ignored_in_french(self):
        t = "Il a dit « stop » et il est parti. C\u2019est fini pour aujourd\u2019hui, et nous avons fini."
        self.assertNotIn("curly", self.kinds(t))

    def test_curly_quotes_ignored_when_text_has_other_typography(self):
        t = "He said \u201cstop\u201d and left\u2026 It\u2019s done, and we have a caf\u00e9 near the park."
        self.assertNotIn("curly", self.kinds(t))

    def test_straight_quotes_not_flagged(self):
        self.assertNotIn("curly", self.kinds('He said "stop" and left. It\'s done, and we have time.'))

    def test_language_detection(self):
        self.assertEqual(slopcheck.detect_lang("Le chat est sur la table et il dort."), "fr")
        self.assertEqual(slopcheck.detect_lang("The cat is on the table and it sleeps."), "en")

    def test_suggestions_for_every_kind(self):
        for kind in slopcheck.KIND_FIX:
            self.assertTrue(slopcheck.suggest({"kind": kind, "match": "x"}))
        self.assertIn("solide", slopcheck.suggest({"kind": "marker", "match": "robuste"}))

    def run_cli(self, *extra):
        import contextlib, io, tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write(FORMULAIC)
        try:
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                slopcheck.main([f.name, *extra])
            return buf.getvalue()
        finally:
            os.unlink(f.name)

    def test_cli_fix_suggestions_output(self):
        self.assertIn("->", self.run_cli("--fix-suggestions"))
        self.assertNotIn("->", self.run_cli())
        self.assertIn('"suggestion"', self.run_cli("--json", "--fix-suggestions"))

    def test_five_families_are_noticeable(self):
        r = slopcheck.analyse(FORMULAIC)
        self.assertTrue(r["noticeable"])
        self.assertGreaterEqual(len(r["families"]), 5)
        self.assertFalse(slopcheck.analyse(PLAIN)["noticeable"])
        self.assertIn("lecteur averti", self.run_cli())


if __name__ == "__main__":
    unittest.main()
