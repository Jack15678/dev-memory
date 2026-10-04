"""Behavior checks using real, disposable Git repositories (stdlib unittest)."""

import importlib.util
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/dev_memory.py"
spec = importlib.util.spec_from_file_location("dev_memory", SCRIPT)
dm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dm)


class MemoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="dev-memory-")
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name) / "中文 项目"
        self.project.mkdir()
        # Match the CLI boundary: Windows runner temp paths may use 8.3 aliases.
        self.project = self.project.resolve()
        self.git("init", "-b", "main")
        self.git("config", "user.email", "dev-memory@example.invalid")
        self.git("config", "user.name", "Dev Memory Test")

    def git(self, *args):
        result = subprocess.run(["git", "-C", str(self.project), *args],
                                capture_output=True, encoding="utf-8", errors="replace")
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def enable(self, hooks="none"):
        return dm.initialize(self.project, hooks)

    def payload(self, event="Stop", **kwargs):
        data = {"cwd": str(self.project), "hook_event_name": event,
                "session_id": "session-1", "turn_id": "turn-1", "stop_hook_active": False}
        data.update(kwargs)
        return data

    def files(self):
        return {str(path.relative_to(self.project)): (path.stat().st_mtime_ns, path.read_bytes())
                for path in self.project.rglob("*") if path.is_file()}

    def test_init_preserves_docs_rules_and_existing_hooks(self):
        (self.project / "AGENTS.md").write_text("# Existing rules\nKeep this.\n", encoding="utf-8")
        hooks_path = self.project / ".codex/hooks.json"
        dm.write_json(hooks_path, {"description": "existing", "hooks": {
            "Stop": [{"hooks": [{"type": "command", "command": "echo existing"}]}]}})
        self.enable("codex")
        history = self.project / dm.DOC_DIR / "HISTORY.md"
        history.write_text("User-owned existing facts\n", encoding="utf-8")
        first_hooks = hooks_path.read_text(encoding="utf-8")
        self.enable("codex")
        self.assertEqual(history.read_text(encoding="utf-8"), "User-owned existing facts\n")
        agents = (self.project / "AGENTS.md").read_text(encoding="utf-8")
        self.assertEqual(agents.count(dm.START), 1)
        self.assertTrue(agents.startswith("# Existing rules\nKeep this."))
        self.assertNotIn(str(self.project), agents)
        self.assertEqual(hooks_path.read_text(encoding="utf-8"), first_hooks)
        self.assertEqual(json.loads(first_hooks)["hooks"]["Stop"][0]["hooks"][0]["command"], "echo existing")
        self.assertEqual(len(json.loads(first_hooks)["hooks"]["Stop"]), 2)
        self.assertEqual(self.git("check-ignore", ".codex/hooks.json"), ".codex/hooks.json")
        self.assertFalse((self.project / ".codex/config.toml").exists())
        self.assertFalse((self.project / dm.RUNTIME).exists())

    def test_init_preserves_user_git_policy(self):
        dm.write_json(self.project / dm.MARKER, {"enabled": False, "git_policy": "manual"})
        self.enable()
        self.enable()
        self.assertEqual(dm.read_json(self.project / dm.MARKER)["git_policy"], "manual")
        rules = (self.project / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("Follow git_policy in .dev-memory.json", rules)
        self.assertIn("Preserve any user-chosen policy", rules)

    def test_invalid_hooks_do_not_partially_initialize(self):
        dm.write_json(self.project / ".codex/hooks.json", {"hooks": {"Stop": "invalid"}})
        with self.assertRaises(ValueError):
            self.enable("codex")
        self.assertFalse((self.project / dm.MARKER).exists())
        self.assertFalse((self.project / dm.DOC_DIR).exists())

    def test_unenabled_and_outside_project_hooks_have_no_effect(self):
        self.assertEqual(dm.hook(self.project, self.payload()), {})
        self.assertFalse((self.project / dm.RUNTIME).exists())
        self.enable()
        sibling = self.project.parent / "sibling"
        sibling.mkdir()
        self.assertEqual(dm.hook(self.project, self.payload(cwd=str(sibling))), {})
        nested = self.project / "child"
        nested.mkdir()
        dm.initialize(nested, "none")
        self.assertEqual(dm.hook(self.project, self.payload(cwd=str(nested))), {})
        self.assertFalse((self.project / dm.RUNTIME).exists())

    def test_stop_is_readonly_host_flag_stops_loop_and_ack_releases_it(self):
        self.enable()
        before = self.files()
        self.assertEqual(dm.hook(self.project, self.payload())["decision"], "block")
        # A repeated false payload is still eligible. Codex marks the continuation active.
        self.assertEqual(dm.hook(self.project, self.payload())["decision"], "block")
        self.assertEqual(dm.hook(self.project, self.payload(turn_id="turn-2", stop_hook_active=True)), {})
        self.assertEqual(self.files(), before)
        for number, outcome in enumerate(("recorded", "noop", "read-only"), start=3):
            turn = f"turn-{number}"
            dm.acknowledge(self.project, "session-1", turn, outcome, "")
            self.assertEqual(dm.hook(self.project, self.payload(turn_id=turn)), {})
        # An acknowledgement from one turn never masks a later turn.
        self.assertEqual(dm.hook(self.project, self.payload(turn_id="turn-6"))["decision"], "block")
        self.assertEqual(dm.hook(self.project, self.payload(turn_id="plan", permission_mode="plan")), {})
        self.assertEqual(dm.hook(self.project, self.payload(turn_id=None)), {})

    def test_prompt_context_has_ack_ids_without_writing_state(self):
        self.enable()
        before = self.files()
        data = dm.hook(self.project, self.payload("UserPromptSubmit"))
        context = data["hookSpecificOutput"]["additionalContext"]
        self.assertIn("session-1", context)
        self.assertIn("turn-1", context)
        self.assertIn("skip it when all writes are prohibited", context)
        self.assertFalse((self.project / dm.RUNTIME).exists())
        self.assertEqual(self.files(), before)

    def test_precompact_no_ack_readonly_or_plan_never_writes(self):
        self.enable()
        before = self.files()
        self.assertEqual(dm.hook(self.project, self.payload("PreCompact")), {})
        self.assertEqual(self.files(), before)
        dm.acknowledge(self.project, "session-1", "turn-1", "read-only", "")
        before = self.files()
        self.assertEqual(dm.hook(self.project, self.payload("PreCompact")), {})
        self.assertEqual(self.files(), before)
        dm.acknowledge(self.project, "session-1", "turn-1", "recorded", "")
        before = self.files()
        self.assertEqual(dm.hook(self.project, self.payload("PreCompact", permission_mode="plan")), {})
        self.assertEqual(dm.hook(self.project, self.payload("PreCompact", turn_id="unacknowledged")), {})
        self.assertEqual(self.files(), before)

    def test_session_start_finds_checkpoint_without_snapshot(self):
        self.enable()
        dm.checkpoint(self.project, "session-1", "待完成工作", "检查已有代码", "", "")
        before = self.files()
        context = dm.hook(self.project, self.payload("SessionStart"))["hookSpecificOutput"]["additionalContext"]
        self.assertIn(str(dm.session_path(self.project, "session-1")), context)
        self.assertNotIn("Existing handoff snapshot", context)
        self.assertEqual(self.files(), before)

    def test_precompact_only_saves_known_notes_and_session_start_points_to_it(self):
        self.enable()
        dm.checkpoint(self.project, "session-1", "讨论已记录", "等用户确认实现", "只允许记录，不实现代码", "没有运行测试")
        dm.acknowledge(self.project, "session-1", "turn-1", "recorded", "")
        docs_before = {name: (self.project / dm.DOC_DIR / name).read_bytes() for name in dm.DOCS}
        result = dm.hook(self.project, self.payload("PreCompact", transcript_path="secret-not-read.jsonl"))
        self.assertEqual(result, {})
        snapshot = self.project / dm.RUNTIME / "handoff-session-1.md"
        content = snapshot.read_text(encoding="utf-8")
        self.assertIn("讨论已记录", content)
        self.assertIn("没有运行测试", content)
        self.assertNotIn("secret-not-read", content)
        context = dm.hook(self.project, self.payload("SessionStart", source="compact"))["hookSpecificOutput"]["additionalContext"]
        self.assertIn(str(snapshot), context)
        self.assertEqual(docs_before, {name: (self.project / dm.DOC_DIR / name).read_bytes() for name in dm.DOCS})
        self.assertEqual(self.git("status", "--porcelain", "--", dm.RUNTIME), "")
        dm.acknowledge(self.project, "session-2", "turn-2", "noop", "")
        dm.hook(self.project, self.payload("PreCompact", session_id="session-2", turn_id="turn-2"))
        self.assertTrue((self.project / dm.RUNTIME / "handoff-session-2.md").exists())

    def test_git_fence_surrounds_backticks_in_paths(self):
        self.enable()
        (self.project / "```four````.txt").write_text("data", encoding="utf-8")
        result = dm.make_handoff(self.project)
        self.assertIn("`````text\n", result)
        self.assertIn("\n`````\n", result)
        self.assertIn("```four````.txt", result)

    def test_handoff_unborn_dirty_detached_and_no_code_export(self):
        self.enable()
        result = dm.make_handoff(self.project)
        self.assertIn("unborn: no commit yet", result)
        self.assertIn("No checkpoint was supplied", result)
        self.git("add", "AGENTS.md", ".gitignore", dm.MARKER, str(dm.DOC_DIR))
        self.git("commit", "-m", "test baseline")
        self.git("checkout", "--detach")
        (self.project / "source.py").write_text("PRIVATE_SOURCE_CONTENT = 123\n", encoding="utf-8")
        result = dm.make_handoff(self.project)
        self.assertIn("(detached HEAD)", result)
        self.assertIn("source.py", result)
        self.assertIn("UNCOMMITTED FILES EXIST", result)
        self.assertIn("another checkout/machine", result)
        self.assertNotIn("PRIVATE_SOURCE_CONTENT", result)
        self.assertIn(self.git("rev-parse", "HEAD"), result)

    def test_handoff_stdout_changes_no_files_and_output_refuses_overwrite(self):
        self.enable()
        self.git("add", "AGENTS.md", ".gitignore", dm.MARKER, str(dm.DOC_DIR))
        self.git("commit", "-m", "test baseline")
        before = {str(path.relative_to(self.project)): (path.stat().st_mtime_ns, path.read_bytes())
                  for path in self.project.rglob("*") if path.is_file()}
        result = subprocess.run([sys.executable, "-X", "utf8", str(SCRIPT), "handoff", "--project", str(self.project)],
                                capture_output=True, encoding="utf-8")
        self.assertEqual(result.returncode, 0, result.stderr)
        after = {str(path.relative_to(self.project)): (path.stat().st_mtime_ns, path.read_bytes())
                 for path in self.project.rglob("*") if path.is_file()}
        self.assertEqual(before, after)
        self.assertIn("(clean)", result.stdout)
        output = self.project.parent / "handoff.md"
        output.write_text("keep", encoding="utf-8")
        result = subprocess.run([sys.executable, str(SCRIPT), "--project", str(self.project),
                                 "handoff", "--output", str(output)], capture_output=True, encoding="utf-8")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(output.read_text(encoding="utf-8"), "keep")

    def test_monorepo_status_is_scoped_and_non_git_is_honest(self):
        self.enable()
        nested = self.project / "subproject"
        nested.mkdir()
        dm.initialize(nested, "none")
        (self.project / "sibling-private.txt").write_text("secret", encoding="utf-8")
        self.assertNotIn("sibling-private.txt", dm.make_handoff(nested))
        outside = self.project.parent / "not git"
        outside.mkdir()
        dm.initialize(outside, "none")
        self.assertIn("not a repository", dm.make_handoff(outside))

    def test_generated_command_executes_with_chinese_and_spaces(self):
        self.enable("codex")
        command = dm.read_json(self.project / ".codex/hooks.json")["hooks"]["UserPromptSubmit"][-1]["hooks"][0]["command"]
        if os.name == "nt":
            argv = shlex.split(command, posix=True)  # Wrapper has no literal paths: encoded payload is one safe token.
        else:
            argv = ["sh", "-c", command]
        result = subprocess.run(argv, input=json.dumps(self.payload("UserPromptSubmit"), ensure_ascii=False),
                                capture_output=True, encoding="utf-8", timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertIn("中文 项目", data["hookSpecificOutput"]["additionalContext"])


if __name__ == "__main__":
    unittest.main()
