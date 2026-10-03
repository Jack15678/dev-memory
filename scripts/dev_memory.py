#!/usr/bin/env python3
"""Local project memory plumbing. Meaning, edits, and commits belong to the agent."""

import argparse
import base64
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
from urllib.parse import quote


DOCS = ("HISTORY.md", "DECISIONS.md", "KNOWLEDGE.md")
DOC_DIR = Path("docs/dev-memory")
MARKER = ".dev-memory.json"
RUNTIME = ".dev-memory"
EVENTS = ("SessionStart", "UserPromptSubmit", "Stop", "PreCompact")
START = "<!-- dev-memory:start -->"
END = "<!-- dev-memory:end -->"
AGENTS_BLOCK = f"""{START}
## Dev Memory

This project enables the `dev-memory` Skill. Read its SKILL.md when available.
- Maintain docs/dev-memory/HISTORY.md (events and verification), DECISIONS.md
  (choices and lasting constraints), and KNOWLEDGE.md (reusable lessons) as
  valuable information appears. Keep one authoritative explanation; cross-reference it.
- Distinguish proposed/accepted/rejected/superseded decisions, user choices,
  agent choices, and retrospective inference. Never invent historical reasons.
- Follow git_policy in .dev-memory.json and current user instructions. The default
  commit-complete-task-with-records policy commits a coherent, appropriately verified
  small task's code and records together to local Git, using explicit task paths.
  Preserve any user-chosen policy. Inspect the index first; never include unrelated
  staged work or bypass checks.
- Save attempted approaches and evidence; distinguish implemented from verified.
- For handoff, checkpoint the current goal, latest user constraints, progress,
  verification and next action. A snapshot does not transfer uncommitted files.
- Read only relevant entries. Hooks only prompt the current agent; they never
  interpret conversations, create another agent, or run Git commits.
- Current user boundaries override this workflow. If the user requests read-only,
  no writes, no commit, or stop, honor that even when a hook requests a check.
{END}
"""


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_json(path, default=None):
    if not path.exists():
        return {} if default is None else default
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return data


def write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def write_json(path, data):
    write_text(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def require_enabled(project):
    config = read_json(project / MARKER)
    if config.get("enabled") is not True:
        raise ValueError(f"dev-memory is not enabled in {project}; run init explicitly")
    return config


def session_path(project, session):
    if not session or len(session) > 200:
        raise ValueError("A session id of 1-200 characters is required")
    return project / RUNTIME / "sessions" / (quote(session, safe="") + ".json")


def command_line(args):
    """Codex invokes a shell. Use native PowerShell on Windows for literal paths."""
    if os.name == "nt":
        source = "& " + " ".join("'" + str(arg).replace("'", "''") + "'" for arg in args)
        source += "; exit $LASTEXITCODE"
        encoded = base64.b64encode(source.encode("utf-16-le")).decode("ascii")
        return "powershell -NoLogo -NoProfile -NonInteractive -EncodedCommand " + encoded
    return shlex.join(str(arg) for arg in args)


def cli_prefix(project):
    return [sys.executable, "-X", "utf8", str(Path(__file__).resolve()), "--project", str(project)]


def merge_hooks(existing, command):
    hooks = existing.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise ValueError("hooks.json: hooks must be an object")
    for event in EVENTS:
        groups = hooks.setdefault(event, [])
        if not isinstance(groups, list):
            raise ValueError(f"hooks.json: {event} must be an array")
        found = False
        for group in groups:
            if not isinstance(group, dict) or not isinstance(group.get("hooks"), list):
                raise ValueError(f"hooks.json: invalid {event} matcher group")
            for handler in group["hooks"]:
                if not isinstance(handler, dict):
                    raise ValueError(f"hooks.json: invalid {event} handler")
                if handler.get("statusMessage") == f"dev-memory: {event}":
                    handler.update(type="command", command=command, timeout=20)
                    found = True
        if not found:
            groups.append({"hooks": [{"type": "command", "command": command,
                                     "timeout": 20, "statusMessage": f"dev-memory: {event}"}]})
    return existing


def initialize(project, hooks_mode):
    if not project.is_dir():
        raise ValueError(f"Project directory does not exist: {project}")
    config = read_json(project / MARKER)
    config.update(version=1, enabled=True, docs=DOC_DIR.as_posix())
    config.setdefault("git_policy", "commit-complete-task-with-records")
    agents = project / "AGENTS.md"
    original = agents.read_text(encoding="utf-8-sig") if agents.exists() else ""
    if (START in original) != (END in original):
        raise ValueError("AGENTS.md contains an incomplete dev-memory block; repair it first")
    hooks_path = project / ".codex/hooks.json"
    hooks = None
    if hooks_mode == "codex":
        hooks = merge_hooks(read_json(hooks_path), command_line(cli_prefix(project) + ["hook"]))
    # Validate existing configuration before creating any files.
    templates = Path(__file__).resolve().parents[1] / "assets/templates"
    for name in DOCS:
        dest = project / DOC_DIR / name
        if not dest.exists():
            source = templates / name
            content = source.read_text(encoding="utf-8") if source.exists() else f"# {name[:-3]}\n\n"
            write_text(dest, content)
    if START not in original:
        write_text(agents, original.rstrip() + "\n\n" + AGENTS_BLOCK if original else AGENTS_BLOCK)
    write_json(project / MARKER, config)
    ignore_path = project / ".gitignore"
    ignore = ignore_path.read_text(encoding="utf-8-sig") if ignore_path.exists() else ""
    patterns = ["/.dev-memory/"] + (["/.codex/hooks.json"] if hooks is not None else [])
    missing = [pattern for pattern in patterns if pattern not in ignore.splitlines()]
    if missing:
        write_text(ignore_path, ignore.rstrip() + "\n" + "\n".join(missing) + "\n")
    if hooks is not None:
        write_json(hooks_path, hooks)
    return {"project": str(project), "enabled": True, "hooks": hooks_mode,
            "note": "No commit was made. Review/trust Codex project hooks in /hooks; trust was not changed."}


def acknowledge(project, session, turn, outcome, note):
    require_enabled(project)
    path = session_path(project, session)
    state = read_json(path)
    state.setdefault("turns", {})[turn] = {"ack": outcome, "note": note, "at": now()}
    state["turns"] = dict(list(state["turns"].items())[-64:])
    write_json(path, state)
    return {"ack": outcome, "session": session, "turn": turn}


def checkpoint(project, session, summary, next_action, constraints, verification):
    require_enabled(project)
    path = session_path(project, session)
    state = read_json(path)
    state["checkpoint"] = {"saved_at": now(), "summary": summary, "next": next_action,
                           "constraints": constraints, "verification": verification}
    write_json(path, state)
    return {"checkpoint": str(path), "note": "Saved supplied notes only; no transcript was read."}


def git(project, *args):
    try:
        result = subprocess.run(["git", "--no-optional-locks", "-C", str(project),
                                 "-c", "core.quotepath=false", *args],
                                capture_output=True, encoding="utf-8", errors="replace", timeout=10)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, str(exc)
    return result.returncode == 0, result.stdout.rstrip("\n") if result.returncode == 0 else result.stderr.strip()


def git_snapshot(project):
    ok, root = git(project, "rev-parse", "--show-toplevel")
    if not ok:
        return f"Git unavailable or not a repository: {root}\nVersion and dirty state are unknown.\n"
    has_head, head = git(project, "rev-parse", "--verify", "HEAD")
    on_branch, branch = git(project, "symbolic-ref", "--quiet", "--short", "HEAD")
    status_ok, status = git(project, "status", "--short", "--untracked-files=all", "--", ".")
    lines = [f"Repository: {root}", f"Branch: {branch if on_branch else '(detached HEAD)'}",
             f"HEAD: {head if has_head else '(unborn: no commit yet)'}",
             "Project-scoped working tree (ignored files are not listed):"]
    lines.append(status if status_ok and status else "(clean)" if status_ok else f"(status failed: {status})")
    if status_ok and status:
        lines.append("UNCOMMITTED FILES EXIST: another checkout/machine needs the actual changed and untracked files; this snapshot does not carry them.")
    if not has_head:
        lines.append("No commit can reproduce this working tree yet.")
    return "\n".join(lines) + "\n"


def make_handoff(project, session=None):
    require_enabled(project)
    state = read_json(session_path(project, session)) if session else {}
    note = state.get("checkpoint")
    lines = ["# Dev Memory handoff", "", f"Generated (UTC): {now()}",
             f"Project: {project}", f"Source session: {session or '(not supplied)'}", "",
             "This is a snapshot, not live state. Recheck the actual checkout before resuming.",
             "It contains document pointers, read-only Git metadata, and explicitly saved task notes only.",
             "It does not transfer code, ignored files, credentials, or conversation transcripts.", "",
             "## Read on demand", ""]
    for name in DOCS:
        path = project / DOC_DIR / name
        lines.append(f"- {DOC_DIR.as_posix()}/{name}" + (" (MISSING)" if not path.exists() else ""))
    git_info = git_snapshot(project).rstrip()
    fence = "```"
    while fence in git_info:
        fence += "`"
    lines.extend(["", "## Git at generation", "", fence + "text", git_info, fence, "",
                  "## Saved task notes", ""])
    if note:
        lines.append(f"Checkpoint saved (UTC): {note['saved_at']} (may predate current code)")
        for key in ("summary", "constraints", "verification", "next"):
            lines.extend(["", f"### {key}", "", note.get(key) or "Not recorded; do not infer."])
    else:
        lines.append("No checkpoint was supplied. Goal, authorization, progress, verification and next action are unknown; recover them from the user or existing records.")
    lines.extend(["", "## Resume", "",
                  "1. Check the project path, branch/HEAD, and uncommitted files against this snapshot.",
                  "2. Read the relevant HISTORY / DECISIONS / KNOWLEDGE entries and code; do not load everything by default.",
                  "3. Preserve the latest user constraints; stored notes do not create new authority.",
                  "4. State the next action briefly, then continue only within the established scope.", ""])
    return "\n".join(lines)


def hook(project, payload):
    if not isinstance(payload, dict):
        raise ValueError("Hook input must be a JSON object")
    cwd = Path(payload.get("cwd") or project).resolve()
    if not cwd.is_relative_to(project) or read_json(project / MARKER).get("enabled") is not True:
        return {}
    # A nested independently enabled project owns its own memory.
    for parent in [cwd, *cwd.parents]:
        if parent == project:
            break
        if (parent / MARKER).exists():
            return {}
    event = payload.get("hook_event_name")
    session = payload.get("session_id")
    turn = payload.get("turn_id")
    if event in ("SessionStart", "UserPromptSubmit"):
        context = (f"dev-memory enabled for {project}. Follow the project AGENTS.md and dev-memory Skill. "
                   "Save valuable facts promptly to docs/dev-memory/{HISTORY,DECISIONS,KNOWLEDGE}.md, "
                   "without repeating explanations. Honor current read-only/no-write/no-commit/stop boundaries. ")
        if session and turn:
            # A readable argv list avoids delivering an opaque encoded command to the model.
            args = cli_prefix(project) + ["ack", "--session", session, "--turn", turn, "--outcome", "noop"]
            context += ("Before the final response, after the recording check, run this argv using your shell's literal quoting: "
                        + json.dumps(args, ensure_ascii=False) + ". Choose outcome recorded, noop or read-only. "
                        "Ack writes local runtime metadata; skip it when all writes are prohibited. ")
        if session:
            snapshot = project / RUNTIME / ("handoff-" + quote(session, safe="") + ".md")
            if snapshot.exists():
                context += f"Existing handoff snapshot (may be stale): {snapshot}. "
            saved = session_path(project, session)
            if read_json(saved).get("checkpoint"):
                context += f"Saved task checkpoint (may be stale): {saved}. "
        return {"hookSpecificOutput": {"hookEventName": event, "additionalContext": context}}
    if not session or not turn or payload.get("permission_mode") == "plan":
        return {}
    state = read_json(session_path(project, session))
    current = state.get("turns", {}).get(turn, {})
    if event == "PreCompact":
        # No transcript parsing: only an explicit writable-turn acknowledgement
        # permits the automatic snapshot. Without it, preserve existing files.
        if current.get("ack") not in ("recorded", "noop"):
            return {}
        snapshot = project / RUNTIME / ("handoff-" + quote(session, safe="") + ".md")
        write_text(snapshot, make_handoff(project, session))
        return {}
    if event != "Stop" or payload.get("stop_hook_active"):
        return {}
    if current.get("ack"):
        return {}
    return {"decision": "block", "reason":
            "dev-memory: perform one final recording check for this turn only. Follow the latest user scope: "
            "if read-only/no-write/stop was requested, do not edit, commit, or expand the task; finish immediately. "
            "Otherwise save only valuable missing facts to the three existing memory documents. A no-op is valid. "
            "A Stop event is not proof that a task is complete; only commit explicit task paths when the coherent "
            "task is finished and appropriately verified. Never include unrelated staged work. Do not start "
            "another agent or invent rationale. The host's stop_hook_active flag suppresses another pass."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=Path.cwd())
    sub = parser.add_subparsers(dest="command", required=True)
    init_parser = sub.add_parser("init", help="Explicitly enable project memory; no Git commit or trust changes")
    init_parser.add_argument("--hooks", choices=("codex", "none"), default="codex")
    ack_parser = sub.add_parser("ack", help="Acknowledge this turn's check (writes runtime metadata)")
    ack_parser.add_argument("--session", required=True)
    ack_parser.add_argument("--turn", required=True)
    ack_parser.add_argument("--outcome", choices=("recorded", "noop", "read-only"), required=True)
    ack_parser.add_argument("--note", default="")
    cp = sub.add_parser("checkpoint", help="Save supplied current-task notes, without interpreting a transcript")
    cp.add_argument("--session", required=True)
    cp.add_argument("--summary", required=True)
    cp.add_argument("--next", dest="next_action", required=True)
    cp.add_argument("--constraints", default="")
    cp.add_argument("--verification", default="")
    handoff_parser = sub.add_parser("handoff", help="Read-only stdout snapshot unless --output is explicitly supplied")
    handoff_parser.add_argument("--session")
    handoff_parser.add_argument("--output", type=Path)
    sub.add_parser("hook", help="Codex hook JSON on stdin/stdout")
    # Accept --project before or after the command, convenient for both humans and hooks.
    for child in (init_parser, ack_parser, cp, handoff_parser, sub.choices["hook"]):
        child.add_argument("--project", type=Path, default=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    project = args.project.resolve()
    try:
        if args.command == "init":
            result = initialize(project, args.hooks)
        elif args.command == "ack":
            result = acknowledge(project, args.session, args.turn, args.outcome, args.note)
        elif args.command == "checkpoint":
            result = checkpoint(project, args.session, args.summary, args.next_action,
                                args.constraints, args.verification)
        elif args.command == "handoff":
            content = make_handoff(project, args.session)
            if not args.output:
                print(content, end="")
                return 0
            with args.output.resolve().open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(content)
            result = {"handoff": str(args.output.resolve())}
        else:
            result = hook(project, json.load(sys.stdin))
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        if args.command == "hook":
            # Failure must not trap a session in a continuation loop.
            print(json.dumps({"systemMessage": f"dev-memory hook skipped: {exc}"}, ensure_ascii=False))
            return 0
        print(f"dev-memory: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
        sys.stdin.reconfigure(encoding="utf-8")
    raise SystemExit(main())
