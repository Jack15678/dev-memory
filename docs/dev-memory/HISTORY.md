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
- 状态：已完成；公开仓库 [Jack15678/dev-memory](https://github.com/Jack15678/dev-memory) 已创建并推送。修正 Windows 测试现场的路径归一化后，[第二轮 CI](https://github.com/Jack15678/dev-memory/actions/runs/37215025159) 在 Windows/Linux、Python 3.10 上均通过 14 项测试，验证提交为 `2956df7`。
- 行为变化：新增源码对比报告、英文说明、两张 SVG 图和 Windows/Linux CI；中文 README 补充安装、实际使用、提交策略选择和已知限制。运行脚本与 Skill 核心协议未改变。
- 来源与取舍：见 [D-005](DECISIONS.md#d-005)；详细发现与固定版本证据只维护在 [对比报告](../comparison.zh-CN.md)，不重复抄入本记录。
- 本轮验证：在本项目运行 `python -X utf8 -m unittest discover -s tests -v`，14 项通过；skill-creator 的 `quick_validate.py` 通过。两张 SVG 渲染为 PNG 并人工视觉检查，文字无裁切、步骤和文件归属清晰。
- 实际观察：本轮会话收到 dev-memory 的维护规则与回执提示；这补充了上下文注入的观察，仍不代表完整 Stop/PreCompact 生命周期经过实际宿主验证。
- 失败与修正：[首轮 CI](https://github.com/Jack15678/dev-memory/actions/runs/37214910700) 的 Windows 临时目录含 `RUNNER~1` 短路径。测试直接调用 Hook 时传入未归一化 project，而 Hook 的 cwd 已 resolve，导致同一目录被判断为范围外。实际 CLI 已在入口 resolve project；测试 fixture 现同样归一化后再调用，未改变运行协议。
- 发布核对：远程为 PUBLIC，默认分支 main；独立树包含 23 个项目文件，未包含其他项目或本机运行状态。通过 GitHub README 渲染接口确认两张 SVG 引用和替代文本正常。
- 版本：沿用子目录历史提取独立发布分支；源仓库 `c7ae79f` 对应首次公开提交 `cb97a33`，测试修正源提交 `c0aa9f7` 对应公开 `2956df7`。本条最终状态随后续文档提交保存。

<a id="h-003"></a>
## H-003 · 2026-10-05 · 采纳三项记录与交接改进

- 目标与验收：落实用户同意的三项借鉴点，在单方案接手试用中核对 agent 对设计冲突和历史验证的处理；同步本机安装及公开仓库。
- 状态：规则修改与独立试用已完成；Skill、记录模板、交接说明和中英文示例已更新，本机安装副本已同步。
- 行为变化与原因：按 [D-006](DECISIONS.md#d-006) 增加决策读取范围，区分实现事实与已批准意图，并将验证证据绑定受测版本；未改变 Python 运行协议。
- 涉及位置：`SKILL.md`、`references/records.md`、`references/handoff.md`、两份 README 和 `docs/comparison.zh-CN.md`。安装副本中三个变动的 Skill 文件已核对旧版无单独修改后同步。
- 验证对象：父仓库基线 `4e63b2a` 加本条所列文档和规则的未提交修改；基线只是起点，不是本次已验证版本。
- 本轮验证：源 Skill 和安装副本的 `quick_validate.py` 均通过；安装的三个改动文件与源文件逐字节一致；本地 Markdown 链接目标检查及 `git diff --check` 通过。
- 独立接手试用：使用上述已修改 Skill，在隔离 Git 项目提供旧快照、已采用的 20 MiB 决策、实际历史测试及已有的 100 MiB 未提交改动。无前文 agent 找到相关 D-001，保留原决定，在 H 和新交接中记录冲突；明确四项通过只属于 fixture 提交 `9551189`，当前基线 `48f1d56` 加 `upload.py` 未提交改动不在该结果覆盖范围。它将预期测试冲突标为静态推断，遵守不改业务代码、不运行测试、不提交的本轮限制。主 agent 核对实际 H/交接、diff 和 HEAD；原 D/K、业务代码差异及提交均保持原状。
- 验证范围：上述为一个合成场景的单方案试用，未做 A/B 测试；它验证了本次规则在该场景下的执行，不证明任意任务或长期使用的语义判断均正确。
- 历史验证：公开提交 `71b76fc` 的 [CI](https://github.com/Jack15678/dev-memory/actions/runs/37215118771) 在 Windows/Linux 上各通过 14 项运行时测试；这是历史证据。本轮修改语义说明，未在本机重跑未改动的运行时测试。
- 社区调研：2026-10-05 核对 [LINUX DO 准则](https://linux.do/guidelines)及[开源推广公告](https://linux.do/t/topic/1776670)，须满足完整开源、链接认可、标签及原则上每周一帖等要求；开源推广专项条款禁止 AI 生成/润色及直接复制 README。[V2EX 节点规则](https://www.v2ex.com/help/node)欢迎个人作品进入分享创造；[AI 文本规则](https://www.v2ex.com/help/anti-flood)设有 AI 节点讨论例外，但不能仅因作品是 AI Skill 就推定分享创造适用例外。建议用户本人写帖，未代拟或发布社区帖子。
- 版本：规则与对应记录随包含 H-003 的提交保存；提交成功前为未提交工作区。公开仓库继续仅发布 `dev-memory/` 子树。
