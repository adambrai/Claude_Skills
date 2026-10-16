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
- **Three different actions, never mixed up**: deleting at the source site, delisting
  from a search engine (a result removed from Google can stay on the source site), and
  limiting the visibility of the user's own profiles. Say which one each step is.
- **Expect a process, not a ten-minute erasure**: rights requests are normally free,
  but they take several steps and a follow-up. Tell the user so up front.
- **Never try to get around a refusal** (a declined search, a CAPTCHA, a login wall):
  explain the limit and switch to the manual path or an official tool.
- **Be honest about limits**: no method finds or removes everything. Some data is kept
  for legal reasons, delisting hides a result without deleting the page, and things
  can reappear.

## Path A — start from the user (search)

1. Check that web search is available in this session. If it is, search public pages
   for the user's name (in quotes), then name + city or an old public username, only if
   needed. Report each page found: URL, a short description without the sensitive
   data, and any doubt about a namesake or an uncertain match. Invent no result and no
   link. Wait for the user to open and verify every link themselves.
2. Wait for the user to confirm which pages are really about them.
3. Also list accounts the user owns (old social profiles, forums, shops) that they
   might close or lock down.
4. Check the usual places where people-search sites and data brokers list individuals
   (online directories, "people finder" sites, old-company or association listings,
   public registers), using only the user's own name and the details they gave. Report
   what is visible, never copy it. Many of these sites have an opt-out page.
5. Remind the user that finding nothing does not prove nothing exists.

If search is unavailable or a search is refused (for example because it targets personal
contact data), explain the limit plainly, do not look for a workaround, and use plan B.

### Plan B — manual searches

Give the user the searches to run themselves: their name in quotes; name + city; name +
an old username or employer; their own profiles on the main platforms (while logged in,
to see what a visitor sees); Google "Results about you" (see official tools). The user
pastes back only the URLs they want help with, with sensitive data masked. If the
assistant refused a search, use official tools or pages the user found; do not push to
bypass.

## Path B — start from one piece of information (reverse)

The user found one specific thing (a page, a photo, a phone number in a directory)
and wants it gone. Work only on that item: identify the site, find its official
removal or privacy procedure, and go straight to step 2 below. Start from one page the
user has verified, with sensitive data masked. Search nothing else about the user unless
they ask. If you cannot read the page, say so. Invent no form, address or email: if the
official procedure cannot be verified, write "to verify" and let the user check.

## Step 2 — choose the right action for each item

| situation | action |
|---|---|
| the user controls the account or post | delete it or change its privacy settings |
| a site publishes the data | deletion request to the site (GDPR art. 17), via its privacy page or DPO contact |
| the page stays online but should not show in search | delisting request to the search engine (Google's personal-information removal form, Bing's equivalent) |
| the page is already gone but still shows in results | the search engine's outdated-content tool |
| the user wants to know what a company holds | access request (art. 15) first |
| marketing use of the data | objection (art. 21) |

For an account the user controls, look first in its privacy or deletion settings. For
anything else, look for "Privacy", "Exercise my rights" or the data protection officer
(DPO) contact on the site. For each URL, say which of the three actions applies (deletion,
delisting or account setting), give the official procedure if you can verify it, and
otherwise "to verify". Ask the user questions to find the real reason (outdated data,
consent withdrawn, harm, no longer needed): it goes into the request.

Data brokers and people-search sites: most publish an opt-out form or a privacy contact;
use it per site, one entry per site in the tracker, and expect that a listing can
reappear later, so plan a re-check.

Unsolicited marketing emails: do not write rights requests for each one. Use the
unsubscribe link of legitimate senders, or the sender's privacy contact, and filter
the rest out of the inbox with a rule or label. Never delete mail permanently on the
user's behalf; sort and filter only, with their approval.

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

Letter template (translate to the language of the recipient, keep placeholders for the
user's details; `suivi.py modele ID` prints it from the tracker):

- Subject: "Demande d'effacement de données personnelles".
- The data concerned (described) and the URL.
- The real reason given by the user.
- Article 17 GDPR, invoked "to the extent its conditions are met", no invented basis.
- Ask to be informed of the outcome within the applicable time, and, in case of refusal,
  of the reasons and the retention obligations relied on.
- The minimum identification information, and a reply address.

Before sending: check the recipient, the data and the reason with the user. Keep the
request, its date and the acknowledgement. Draft, sent and confirmed deletion are three
different states.

### Optional browser help

If the user has Claude in Chrome (paid) and wants it, you may fill an official, verified
page with the approved draft. Show the fields and the recipient before submitting and
wait for an explicit OK. Stop at any CAPTCHA, login or identity check. Report only a
confirmation you observed. If it fails, fall back to the manual path.

### Official tools that need no assistant

- Google "Results about you": find and ask to remove results showing contact details.
- Google's personal-information removal request: removes the result from Google only; it
  does not delete the source page and is not automatic.
- Google's outdated-content tool: for pages already changed or deleted but still shown.
- Bing's equivalent form for delisting.
- The CNIL pages on the right to erasure and the right to delisting.

### Outside the EU

Users in Algeria are covered by law 18-07 on personal data protection (national authority:
ANPDP; it gives rights such as information, access, rectification and objection; check the
current text for what it says about erasure). A site or company established in the EU, or targeting EU
residents, still falls under the GDPR whatever the user's country. Say which regime you
think applies, mark it "to verify" when unsure, and use the site's official channel. For a
GDPR complaint the user can approach the data protection authority of an EU country; for
Algerian controllers, the ANPDP.

## Step 4 — track and follow up

Use the tracker, in the user's working folder:

```bash
python3 "${CLAUDE_SKILL_DIR}/suivi.py" add --site "Nom" --url URL --donnees "description" --demarche suppression
python3 "${CLAUDE_SKILL_DIR}/suivi.py" envoyee ID --date AAAA-MM-JJ --preuve "accusé de réception"
python3 "${CLAUDE_SKILL_DIR}/suivi.py" prolongation ID
python3 "${CLAUDE_SKILL_DIR}/suivi.py" reponse ID --statut supprime|partiel|refus
python3 "${CLAUDE_SKILL_DIR}/suivi.py" verifie ID --source disparu --recherche visible
python3 "${CLAUDE_SKILL_DIR}/suivi.py" liste
python3 "${CLAUDE_SKILL_DIR}/suivi.py" echeances
python3 "${CLAUDE_SKILL_DIR}/suivi.py" resume
python3 "${CLAUDE_SKILL_DIR}/suivi.py" modele ID      # erasure letter draft
python3 "${CLAUDE_SKILL_DIR}/suivi.py" relance ID     # follow-up draft, never sent
python3 "${CLAUDE_SKILL_DIR}/suivi.py" export --format markdown
```

The table holds: site, URL, data targeted (described, not copied), action, sent date,
proof, answer, follow-up date and verified result (source page and search results
checked separately with `verifie`). `--demarche` also accepts `desabonnement` and
`parametre`. Keep drafts, sent requests, refusals and confirmed deletions apart.
On request, prepare a follow-up with `relance`; never send it automatically.

Keep the states distinct: a draft is not a sent request, and a sent request is not a
confirmed deletion. An organisation normally answers within one month, extendable by
two months if it says so within the first month. Past the deadline, or after an
unsatisfying answer, the user can complain to the CNIL with their proofs. The deadline is
a legal limit, not a guarantee that it will be met. Check the source page and the search
results separately afterwards.

A reminder needs a real scheduled task; offer to set one up with the scheduling
skill if the session has one, and never present a promise in chat as monitoring.

## Prevention

Finish with a short list for the user: review privacy settings on remaining profiles,
close unused accounts, avoid publishing personal contact details, use an alias email
for sign-ups.

Also offer these related clean-ups, one at a time, each only with the user's approval and
done by them in the service's settings (give the steps, do not change accounts yourself):

- AI assistants: turn off the use of conversations for model training, and review or
  clear what the assistant has memorised about the user.
- Gmail: turn off the "smart features" that use email content for personalisation.
- Marketing emails: unsubscribe from what the user no longer wants and filter the rest
  out of the inbox; no permanent deletion by the assistant.

This is general practical help, not legal advice for a specific situation.
