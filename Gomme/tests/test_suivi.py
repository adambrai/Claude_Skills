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

    @staticmethod
    def read(path):
        with open(path, encoding="utf-8") as fh:
            return fh.read()

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

    def make_sent(self, date="2026-01-01"):
        self.run_cmd("add", "--site", "Annuaire", "--url", "https://ex.test/p", "--donnees", "adresse postale",
                     "--demarche", "suppression")
        self.run_cmd("envoyee", "1", "--date", date, "--preuve", "accusé n°1")

    def test_verifie_records_source_and_search_separately(self):
        self.make_sent()
        self.run_cmd("reponse", "1", "--statut", "supprime")
        out = self.run_cmd("verifie", "1", "--source", "disparu", "--recherche", "visible", "--date", "2026-02-02")
        row = suivi.load(self.f)[0]
        self.assertEqual((row["verif_source"], row["verif_recherche"], row["date_verif"]),
                         ("disparu", "visible", "2026-02-02"))
        self.assertIn("visible", out)

    def test_verifie_needs_something(self):
        self.make_sent()
        with self.assertRaises(SystemExit):
            self.run_cmd("verifie", "1")

    def test_modele_and_relance_are_drafts_only(self):
        self.make_sent()
        before = self.read(self.f)
        letter = self.run_cmd("modele", "1")
        self.assertIn("Demande d'effacement de données personnelles", letter)
        self.assertIn("article 17", letter)
        self.assertIn("adresse postale", letter)
        self.assertIn("rien n'a été envoyé", letter)
        rel = self.run_cmd("relance", "1")
        self.assertIn("2026-02-01", rel)
        self.assertIn("CNIL", rel)
        self.assertEqual(before, self.read(self.f))

    def test_resume_counts_states(self):
        self.make_sent()
        self.run_cmd("add", "--site", "B", "--url", "u", "--donnees", "d", "--demarche", "compte")
        out = self.run_cmd("resume")
        self.assertIn("brouillon", out)
        self.assertIn("envoyee", out)

    def test_export_markdown_and_csv(self):
        self.make_sent()
        md = self.run_cmd("export")
        self.assertIn("| site |", md)
        self.assertIn("Annuaire", md)
        self.assertIn("2026-02-01", md)
        out_file = os.path.join(self.tmp, "t.csv")
        self.run_cmd("export", "--format", "csv", "--sortie", out_file)
        self.assertIn("verif_source", self.read(out_file))

    def test_old_csv_without_new_columns_still_loads(self):
        old = ("id,site,url,donnees,demarche,statut,date_envoi,preuve,prolongation,echeance,"
               "date_reponse,notes\n1,S,u,d,suppression,envoyee,2026-01-01,p,non,,,\n")
        with open(self.f, "w", encoding="utf-8") as fh:
            fh.write(old)
        self.run_cmd("verifie", "1", "--source", "en_ligne")
        self.assertEqual(suivi.load(self.f)[0]["verif_source"], "en_ligne")

    def test_new_demarches_accepted(self):
        for d in ("desabonnement", "parametre"):
            self.run_cmd("add", "--site", "S", "--url", "u", "--donnees", "d", "--demarche", d)
        self.assertEqual(len(suivi.load(self.f)), 2)


if __name__ == "__main__":
    unittest.main()
