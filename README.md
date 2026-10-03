# Dev Memory · 开发记忆

让 agent 自动维护三份职责清楚的文档，完成一个完整的小任务后把代码与记录一起提交到本地 Git，并支持交接给新会话。

| 文档 | 负责回答 |
|---|---|
| `HISTORY.md` | 改了什么、为什么改、试过什么、验证到哪、对应哪个版本？ |
| `DECISIONS.md` | 当时为什么这样选择、哪些特殊处理还有效、何时应该重新考虑？ |
| `KNOWLEDGE.md` | 有哪些能带到其他项目的经验或想法，适用边界是什么？ |

同一事实只在一处完整维护，其他位置引用编号。Handoff 是按需生成的快照，不新增第四份长期文档。

## 开始使用

运行条件：支持文件读写与命令执行的 agent、Python 3.10+；版本保存需要已有 Git 仓库。脚本仅用标准库，不调用额外模型 API，不在后台启动另一个 agent。

将 `SKILL.md`、`agents/`、`references/`、`assets/`、`scripts/` 和 `LICENSE` 放入个人 Skills 目录中的 `dev-memory/`。本机 Codex 的个人目录为 `~/.codex/skills`；当前官方也支持 `~/.agents/skills`。选择一个位置安装，避免同名重复。

在要启用的具体项目中说：

```text
使用 $dev-memory 为当前项目启用开发记忆和 Codex Hooks。
```

初始化会创建三份文档、项目配置和 AGENTS 维护约定，并合并项目内的 `.codex/hooks.json`。在该项目启动的 Codex 中通过 `/hooks` 审阅并信任生成的 Hook。它不会改全局 Hook、覆盖其他 Hook，或替你绕过宿主信任。

若新 Skill 未出现在列表中，可重启宿主刷新，或直接让 agent 读取本项目 [SKILL.md](SKILL.md)。安装 Skill 不会给所有项目自动启用文档或提交策略。

## 日常工作

- 出现有价值的新事实、决定或经验时，agent 及时更新相应文档。
- 完整小任务完成并做了适当验证后，agent 自动提交本任务的代码和记录；不会把其他任务的改动一起提交。
- 未完成任务保留真实进度与验证缺口；没有新信息不刷新日期、不凑日志。
- 「先讨论」「只回答」「不落盘」可以覆盖本轮自动记录。追溯设计原因默认只读。

```text
修复切换文件后仍显示旧结果的问题。
为什么这里保留固定大小上限？依据是什么？
把当前任务交接一下，我准备换个对话。
使用 $dev-memory 读取这个交接包并继续，先核对实际版本。
```

一条记录的例子（虚构）：

> H-012：新增超限提示，依据 D-004；实际验证文件边界测试通过；随包含 H-012 的提交保存。
>
> D-004：首版固定上限由用户选择，代价是拒绝部分大文件；出现真实需求后重审；常量位置为上传校验入口。
>
> KNOWLEDGE 不变，因为这次选择尚未产生可跨项目复用的经验。

## Hook 如何工作

Skill 定义什么值得写、写到哪里和什么时候提交。Hook 用于提醒当前 agent 检查遗漏，不理解或代写设计理由，也不执行 Git 提交。

| 事件 | 行为 |
|---|---|
| SessionStart | 提供文档入口与维护约定；压缩后提供快照入口 |
| UserPromptSubmit | 提供当前回合标识，供 agent 完成检查后回执 |
| Stop | 只读检查；未回执时请求补查一次，宿主标明已经续过本轮则放行 |
| PreCompact | 本轮已有允许记录的回执时，从已有 checkpoint 和 Git 现场生成快照；无回执或只读则跳过 |

首版自动 Hook 适配 Codex 本地运行。其他 agent 可用同一 Skill 和交接材料，但 Hook 配置需适配其宿主。Hook 信任、配置加载和语义记录质量是不同环节；脚本测试通过不等于所有宿主都已自动触发。

## 脚本入口

在本目录运行以下命令；用于其他项目时把 `.` 换成项目路径。已经安装时使用安装目录下脚本的实际路径。

```sh
python scripts/dev_memory.py init --project . --hooks codex
python scripts/dev_memory.py checkpoint --project . --session local-handoff --summary "当前目标与进度" --next "接手后的第一个动作" --constraints "当前操作边界" --verification "已运行检查与缺口"
python scripts/dev_memory.py handoff --project . --session local-handoff
python -m unittest discover -s tests -v
```

`handoff` 不带 `--output` 时只输出文本；需要文件时指定新路径。它不打包补丁、未跟踪文件或原始聊天，接手者仍须能访问对应代码。`.dev-memory/` 中的运行状态和快照被本地忽略；长期文档随代码提交。

完整命令和回执协议见 [运行说明](references/runtime.md)，交接字段与接手步骤见 [交接流程](references/handoff.md)。

## 验证

14 项运行时检查通过，覆盖初始化和既有配置保留、Hook 回执与防循环、只读边界及不同 Git 状态下的交接。Skill 已通过 skill-creator 格式检查，以及独立的修改提交和只读接手试用。证据及验证范围见 [H-001](docs/dev-memory/HISTORY.md#h-001)；实际宿主自动触发尚未验证。

## 依据与替代方案

- [ADR 原始说明](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)：已有的轻量决策记录方法。
- [OpenAI 官方 Skills 文档](https://learn.chatgpt.com/docs/build-skills)及 [Hooks 文档](https://learn.chatgpt.com/docs/hooks)：Skill 结构和宿主生命周期事件。
- [Anthropic 的长任务工程实践](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)：通过明确进度、Git 和验证结果支持跨会话接续。

这些方式也可以手工组合。Dev Memory 的作用是固定分工、维护时机与交接步骤，不主张发明了决策记录或 Git 版本管理。MIT 许可。
