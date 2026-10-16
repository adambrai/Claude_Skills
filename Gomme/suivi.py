#!/usr/bin/env python3
"""suivi.py — tracker for personal-data removal requests (EU / GDPR).

Keeps a CSV file (default: ./gomme/suivi.csv) with one row per request and
computes the legal answer deadline: one month after sending, extended by two
more months if the organisation announced an extension.

Usage:
  python3 suivi.py add --site "Exemple" --url URL --donnees "adresse, téléphone" --demarche suppression
  python3 suivi.py envoyee ID --date 2026-10-16 --preuve "accusé de réception n°123"
  python3 suivi.py prolongation ID
  python3 suivi.py reponse ID --statut supprime|refus|partiel --date 2026-11-02 [--notes "..."]
  python3 suivi.py liste
  python3 suivi.py echeances          # what is due or overdue today

The file never stores the personal data itself: describe it ("adresse postale"),
do not paste it. Standard library only.
"""
import argparse
import calendar
import csv
import datetime as dt
import os
import sys

FIELDS = ["id", "site", "url", "donnees", "demarche", "statut", "date_envoi", "preuve",
          "prolongation", "echeance", "date_reponse", "notes"]
DEMARCHES = ("suppression", "dereferencement", "compte", "acces", "opposition")
STATUTS = ("brouillon", "envoyee", "supprime", "partiel", "refus", "sans_reponse")


def add_months(d, n):
    m = d.month - 1 + n
    y = d.year + m // 12
    m = m % 12 + 1
    return dt.date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


def parse_date(s):
    return dt.date.fromisoformat(s) if s else None


def deadline(row):
    sent = parse_date(row.get("date_envoi"))
    if not sent:
        return ""
    months = 3 if row.get("prolongation") == "oui" else 1
    return add_months(sent, months).isoformat()


def load(path):
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save(path, rows):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for r in rows:
            r["echeance"] = deadline(r)
            w.writerow({k: r.get(k, "") for k in FIELDS})


def find(rows, rid):
    for r in rows:
        if r["id"] == str(rid):
            return r
    sys.exit(f"demande {rid} introuvable")


def cmd_add(a, rows):
    rid = str(max([int(r["id"]) for r in rows] or [0]) + 1)
    rows.append({"id": rid, "site": a.site, "url": a.url, "donnees": a.donnees,
                 "demarche": a.demarche, "statut": "brouillon", "prolongation": "non", "notes": a.notes or ""})
    print(f"demande {rid} ajoutée (brouillon)")


def cmd_envoyee(a, rows):
    r = find(rows, a.id)
    r.update(statut="envoyee", date_envoi=a.date or dt.date.today().isoformat(), preuve=a.preuve or "")
    print(f"demande {a.id} marquée envoyée le {r['date_envoi']}, réponse attendue avant le {deadline(r)}")


def cmd_prolongation(a, rows):
    r = find(rows, a.id)
    r["prolongation"] = "oui"
    print(f"demande {a.id} : délai prolongé, nouvelle échéance {deadline(r)}")


def cmd_reponse(a, rows):
    r = find(rows, a.id)
    r.update(statut=a.statut, date_reponse=a.date or dt.date.today().isoformat())
    if a.notes:
        r["notes"] = (r.get("notes", "") + " | " + a.notes).strip(" |")
    print(f"demande {a.id} : {a.statut}")


def cmd_liste(a, rows):
    if not rows:
        print("aucune demande")
        return
    for r in rows:
        print(f"[{r['id']}] {r['site']:<20} {r['demarche']:<16} {r['statut']:<12} "
              f"envoi {r.get('date_envoi') or '-':<10} échéance {deadline(r) or '-'}")


def cmd_echeances(a, rows, today=None):
    today = today or dt.date.today()
    late, soon = [], []
    for r in rows:
        if r["statut"] != "envoyee" or not r.get("date_envoi"):
            continue
        d = parse_date(deadline(r))
        if d < today:
            late.append((r, d))
        elif (d - today).days <= 7:
            soon.append((r, d))
    for r, d in late:
        print(f"EN RETARD [{r['id']}] {r['site']} : échéance dépassée depuis le {d}. "
              "Relance l'organisme ; sans réponse, tu peux saisir la CNIL avec tes preuves.")
    for r, d in soon:
        print(f"BIENTÔT [{r['id']}] {r['site']} : réponse attendue avant le {d}.")
    if not late and not soon:
        print("rien d'urgent")
    return late, soon


def build_parser():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--fichier", default=os.path.join("gomme", "suivi.csv"))
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("add")
    s.add_argument("--site", required=True)
    s.add_argument("--url", required=True)
    s.add_argument("--donnees", required=True, help="description des données, pas les données")
    s.add_argument("--demarche", choices=DEMARCHES, required=True)
    s.add_argument("--notes")
    s = sub.add_parser("envoyee")
    s.add_argument("id")
    s.add_argument("--date")
    s.add_argument("--preuve")
    s = sub.add_parser("prolongation")
    s.add_argument("id")
    s = sub.add_parser("reponse")
    s.add_argument("id")
    s.add_argument("--statut", choices=STATUTS[2:], required=True)
    s.add_argument("--date")
    s.add_argument("--notes")
    sub.add_parser("liste")
    sub.add_parser("echeances")
    return p


def main(argv=None):
    a = build_parser().parse_args(argv)
    rows = load(a.fichier)
    {"add": cmd_add, "envoyee": cmd_envoyee, "prolongation": cmd_prolongation,
     "reponse": cmd_reponse, "liste": cmd_liste, "echeances": cmd_echeances}[a.cmd](a, rows)
    if a.cmd not in ("liste", "echeances"):
        save(a.fichier, rows)
    return 0


if __name__ == "__main__":
    sys.exit(main())
