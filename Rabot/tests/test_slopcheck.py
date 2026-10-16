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


if __name__ == "__main__":
    unittest.main()
