"""End-to-end tests for debat.py with stand-in sub-agents.

Run from the Debat folder:  python3 -m unittest discover -s tests -v
"""
import io
import json
import os
import random
import re
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import debat  # noqa: E402


def run_cli(*argv):
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = debat.main(list(argv))
    return code, buf.getvalue()


def fake_scores(rng, ids, fatal_ids=()):
    return {a: {"correctness": rng.randint(3, 10), "requirements": rng.randint(3, 10),
                "robustness": rng.randint(3, 10), "actionability": rng.randint(3, 10),
                "clarity": rng.randint(3, 10), "fatal": a in fatal_ids} for a in ids}


class StandIn:
    """Plays every sub-agent: writes plausible outputs for each listed job."""

    def __init__(self, seed=0, fail_ids=(), fatal_ids=(), bad_json_once=()):
        self.rng = random.Random(seed)
        self.fail_ids = set(fail_ids)
        self.fatal_ids = set(fatal_ids)
        self.bad_json_once = set(bad_json_once)
        self.prompts_seen = []

    def play(self, state, job):
        if job["id"] in self.fail_ids:
            return
        k = job["kind"]
        if job["id"] in self.bad_json_once and k in debat.JUDGE_KINDS:
            self.bad_json_once.discard(job["id"])
            debat.write(job["outs"][0], "I think A is better.")
            return
        if k in ("competitor", "attacker", "critique", "synth", "redteam"):
            debat.write(job["outs"][0], f"answer from {job['id']}\n")
        elif k in ("defender", "revise", "fix"):
            debat.write(job["outs"][0], "ATTACK 1: CONCEDE. fixed\n")
            debat.write(job["outs"][1], f"revised by {job['id']}\n")
        elif k == "triage":
            ids = job["batch"]["agents"]
            debat.write(job["outs"][0], json.dumps({"scores": fake_scores(self.rng, ids, self.fatal_ids),
                                                    "ideas": [{"from": ids[0], "idea": f"idea {self.rng.random()}"}]}))
        elif k in ("judge", "judge2"):
            f, s = job["order"]
            sc = fake_scores(self.rng, (f, s), self.fatal_ids)
            w = max((f, s), key=lambda x: debat.total(sc[x]))
            debat.write(job["outs"][0], "```json\n" + json.dumps({
                "scores": sc, "winner": w, "reason": "r", "survived": ["a1"], "standing": {f: [], s: []},
                "ideas": [{"from": s, "idea": "keep the cache invalidation trick"}]}) + "\n```")
        elif k == "cjudge":
            mem = state["council"]["members"]
            sc = fake_scores(self.rng, mem)
            debat.write(job["outs"][0], json.dumps({
                "scores": sc, "standing": {m: [{"severity": "MINOR", "issue": "x"}] for m in mem},
                "leader": mem[0], "reason": "r"}))
        elif k in ("compare", "final"):
            sc = fake_scores(self.rng, ("X", "Y"))
            debat.write(job["outs"][0], json.dumps({"scores": sc, "winner": "X", "reason": "r", "better": []}))
        else:
            raise AssertionError(f"unknown kind {k}")


def drive(testcase, standin, max_loops=400):
    """Loop `next` like the orchestrator would, playing every job it lists."""
    for _ in range(max_loops):
        code, out = run_cli("next")
        testcase.assertEqual(code, 0, out)
        if out.startswith("DONE"):
            return
        listed = re.findall(r"JOB (\S+) \|", out)
        testcase.assertTrue(listed, out)
        state = debat.load_state(debat.run_dir_from(type("A", (), {"run": None})()))
        jobs = {j["id"]: j for j in debat.jobs_for(state)}
        for jid in listed:
            testcase.assertIn(jid, jobs)
            prompt = os.path.join(state["run_dir"], "prompts", f"{jid}.txt")
            text = debat.read(prompt)
            testcase.assertNotIn("{{", text, f"unfilled placeholder in {jid}")
            standin.prompts_seen.append(text)
            standin.play(state, jobs[jid])
    testcase.fail("debate did not finish")


class DebatTests(unittest.TestCase):
    def setUp(self):
        debat.RETRY_GAP = 0  # stand-ins answer instantly
        self.tmp = tempfile.mkdtemp()
        self.old = os.getcwd()
        os.chdir(self.tmp)
        debat.write("task.md", "Write the best possible function to merge two sorted lists.\n")
        debat.write("baseline.md", "Just concatenate and sort.\n")

    def tearDown(self):
        os.chdir(self.old)
        shutil.rmtree(self.tmp)

    def result(self):
        code, out = run_cli("result")
        self.assertEqual(code, 0, out)
        return json.loads(out)

    def test_templates_and_cards_load(self):
        T = debat.load_templates()
        for name in ("competitor", "competitor_ext", "triage", "attacker", "defender", "judge",
                     "critique", "revise", "cjudge", "synth", "redteam", "fix", "compare"):
            self.assertIn(name, T)
        data = debat.load_cards()
        self.assertGreaterEqual(len(data["reasoning"]) * len(data["methods"]) * len(data["priorities"]), 1000)

    def test_deal_is_distinct_and_balanced(self):
        data = debat.load_cards()
        for n in (2, 12, 32, 100):
            hand = debat.deal(n, random.Random(n), data)
            combos = {(c["reasoning"], c["method"], c["priority"]) for c in hand}
            self.assertEqual(len(combos), n)
            counts = {}
            for c in hand:
                counts[c["reasoning"]] = counts.get(c["reasoning"], 0) + 1
            self.assertLessEqual(max(counts.values()) - min(counts.values()), 1 if n >= len(data["reasoning"]) else 1)

    def test_same_seed_same_cards(self):
        run_cli("init", "--task-file", "task.md", "--seed", "7")
        a = debat.load_state(debat.run_dir_from(type("A", (), {"run": None})()))
        cards_a = [v["card"] for _, v in sorted(a["agents"].items())]
        import time; time.sleep(1.1)
        run_cli("init", "--task-file", "task.md", "--seed", "7")
        b = debat.load_state(debat.run_dir_from(type("A", (), {"run": None})()))
        self.assertEqual(cards_a, [v["card"] for _, v in sorted(b["agents"].items())])

    def test_full_std_debate_with_baseline(self):
        code, out = run_cli("init", "--task-file", "task.md", "--baseline-file", "baseline.md", "--seed", "3")
        self.assertEqual(code, 0, out)
        drive(self, StandIn(seed=3))
        r = self.result()
        self.assertTrue(os.path.isfile(r["answer_file"]))
        self.assertEqual(r["debaters"], 12)
        self.assertGreaterEqual(r["council_rounds"], 1)
        self.assertIsNotNone(r["baseline_check"]["winner"])
        state = debat.load_state(r["run_dir"])
        self.assertEqual(sum(1 for a in state["agents"].values() if a["status"] == "cut"), 4)
        self.assertTrue(state["ideas"])
        # Every debater got the task byte for byte.
        task = debat.read(os.path.join(r["run_dir"], "task.md"))
        spawn_prompts = [p for p in os.listdir(os.path.join(r["run_dir"], "prompts")) if p.startswith("spawn-")]
        self.assertEqual(len(spawn_prompts), 12)
        for p in spawn_prompts:
            self.assertIn(task, debat.read(os.path.join(r["run_dir"], "prompts", p)))

    def test_eco_and_max_sizes_finish(self):
        for mode, n in (("eco", None), ("max", None), ("std", 2), ("std", 3), ("std", 5), ("std", 100)):
            args = ["init", "--task-file", "task.md", "--mode", mode, "--seed", "11"]
            if n:
                args += ["--agents", str(n)]
            code, out = run_cli(*args)
            self.assertEqual(code, 0, out)
            drive(self, StandIn(seed=11), max_loops=800)
            r = self.result()
            self.assertTrue(os.path.isfile(r["answer_file"]), (mode, n))
            shutil.rmtree(debat.ROOT)

    def test_failures_are_retried_then_skipped(self):
        run_cli("init", "--task-file", "task.md", "--seed", "5")
        # d01 never answers; a judge returns prose once, then valid JSON.
        drive(self, StandIn(seed=5, fail_ids={"spawn-d01"}, bad_json_once={"triage-t01"}))
        r = self.result()
        state = debat.load_state(r["run_dir"])
        self.assertEqual(debat.read(os.path.join(r["run_dir"], "spawn", "d01.md")).strip(), "NO OUTPUT")
        self.assertTrue(any("gave up" in line for line in state["log"]))
        self.assertTrue(os.path.isfile(r["answer_file"]))

    def test_fatal_never_beats_non_fatal(self):
        run_cli("init", "--task-file", "task.md", "--seed", "9", "--agents", "4", "--keep", "4", "--council", "2")
        state = debat.load_state(debat.run_dir_from(type("A", (), {"run": None})()))
        debat.complete_step(state)  # spawn -> bracket (no triage: n == keep)
        mt = state["rounds"][-1]["matches"][0]
        d = os.path.join(state["run_dir"], "r1", mt["id"])
        good = {"correctness": 5, "requirements": 5, "robustness": 5, "actionability": 5, "clarity": 5, "fatal": False}
        bad = {"correctness": 10, "requirements": 10, "robustness": 10, "actionability": 10, "clarity": 10, "fatal": True}
        debat.write(os.path.join(d, "verdict-1.json"),
                    json.dumps({"scores": {mt["a"]: bad, mt["b"]: good}, "winner": mt["a"]}))
        debat.decide_match(state, mt)
        self.assertEqual(mt["winner"], mt["b"])

    def test_close_match_gets_second_judge(self):
        run_cli("init", "--task-file", "task.md", "--seed", "4", "--agents", "4", "--keep", "4", "--council", "2")
        state = debat.load_state(debat.run_dir_from(type("A", (), {"run": None})()))
        debat.complete_step(state)
        state["step"] = "judge"
        same = {"correctness": 7, "requirements": 7, "robustness": 7, "actionability": 7, "clarity": 7, "fatal": False}
        for mt in state["rounds"][-1]["matches"]:
            debat.write(os.path.join(state["run_dir"], "r1", mt["id"], "verdict-1.json"),
                        json.dumps({"scores": {mt["a"]: same, mt["b"]: same}, "winner": mt["a"]}))
        debat.complete_step(state)
        self.assertEqual(state["step"], "judge2")
        jobs = debat.jobs_for(state)
        self.assertEqual(len(jobs), len(state["rounds"][-1]["matches"]))
        self.assertEqual(jobs[0]["order"], (jobs[0]["match"]["b"], jobs[0]["match"]["a"]))

    def test_council_converges_on_plateau(self):
        run_cli("init", "--task-file", "task.md", "--seed", "8", "--agents", "3", "--keep", "3",
                "--council", "3", "--council-rounds", "6")
        state = debat.load_state(debat.run_dir_from(type("A", (), {"run": None})()))
        debat.complete_step(state)
        self.assertEqual(state["stage"], "council")
        flat = {"correctness": 8, "requirements": 8, "robustness": 8, "actionability": 8, "clarity": 8, "fatal": False}
        for rnd in (1, 2):
            state["step"] = "cjudge"
            cdir = os.path.join(state["run_dir"], "council", f"c{state['council']['round']}")
            mem = state["council"]["members"]
            debat.write(os.path.join(cdir, "verdict.json"), json.dumps(
                {"scores": {m: flat for m in mem}, "standing": {m: [] for m in mem}, "leader": mem[0]}))
            debat.complete_step(state)
        self.assertEqual(state["stage"], "synth")
        self.assertEqual(len(state["council"]["history"]), 2)
        self.assertTrue(state["council"]["history"][-1]["converged"])

    def test_plan_prints(self):
        code, out = run_cli("plan", "--mode", "max")
        self.assertEqual(code, 0)
        self.assertIn("total:", out)

    def test_ext_requires_helper(self):
        code, _ = run_cli("init", "--task-file", "task.md", "--ext", "codex", "--ask", "/nonexistent/ask.sh")
        self.assertEqual(code, 1)

    def test_ext_jobs_are_bash_commands(self):
        fake_ask = os.path.join(self.tmp, "ask.sh")
        debat.write(fake_ask, "#!/bin/bash\necho answer\n")
        os.chmod(fake_ask, 0o755)
        run_cli("init", "--task-file", "task.md", "--seed", "2", "--ext", "codex,opus", "--ask", fake_ask)
        code, out = run_cli("next")
        self.assertIn("bash:", out)
        self.assertEqual(out.count("bash:"), 2)
        self.assertIn(fake_ask, out)


if __name__ == "__main__":
    unittest.main()
