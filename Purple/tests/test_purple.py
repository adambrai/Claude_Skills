"""End-to-end tests for purple.py with stand-in sub-agents.

Run from the Purple folder:  python3 -m unittest discover -s tests -v
"""
import io
import json
import os
import re
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import purple  # noqa: E402


def run_cli(*argv):
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = purple.main(list(argv))
    return code, buf.getvalue()


class StandIn:
    """Plays every sub-agent. `finds_per_round` controls how many weaknesses red
    'finds' each round, so we can drive convergence."""

    def __init__(self, finds_per_round=(2, 0), fail_ids=()):
        self.finds_per_round = finds_per_round
        self.fail_ids = set(fail_ids)

    def n_finds(self, rnd):
        i = rnd - 1
        return self.finds_per_round[i] if i < len(self.finds_per_round) else 0

    def play(self, state, job):
        if job["id"] in self.fail_ids:
            return
        k = job["kind"]
        if k == "recon":
            purple.write(job["outs"][0], "# Map\nEntry: app.py:10 GET /u\nSink: app.py:20 db query\n")
        elif k == "red":
            n = self.n_finds(state["round"])
            lines = [f"FINDING {i} [HIGH] weakness {i}\nSink: app.py:{20+i}\nReaches it: /u?id=\nImpact: x\nProof idea: y"
                     for i in range(1, n + 1)] or ["NO NEW FINDINGS"]
            purple.write(job["outs"][0], "\n".join(lines))
        elif k == "verify":
            n = self.n_finds(state["round"])
            confirmed = [{"id": f"f{i}", "severity": "HIGH", "title": f"w{i}", "file": "app.py:20",
                          "class": "sql-injection", "input": "/u?id=", "impact": "x", "proof": None}
                         for i in range(1, n + 1)]
            purple.write(job["outs"][0], json.dumps({"confirmed": confirmed, "rejected": [{"title": "fp", "why": "no"}]}))
        elif k == "blue":
            purple.write(job["outs"][0], "# hardened app.py\nquery(db, '...', (id,))\n")
            purple.write(job["outs"][1], "f1: parameterized the query\n")
        elif k == "confirm":
            finds = purple.confirmed_this_round(state, state["round"])
            res = [{"id": f["id"], "status": "CLOSED", "proof_now": "skipped",
                    "regress_test": None, "note": "ok"} for f in finds]
            purple.write(job["outs"][0], json.dumps(
                {"results": res, "regressions": {"ran": True, "command": "pytest", "passed": True, "broke": []}}))
        elif k == "report":
            purple.write(job["outs"][0], "# Rapport\nTout est corrigé.\n")
        else:
            raise AssertionError(f"unknown kind {k}")


def drive(testcase, standin, max_loops=200):
    for _ in range(max_loops):
        code, out = run_cli("next")
        testcase.assertEqual(code, 0, out)
        if out.startswith("DONE"):
            return
        listed = re.findall(r"JOB (\S+) \|", out)
        testcase.assertTrue(listed, out)
        state = purple.load_state(purple.run_dir_from(type("A", (), {"run": None})()))
        jobs = {j["id"]: j for j in purple.jobs_for(state)}
        for jid in listed:
            testcase.assertIn(jid, jobs)
            prompt = os.path.join(state["run_dir"], "prompts", f"{jid}.txt")
            text = purple.read(prompt)
            testcase.assertNotIn("{{", text, f"unfilled placeholder in {jid}")
            standin.play(state, jobs[jid])
    testcase.fail("run did not finish")


class PurpleTests(unittest.TestCase):
    def setUp(self):
        purple.RETRY_GAP = 0
        self.tmp = tempfile.mkdtemp()
        self.old = os.getcwd()
        self.proj = os.path.join(self.tmp, "proj")
        os.makedirs(os.path.join(self.proj, "node_modules"))  # must be ignored
        purple.write(os.path.join(self.proj, "app.py"), "def q(id):\n    db.execute('select * from u where id='+id)\n")
        purple.write(os.path.join(self.proj, "requirements.txt"), "flask\n")
        purple.write(os.path.join(self.proj, "node_modules", "junk.js"), "x\n")
        os.makedirs(os.path.join(self.tmp, "work"))
        os.chdir(os.path.join(self.tmp, "work"))

    def tearDown(self):
        os.chdir(self.old)
        shutil.rmtree(self.tmp)

    def result(self):
        code, out = run_cli("result")
        self.assertEqual(code, 0, out)
        return json.loads(out)

    def test_templates_and_angles(self):
        T = purple.load_templates()
        for n in ("recon", "red", "verify", "blue", "confirm", "report"):
            self.assertIn(n, T)
        self.assertGreaterEqual(len(purple.load_angles()), 6)

    def test_copytree_ignores_node_modules(self):
        run_cli("init", "--project", self.proj, "--seed", "1")
        state = purple.load_state(purple.run_dir_from(type("A", (), {"run": None})()))
        tree0 = purple.tree_dir(state, 0)
        self.assertTrue(os.path.exists(os.path.join(tree0, "app.py")))
        self.assertFalse(os.path.exists(os.path.join(tree0, "node_modules")))
        self.assertEqual(state["stack"], "Python")

    def test_converges_when_red_finds_nothing(self):
        run_cli("init", "--project", self.proj, "--mode", "eco", "--seed", "2")
        # round 1 finds 2, gets fixed; round 2 finds 0 -> clean -> stop
        drive(self, StandIn(finds_per_round=(2, 0)))
        r = self.result()
        self.assertEqual(r["stopped_because"], "clean red round")
        self.assertEqual(r["findings_total"], 2)
        self.assertEqual(r["closed"], 2)
        self.assertTrue(os.path.isfile(r["report_file"]))
        self.assertTrue(os.path.isfile(r["diff_file"]))
        # the hardened tree differs from the original
        diff = purple.read(r["diff_file"])
        self.assertIn("app.py", diff)

    def test_stops_at_round_cap(self):
        run_cli("init", "--project", self.proj, "--mode", "eco", "--rounds", "2", "--seed", "3")
        # finds weaknesses every round -> never clean -> stops at cap (2)
        drive(self, StandIn(finds_per_round=(2, 2, 2, 2)))
        r = self.result()
        self.assertEqual(r["stopped_because"], "round cap")
        self.assertEqual(r["rounds"], 2)

    def test_patched_tree_overlays_blue_files(self):
        run_cli("init", "--project", self.proj, "--mode", "eco", "--seed", "4")
        drive(self, StandIn(finds_per_round=(1, 0)))
        state = purple.load_state(purple.run_dir_from(type("A", (), {"run": None})()))
        hardened = purple.read(os.path.join(purple.tree_dir(state, 1), "app.py"))
        self.assertIn("hardened", hardened)  # blue's version was applied
        original = purple.read(os.path.join(self.proj, "app.py"))
        self.assertNotIn("hardened", original)  # user's real project untouched

    def test_real_project_never_modified(self):
        before = purple.read(os.path.join(self.proj, "app.py"))
        run_cli("init", "--project", self.proj, "--mode", "eco", "--seed", "5")
        drive(self, StandIn(finds_per_round=(2, 0)))
        self.assertEqual(before, purple.read(os.path.join(self.proj, "app.py")))

    def test_failed_agents_retry_then_skip(self):
        run_cli("init", "--project", self.proj, "--mode", "eco", "--seed", "6")
        drive(self, StandIn(finds_per_round=(2, 0), fail_ids={"recon"}))
        state = purple.load_state(purple.run_dir_from(type("A", (), {"run": None})()))
        self.assertEqual(purple.read(os.path.join(state["run_dir"], "recon.md")).strip(), "NO OUTPUT")
        self.assertTrue(any("gave up" in l for l in state["log"]))

    def test_plan_and_status(self):
        code, out = run_cli("plan", "--mode", "max")
        self.assertEqual(code, 0)
        self.assertIn("total:", out)


if __name__ == "__main__":
    unittest.main()
