"""Tests for suivi.py. Run from the Gomme folder: python3 -m unittest discover -s tests -v"""
import datetime as dt
import io
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import suivi  # noqa: E402


class SuiviTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.f = os.path.join(self.tmp, "suivi.csv")

    def run_cmd(self, *args):
        buf = io.StringIO()
        with redirect_stdout(buf):
            suivi.main(["--fichier", self.f, *args])
        return buf.getvalue()

    def test_add_send_deadline_one_month(self):
        self.run_cmd("add", "--site", "Annuaire", "--url", "https://ex.test/p", "--donnees", "adresse",
                     "--demarche", "suppression")
        out = self.run_cmd("envoyee", "1", "--date", "2026-01-31")
        self.assertIn("2026-02-28", out)  # end-of-month clamp

    def test_extension_adds_two_months(self):
        self.run_cmd("add", "--site", "S", "--url", "u", "--donnees", "d", "--demarche", "suppression")
        self.run_cmd("envoyee", "1", "--date", "2026-10-16")
        out = self.run_cmd("prolongation", "1")
        self.assertIn("2027-01-16", out)

    def test_overdue_listed(self):
        self.run_cmd("add", "--site", "Vieux", "--url", "u", "--donnees", "d", "--demarche", "dereferencement")
        self.run_cmd("envoyee", "1", "--date", "2026-01-01")
        rows = suivi.load(self.f)
        buf = io.StringIO()
        with redirect_stdout(buf):
            late, soon = suivi.cmd_echeances(None, rows, today=dt.date(2026, 3, 1))
        self.assertEqual(len(late), 1)
        self.assertIn("CNIL", buf.getvalue())

    def test_answered_requests_are_not_due(self):
        self.run_cmd("add", "--site", "S", "--url", "u", "--donnees", "d", "--demarche", "suppression")
        self.run_cmd("envoyee", "1", "--date", "2026-01-01")
        self.run_cmd("reponse", "1", "--statut", "supprime", "--date", "2026-01-10")
        late, soon = suivi.cmd_echeances(None, suivi.load(self.f), today=dt.date(2026, 6, 1))
        self.assertEqual(late, [])

    def test_ids_increment(self):
        for _ in range(3):
            self.run_cmd("add", "--site", "S", "--url", "u", "--donnees", "d", "--demarche", "compte")
        self.assertEqual([r["id"] for r in suivi.load(self.f)], ["1", "2", "3"])


if __name__ == "__main__":
    unittest.main()
