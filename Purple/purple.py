#!/usr/bin/env python3
"""purple.py — state machine for the /purple skill (standard library only).

Defensive, iterative source hardening of a project the user owns. Each round:
red agents find concrete weaknesses, a judge confirms them and rates severity,
blue agents rewrite the affected files to close them, and a judge checks each
weakness is closed with no regression. The loop stops when a red round finds no
new confirmed weakness (or at the round cap). Everything runs locally, on a copy
of the project, with no network.

The orchestrator only ever runs `purple.py next`, launches the jobs it lists, and
repeats. All work lives on disk under .purple/<run>/.
"""
import argparse
import json
import os
import random
import re
import shlex
import shutil
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_PATH = os.path.join(HERE, "templates.md")
RUBRIC_PATH = os.path.join(HERE, "rubric.md")
ANGLES_PATH = os.path.join(HERE, "angles.json")
ROOT = ".purple"

SEVERITY = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
JUDGE_KINDS = {"verify", "confirm"}
# Skip these when copying the project into the isolated working tree.
IGNORE = {".git", ".purple", ".debat", "node_modules", "__pycache__", ".venv", "venv",
          ".mypy_cache", ".pytest_cache", "dist", "build", ".next", ".DS_Store", ".idea"}

PRESETS = {
    "eco": {"red": 3, "rounds": 2,
            "models": {"recon": "sonnet", "red": "sonnet", "verify": "sonnet", "blue": "sonnet",
                       "confirm": "sonnet", "report": "sonnet"}},
    "std": {"red": 4, "rounds": 3,
            "models": {"recon": "sonnet", "red": "opus", "verify": "opus", "blue": "opus",
                       "confirm": "opus", "report": "sonnet"}},
    "max": {"red": 6, "rounds": 5,
            "models": dict.fromkeys(["recon", "red", "verify", "blue", "confirm", "report"], "opus")},
}
MAX_TRIES = {"judge": 3, "default": 2}
RETRY_GAP = float(os.environ.get("PURPLE_RETRY_GAP", "30"))


class PurpleError(Exception):
    pass


# -------------------------------------------------------------- utilities

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
    return has_output(path) and read(path).strip() != "NO OUTPUT"


def extract_json(text):
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    a, b = text.find("{"), text.rfind("}")
    if a < 0 or b <= a:
        raise ValueError("no JSON object")
    return json.loads(text[a:b + 1])


def load_json_output(path):
    if not has_output(path):
        return None
    t = read(path)
    if t.strip() == "NO OUTPUT":
        return {"failed": True}
    try:
        return extract_json(t)
    except (ValueError, json.JSONDecodeError):
        return None


def copytree(src, dst):
    os.makedirs(dst, exist_ok=True)
    for name in os.listdir(src):
        if name in IGNORE:
            continue
        s, d = os.path.join(src, name), os.path.join(dst, name)
        if os.path.islink(s):
            continue
        if os.path.isdir(s):
            copytree(s, d)
        else:
            shutil.copy2(s, d)


def load_templates(path=TEMPLATES_PATH):
    text = read(path)
    return {m.group(1): m.group(2) for m in
            re.finditer(r"<!-- template:(\w+) -->\s*```text\n(.*?)\n```\s*<!-- /template:\1 -->", text, re.S)}


def fill(template, values):
    def rep(m):
        if m.group(1) not in values:
            raise PurpleError(f"missing template value: {m.group(1)}")
        return str(values[m.group(1)])
    return re.sub(r"\{\{(\w+)\}\}", rep, template)


def load_angles(path=ANGLES_PATH):
    return json.loads(read(path))["angles"]


# -------------------------------------------------------------- state

def run_dir_from(args):
    if getattr(args, "run", None):
        return os.path.abspath(args.run)
    latest = os.path.join(ROOT, "LATEST")
    if not os.path.isfile(latest):
        raise PurpleError("no run here: `purple.py init` first, from the project directory")
    return os.path.abspath(read(latest).strip())


def load_state(run_dir):
    return json.loads(read(os.path.join(run_dir, "purple.json")))


def save_state(state):
    write(os.path.join(state["run_dir"], "purple.json"), json.dumps(state, indent=2, ensure_ascii=False))


def P(state, *parts):
    return os.path.join(state["run_dir"], *parts)


def tree_dir(state, rnd):
    return P(state, f"tree-r{rnd}")


def detect_stack(root):
    marks = {"requirements.txt": "Python", "pyproject.toml": "Python", "package.json": "Node/JS",
             "composer.json": "PHP", "Gemfile": "Ruby", "go.mod": "Go", "pom.xml": "Java",
             "Cargo.toml": "Rust", "artisan": "Laravel/PHP", "manage.py": "Django/Python"}
    found = [v for f, v in marks.items() if os.path.exists(os.path.join(root, f))]
    return ", ".join(dict.fromkeys(found)) or "unknown"


def guess_test_cmd(root):
    if os.path.exists(os.path.join(root, "package.json")):
        try:
            if '"test"' in read(os.path.join(root, "package.json")):
                return "npm test"
        except OSError:
            pass
    if any(os.path.exists(os.path.join(root, f)) for f in ("pytest.ini", "pyproject.toml", "tox.ini")) \
            or os.path.isdir(os.path.join(root, "tests")):
        return "python3 -m pytest -q"
    if os.path.exists(os.path.join(root, "artisan")):
        return "php artisan test"
    if os.path.exists(os.path.join(root, "go.mod")):
        return "go test ./..."
    return ""


def new_state(args, run_dir, project):
    preset = PRESETS[args.mode]
    red_n = args.red or preset["red"]
    angles = load_angles()
    if red_n > len(angles):
        red_n = len(angles)
    os.makedirs(run_dir, exist_ok=True)
    copytree(project, tree_dir({"run_dir": run_dir}, 0))
    state = {
        "version": 1, "run_dir": run_dir, "project": os.path.abspath(project),
        "created": time.strftime("%Y-%m-%d %H:%M:%S"), "seed": args.seed if args.seed is not None else random.randrange(1, 10**6),
        "mode": args.mode, "red_n": red_n, "max_rounds": args.rounds or preset["rounds"],
        "models": dict(preset["models"]), "wave": args.wave,
        "stack": args.stack or detect_stack(project), "notes": args.notes or "",
        "test_cmd": args.test_cmd if args.test_cmd is not None else guess_test_cmd(project),
        "angles": [a["id"] for a in angles],
        "stage": "recon", "step": "recon", "round": 0,
        "rounds": [], "all_findings": [], "attempts": {}, "listed": {}, "log": [],
    }
    if args.model:
        for kv in args.model:
            role, _, alias = kv.partition("=")
            if role not in state["models"] or not alias:
                raise PurpleError(f"--model expects role=alias with role in {sorted(state['models'])}")
            state["models"][role] = alias
    return state


# -------------------------------------------------------------- round helpers

def round_angles(state, rnd):
    rng = random.Random(f"{state['seed']}-{rnd}")
    angles = load_angles()
    rng.shuffle(angles)
    # rotate so each round leads with different angles
    start = (rnd - 1) * state["red_n"] % len(angles)
    picked = [angles[(start + i) % len(angles)] for i in range(state["red_n"])]
    return picked


def confirmed_this_round(state, rnd):
    r = state["rounds"][rnd - 1]
    return r.get("confirmed", [])


def affected_files(confirmed):
    files = {}
    for f in confirmed:
        path = (f.get("file") or "").split(":")[0].strip()
        if path:
            files.setdefault(path, []).append(f)
    return files


# -------------------------------------------------------------- jobs

def jobs_for(state):
    step, m = state["step"], state["models"]
    jobs = []
    if step == "recon":
        jobs.append({"id": "recon", "kind": "recon", "model": m["recon"],
                     "outs": [P(state, "recon.md")]})
        return jobs
    rnd = state["round"]
    rd = P(state, f"r{rnd}")
    if step == "red":
        for i, angle in enumerate(round_angles(state, rnd), 1):
            aid = f"red{i}"
            jobs.append({"id": f"r{rnd}-{aid}", "kind": "red", "model": m["red"],
                         "agent": aid, "angle": angle, "outs": [os.path.join(rd, f"{aid}.md")]})
    elif step == "verify":
        jobs.append({"id": f"r{rnd}-verify", "kind": "verify", "model": m["verify"],
                     "outs": [os.path.join(rd, "verified.json")]})
    elif step == "blue":
        for path, finds in affected_files(confirmed_this_round(state, rnd)).items():
            safe = path.replace("/", "__")
            jobs.append({"id": f"r{rnd}-blue-{safe}", "kind": "blue", "model": m["blue"],
                         "rel": path, "finds": finds,
                         "outs": [os.path.join(rd, "fixes", path), os.path.join(rd, "fixes", f"{safe}.note.md")]})
    elif step == "confirm":
        jobs.append({"id": f"r{rnd}-confirm", "kind": "confirm", "model": m["confirm"],
                     "outs": [os.path.join(rd, "confirmed.json")]})
    elif step == "report":
        jobs.append({"id": "report", "kind": "report", "model": m["report"],
                     "outs": [P(state, "report.md")]})
    return jobs


def job_done(job):
    if job["kind"] in JUDGE_KINDS:
        return load_json_output(job["outs"][0]) is not None
    return all(has_output(o) for o in job["outs"])


def render(state, job, T):
    k = job["kind"]
    base = {"rubric": RUBRIC_PATH, "recon": P(state, "recon.md")}
    rnd = state.get("round", 0)
    if k == "recon":
        base.update(tree=tree_dir(state, 0), stack=state["stack"], notes=state["notes"] or "(none)",
                    out=job["outs"][0])
        return fill(T["recon"], base)
    tree = tree_dir(state, rnd - 1)
    scratch = P(state, f"r{rnd}", "scratch", job.get("agent", k))
    if k == "red":
        fixed = ""
        if rnd > 1:
            fixed = ("This code was already hardened in previous rounds. Attack the CURRENT code, "
                     "including the fixes themselves — a fix can open a new hole. Do not re-report "
                     "weaknesses already closed.")
        base.update(agent=job["agent"], round=rnd, tree=tree, scratch=scratch,
                    angle_name=job["angle"]["name"], angle_how=job["angle"]["how"],
                    fixed_note=fixed, out=job["outs"][0])
        return fill(T["red"], base)
    if k == "verify":
        reds = [os.path.join(P(state, f"r{rnd}"), f"red{i}.md") for i in range(1, state["red_n"] + 1)]
        base.update(tree=tree, proofs=P(state, f"r{rnd}", "proofs"), out=job["outs"][0],
                    findings_list="\n".join(f"- {p}" for p in reds))
        return fill(T["verify"], base)
    if k == "blue":
        rel = job["rel"]
        src = os.path.join(tree, rel)
        base.update(rel=rel, src=src if os.path.exists(src) else "(new file — create it)",
                    findings_here="\n".join(
                        f'- {f["id"]} [{f.get("severity")}] {f.get("title")} | {f.get("file")} | {f.get("impact","")}'
                        for f in job["finds"]),
                    out=job["outs"][0], note=job["outs"][1])
        return fill(T["blue"], base)
    if k == "confirm":
        finds = confirmed_this_round(state, rnd)
        notes_dir = os.path.join(P(state, f"r{rnd}"), "fixes")
        base.update(tree=tree_dir(state, rnd), regress=P(state, f"r{rnd}", "regress"),
                    test_cmd=state["test_cmd"] or "(none detected)",
                    notes=notes_dir, out=job["outs"][0],
                    findings_list="\n".join(
                        f'- {f["id"]} [{f.get("severity")}] {f.get("title")} | {f.get("file")} | proof: {f.get("proof")}'
                        for f in finds))
        return fill(T["confirm"], base)
    if k == "report":
        base.update(project=state["project"], rounds=len(state["rounds"]),
                    record=P(state, "record.json"), diff=P(state, "hardening.diff"), out=job["outs"][0])
        return fill(T["report"], base)
    raise PurpleError(f"no template for {k}")


# -------------------------------------------------------------- step completion

def build_patched_tree(state, rnd):
    """tree-r{rnd} = tree-r{rnd-1} with this round's blue files overlaid."""
    prev, cur = tree_dir(state, rnd - 1), tree_dir(state, rnd)
    if os.path.isdir(cur):
        shutil.rmtree(cur)
    copytree(prev, cur)
    fixes = P(state, f"r{rnd}", "fixes")
    applied = []
    for path in affected_files(confirmed_this_round(state, rnd)):
        src = os.path.join(fixes, path)
        if real_output(src):
            dst = os.path.join(cur, path)
            os.makedirs(os.path.dirname(dst) or cur, exist_ok=True)
            shutil.copy2(src, dst)
            applied.append(path)
    return applied


def finish_verify(state):
    rnd = state["round"]
    v = load_json_output(P(state, f"r{rnd}", "verified.json")) or {"failed": True}
    r = state["rounds"][rnd - 1]
    confirmed = [] if v.get("failed") else v.get("confirmed", [])
    # stable unique ids across the whole run
    for i, f in enumerate(confirmed, 1):
        f["id"] = f.get("id") or f"r{rnd}f{i}"
        f["round"] = rnd
    r["confirmed"] = confirmed
    r["rejected"] = [] if v.get("failed") else v.get("rejected", [])
    state["all_findings"].extend(confirmed)
    state["log"].append(f"round {rnd}: {len(confirmed)} confirmed, {len(r['rejected'])} rejected")


def finish_confirm(state):
    rnd = state["round"]
    c = load_json_output(P(state, f"r{rnd}", "confirmed.json")) or {"failed": True}
    r = state["rounds"][rnd - 1]
    r["fix_results"] = [] if c.get("failed") else c.get("results", [])
    r["regressions"] = {} if c.get("failed") else c.get("regressions", {})
    closed = sum(1 for x in r["fix_results"] if x.get("status") == "CLOSED")
    r["closed"] = closed
    state["log"].append(f"round {rnd}: {closed}/{len(r['fix_results'])} closed, "
                        f"regressions {'broken' if r['regressions'].get('broke') else 'ok'}")


def write_record_and_diff(state):
    record = [{"round": r["n"], "confirmed": r.get("confirmed", []), "fix_results": r.get("fix_results", []),
               "regressions": r.get("regressions", {})} for r in state["rounds"]]
    write(P(state, "record.json"), json.dumps(record, indent=2, ensure_ascii=False))
    # unified diff original -> final hardened tree
    final = tree_dir(state, state["round"])
    import difflib
    out = []
    for dirpath, dirs, files in os.walk(final):
        dirs[:] = [d for d in dirs if d not in IGNORE]
        for fn in files:
            fp = os.path.join(dirpath, fn)
            rel = os.path.relpath(fp, final)
            orig = os.path.join(tree_dir(state, 0), rel)
            try:
                new = read(fp).splitlines(keepends=True)
                old = read(orig).splitlines(keepends=True) if os.path.exists(orig) else []
            except (OSError, UnicodeDecodeError):
                continue
            if old != new:
                out += list(difflib.unified_diff(old, new, f"a/{rel}", f"b/{rel}"))
    write(P(state, "hardening.diff"), "".join(out) or "(no changes)\n")


def complete_step(state):
    step = state["step"]
    if step == "recon":
        start_round(state, 1)
    elif step == "red":
        state["step"] = "verify"
    elif step == "verify":
        finish_verify(state)
        if not confirmed_this_round(state, state["round"]):
            # a clean red round: hardening has converged
            state["rounds"][state["round"] - 1]["clean"] = True
            # carry the previous patched tree forward as the final tree
            if not os.path.isdir(tree_dir(state, state["round"])):
                copytree(tree_dir(state, state["round"] - 1), tree_dir(state, state["round"]))
            finish_run(state)
        else:
            state["step"] = "blue"
    elif step == "blue":
        build_patched_tree(state, state["round"])
        state["step"] = "confirm"
    elif step == "confirm":
        finish_confirm(state)
        rnd = state["round"]
        still_open = [x for x in state["rounds"][rnd - 1].get("fix_results", [])
                      if x.get("status") in ("OPEN", "PARTIAL")]
        if rnd >= state["max_rounds"]:
            state["rounds"][rnd - 1]["stopped_at_cap"] = True
            finish_run(state)
        else:
            start_round(state, rnd + 1)
    elif step == "report":
        state["stage"], state["step"] = "done", "done"


def start_round(state, rnd):
    state["round"] = rnd
    state["stage"], state["step"] = f"round{rnd}", "red"
    state["rounds"].append({"n": rnd, "confirmed": [], "rejected": [], "fix_results": []})


def finish_run(state):
    write_record_and_diff(state)
    state["stage"], state["step"] = "report", "report"


# -------------------------------------------------------------- next / cli

def tries_allowed(job):
    return MAX_TRIES["judge"] if job["kind"] in JUDGE_KINDS else MAX_TRIES["default"]


def cmd_next(args):
    run_dir = run_dir_from(args)
    state = load_state(run_dir)
    T = load_templates()
    script = os.path.abspath(__file__)
    for _ in range(60):
        if state["step"] == "done":
            save_state(state)
            print(f"DONE. Run: python3 {shlex.quote(script)} result --run {shlex.quote(run_dir)}")
            return
        jobs = jobs_for(state)
        missing = [j for j in jobs if not job_done(j)]
        gave_up = []
        for j in list(missing):
            if state["attempts"].get(j["id"], 0) >= tries_allowed(j):
                for o in j["outs"]:
                    if not has_output(o) or (j["kind"] in JUDGE_KINDS and load_json_output(o) is None):
                        write(o, "NO OUTPUT\n")
                gave_up.append(j["id"])
                missing.remove(j)
        if gave_up:
            state["log"].append(f"gave up on {', '.join(gave_up)}")
        if missing:
            break
        complete_step(state)
        save_state(state)
    else:
        raise PurpleError("state machine did not settle; inspect purple.json")

    now = time.time()
    listed = state.setdefault("listed", {})
    for j in missing:
        if now - listed.get(j["id"], 0) >= RETRY_GAP:
            state["attempts"][j["id"]] = state["attempts"].get(j["id"], 0) + 1
            listed[j["id"]] = now
        write(P(state, "prompts", f"{j['id']}.txt"), render(state, j, T))
    save_state(state)
    w = state["wave"]
    print(f"STEP {state['stage']}/{state['step']}: {len(missing)} job(s)")
    print(f"Launch with the Agent tool, subagent_type general-purpose, waves of {w} "
          "(one message per wave, wait for each wave):")
    for i in range(0, len(missing), w):
        print(f"WAVE {i // w + 1}")
        for j in missing[i:i + w]:
            p = P(state, "prompts", f"{j['id']}.txt")
            print(f"  JOB {j['id']} | model={j['model']} | prompt=Read {p} and follow it exactly. It is your whole brief.")
    print(f"Then run: python3 {shlex.quote(script)} next --run {shlex.quote(run_dir)}")


def cmd_init(args):
    project = os.path.abspath(args.project)
    if not os.path.isdir(project):
        raise PurpleError(f"project folder not found: {project}")
    run = os.path.join(ROOT, time.strftime("%Y%m%d-%H%M%S"))
    run_dir = os.path.abspath(run)
    state = new_state(args, run_dir, project)
    save_state(state)
    write(os.path.join(ROOT, "LATEST"), run_dir + "\n")
    print(f"run {run_dir}")
    print(f"project {project} | stack {state['stack']} | mode {state['mode']} | "
          f"{state['red_n']} red agents x up to {state['max_rounds']} rounds")
    print(f"test command: {state['test_cmd'] or '(none detected — set with --test-cmd for regression checks)'}")
    print(f"next: python3 {shlex.quote(os.path.abspath(__file__))} next --run {shlex.quote(run_dir)}")


def cmd_plan(args):
    pr = PRESETS[args.mode]
    red = args.red or pr["red"]
    rounds = args.rounds or pr["rounds"]
    print(f"mode {args.mode}: {red} red agents, up to {rounds} rounds")
    print(f"models: " + ", ".join(f"{k}={v}" for k, v in pr["models"].items()))
    per_round = red + 1 + 2 + 1  # red + verify + (blue files, ~2) + confirm
    print(f"per round: ~{per_round} sub-agent calls (more if many files are patched)")
    print(f"total: recon + up to {rounds} rounds ≈ {1 + rounds * per_round} calls; "
          "fewer when a clean round ends it early, plus 1 for the report")


def cmd_status(args):
    state = load_state(run_dir_from(args))
    print(f"stage {state['stage']}, step {state['step']}, round {state['round']}/{state['max_rounds']}")
    for line in state["log"][-12:]:
        print(f"  {line}")


def cmd_result(args):
    state = load_state(run_dir_from(args))
    if state["step"] != "done":
        raise PurpleError(f"not finished: {state['stage']}/{state['step']}. Run `next`.")
    allf = state["all_findings"]
    by_sev = {s: sum(1 for f in allf if (f.get("severity") or "").upper() == s) for s in SEVERITY}
    last = state["rounds"][-1]
    results = {x["id"]: x for r in state["rounds"] for x in r.get("fix_results", [])}
    closed = sum(1 for x in results.values() if x.get("status") == "CLOSED")
    still_open = [x for x in results.values() if x.get("status") in ("OPEN", "PARTIAL")]
    out = {
        "project": state["project"],
        "report_file": P(state, "report.md"),
        "hardened_tree": tree_dir(state, state["round"]),
        "diff_file": P(state, "hardening.diff"),
        "rounds": len(state["rounds"]),
        "stopped_because": "clean red round" if last.get("clean") else
                           ("round cap" if last.get("stopped_at_cap") else "finished"),
        "findings_total": len(allf),
        "by_severity": by_sev,
        "closed": closed,
        "still_open": [{"id": x["id"], "status": x["status"], "note": x.get("note", "")} for x in still_open],
        "regressions_last_round": last.get("regressions", {}),
        "run_dir": state["run_dir"],
        "log": state["log"],
    }
    print(json.dumps(out, indent=2, ensure_ascii=False))


def build_parser():
    p = argparse.ArgumentParser(prog="purple.py", description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)

    def sizing(sp):
        sp.add_argument("--mode", choices=sorted(PRESETS), default="std")
        sp.add_argument("--red", type=int, help="number of red agents per round")
        sp.add_argument("--rounds", type=int, help="max rounds")

    sp = sub.add_parser("plan", help="print size and cost; writes nothing")
    sizing(sp)
    sp.set_defaults(func=cmd_plan)

    sp = sub.add_parser("init", help="start a hardening run on a project folder")
    sizing(sp)
    sp.add_argument("--project", required=True, help="path to the project to harden (a copy is made)")
    sp.add_argument("--stack", help="override detected stack")
    sp.add_argument("--notes", help="anything the agents should know about the app")
    sp.add_argument("--test-cmd", dest="test_cmd", help="command that runs the project's tests (for regression checks)")
    sp.add_argument("--seed", type=int)
    sp.add_argument("--wave", type=int, default=10)
    sp.add_argument("--model", action="append", help="override a role's model alias, e.g. red=opus")
    sp.set_defaults(func=cmd_init)

    for name, fn, hlp in (("next", cmd_next, "advance and list the jobs to run"),
                          ("status", cmd_status, "where the run is"),
                          ("result", cmd_result, "final summary as JSON")):
        sp = sub.add_parser(name, help=hlp)
        sp.add_argument("--run", help="run directory (default: .purple/LATEST)")
        sp.set_defaults(func=fn)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        args.func(args)
    except PurpleError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
