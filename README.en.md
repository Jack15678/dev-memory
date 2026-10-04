# Dev Memory

**Keep the reason beside the code.**

[简体中文](README.md) · [Detailed comparison (Chinese)](docs/comparison.zh-CN.md) · [Skill instructions](SKILL.md) · [MIT](LICENSE)

[![Runtime tests](https://github.com/Jack15678/dev-memory/actions/workflows/tests.yml/badge.svg)](https://github.com/Jack15678/dev-memory/actions/workflows/tests.yml)

Your coding agent moves fast. A week later, you may have forgotten why a value was hardcoded, why an alternative was rejected, or which checks actually ran. A new session needs that context again.

Dev Memory is a Codex-first skill that maintains three Markdown documents, commits code and relevant records after a coherent task is verified, and prepares a handoff snapshot for the next session.

![Three documents route changes, lasting decisions, and reusable lessons into task-based Git commits](docs/images/memory-map.svg)

## Three documents, one home for each fact

| Document | Purpose |
|---|---|
| `HISTORY.md` | Behavior changes, direct reasons, useful failed attempts, actual verification and version links |
| `DECISIONS.md` | Lasting choices, constraints, hardcoding, tradeoffs and conditions for revisiting them |
| `KNOWLEDGE.md` | Reusable lessons and ideas, with evidence and applicability limits |

Entries cross-reference stable H/D/K identifiers. No new information means no update. A project choice does not automatically become a general lesson.

## Install and enable

Requirements: an agent with file and command access, **Python 3.10+**, and an existing Git repository for versioning. The helper uses only the Python standard library.

Clone into the personal Skill directory documented by Codex. If you already installed the skill elsewhere, keep that location to avoid duplicate discovery.

**macOS / Linux**

```sh
mkdir -p ~/.agents/skills
git clone https://github.com/Jack15678/dev-memory.git ~/.agents/skills/dev-memory
```

**Windows PowerShell**

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE/.agents/skills" | Out-Null
git clone https://github.com/Jack15678/dev-memory.git "$env:USERPROFILE/.agents/skills/dev-memory"
```

From **the project you want to work on**, ask:

```text
Use $dev-memory to enable development memory and Codex Hooks for this project.
```

Initialization adds missing documents, `.dev-memory.json`, a maintenance block in `AGENTS.md`, and merged project-local `.codex/hooks.json` entries. Its default policy is to commit coherent, verified tasks to local Git. Installation alone does not enable every project.

Review and trust the generated hooks with `/hooks` in Codex CLI. New or changed hook definitions require host review. Restart Codex if the skill does not appear. See the official [Skill locations](https://learn.chatgpt.com/docs/build-skills) and [Hook trust rules](https://learn.chatgpt.com/docs/hooks).

Options you can ask your agent to apply:

- **Record without auto-committing:** set the project's `.dev-memory.json` `git_policy` to `manual`. The agent follows this policy; the helper never commits.
- **Start without hooks:** initialize with `--hooks none`. This skips hook creation; it does not remove existing hooks.
- **Discussion only:** say “Discuss only; do not edit files.” Current user instructions take priority.

## Example

Illustrative scenario:

> Keep the upload cap at 20 MiB for the first version. Do not add a configuration option until a real need appears.

The agent records the choice, source, tradeoff, code location and revisit condition in **D-004**, including when to read it: before changing upload validation or size hints. After modifying validation, **H-012** records the change, actual boundary checks and the commit or uncommitted working state they apply to, with a reference to D-004. **KNOWLEDGE stays unchanged** if no reusable lesson emerged.

Once the task is complete and appropriately checked, code and records go into one commit. A later “Why is this hardcoded?” can be answered from the recorded evidence. Missing historical rationale stays unknown.

If the code later allows 100 MiB, the agent first looks for a new decision. Without supporting evidence, it records the conflict with the approved 20 MiB rule and preserves that decision. An existing test file, a past passing result and a test run in the current task are recorded separately; past success does not establish that the current code passes.

## Handoff and resume

```text
Use $dev-memory to prepare a handoff; I am switching sessions.
```

![Capture current task notes, generate a snapshot, verify the actual checkout and resume within current instructions](docs/images/handoff.svg)

Give the snapshot path to the next session:

```text
Use $dev-memory to read this handoff. Verify HEAD and the working tree before continuing.
```

A snapshot contains explicitly saved task notes, Git metadata and document pointers. Local state lives in the ignored `.dev-memory/` directory. Uncommitted files and running processes do not travel with the snapshot. An unfinished task is not committed just to create a handoff.

## Automation

| Event | Role |
|---|---|
| `SessionStart` | Supply rules, document pointers and existing handoff context |
| `UserPromptSubmit` | Supply the turn identifier and acknowledgement command |
| `Stop` | Read-only check, requesting one follow-up pass when needed |
| `PreCompact` | Save a snapshot when this turn has a writable acknowledgement |

Hooks prompt the current agent to check its work. The agent decides what belongs in the records and whether a task is ready to commit. No additional recording agent, model API or database is used. Normal agent reasoning and follow-up checks still consume context and tokens.

See the [runtime reference](references/runtime.md) and [handoff guide](references/handoff.md) for commands and behavior.

## Scope and validation

Best suited to individual developers who use Git, switch sessions and want to retain design rationale. The document workflow is language-independent; automatic hooks currently target Codex.

- Fourteen runtime tests and independent edit/commit and read-only resume trials are recorded in [H-001](docs/dev-memory/HISTORY.md#h-001). CI runs protocol checks in real temporary repositories on Windows and Linux.
- An independent resume trial in [H-003](docs/dev-memory/HISTORY.md#h-003) preserved an approved constraint despite conflicting code and identified that historical test results did not cover an uncommitted change. This validates one synthetic scenario.
- Maintenance-context injection has been observed in an actual session. Full host stop/compaction behavior and long-term record quality need further use; protocol tests are not complete host validation.
- macOS, other agents' hooks, and concurrent agents editing the same memory documents have not been validated.
- The skill relies on agent judgment. It does not provide semantic auditing, a search service or concurrent ID allocation.
- Without Git, records can still be saved; the helper does not initialize repositories. Unrelated edits remain untouched, and local commit policy does not authorize a push.

## Related work

[OwnMem](https://github.com/grpcer/ownmem) provides structured engineering memory and retrieval. [Fractal Skills](https://github.com/yaukwan/fractal-skills) organizes scoped project context and decision skills. The [LINUX DO project-handoff Skill post](https://linux.do/t/topic/2230307/3) describes a dedicated handoff workflow.

Our [source-based comparison](docs/comparison.zh-CN.md) distinguishes current implementations from author descriptions and lists ideas worth borrowing. Dev Memory combines three long-term documents, task-based local commits and temporary handoff snapshots. No upstream code or templates were copied.

## Development

```sh
python -X utf8 -m unittest discover -s tests -v
```

Issues are welcome: include your agent and OS, minimal steps, expected behavior and sanitized records. Reports about missing rationale, noisy notes and handoff gaps are particularly useful.

MIT licensed. The workflow draws on [architecture decision records](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions) and [long-running agent practices](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents).
