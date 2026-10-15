#!/usr/bin/env python3
"""debat.py — state machine for the /debat skill (standard library only).

Pipeline: spawn -> triage -> bracket (attack/defend/judge, second judge on close
matches) -> council (critique/revise/judge until convergence) -> synthesis
(synth/red team/fix/blind compare) -> optional blind check against a rejected
baseline -> result.

The orchestrator only ever runs `debat.py next`, launches the jobs it lists, and
repeats. All work lives on disk under .debat/<run>/.
"""
import argparse
import itertools
import json
import math
import os
import random
import re
import shlex
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
CARDS_PATH = os.path.join(HERE, "cards.json")
TEMPLATES_PATH = os.path.join(HERE, "templates.md")
RUBRIC_PATH = os.path.join(HERE, "rubric.md")
DEFAULT_ASK = os.path.expanduser("~/.claude/skills/multi-agents/ask.sh")
ROOT = ".debat"

WEIGHTS = {"correctness": 30, "requirements": 25, "robustness": 20, "actionability": 15, "clarity": 10}

# Model aliases always resolve to the newest model of each tier in Claude Code.
PRESETS = {
    "eco": {"agents": 6, "keep": 4, "council": 2, "council_rounds": 2,
            "models": dict.fromkeys(["competitor", "triage", "attacker", "defender", "judge",
                                     "council", "cjudge", "synth", "redteam", "compare"], "sonnet")},
    "std": {"agents": 12, "keep": 8, "council": 3, "council_rounds": 4,
            "models": {"competitor": "sonnet", "triage": "sonnet", "attacker": "sonnet",
                       "defender": "sonnet", "judge": "opus", "council": "opus", "cjudge": "opus",
                       "synth": "opus", "redteam": "opus", "compare": "opus"}},
    "max": {"agents": 32, "keep": 8, "council": 3, "council_rounds": 6,
            "models": dict.fromkeys(["competitor", "triage", "attacker", "defender", "judge",
                                     "council", "cjudge", "synth", "redteam", "compare"], "opus")},
}
TRIAGE_BATCH = 4          # answers per triage judge
TRIAGE_COVER = 2          # independent triage judges per answer
CLOSE_MARGIN = 5.0        # points; closer matches get a second, order-swapped judge
COUNCIL_EPS = 2.0         # leader improvement below this = converged
COUNCIL_DROP = 15.0       # members this far behind the leader leave the council
JUDGE_KINDS = {"triage", "judge", "judge2", "cjudge", "compare", "final"}
MAX_TRIES = {"judge": 3, "default": 2}
RETRY_GAP = float(os.environ.get("DEBAT_RETRY_GAP", "30"))  # seconds between counted tries


class DebatError(Exception):
    pass


# ----------------------------------------------------------------- utilities

def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def write(path, text):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def has_output(path):
    return os.path.isfile(path) and os.path.getsize(path) > 0


def real_output(path):
    """A usable answer file: present and not the give-up marker."""
    return has_output(path) and read(path).strip() != "NO OUTPUT"


def extract_json(text):
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("no JSON object")
    return json.loads(text[start:end + 1])


def load_json_output(path):
    """Parsed JSON, {'failed': True} for a give-up marker, or None if unusable."""
    if not has_output(path):
        return None
    text = read(path)
    if text.strip() == "NO OUTPUT":
        return {"failed": True}
    try:
        return extract_json(text)
    except (ValueError, json.JSONDecodeError):
        return None


def total(scores):
    if not isinstance(scores, dict):
        return 0.0
    s = 0.0
    for k, w in WEIGHTS.items():
        try:
            v = float(scores.get(k, 0))
        except (TypeError, ValueError):
            v = 0.0
        s += max(0.0, min(10.0, v)) * w
    return round(s / 10.0, 2)


def is_fatal(scores):
    v = scores.get("fatal", False) if isinstance(scores, dict) else False
    return v is True or str(v).strip().lower() in ("true", "yes", "1")


def agent_ids(n):
    width = max(2, len(str(n)))
    return [f"d{str(i).zfill(width)}" for i in range(1, n + 1)]


# ----------------------------------------------------------------- cards

def load_cards(path=CARDS_PATH):
    data = json.loads(read(path))
    for key in ("reasoning", "methods", "priorities"):
        ids = [c["id"] for c in data[key]]
        if len(ids) != len(set(ids)):
            raise DebatError(f"duplicate ids in cards.json:{key}")
    return data


def deal(n, rng, data):
    """n distinct cards; spread every entry evenly and avoid shared pairs."""
    R, M, P = data["reasoning"], data["methods"], data["priorities"]
    combos = list(itertools.product(range(len(R)), range(len(M)), range(len(P))))
    if n > len(combos):
        raise DebatError(f"only {len(combos)} distinct cards; ask for fewer agents")
    rng.shuffle(combos)
    used = set()
    cr, cm, cp = [0] * len(R), [0] * len(M), [0] * len(P)
    pairs = {}
    hand = []
    for _ in range(n):
        best, best_key = None, None
        for c in combos:
            if c in used:
                continue
            r, m, p = c
            overlap = pairs.get(("rm", r, m), 0) + pairs.get(("rp", r, p), 0) + pairs.get(("mp", m, p), 0)
            key = (overlap, cr[r] + cm[m] + cp[p])
            if best_key is None or key < best_key:
                best, best_key = c, key
                if key == (0, 0):
                    break
        used.add(best)
        r, m, p = best
        cr[r] += 1; cm[m] += 1; cp[p] += 1
        for k in (("rm", r, m), ("rp", r, p), ("mp", m, p)):
            pairs[k] = pairs.get(k, 0) + 1
        hand.append({"reasoning": R[r]["id"], "method": M[m]["id"], "priority": P[p]["id"]})
    return hand


def card_values(card, data):
    def find(lst, cid):
        return next(c for c in data[lst] if c["id"] == cid)
    r, m, p = find("reasoning", card["reasoning"]), find("methods", card["method"]), find("priorities", card["priority"])
    return {"reasoning_name": r["name"], "reasoning_how": r["how"], "method_name": m["name"],
            "method_how": m["how"], "priority_name": p["name"], "priority_how": p["how"]}


def card_line(card, data):
    v = card_values(card, data)
    return f'{v["reasoning_name"]} + {v["method_name"]} + {v["priority_name"]}'


# ----------------------------------------------------------------- templates

def load_templates(path=TEMPLATES_PATH):
    text = read(path)
    out = {}
    for m in re.finditer(r"<!-- template:(\w+) -->\s*```text\n(.*?)\n```\s*<!-- /template:\1 -->", text, re.S):
        out[m.group(1)] = m.group(2)
    return out


def fill(template, values):
    def rep(m):
        key = m.group(1)
        if key not in values:
            raise DebatError(f"template placeholder without value: {key}")
        return str(values[key])
    return re.sub(r"\{\{(\w+)\}\}", rep, template)


# ----------------------------------------------------------------- state

def run_dir_from(args):
    if getattr(args, "run", None):
        return os.path.abspath(args.run)
    latest = os.path.join(ROOT, "LATEST")
    if not os.path.isfile(latest):
        raise DebatError("no debate here: run `debat.py init` first (from the same directory)")
    return os.path.abspath(read(latest).strip())


def load_state(run_dir):
    return json.loads(read(os.path.join(run_dir, "debat.json")))


def save_state(state):
    write(os.path.join(state["run_dir"], "debat.json"), json.dumps(state, indent=2, ensure_ascii=False))


def P(state, *parts):
    return os.path.join(state["run_dir"], *parts)


def alive(state):
    return [a for a, v in sorted(state["agents"].items()) if v["status"] == "alive"]


def add_ideas(state, ideas, stage):
    if not isinstance(ideas, list):
        return
    seen = {i["idea"].strip().lower() for i in state["ideas"]}
    for it in ideas:
        if not isinstance(it, dict):
            continue
        idea = str(it.get("idea", "")).strip()
        if len(idea) < 8 or idea.lower() in seen:
            continue
        seen.add(idea.lower())
        state["ideas"].append({"from": str(it.get("from", "?")), "idea": idea[:400], "stage": stage})
    state["ideas"] = state["ideas"][-40:]
    lines = ["# Idea bank", "", "Specific ideas judges found worth keeping, from any answer.", ""]
    lines += [f"- {i['idea']}" for i in state["ideas"]] or ["- (none yet)"]
    write(P(state, "ideas.md"), "\n".join(lines) + "\n")


def new_state(args, run_dir, task_file, baseline_file):
    preset = PRESETS[args.mode]
    n = args.agents or preset["agents"]
    if n < 2:
        raise DebatError("need at least 2 agents")
    seed = args.seed if args.seed is not None else random.randrange(1, 10**6)
    rng = random.Random(seed)
    data = load_cards()
    cards = deal(n, rng, data)
    ext = [t for t in (args.ext or "").split(",") if t.strip()]
    if len(ext) >= n:
        raise DebatError("--ext lists as many tools as agents; keep at least one Claude debater")
    if ext and not os.path.isfile(args.ask):
        raise DebatError(f"--ext needs the multi-agents helper at {args.ask}")
    ids = agent_ids(n)
    ext_slots = {ids[-(i + 1)]: t for i, t in enumerate(reversed(ext))}
    agents = {}
    for aid, card in zip(ids, cards):
        agents[aid] = {"card": card, "kind": "ext" if aid in ext_slots else "claude",
                       "tool": ext_slots.get(aid), "solution": f"spawn/{aid}.md",
                       "status": "alive", "triage": [], "triage_fatal": [], "score": 0.0, "byes": 0}
    keep = min(args.keep or preset["keep"], n)
    council = min(args.council or preset["council"], keep)
    state = {
        "version": 1, "run_dir": run_dir, "created": time.strftime("%Y-%m-%d %H:%M:%S"),
        "seed": seed, "mode": args.mode, "n": n, "keep": keep, "council_size": council,
        "council_rounds": args.council_rounds or preset["council_rounds"],
        "models": dict(preset["models"]), "wave": args.wave, "ask": args.ask,
        "has_baseline": bool(baseline_file), "agents": agents, "ideas": [],
        "stage": "spawn", "step": "spawn", "triage_batches": [], "rounds": [],
        "council": {"members": [], "round": 0, "history": [], "dropped": []},
        "synth": {}, "final": {}, "attempts": {}, "log": [],
    }
    if args.model:
        for kv in args.model:
            role, _, alias = kv.partition("=")
            if role not in state["models"] or not alias:
                raise DebatError(f"--model expects role=alias with role in {sorted(state['models'])}")
            state["models"][role] = alias
    return state


# ----------------------------------------------------------------- planning

def triage_batches(ids, rng):
    """Each answer appears in TRIAGE_COVER batches with mostly different peers."""
    batches = []
    for cover in range(TRIAGE_COVER):
        order = ids[:]
        best, best_rep = None, None
        for _ in range(30):
            rng.shuffle(order)
            chunks = [order[i:i + TRIAGE_BATCH] for i in range(0, len(order), TRIAGE_BATCH)]
            if len(chunks) > 1 and len(chunks[-1]) == 1:
                chunks[-2].append(chunks[-1].pop())
                chunks.pop()
            prev = {frozenset(p) for b in batches for p in itertools.combinations(b, 2)}
            rep = sum(1 for c in chunks for p in itertools.combinations(c, 2) if frozenset(p) in prev)
            if best_rep is None or rep < best_rep:
                best, best_rep = [c[:] for c in chunks], rep
            if rep == 0:
                break
        batches.extend(best)
    return [{"id": f"t{str(i + 1).zfill(2)}", "agents": b} for i, b in enumerate(batches)]


def pair_round(state, ids):
    """Seeded pairing: strongest vs weakest, avoiding identical reasoning modes."""
    ranked = sorted(ids, key=lambda a: -state["agents"][a]["score"])
    bye = None
    if len(ranked) % 2:
        cands = sorted(ranked, key=lambda a: (state["agents"][a]["byes"], -state["agents"][a]["score"]))
        bye = cands[0]
        state["agents"][bye]["byes"] += 1
        ranked.remove(bye)
    half = len(ranked) // 2
    top, bottom = ranked[:half], ranked[half:][::-1]
    reasoning = lambda a: state["agents"][a]["card"]["reasoning"]
    for i in range(half):
        if reasoning(top[i]) == reasoning(bottom[i]):
            for j in range(i + 1, half):
                if reasoning(top[i]) != reasoning(bottom[j]) and reasoning(top[j]) != reasoning(bottom[i]):
                    bottom[i], bottom[j] = bottom[j], bottom[i]
                    break
    rnd = len(state["rounds"]) + 1
    matches = [{"id": f"r{rnd}-m{str(i + 1).zfill(2)}", "a": top[i], "b": bottom[i], "winner": None,
                "totals": {}, "judges": 1, "reason": "", "survived": [], "standing": {}} for i in range(half)]
    state["rounds"].append({"n": rnd, "matches": matches, "bye": bye})


def plan(n, mode, keep=None, council=None, council_rounds=None):
    pr = PRESETS[mode]
    keep = min(keep or pr["keep"], n)
    council = min(council or pr["council"], keep)
    crounds = council_rounds or pr["council_rounds"]
    rows = [("spawn", n, n)]
    calls_min = calls_max = n
    alive_n = n
    if n > keep:
        t = math.ceil(TRIAGE_COVER * n / TRIAGE_BATCH)
        rows.append(("triage", f"{n}->{keep}", t))
        calls_min += t; calls_max += t
        alive_n = keep
    r = 0
    while alive_n > council:
        r += 1
        m = alive_n // 2
        base = 5 * m
        rows.append((f"round {r}", f"{alive_n}->{alive_n - m}", f"{base}-{base + m}"))
        calls_min += base; calls_max += base + m
        alive_n -= m
    per = 2 * council + 1 if council > 1 else 0
    if per:
        rows.append(("council", f"{council} members, 1-{crounds} rounds", f"{per}-{per * crounds}"))
        calls_min += per; calls_max += per * crounds
    rows.append(("synthesis", "synth + red team + fix + blind check", 4))
    calls_min += 4; calls_max += 4
    return rows, calls_min, calls_max


# ----------------------------------------------------------------- jobs

def jobs_for(state):
    """Jobs of the current step: dicts with id, kind, model, template, outs, values."""
    step, A = state["step"], state["agents"]
    jobs = []
    m = state["models"]
    if step == "spawn":
        for aid, a in sorted(A.items()):
            jobs.append({"id": f"spawn-{aid}", "kind": "competitor", "model": m["competitor"],
                         "ext": a["tool"], "agent": aid, "outs": [P(state, "spawn", f"{aid}.md")]})
    elif step == "triage":
        for b in state["triage_batches"]:
            jobs.append({"id": f"triage-{b['id']}", "kind": "triage", "model": m["triage"],
                         "batch": b, "outs": [P(state, "triage", f"{b['id']}.json")]})
    elif step in ("attack", "defend", "judge", "judge2"):
        rnd = state["rounds"][-1]
        for mt in rnd["matches"]:
            d = P(state, f"r{rnd['n']}", mt["id"])
            if step == "attack":
                for me, opp in ((mt["a"], mt["b"]), (mt["b"], mt["a"])):
                    jobs.append({"id": f"{mt['id']}-attack-{me}", "kind": "attacker", "model": m["attacker"],
                                 "agent": me, "target": opp, "match": mt, "outs": [os.path.join(d, f"attack-{me}.md")]})
            elif step == "defend":
                for me, opp in ((mt["a"], mt["b"]), (mt["b"], mt["a"])):
                    jobs.append({"id": f"{mt['id']}-defend-{me}", "kind": "defender", "model": m["defender"],
                                 "agent": me, "attacker": opp, "match": mt,
                                 "outs": [os.path.join(d, f"defense-{me}.md"), os.path.join(d, f"solution-{me}.md")]})
            elif step == "judge":
                jobs.append({"id": f"{mt['id']}-judge", "kind": "judge", "model": m["judge"], "match": mt,
                             "order": (mt["a"], mt["b"]), "outs": [os.path.join(d, "verdict-1.json")]})
            elif step == "judge2" and mt.get("needs_second"):
                jobs.append({"id": f"{mt['id']}-judge2", "kind": "judge2", "model": m["judge"], "match": mt,
                             "order": (mt["b"], mt["a"]), "outs": [os.path.join(d, "verdict-2.json")]})
    elif step in ("critique", "revise", "cjudge"):
        c = state["council"]
        d = P(state, "council", f"c{c['round']}")
        for me in c["members"]:
            if step == "critique":
                jobs.append({"id": f"c{c['round']}-critique-{me}", "kind": "critique", "model": m["council"],
                             "agent": me, "outs": [os.path.join(d, f"critique-{me}.md")]})
            elif step == "revise":
                jobs.append({"id": f"c{c['round']}-revise-{me}", "kind": "revise", "model": m["council"],
                             "agent": me, "outs": [os.path.join(d, f"defense-{me}.md"), os.path.join(d, f"solution-{me}.md")]})
        if step == "cjudge":
            jobs.append({"id": f"c{c['round']}-judge", "kind": "cjudge", "model": m["cjudge"],
                         "outs": [os.path.join(d, "verdict.json")]})
    elif step == "synth":
        jobs.append({"id": "synth", "kind": "synth", "model": m["synth"], "outs": [P(state, "synth", "draft.md")]})
    elif step == "redteam":
        jobs.append({"id": "redteam", "kind": "redteam", "model": m["redteam"], "outs": [P(state, "synth", "redteam.md")]})
    elif step == "fix":
        jobs.append({"id": "fix", "kind": "fix", "model": m["synth"],
                     "outs": [P(state, "synth", "defense.md"), P(state, "synth", "final.md")]})
    elif step == "compare":
        jobs.append({"id": "compare", "kind": "compare", "model": m["compare"], "outs": [P(state, "synth", "compare.json")]})
    elif step == "final":
        jobs.append({"id": "final", "kind": "final", "model": m["compare"], "outs": [P(state, "final", "verdict.json")]})
    return jobs


def job_done(job):
    if job["kind"] in JUDGE_KINDS:
        return load_json_output(job["outs"][0]) is not None
    return all(has_output(o) for o in job["outs"])


def sol(state, aid):
    return P(state, state["agents"][aid]["solution"])


def render(state, job, T, data):
    task = read(P(state, "task.md"))
    rd = state["run_dir"]
    base = {"task": task, "run_dir": rd, "rubric": RUBRIC_PATH, "n": state["n"], "job": job["id"],
            "ideas": P(state, "ideas.md")}
    k = job["kind"]
    if "agent" in job:
        base.update(card_values(state["agents"][job["agent"]]["card"], data))
        base["agent"] = job["agent"]
    if k == "competitor":
        note = ""
        if state["has_baseline"]:
            note = (f"An earlier answer to this task was rejected by the user. It is at {P(state, 'baseline.md')}. "
                    "Read it; your answer must clearly beat it. Do not copy it.")
        base.update(baseline_note=note, out=job["outs"][0])
        return fill(T["competitor_ext" if job.get("ext") else "competitor"], base)
    if k == "triage":
        ids = job["batch"]["agents"]
        base.update(out=job["outs"][0],
                    answer_list="\n".join(f"- {a}: {sol(state, a)}" for a in ids),
                    score_skeleton=",\n".join(
                        f'    "{a}": {{"correctness": 0, "requirements": 0, "robustness": 0, "actionability": 0, "clarity": 0, "fatal": false}}'
                        for a in ids))
        return fill(T["triage"], base)
    if k == "attacker":
        mt = job["match"]
        base.update(round=len(state["rounds"]), match=mt["id"], target=job["target"],
                    target_solution=sol(state, job["target"]), own_solution=sol(state, job["agent"]), out=job["outs"][0])
        return fill(T["attacker"], base)
    if k == "defender":
        mt = job["match"]
        d = P(state, f"r{len(state['rounds'])}", mt["id"])
        base.update(round=len(state["rounds"]), match=mt["id"], attacker=job["attacker"],
                    own_solution=sol(state, job["agent"]), attacks=os.path.join(d, f"attack-{job['attacker']}.md"),
                    defense_out=job["outs"][0], solution_out=job["outs"][1])
        return fill(T["defender"], base)
    if k in ("judge", "judge2"):
        mt = job["match"]
        d = P(state, f"r{len(state['rounds'])}", mt["id"])
        f, s = job["order"]
        base.update(round=len(state["rounds"]), match=mt["id"], first=f, second=s, out=job["outs"][0],
                    first_solution=os.path.join(d, f"solution-{f}.md"), second_solution=os.path.join(d, f"solution-{s}.md"),
                    first_attacks=os.path.join(d, f"attack-{s}.md"), second_attacks=os.path.join(d, f"attack-{f}.md"),
                    first_defense=os.path.join(d, f"defense-{f}.md"), second_defense=os.path.join(d, f"defense-{s}.md"))
        return fill(T["judge"], base)
    c = state["council"]
    cdir = P(state, "council", f"c{c['round']}")
    last = c["history"][-1]["verdict_path"] if c["history"] else "(none yet: this is round 1)"
    if k == "critique":
        others = [x for x in c["members"] if x != job["agent"]]
        base.update(round=c["round"], last_verdict=last, out=job["outs"][0],
                    others_list="\n".join(f"- {x}: {sol(state, x)}" for x in others))
        return fill(T["critique"], base)
    if k == "revise":
        others = [x for x in c["members"] if x != job["agent"]]
        base.update(round=c["round"], last_verdict=last, own_solution=sol(state, job["agent"]),
                    critiques=", ".join(os.path.join(cdir, f"critique-{x}.md") for x in others),
                    others=", ".join(sol(state, x) for x in others),
                    defense_out=job["outs"][0], solution_out=job["outs"][1])
        return fill(T["revise"], base)
    if k == "cjudge":
        mem = c["members"]
        crit = ", ".join(os.path.join(cdir, f"critique-{x}.md") for x in mem)
        base.update(round=c["round"], out=job["outs"][0],
                    member_list="\n".join(
                        f"- {x}: revised answer {os.path.join(cdir, f'solution-{x}.md')}; defense {os.path.join(cdir, f'defense-{x}.md')}; "
                        f"objections about it: sections \"ON {x}\" in {crit}" for x in mem),
                    score_skeleton=",\n".join(
                        f'    "{x}": {{"correctness": 0, "requirements": 0, "robustness": 0, "actionability": 0, "clarity": 0, "fatal": false}}'
                        for x in mem),
                    standing_skeleton=",\n".join(f'    "{x}": []' for x in mem))
        return fill(T["cjudge"], base)
    leader = state["synth"].get("leader")
    if k == "synth":
        others = [x for x in c["members"] if x != leader] + [x for x in c["dropped"]]
        base.update(leader_solution=sol(state, leader), out=job["outs"][0],
                    others=", ".join(sol(state, x) for x in others) or "(none)",
                    last_verdict=c["history"][-1]["verdict_path"] if c["history"] else "(no council round)")
        return fill(T["synth"], base)
    if k == "redteam":
        base.update(target_solution=P(state, "synth", "draft.md"), out=job["outs"][0])
        return fill(T["redteam"], base)
    if k == "fix":
        base.update(own_solution=P(state, "synth", "draft.md"), attacks=P(state, "synth", "redteam.md"),
                    defense_out=job["outs"][0], solution_out=job["outs"][1])
        return fill(T["fix"], base)
    if k in ("compare", "final"):
        if k == "compare":
            pair = [("synth", P(state, "synth", "final.md")), ("leader", sol(state, leader))]
            note = ""
        else:
            pair = [("champion", P(state, state["final"]["champion_path"])), ("baseline", P(state, "baseline.md"))]
            note = "One of them is an answer the user already rejected; judge both on merit only."
        rng = random.Random(f"{state['seed']}-{k}")
        if rng.random() < 0.5:
            pair.reverse()
        state.setdefault("blind", {})[k] = {"X": pair[0][0], "Y": pair[1][0]}
        base.update(x_solution=pair[0][1], y_solution=pair[1][1], out=job["outs"][0], compare_note=note)
        return fill(T["compare"], base)
    raise DebatError(f"no template for {k}")


# ----------------------------------------------------------------- step completion

def decide_match(state, mt):
    a, b = mt["a"], mt["b"]
    d = P(state, f"r{len(state['rounds'])}", mt["id"])
    verdicts = [v for v in (load_json_output(os.path.join(d, "verdict-1.json")),
                            load_json_output(os.path.join(d, "verdict-2.json"))) if v and not v.get("failed")]
    if not verdicts:
        winner = a if state["agents"][a]["score"] >= state["agents"][b]["score"] else b
        mt.update(winner=winner, reason="both judges failed: decided by earlier score")
        return
    tot = {x: sum(total(v.get("scores", {}).get(x, {})) for v in verdicts) / len(verdicts) for x in (a, b)}
    fatal = {x: all(is_fatal(v.get("scores", {}).get(x, {})) for v in verdicts) for x in (a, b)}
    corr = {x: sum(float(v.get("scores", {}).get(x, {}).get("correctness", 0) or 0) for v in verdicts) for x in (a, b)}
    stand = {x: len((verdicts[0].get("standing") or {}).get(x, []) or []) for x in (a, b)}
    def key(x):
        return (not fatal[x], tot[x], -stand[x], corr[x])
    winner = max((a, b), key=key)
    if key(a) == key(b):
        w1 = str(verdicts[0].get("winner", "")).strip()
        winner = w1 if w1 in (a, b) else a
    v0 = verdicts[0]
    mt.update(winner=winner, totals=tot, judges=len(verdicts), fatal=fatal,
              reason=str(v0.get("reason", ""))[:300] if str(v0.get("winner", "")).strip() == winner else
              f"averaged over {len(verdicts)} judges",
              survived=[str(s)[:160] for s in (v0.get("survived") or [])][:7] if str(v0.get("winner", "")).strip() == winner else [],
              standing={x: [str(s)[:160] for s in ((v0.get("standing") or {}).get(x) or [])][:7] for x in (a, b)})
    for v in verdicts:
        add_ideas(state, v.get("ideas"), mt["id"])


def finish_triage(state):
    for b in state["triage_batches"]:
        v = load_json_output(P(state, "triage", f"{b['id']}.json"))
        if not v or v.get("failed"):
            continue
        for aid in b["agents"]:
            s = (v.get("scores") or {}).get(aid)
            if s:
                state["agents"][aid]["triage"].append(total(s))
                state["agents"][aid]["triage_fatal"].append(is_fatal(s))
        add_ideas(state, v.get("ideas"), "triage")
    for a in state["agents"].values():
        a["score"] = round(sum(a["triage"]) / len(a["triage"]), 2) if a["triage"] else 0.0
    ranked = sorted(alive(state), key=lambda x: (
        not (state["agents"][x]["triage_fatal"] and all(state["agents"][x]["triage_fatal"])),
        state["agents"][x]["score"]), reverse=True)
    for aid in ranked[state["keep"]:]:
        state["agents"][aid]["status"] = "cut"
    state["log"].append(f"triage: kept {', '.join(ranked[:state['keep']])}")


def start_bracket_or_council(state):
    ids = alive(state)
    if len(ids) > state["council_size"]:
        state["stage"], state["step"] = "bracket", "attack"
        pair_round(state, ids)
    else:
        start_council(state, ids)


def advance_round(state):
    rnd = state["rounds"][-1]
    d = P(state, f"r{rnd['n']}")
    losers = []
    for mt in rnd["matches"]:
        w = mt["winner"]
        l = mt["b"] if w == mt["a"] else mt["a"]
        state["agents"][l]["status"] = "out"
        state["agents"][l]["eliminated"] = mt["id"]
        losers.append((l, mt["totals"].get(l, 0.0)))
        for x in (mt["a"], mt["b"]):
            if real_output(os.path.join(d, mt["id"], f"solution-{x}.md")):
                state["agents"][x]["solution"] = os.path.relpath(os.path.join(d, mt["id"], f"solution-{x}.md"), state["run_dir"])
        state["agents"][w]["score"] = mt["totals"].get(w, state["agents"][w]["score"])
        state["agents"][w].setdefault("survived", []).extend(mt["survived"])
    ids = alive(state)
    # Keep the council full: bring back this round's strongest losers if needed.
    if len(ids) < state["council_size"]:
        for l, t in sorted(losers, key=lambda x: -x[1]):
            if len(ids) >= state["council_size"]:
                break
            state["agents"][l]["status"] = "alive"
            state["agents"][l]["score"] = t
            ids.append(l)
    state["log"].append(f"round {rnd['n']}: {len(ids)} left ({', '.join(sorted(ids))})")
    if len(ids) > state["council_size"]:
        state["step"] = "attack"
        pair_round(state, ids)
    else:
        start_council(state, ids)


def start_council(state, ids):
    c = state["council"]
    c["members"] = sorted(ids, key=lambda a: -state["agents"][a]["score"])
    if len(c["members"]) < 2:
        start_synth(state, c["members"][0])
        return
    state["stage"], state["step"] = "council", "critique"
    c["round"] = 1


def finish_council_round(state):
    c = state["council"]
    cdir = P(state, "council", f"c{c['round']}")
    for x in c["members"]:
        p = os.path.join(cdir, f"solution-{x}.md")
        if real_output(p):
            state["agents"][x]["solution"] = os.path.relpath(p, state["run_dir"])
    v = load_json_output(os.path.join(cdir, "verdict.json")) or {"failed": True}
    entry = {"round": c["round"], "verdict_path": os.path.join(cdir, "verdict.json")}
    if v.get("failed"):
        leader = c["members"][0]
        entry.update(leader=leader, totals={}, failed=True, converged=True)
        c["history"].append(entry)
        state["log"].append(f"council {c['round']}: judge failed, stopping with {leader}")
        start_synth(state, leader)
        return
    scores = v.get("scores") or {}
    totals = {x: total(scores.get(x, {})) for x in c["members"]}
    fatal = {x: is_fatal(scores.get(x, {})) for x in c["members"]}
    standing = v.get("standing") or {}
    leader = max(c["members"], key=lambda x: (not fatal[x], totals[x]))
    sev = lambda x: [str(i.get("severity", "")).upper() if isinstance(i, dict) else "MINOR"
                     for i in (standing.get(x) or [])]
    serious = [s for s in sev(leader) if s in ("FATAL", "MAJOR")]
    prev = c["history"][-1]["totals"].get(c["history"][-1].get("leader"), 0.0) if c["history"] else None
    gain = None if prev is None else totals[leader] - prev
    converged = (
        c["round"] >= state["council_rounds"]
        or (not serious and not sev(leader) and totals[leader] >= 96)
        or (not serious and gain is not None and gain < COUNCIL_EPS)
    )
    entry.update(leader=leader, totals=totals, fatal=fatal, gain=gain, serious=len(serious),
                 standing={x: len(standing.get(x) or []) for x in c["members"]}, converged=converged)
    c["history"].append(entry)
    for x in c["members"]:
        state["agents"][x]["score"] = totals[x]
    state["log"].append(f"council {c['round']}: leader {leader} {totals[leader]}"
                        + (f" (+{gain:.1f})" if gain is not None else "") + (" converged" if converged else ""))
    if converged:
        start_synth(state, leader)
        return
    # Members far behind stop costing tokens; their ideas still reach the synthesis.
    if len(c["members"]) > 2:
        keep = [x for x in c["members"] if totals[leader] - totals[x] <= COUNCIL_DROP or x == leader]
        if len(keep) >= 2:
            c["dropped"] += [x for x in c["members"] if x not in keep]
            c["members"] = keep
    c["round"] += 1
    state["step"] = "critique"


def start_synth(state, leader):
    state["stage"], state["step"] = "synth", "synth"
    state["synth"]["leader"] = leader


def finish_compare(state, path, kind):
    v = load_json_output(path) or {"failed": True}
    blind = state.get("blind", {}).get(kind, {"X": None, "Y": None})
    if v.get("failed"):
        return None, {}, "judge failed"
    sc = v.get("scores") or {}
    t = {blind["X"]: total(sc.get("X", {})), blind["Y"]: total(sc.get("Y", {}))}
    f = {blind["X"]: is_fatal(sc.get("X", {})), blind["Y"]: is_fatal(sc.get("Y", {}))}
    win = max(t, key=lambda x: (not f[x], t[x]))
    return win, t, str(v.get("reason", ""))[:300]


def complete_step(state):
    """Called when every job of the current step has its outputs. Moves on."""
    step = state["step"]
    if step == "spawn":
        if state["n"] > state["keep"]:
            state["stage"], state["step"] = "triage", "triage"
            state["triage_batches"] = triage_batches(sorted(state["agents"]), random.Random(f"{state['seed']}-triage"))
        else:
            for a in state["agents"].values():
                a["score"] = 0.0
            start_bracket_or_council(state)
    elif step == "triage":
        finish_triage(state)
        start_bracket_or_council(state)
    elif step == "attack":
        state["step"] = "defend"
    elif step == "defend":
        state["step"] = "judge"
    elif step == "judge":
        rnd = state["rounds"][-1]
        any_close = False
        for mt in rnd["matches"]:
            v = load_json_output(P(state, f"r{rnd['n']}", mt["id"], "verdict-1.json"))
            if not v or v.get("failed"):
                mt["needs_second"] = True
            else:
                sc = v.get("scores") or {}
                ta, tb = total(sc.get(mt["a"], {})), total(sc.get(mt["b"], {}))
                fa, fb = is_fatal(sc.get(mt["a"], {})), is_fatal(sc.get(mt["b"], {}))
                mt["needs_second"] = fa == fb and abs(ta - tb) < CLOSE_MARGIN
            any_close = any_close or mt["needs_second"]
        if any_close:
            state["step"] = "judge2"
        else:
            for mt in rnd["matches"]:
                decide_match(state, mt)
            advance_round(state)
    elif step == "judge2":
        for mt in state["rounds"][-1]["matches"]:
            decide_match(state, mt)
        advance_round(state)
    elif step == "critique":
        state["step"] = "revise"
    elif step == "revise":
        state["step"] = "cjudge"
    elif step == "cjudge":
        finish_council_round(state)
    elif step == "synth":
        state["step"] = "redteam"
    elif step == "redteam":
        state["step"] = "fix"
    elif step == "fix":
        state["step"] = "compare"
    elif step == "compare":
        win, t, reason = finish_compare(state, P(state, "synth", "compare.json"), "compare")
        leader = state["synth"]["leader"]
        champ = "synth/final.md" if win in ("synth", None) and real_output(P(state, "synth", "final.md")) \
            else state["agents"][leader]["solution"]
        state["synth"].update(winner=win or "synth", totals=t, reason=reason)
        state["final"]["champion_path"] = champ
        if state["has_baseline"]:
            state["stage"], state["step"] = "final", "final"
        else:
            state["stage"], state["step"] = "done", "done"
    elif step == "final":
        win, t, reason = finish_compare(state, P(state, "final", "verdict.json"), "final")
        state["final"].update(winner=win, totals=t, reason=reason)
        state["stage"], state["step"] = "done", "done"


# ----------------------------------------------------------------- commands

def cmd_plan(args):
    rows, lo, hi = plan(args.agents or PRESETS[args.mode]["agents"], args.mode, args.keep, args.council, args.council_rounds)
    print(f"mode {args.mode}: " + ", ".join(f"{k}={v}" for k, v in PRESETS[args.mode]["models"].items()))
    print(f"{'phase':<12}{'agents':<34}{'sub-agent calls':>16}")
    for r in rows:
        print(f"{r[0]:<12}{str(r[1]):<34}{str(r[2]):>16}")
    print(f"total: {lo}-{hi} sub-agent calls (fewer when the council converges early)")


def cmd_init(args):
    if not os.path.isfile(args.task_file):
        raise DebatError(f"task file not found: {args.task_file}")
    run = os.path.join(ROOT, time.strftime("%Y%m%d-%H%M%S"))
    run_dir = os.path.abspath(run)
    os.makedirs(run_dir)
    write(os.path.join(run_dir, "task.md"), read(args.task_file))
    if args.baseline_file:
        write(os.path.join(run_dir, "baseline.md"), read(args.baseline_file))
    state = new_state(args, run_dir, args.task_file, args.baseline_file)
    add_ideas(state, [], "init")
    save_state(state)
    write(os.path.join(ROOT, "LATEST"), run_dir + "\n")
    data = load_cards()
    print(f"run {run_dir}")
    print(f"seed {state['seed']}, {state['n']} debaters, mode {state['mode']}, keep {state['keep']}, "
          f"council {state['council_size']} x up to {state['council_rounds']} rounds")
    for aid, a in sorted(state["agents"].items()):
        tag = f" [external: {a['tool']}]" if a["tool"] else ""
        print(f"  {aid}: {card_line(a['card'], data)}{tag}")
    print(f"next: python3 {shlex.quote(os.path.abspath(__file__))} next --run {shlex.quote(run_dir)}")


def tries_allowed(job):
    return MAX_TRIES["judge"] if job["kind"] in JUDGE_KINDS else MAX_TRIES["default"]


def cmd_next(args):
    run_dir = run_dir_from(args)
    state = load_state(run_dir)
    T, data = load_templates(), load_cards()
    script = os.path.abspath(__file__)
    for _ in range(100):
        if state["step"] == "done":
            save_state(state)
            print(f"DONE. Run: python3 {shlex.quote(script)} result --run {shlex.quote(run_dir)}")
            return
        jobs = jobs_for(state)
        missing = [j for j in jobs if not job_done(j)]
        gave_up = []
        for j in missing:
            if state["attempts"].get(j["id"], 0) >= tries_allowed(j):
                for o in j["outs"]:
                    if not has_output(o) or (j["kind"] in JUDGE_KINDS and load_json_output(o) is None):
                        write(o, "NO OUTPUT\n")
                gave_up.append(j["id"])
        if gave_up:
            state["log"].append(f"gave up on {', '.join(gave_up)}")
            missing = [j for j in missing if j["id"] not in gave_up]
        if missing:
            break
        complete_step(state)
        save_state(state)
    else:
        raise DebatError("state machine did not settle; inspect debat.json")
    claude_jobs, ext_jobs = [], []
    now = time.time()
    listed = state.setdefault("listed", {})
    for j in missing:
        # Count a new try only when the job had time to run since it was last
        # listed, so calling `next` twice in a row does not burn a retry.
        if now - listed.get(j["id"], 0) >= RETRY_GAP:
            state["attempts"][j["id"]] = state["attempts"].get(j["id"], 0) + 1
            listed[j["id"]] = now
        prompt = fill_prompt(state, j, T, data)
        if j.get("ext"):
            ext_jobs.append((j, prompt))
        else:
            claude_jobs.append((j, prompt))
    save_state(state)
    print(f"STEP {state['stage']}/{state['step']}: {len(missing)} job(s) to run")
    if claude_jobs:
        w = state["wave"]
        print(f"Launch with the Agent tool, subagent_type general-purpose, waves of {w} "
              "(one message per wave, wait for the wave before the next):")
        for i in range(0, len(claude_jobs), w):
            print(f"WAVE {i // w + 1}")
            for j, p in claude_jobs[i:i + w]:
                print(f"  JOB {j['id']} | model={j['model']} | prompt=Read {p} and follow it exactly. It is your whole brief.")
    if ext_jobs:
        print("Run with the Bash tool, all in parallel with run_in_background=true, from the project directory:")
        for j, p in ext_jobs:
            cmd = f"ASK_TIMEOUT=900 {shlex.quote(state['ask'])} {shlex.quote(j['ext'])} \"$(cat {shlex.quote(p)})\" > {shlex.quote(j['outs'][0])}"
            print(f"  JOB {j['id']} | bash: {cmd}")
    print(f"Then run: python3 {shlex.quote(script)} next --run {shlex.quote(run_dir)}")


def fill_prompt(state, job, T, data):
    path = P(state, "prompts", f"{job['id']}.txt")
    write(path, render(state, job, T, data))
    return path


def cmd_status(args):
    state = load_state(run_dir_from(args))
    a = alive(state)
    print(f"stage {state['stage']}, step {state['step']}, {len(a)} of {state['n']} alive: {', '.join(a)}")
    for line in state["log"][-12:]:
        print(f"  {line}")


def cmd_result(args):
    state = load_state(run_dir_from(args))
    if state["step"] != "done":
        raise DebatError(f"not finished: stage {state['stage']}, step {state['step']}. Run `next`.")
    data = load_cards()
    leader = state["synth"].get("leader")
    champ = P(state, state["final"]["champion_path"])
    rounds = len(state["rounds"])
    c = state["council"]
    out = {
        "answer_file": champ,
        "source": "synthesis of the finalists" if state["final"]["champion_path"].startswith("synth/")
        else f"council leader {leader}",
        "leader": leader,
        "leader_card": card_line(state["agents"][leader]["card"], data) if leader else None,
        "debaters": state["n"], "bracket_rounds": rounds, "council_rounds": len(c["history"]),
        "council_progress": [{"round": h["round"], "leader": h.get("leader"),
                              "leader_total": h.get("totals", {}).get(h.get("leader")), "converged": h.get("converged")}
                             for h in c["history"]],
        "survived_attacks": state["agents"][leader].get("survived", [])[:12] if leader else [],
        "synth_vs_leader": {"winner": state["synth"].get("winner"), "totals": state["synth"].get("totals"),
                            "reason": state["synth"].get("reason")},
        "baseline_check": state["final"] if state["has_baseline"] else None,
        "ideas_kept": len(state["ideas"]),
        "run_dir": state["run_dir"],
        "log": state["log"],
    }
    print(json.dumps(out, indent=2, ensure_ascii=False))


def build_parser():
    p = argparse.ArgumentParser(prog="debat.py", description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)

    def sizing(sp):
        sp.add_argument("--mode", choices=sorted(PRESETS), default="std")
        sp.add_argument("--agents", type=int)
        sp.add_argument("--keep", type=int, help="answers kept after triage")
        sp.add_argument("--council", type=int, help="council size")
        sp.add_argument("--council-rounds", type=int, dest="council_rounds")

    sp = sub.add_parser("plan", help="print the size and cost of a debate; writes nothing")
    sizing(sp)
    sp.set_defaults(func=cmd_plan)

    sp = sub.add_parser("init", help="create a debate")
    sizing(sp)
    sp.add_argument("--task-file", required=True)
    sp.add_argument("--baseline-file")
    sp.add_argument("--seed", type=int)
    sp.add_argument("--wave", type=int, default=10)
    sp.add_argument("--ext", help="comma-separated multi-agents tools that write a spawn answer (e.g. codex,opus,antigravity)")
    sp.add_argument("--ask", default=DEFAULT_ASK, help="path to multi-agents ask.sh")
    sp.add_argument("--model", action="append", help="override a role's model alias, e.g. judge=opus")
    sp.set_defaults(func=cmd_init)

    for name, fn, hlp in (("next", cmd_next, "advance as far as possible and list the jobs to run"),
                          ("status", cmd_status, "where the debate is"),
                          ("result", cmd_result, "final report as JSON")):
        sp = sub.add_parser(name, help=hlp)
        sp.add_argument("--run", help="run directory (default: .debat/LATEST)")
        sp.set_defaults(func=fn)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        args.func(args)
    except DebatError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
