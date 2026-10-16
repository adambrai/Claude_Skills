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
  python3 suivi.py verifie ID --source en_ligne|disparu|inconnu --recherche visible|disparu|inconnu
  python3 suivi.py liste
  python3 suivi.py echeances          # what is due or overdue today
  python3 suivi.py resume             # counts per state (draft / sent / refused / confirmed)
  python3 suivi.py modele ID          # prints the erasure letter draft (nothing is sent)
  python3 suivi.py relance ID         # prints a follow-up draft (nothing is sent)
  python3 suivi.py export [--format csv|markdown] [--sortie FICHIER]

The file never stores the personal data itself: describe it ("adresse postale"),
do not paste it. Standard library only.
"""
import argparse
import calendar
import csv
import datetime as dt
import io
import os
import sys

FIELDS = ["id", "site", "url", "donnees", "demarche", "statut", "date_envoi", "preuve",
          "prolongation", "echeance", "date_reponse", "verif_source", "verif_recherche", "date_verif",
          "notes"]
DEMARCHES = ("suppression", "dereferencement", "compte", "acces", "opposition", "desabonnement",
             "parametre")
VERIF_SOURCE = ("en_ligne", "disparu", "inconnu")
VERIF_RECHERCHE = ("visible", "disparu", "inconnu")
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


def cmd_verifie(a, rows):
    """Record what the user observed on the source page and in search results, separately."""
    r = find(rows, a.id)
    if a.source:
        r["verif_source"] = a.source
    if a.recherche:
        r["verif_recherche"] = a.recherche
    if not (a.source or a.recherche):
        sys.exit("indique --source et/ou --recherche")
    r["date_verif"] = a.date or dt.date.today().isoformat()
    if a.notes:
        r["notes"] = (r.get("notes", "") + " | " + a.notes).strip(" |")
    print(f"demande {a.id} : page source {r.get('verif_source') or '?'}, "
          f"résultats de recherche {r.get('verif_recherche') or '?'}")


LETTRE = """Objet : Demande d'effacement de données personnelles

Madame, Monsieur,

Je vous demande d'effacer les données personnelles me concernant ({donnees}) publiées à
l'adresse suivante : {url}

Motif : [à compléter : la vraie raison, par exemple données devenues inutiles, retrait de
mon consentement, opposition].

Je fonde cette demande sur l'article 17 du RGPD, dans la mesure où ses conditions sont
réunies. Merci de m'informer des suites données dans le délai applicable. En cas de refus,
merci de m'en indiquer les raisons et les obligations de conservation invoquées.

Pour m'identifier, je peux fournir le minimum nécessaire par votre canal officiel :
[à compléter, sans pièce d'identité par défaut].

Adresse de réponse : [à compléter]
Fait le [date]. [Nom]
"""

RELANCE = """Objet : Relance - demande d'effacement du {date_envoi} ({site})

Madame, Monsieur,

Le {date_envoi}, je vous ai adressé une demande concernant les données suivantes : {donnees}
({url}). Je n'ai pas reçu de réponse à ce jour ; le délai applicable est échu depuis le
{echeance}. Merci de me communiquer la suite donnée à ma demande, ou les raisons d'un
éventuel refus. À défaut, je pourrai saisir la CNIL avec les pièces conservées.

Référence / preuve d'envoi : {preuve}
Adresse de réponse : [à compléter]
[Nom]
"""


def cmd_modele(a, rows):
    r = find(rows, a.id)
    print(LETTRE.format(donnees=r["donnees"], url=r["url"]))
    print("(brouillon à relire : rien n'a été envoyé)")


def cmd_relance(a, rows):
    r = find(rows, a.id)
    print(RELANCE.format(date_envoi=r.get("date_envoi") or "[date]", site=r["site"],
                         donnees=r["donnees"], url=r["url"], echeance=deadline(r) or "[date]",
                         preuve=r.get("preuve") or "[à compléter]"))
    print("(brouillon à relire : rien n'a été envoyé)")


def cmd_resume(a, rows):
    if not rows:
        print("aucune demande")
        return {}
    counts = {}
    for r in rows:
        counts[r["statut"]] = counts.get(r["statut"], 0) + 1
    for k in STATUTS:
        if k in counts:
            print(f"{k:<12} {counts[k]}")
    return counts


def cmd_export(a, rows):
    out = io.StringIO()
    if a.format == "csv":
        w = csv.DictWriter(out, fieldnames=FIELDS)
        w.writeheader()
        for r in rows:
            r["echeance"] = deadline(r)
            w.writerow({k: r.get(k, "") for k in FIELDS})
    else:
        cols = ["site", "url", "donnees", "demarche", "statut", "date_envoi", "preuve", "echeance",
                "date_reponse", "verif_source", "verif_recherche"]
        out.write("| " + " | ".join(cols) + " |\n|" + "---|" * len(cols) + "\n")
        for r in rows:
            r["echeance"] = deadline(r)
            out.write("| " + " | ".join((r.get(c) or "-").replace("|", "/") for c in cols) + " |\n")
    text = out.getvalue()
    if a.sortie:
        with open(a.sortie, "w", encoding="utf-8", newline="") as f:
            f.write(text)
        print(f"export écrit dans {a.sortie}")
    else:
        print(text, end="")


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
    s = sub.add_parser("verifie")
    s.add_argument("id")
    s.add_argument("--source", choices=VERIF_SOURCE)
    s.add_argument("--recherche", choices=VERIF_RECHERCHE)
    s.add_argument("--date")
    s.add_argument("--notes")
    for name in ("modele", "relance"):
        s = sub.add_parser(name)
        s.add_argument("id")
    s = sub.add_parser("export")
    s.add_argument("--format", choices=("csv", "markdown"), default="markdown")
    s.add_argument("--sortie")
    sub.add_parser("liste")
    sub.add_parser("echeances")
    sub.add_parser("resume")
    return p


def main(argv=None):
    a = build_parser().parse_args(argv)
    rows = load(a.fichier)
    {"add": cmd_add, "envoyee": cmd_envoyee, "prolongation": cmd_prolongation,
     "reponse": cmd_reponse, "liste": cmd_liste, "echeances": cmd_echeances,
     "verifie": cmd_verifie, "modele": cmd_modele, "relance": cmd_relance,
     "resume": cmd_resume, "export": cmd_export}[a.cmd](a, rows)
    if a.cmd in ("add", "envoyee", "prolongation", "reponse", "verifie"):
        save(a.fichier, rows)
    return 0


if __name__ == "__main__":
    sys.exit(main())
