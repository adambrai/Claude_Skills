"""Tests for audit_context.py and merge_block.py. Run from the Fourmi folder:
python3 -m unittest discover -s tests -v
"""
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import audit_context  # noqa: E402
import merge_block  # noqa: E402


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


class AuditContextTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = os.path.join(self.tmp.name, "home")
        self.project = os.path.join(self.tmp.name, "projet")
        os.makedirs(self.home)
        os.makedirs(self.project)
        self.old_home = audit_context.HOME
        audit_context.HOME = self.home

    def tearDown(self):
        audit_context.HOME = self.old_home
        self.tmp.cleanup()

    def test_empty_project_suggests_a_claude_md(self):
        r = audit_context.audit(self.project)
        self.assertEqual(r["memory_tokens"], 0)
        self.assertTrue(any("Aucun CLAUDE.md" in a for a in r["advice"]))

    def test_imports_are_counted(self):
        write(os.path.join(self.project, "CLAUDE.md"), "Règles.\nVoir @docs/style.md\n")
        write(os.path.join(self.project, "docs", "style.md"), "x" * 4000)
        r = audit_context.audit(self.project)
        entry = r["claude_md_always"][0]
        self.assertEqual(len(entry["imports"]), 1)
        self.assertGreaterEqual(r["memory_tokens"], 1000)

    def test_imports_inside_code_blocks_are_ignored(self):
        write(os.path.join(self.project, "CLAUDE.md"), "```\n@docs/style.md\n```\n")
        write(os.path.join(self.project, "docs", "style.md"), "x" * 4000)
        r = audit_context.audit(self.project)
        self.assertEqual(r["claude_md_always"][0]["imports"], [])

    def test_import_cycle_does_not_loop(self):
        write(os.path.join(self.project, "CLAUDE.md"), "@a.md\n")
        write(os.path.join(self.project, "a.md"), "@CLAUDE.md\n")
        r = audit_context.audit(self.project)
        self.assertEqual(len(r["claude_md_always"][0]["imports"]), 1)

    def test_global_and_nested_claude_md(self):
        write(os.path.join(self.home, ".claude", "CLAUDE.md"), "global\n")
        write(os.path.join(self.project, "src", "CLAUDE.md"), "local\n")
        r = audit_context.audit(self.project)
        self.assertEqual(len(r["claude_md_always"]), 1)
        self.assertEqual(len(r["claude_md_nested"]), 1)

    def test_long_claude_md_is_flagged(self):
        write(os.path.join(self.project, "CLAUDE.md"), "règle\n" * 2000)
        r = audit_context.audit(self.project)
        self.assertTrue(any("tokens à lui seul" in a for a in r["advice"]))

    def test_skill_description_is_measured(self):
        write(os.path.join(self.home, ".claude", "skills", "demo", "SKILL.md"),
              "---\nname: demo\ndescription: >-\n  Une description\n  sur deux lignes.\n---\n\nCorps.\n")
        r = audit_context.audit(self.project)
        self.assertEqual(r["skills"], 1)
        self.assertGreater(r["skill_description_tokens"], 0)

    def test_mcp_servers_report_names_only(self):
        write(os.path.join(self.project, ".mcp.json"),
              json.dumps({"mcpServers": {"base": {"env": {"TOKEN": "secret-value-123"}}}}))
        r = audit_context.audit(self.project)
        self.assertEqual(r["mcp_servers"], [{"name": "base", "scope": "project (.mcp.json)"}])
        self.assertNotIn("secret-value-123", json.dumps(r))

    def test_big_file_without_deny_rule_is_flagged(self):
        write(os.path.join(self.project, "data.json"), "x" * (audit_context.BIG_FILE + 10))
        r = audit_context.audit(self.project)
        self.assertEqual(r["big_files"][0]["file"], "data.json")
        self.assertTrue(any("data.json" in a for a in r["advice"]))

    def test_big_file_with_deny_rule_is_not_flagged(self):
        write(os.path.join(self.project, "data.json"), "x" * (audit_context.BIG_FILE + 10))
        write(os.path.join(self.project, ".claude", "settings.json"),
              json.dumps({"permissions": {"deny": ["Read(./data.json)"]}}))
        r = audit_context.audit(self.project)
        self.assertFalse(any("Gros fichiers" in a for a in r["advice"]))

    def test_cli_json_output(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = audit_context.main([self.project, "--json"])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(buf.getvalue())["project"], os.path.abspath(self.project))

    def test_save_then_compare_shows_the_drop(self):
        write(os.path.join(self.project, "CLAUDE.md"), "règle\n" * 1000)
        snap = os.path.join(self.tmp.name, "before.json")
        with redirect_stdout(io.StringIO()):
            self.assertEqual(audit_context.main([self.project, "--save", snap]), 0)
        before = json.load(open(snap, encoding="utf-8"))
        self.assertGreater(before["memory_tokens"], 0)
        write(os.path.join(self.project, "CLAUDE.md"), "règle\n")
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(audit_context.main([self.project, "--compare", snap]), 0)
        out = buf.getvalue()
        self.assertIn("Mémoire chargée", out)
        self.assertIn("-", out.split("Mémoire chargée")[1].splitlines()[0])

    def test_compare_with_missing_snapshot_fails(self):
        with redirect_stdout(io.StringIO()):
            code = audit_context.main([self.project, "--compare", os.path.join(self.tmp.name, "nope.json")])
        self.assertEqual(code, 2)

    def test_compare_function_handles_zero_before(self):
        lines = audit_context.compare({}, {"memory_tokens": 10})
        self.assertTrue(any("0 -> 10 (+10)" in l for l in lines))


BLOCK = "<!-- fourmi:start -->\n## Bloc\n- règle\n<!-- fourmi:end -->\n"


class MergeBlockTests(unittest.TestCase):
    def test_append_to_existing_file(self):
        out = merge_block.merge("# Projet\n\nTexte.\n", BLOCK)
        self.assertTrue(out.startswith("# Projet\n\nTexte.\n\n<!-- fourmi:start -->"))
        self.assertTrue(out.endswith("<!-- fourmi:end -->\n"))

    def test_empty_file_gets_block_only(self):
        self.assertEqual(merge_block.merge("", BLOCK), BLOCK)

    def test_replace_existing_block_keeps_the_rest(self):
        old = "Avant\n\n<!-- fourmi:start -->\nvieux\n<!-- fourmi:end -->\n\nAprès\n"
        out = merge_block.merge(old, BLOCK)
        self.assertNotIn("vieux", out)
        self.assertIn("Avant\n\n", out)
        self.assertIn("\nAprès\n", out)
        self.assertEqual(out.count("fourmi:start"), 1)

    def test_merge_is_idempotent(self):
        once = merge_block.merge("Texte\n", BLOCK)
        self.assertEqual(merge_block.merge(once, BLOCK), once)

    def test_other_blocks_are_left_alone(self):
        other = "<!-- fourmi-agent:start -->\n- ligne\n<!-- fourmi-agent:end -->\n"
        out = merge_block.merge(other, BLOCK)
        self.assertIn("- ligne", out)
        self.assertEqual(out.count("start -->"), 2)

    def test_block_without_markers_is_refused(self):
        with self.assertRaises(ValueError):
            merge_block.merge("x", "pas de marqueurs\n")

    def test_shipped_blocks_are_valid(self):
        for name in ("claude-md-block.md", "claude-md-block.en.md", "claude-md-web.md",
                     "claude-md-web.en.md", "delegation-line.md", "delegation-line.en.md"):
            with open(os.path.join(HERE, name), encoding="utf-8") as f:
                merge_block.merge("", f.read())

    def test_cli_preview_does_not_write(self):
        with tempfile.TemporaryDirectory() as d:
            target, src = os.path.join(d, "CLAUDE.md"), os.path.join(d, "b.md")
            write(target, "Texte\n")
            write(src, BLOCK)
            with redirect_stdout(io.StringIO()):
                merge_block.main([target, src])
            self.assertEqual(merge_block.read(target), "Texte\n")
            with redirect_stdout(io.StringIO()):
                merge_block.main([target, src, "--write"])
            self.assertIn("fourmi:start", merge_block.read(target))

    def test_cli_copy_creates_missing_folder(self):
        with tempfile.TemporaryDirectory() as d:
            target = os.path.join(d, "agents", "ouvriere.md")
            with redirect_stdout(io.StringIO()):
                merge_block.main([target, os.path.join(HERE, "agent-ouvriere.md"), "--copy", "--write"])
            self.assertIn("model: haiku", merge_block.read(target))


class AgentFileTests(unittest.TestCase):
    def test_agent_frontmatter(self):
        with open(os.path.join(HERE, "agent-ouvriere.md"), encoding="utf-8") as f:
            text = f.read()
        head = text.split("---")[1]
        self.assertIn("name: ouvriere", head)
        self.assertIn("model: haiku", head)
        self.assertIn("tools: Read, Grep, Glob, Bash, Edit", head)

    def test_english_blocks_share_markers_with_french_ones(self):
        pairs = (("claude-md-block.md", "claude-md-block.en.md", "fourmi"),
                 ("claude-md-web.md", "claude-md-web.en.md", "fourmi-web"),
                 ("delegation-line.md", "delegation-line.en.md", "fourmi-agent"))
        for fr, en, name in pairs:
            for f in (fr, en):
                text = open(os.path.join(HERE, f), encoding="utf-8").read()
                self.assertTrue(text.startswith(f"<!-- {name}:start -->"), f)
                self.assertIn(f"<!-- {name}:end -->", text)

    def test_english_block_replaces_french_block(self):
        fr = open(os.path.join(HERE, "claude-md-block.md"), encoding="utf-8").read()
        en = open(os.path.join(HERE, "claude-md-block.en.md"), encoding="utf-8").read()
        out = merge_block.merge(merge_block.merge("Texte\n", fr), en)
        self.assertEqual(out.count("fourmi:start"), 1)
        self.assertIn("Texte", out)
        self.assertIn("haiku", out)

    def test_blocks_cover_routing_rules(self):
        for f in ("claude-md-block.md", "claude-md-block.en.md"):
            text = open(os.path.join(HERE, f), encoding="utf-8").read().lower()
            for word in ("haiku", "sonnet", "opus", "model"):
                self.assertIn(word, text, f)

    def test_web_blocks_mention_models_and_single_validation(self):
        for f in ("claude-md-web.md", "claude-md-web.en.md"):
            text = open(os.path.join(HERE, f), encoding="utf-8").read().lower()
            for word in ("haiku", "sonnet", "opus", "seo"):
                self.assertIn(word, text, f)


class AgentFileExtraTests(unittest.TestCase):
    def test_agent_has_description_and_hands_back(self):
        text = open(os.path.join(HERE, "agent-ouvriere.md"), encoding="utf-8").read()
        self.assertIn("description:", text)
        self.assertIn("Use proactively", text)
        self.assertIn("Hand back", text)


if __name__ == "__main__":
    unittest.main()
