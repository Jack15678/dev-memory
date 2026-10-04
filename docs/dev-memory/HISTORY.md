# 开发记录

按完整任务保存行为变化、直接原因、验证与版本关系。长期设计理由引用 DECISIONS 中的条目。

<a id="h-001"></a>
## H-001 · 2026-10-03 · 完成开发记忆 Skill 首版

- 目标与验收：实现三份职责正交的记录、按完整任务提交本地 Git、Codex Hook 提醒以及跨会话交接；用真实隔离项目检验修改、记录、提交和接手流程。
- 实现状态：已完成 Skill、文档模板、Python 标准库运行脚本、运行说明和 MIT 许可；已安装个人 Skill，并在本子项目启用自身维护。目标目录之外的项目未批量启用。
- 行为变化：agent 可按记录用途保存新信息、区分决策来源与成熟度、记录失败及验证缺口、处理决策替代、按需检索和追溯设计依据。运行脚本提供初始化、回执、checkpoint、交接快照及 Codex Hook 协议。
- 原因与约束：实现用户讨论后确认的开发记忆流程；长期选择见 [D-001](DECISIONS.md#d-001) 至 [D-004](DECISIONS.md#d-004)。
- 本轮修正：重复初始化保留用户配置的 Git 策略；Stop 检查改为完全只读；PreCompact 按当前回执决定是否保存。这些行为已纳入运行时检查。
- 涉及位置：`SKILL.md`、`agents/openai.yaml`、`references/`、`assets/templates/`、`scripts/dev_memory.py`、`tests/test_dev_memory.py`；本目录保存本项目的真实记录。
- 版本：代码与记录随包含 H-001 的任务提交保存；提交成功前属于未提交工作区。沿用上级已有 Git 仓库，只纳入 `dev-memory/` 明确路径。

### 实际验证

- 在本仓库 `dev-memory/` 运行 `python -X utf8 -m unittest discover -s tests -v`：14 项检查通过。覆盖初始化保留、提交策略保留、嵌套项目范围、Hook 回执与防循环、只读回合与 Git 索引不落盘、压缩快照、未提交/未跟踪/空仓库/分离 HEAD、交接覆盖拒绝，以及 Windows 中文和空格路径命令。
- 使用本机 skill-creator 的 `quick_validate.py` 检查源目录与已安装副本：均返回 `Skill is valid!`。检查本地 Markdown 目标、UI 元数据及安装文件逐字节一致性：通过。
- 独立修改试用：在临时 Git 项目启用 Skill（`--hooks none`），修改上传大小判断并运行既有四项边界检查；agent 写入 H/D 条目、保持 KNOWLEDGE 无新增内容，将代码与记录一并提交为 `5fbb319`。主 agent 核对提交文件和工作区，确认用户原有笔记修改及未跟踪草稿未被纳入。
- 独立接手试用：另一个无前文 agent 只读取交接包和真实项目，找回固定上限的理由、核对 HEAD 和工作区，并明确测试结果属于历史证据。前后检查临时项目全部 53 个文件（含 `.git`）的路径、大小与修改时间，均无变化。
- 验证范围：以上为单方案试用和运行时协议检查，未做 A/B 测试；未在实际 Codex 宿主中信任并观察自动 Hook 触发。宿主仍要求通过 `/hooks` 审阅，不能将生成配置称为已激活。

<a id="h-002"></a>
## H-002 · 2026-10-04 · 比较已有方案并准备独立开源发布

- 目标与验收：深入比较三个已有方案，明确值得借鉴的能力及成本；完善带图 README，并将本 Skill 独立推送到新的公开 GitHub 仓库。
- 状态：本地比较和发布材料已完成；公开仓库 [Jack15678/dev-memory](https://github.com/Jack15678/dev-memory) 已创建并推送。首轮 CI 中 Linux 通过；Windows 测试现场的路径归一化已修正，待下一轮 CI 确认。
- 行为变化：新增源码对比报告、英文说明、两张 SVG 图和 Windows/Linux CI；中文 README 补充安装、实际使用、提交策略选择和已知限制。运行脚本与 Skill 核心协议未改变。
- 来源与取舍：见 [D-005](DECISIONS.md#d-005)；详细发现与固定版本证据只维护在 [对比报告](../comparison.zh-CN.md)，不重复抄入本记录。
- 本轮验证：在本项目运行 `python -X utf8 -m unittest discover -s tests -v`，14 项通过；skill-creator 的 `quick_validate.py` 通过。两张 SVG 渲染为 PNG 并人工视觉检查，文字无裁切、步骤和文件归属清晰。
- 实际观察：本轮会话收到 dev-memory 的维护规则与回执提示；这补充了上下文注入的观察，仍不代表完整 Stop/PreCompact 生命周期经过实际宿主验证。
- 失败与修正：[首轮 CI](https://github.com/Jack15678/dev-memory/actions/runs/37214910700) 的 Windows 临时目录含 `RUNNER~1` 短路径。测试直接调用 Hook 时传入未归一化 project，而 Hook 的 cwd 已 resolve，导致同一目录被判断为范围外。实际 CLI 已在入口 resolve project；测试 fixture 现同样归一化后再调用，未改变运行协议。
- 版本：随包含 H-002 的发布准备提交保存；远程结果在实际完成后更新。不纳入其他项目、研究临时文件、机器路径 Hook 配置或 `.dev-memory/` 运行状态。
