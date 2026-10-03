# 运行与 Codex Hook 接入

运行时只依赖 Python 3.10+ 标准库；Git 用于本地只读版本检查，实际提交由当前 agent 使用原生 Git 执行。将下文 `SKILL_DIR` 替换为当前 Skill 的实际路径。首次启用和处理 Hook 反馈时阅读本页。

## 初始化

```text
python -X utf8 SKILL_DIR/scripts/dev_memory.py init --project PROJECT_DIR --hooks codex
```

`--hooks none` 仅启用文档和项目规则。目标项目应是用户指定的实际子项目，不必是上级 Git 根；从该项目目录启动后续会话以加载它的项目配置。

初始化保留已有文档、AGENTS 内容和其他 Hook。`.dev-memory.json` 是可移植的项目启用配置；`.dev-memory/` 是本地运行状态与快照，不是第四份长期文档。含本机路径的 `.codex/hooks.json` 也保持本地忽略。重复初始化不会清空记录。

启用意味着采用项目配置中的本地任务提交策略；用户指定不同策略时保留或调整配置并遵守。脚本不会执行 git add/commit、初始化 Git 或推送。

## Hook 事件

| 事件 | 行为 |
|---|---|
| SessionStart | 注入短规则与文档入口；压缩后提供已保存交接快照入口 |
| UserPromptSubmit | 提供当前 session/turn 和回执命令，便于正常回合结束前确认已检查 |
| Stop | 只读检查；已有回执或宿主标明已经续过本轮则放行，否则请求当前 agent 补查一次 |
| PreCompact | 仅在本轮已有允许记录的回执时，从已有 checkpoint 和 Git 状态生成本地快照；无回执或只读则跳过 |

`UserPromptSubmit` 只提供当前回合标识，避免正常完成记录后仍无条件多跑一次收尾。写入代码时的判断仍由 Skill 执行；没有逐次文件编辑 Hook，不把每次工具调用写成日志。

防循环采用宿主提供的 `stop_hook_active`，不靠 Stop 额外写入一个状态文件。无法确认本轮写权限时，PreCompact 不创建文件；恢复会话仍可读取已有 checkpoint。长任务中及时保存重要记录，不能把首次保存拖到压缩前。

Hook 脚本接收 stdin JSON，可以直接进行协议测试，但这不等同于宿主真的调用过 Hook。Codex 的当前命令/MCP Hook 支持和输出约定见[官方文档](https://learn.chatgpt.com/docs/hooks)。

## 正常回合的回执

完成记录检查后，采用 Hook 实际提供的 session/turn，不猜 ID：

```text
python -X utf8 SKILL_DIR/scripts/dev_memory.py ack --project PROJECT_DIR --session SESSION_ID --turn TURN_ID --outcome recorded
```

没有新信息用 `noop`；受只读范围限制用 `read-only`。回执是本地运行元数据，不代表语义内容通过审核，不会生成 HISTORY 条目。用户禁止任何落盘时连回执也不写，遵守限制即可；Hook 的一次续问不能授予写权限。

## 任务 checkpoint

長任务中重要进展形成后、或需要交接前，保存当前任务的简短摘要：

```text
python -X utf8 SKILL_DIR/scripts/dev_memory.py checkpoint --project PROJECT_DIR --session SESSION_ID --summary "目标、验收、已做与未完成事项、相关 H/D 编号" --next "接手后的第一个具体动作" --constraints "用户最新要求和有效操作边界" --verification "已经运行的检查、结果与剩余缺口"
```

这是待交接的短期状态；持续生效的设计理由已经写入 DECISIONS，checkpoint 只引用它。没有 Hook 提供 session 时使用明确的本地交接标识，并在 handoff 中传入同一标识，不冒充宿主 session ID。

## 生成快照

```text
python -X utf8 SKILL_DIR/scripts/dev_memory.py handoff --project PROJECT_DIR --session SESSION_ID
```

不带 output 时只输出到 stdout；要存文件，显式传 `--output` 指定新文件。手动使用时先读取目标路径，不能覆盖用户既有文件。交接过程见 [handoff.md](handoff.md)。

## 宿主信任和作用范围

Codex 要求项目配置受信任，且新建/改动的非托管 Hook 需要审阅信任。初始化给出具体配置后，由用户在该项目启动的 Codex 中通过 `/hooks` 审阅；不要修改信任数据库或使用绕过信任参数。安装了 Skill 或写好了配置不等于 Hook 已经激活。

首版只生成 Codex 本地 Hook 配置。其他支持 Skill 的 agent 可以按同样三文档与交接流程工作，但 Hook 事件协议需要单独适配。初始化不修改全局 Hook 配置。
