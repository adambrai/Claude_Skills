---
name: gomme
description: >-
  Help the user reduce their own digital footprint in the EU: find public pages
  about themselves (with their confirmation of each result), pick the right
  action for each one (deletion at the source, search-engine delisting, or a
  setting in an account they control), draft GDPR requests, and track answers
  and legal deadlines with suivi.py. Also works backwards from one specific
  piece of information the user wants removed. Only for the user's own data;
  nothing is sent or submitted without their explicit approval. Use when the
  user types /gomme or asks to erase or reduce their online traces.
argument-hint: "[recherche | une URL ou une info précise à faire retirer | suivi]"
---

# gomme

Reduce what the internet shows about the user, step by step, and keep proof of every
request. This skill prepares and tracks; the websites decide what they delete.

What the user typed after `/gomme`: `$ARGUMENTS`

## Ground rules

- **Only the user's own information.** Never search for, collect or compile data about
  anyone else. If a result is about a namesake, drop it.
- **The user confirms every result** before anything is done with it.
- **Nothing leaves without explicit approval**: no form submitted, no email sent, no
  account changed. Show the draft and the recipient, then wait.
- **Ask for the minimum**: a name and, only if needed, a city or a public username.
  Never ask for passwords, ID documents or sensitive numbers.
- **Never copy the sensitive data itself** into notes or the tracker: describe it
  ("adresse postale", "numéro de téléphone").
- **Be honest about limits**: no method finds or removes everything. Some data is kept
  for legal reasons, delisting hides a result without deleting the page, and things
  can reappear.

## Path A — start from the user (search)

1. If web search is available in this session, search public pages for the user's
   name (in quotes), then name + city or an old public username. Report each page
   found: URL, a short description without the sensitive data, and any doubt about a
   namesake. Invent nothing; if search is unavailable, say so and give the user the
   exact searches to run themselves.
2. Wait for the user to confirm which pages are really about them.
3. Also list accounts the user owns (old social profiles, forums, shops) that they
   might close or lock down.

## Path B — start from one piece of information (reverse)

The user found one specific thing (a page, a photo, a phone number in a directory)
and wants it gone. Work only on that item: identify the site, find its official
removal or privacy procedure, and go straight to step 2 below. Do not search for
other information about the user unless they ask.

## Step 2 — choose the right action for each item

| situation | action |
|---|---|
| the user controls the account or post | delete it or change its privacy settings |
| a site publishes the data | deletion request to the site (GDPR art. 17), via its privacy page or DPO contact |
| the page stays online but should not show in search | delisting request to the search engine (Google's personal-information removal form, Bing's equivalent) |
| the page is already gone but still shows in results | the search engine's outdated-content tool |
| the user wants to know what a company holds | access request (art. 15) first |
| marketing use of the data | objection (art. 21) |

The right to erasure has conditions and exceptions (legal retention duties, freedom of
expression and information): an annoying page is not automatically removable. Say so
when it applies, without inventing a legal basis.

## Step 3 — draft the request

For each item, write a short, precise draft: the URL, the data concerned, the real
reason given by the user, the article invoked only when its conditions plausibly
apply, a request to be told the outcome and the reasons for any refusal, and
placeholders for the user's contact details. Do not attach ID by default; if a site
requires identity checks, use its official channel and share the minimum.

Show the draft. Only after the user approves may you help fill an official form or
prepare the email, and the user (or you, with their explicit OK for that one send)
submits it. Stop at any CAPTCHA, login or identity check and hand over to the user.
Report only a confirmation you actually saw.

## Step 4 — track and follow up

Use the tracker, in the user's working folder:

```bash
python3 "${CLAUDE_SKILL_DIR}/suivi.py" add --site "Nom" --url URL --donnees "description" --demarche suppression
python3 "${CLAUDE_SKILL_DIR}/suivi.py" envoyee ID --date AAAA-MM-JJ --preuve "accusé de réception"
python3 "${CLAUDE_SKILL_DIR}/suivi.py" prolongation ID
python3 "${CLAUDE_SKILL_DIR}/suivi.py" reponse ID --statut supprime|partiel|refus
python3 "${CLAUDE_SKILL_DIR}/suivi.py" liste
python3 "${CLAUDE_SKILL_DIR}/suivi.py" echeances
```

Keep the states distinct: a draft is not a sent request, and a sent request is not a
confirmed deletion. An organisation normally answers within one month, extendable by
two months if it says so within the first month. Past the deadline, or after an
unsatisfying answer, the user can complain to the CNIL with their proofs. Check the
source page and the search results separately afterwards.

A reminder needs a real scheduled task; offer to set one up with the scheduling
skill if the session has one, and never present a promise in chat as monitoring.

## Prevention

Finish with a short list for the user: review privacy settings on remaining profiles,
close unused accounts, avoid publishing personal contact details, use an alias email
for sign-ups.

This is general practical help, not legal advice for a specific situation.
