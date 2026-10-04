# Dev Memory 与三个已有方案的比较

核查日期：2026-10-04。本文区分源码事实、作者说明和我们的建议。阅读上游实现与测试代码，不代表运行验证；本次未安装竞品、运行其测试或做 A/B 测试。

采纳更新：2026-10-05，用户确认实施下表前三项优先建议；已更新本仓库 Skill 的记录与交接规则，见 [D-006](dev-memory/DECISIONS.md#d-006)。上游比较仍以表内固定版本为准。

## 比较对象和证据

| 对象 | 固定版本 / 来源 | 实际阅读范围 |
|---|---|---|
| OwnMem | [0134632，包版本 0.8.0](https://github.com/grpcer/ownmem/tree/01346322f22e87c04fe1dcecc7117f32589aa208) | README、Skill、schema、生成/audit/检索/证据核验代码，以及代表性测试源码 |
| Fractal Skills | [3dccdb8](https://github.com/yaukwan/fractal-skills/tree/3dccdb8fa4e69d99ee5ae38f5d92b6116019f195) | 当前 Skill、决策准入/替代规则、scope checker、验证脚本、协议与模板；另读旧 audit/repo 的历史版本 |
| Codex project-handoff Skill | [LINUX DO 第 3 楼，symy，2026-05-23](https://linux.do/t/topic/2230307/3) | 作者公开设计说明与附件入口；ZIP 下载受阻，未核验源码和许可证 |
| Dev Memory | 本仓库 [SKILL.md](../SKILL.md)、[运行脚本](../scripts/dev_memory.py)和 [references](../references) | 三份记录的语义规则、实际 Python 初始化/Hook/checkpoint/handoff 路径、现有测试 |

上游的帖子是使用背景，固定提交才是代码比较依据。本文不评价未测量的 token 节省、运行速度或真实用户效果。

## 主要异同

| 维度 | Dev Memory | OwnMem | Fractal Skills（当前版本） | Codex 交接 Skill（作者说明） |
|---|---|---|---|---|
| 主要问题 | 开发过程、理由与版本如何保留，换会话如何接手 | 修改代码前如何找回适用的工程教训 | 后续 agent 如何发现并遵守当前模块合约与架构约束 | 新会话如何恢复当前任务 |
| 长期材料 | H 历史、D 决策、K 经验三份文档 | 总目录、领域目录、每条经验一个文件 | 多层 AGENTS、源码合约、决策 Skill、分类 docs | 未核验长期记忆能力 |
| 局部取舍/硬编码 | 可写入 D，注明理由、位置、重审条件 | 可作为有范围和证据的经验或决定指针 | 局部实现说明通常进 engineering，决策 Skill 聚焦长期系统约束 | 作为当前任务背景交接 |
| 写入时机 | 项目启用后，agent 按信息价值及时更新 | 按工作流起草记忆，工具生成结构并检查 | Skill 被选择后按职责维护受影响上下文 | 生成、更新交接时 |
| 自动触发 | Codex 生命周期 Hook 提醒当前 agent | 有修改前按文件召回的 Hook 和 MCP 读取入口 | 本次读取的当前树未发现生命周期 Hook；依赖 Skill 路由与流程 | 是否有 Hook 未核验 |
| 程序能检查什么 | 初始化保留、回执、Git 现场、输出防覆盖 | schema、引用、证据变化、配额、索引和投递策略 | 路径范围匹配、Skill 基础结构 | 锁与自检仅见作者描述 |
| Git | 默认完整任务验证后由 agent 提交代码与记录，策略可覆盖 | 文件随仓库流转，工具不替代审查和提交 | 完成任务规格不自动授予 commit/push 权限 | 恢复时检查 Git 状态；自动提交未知 |
| 接手材料 | 短期 checkpoint + Git 快照 + H/D/K 入口 | 工程经验库；本次未确认等价的任务快照协议 | 可从任务规格进度与证据续接 | 时间戳交接、latest/index、工作区核对 |
| 维护成本来源 | agent 的记录判断、文档增长与引用维护 | schema、凭据、索引、宿主适配和检索治理 | 合约层级、决策 Skill 路由与同步关系 | 历史快照、共享入口与并发管理 |

共同基础很明确：项目内可阅读的记录、代码/证据引用、生命周期意识，以及恢复时核对现场，都已有先例。Dev Memory 的具体取舍是三份长期文档、任务级本地提交与临时交接快照；这是一种组合选择，不代表已经证明优于其他方案。

## OwnMem：工程经验的检索与治理

其典型链路是：agent 提出经验 → CLI 生成主题和路由 → 补充正文及证据 → 生成内容凭据 → audit → 审查并提交。读取时从 Markdown 编译索引，按路径/词语等检索，再结合证据、适用条件和上下文预算决定交付正文、入口指针或不交付。具体入口见 [Skill](https://github.com/grpcer/ownmem/blob/01346322f22e87c04fe1dcecc7117f32589aa208/skills/ownmem/SKILL.md)、[schema](https://github.com/grpcer/ownmem/blob/01346322f22e87c04fe1dcecc7117f32589aa208/schemas/memory.schema.json)、[运行时](https://github.com/grpcer/ownmem/blob/01346322f22e87c04fe1dcecc7117f32589aa208/lib/memory-runtime.mjs)。

值得理解的实现边界：

- **证据存在、测试执行过、当前仍适用是不同状态。** 它把测试锚点与执行结果分开；发现符号内容变化时可以降级，不能靠重新生成凭据把失败结果变为通过。[证据核验](https://github.com/grpcer/ownmem/blob/01346322f22e87c04fe1dcecc7117f32589aa208/lib/memory-evidence-verifier.mjs)
- **结构检查并不能判定理由真实。** 新主题模板允许初始空 evidence；audit 检查格式、路由、引用、证据和治理状态，不会理解正文真伪或执行其中所有测试。[生成器](https://github.com/grpcer/ownmem/blob/01346322f22e87c04fe1dcecc7117f32589aa208/lib/memory-scaffold.mjs)、[audit](https://github.com/grpcer/ownmem/blob/01346322f22e87c04fe1dcecc7117f32589aa208/lib/memory-audit.mjs)
- **不同工具的“只读”含义需要核对。** 部分 audit 路径会更新配额状态，召回可能重编索引并保存本地观测；这与“不改主题正文”可以同时成立。Dev Memory 的 Stop 则以不写文件为检查目标。
- **内容凭据不等于身份签名。** `trust.lock` 使用内容摘要和链校验来发现变化；摘要本身不能证明独立的人批准了改动。[凭据代码](https://github.com/grpcer/ownmem/blob/01346322f22e87c04fe1dcecc7117f32589aa208/lib/memory-trust-store.mjs)

它有独立检索系统；Dev Memory 目前依靠 agent 按编号、路径和 Git 历史查记录。后者减少了索引维护，也把查找质量更多交给 agent，文档增长后的表现尚未验证。

上游提供 benchmark，但其检索命中包括入口指针；公开 grep 基线是整句包含匹配。本文不把这个指标解释成通用问答正确率，也不将它用于给四个方案排名。[统计实现](https://github.com/grpcer/ownmem/blob/01346322f22e87c04fe1dcecc7117f32589aa208/benchmarks/public-benchmark.mjs)

## Fractal：让当前约束可被发现和执行

**当前源码与 5 月的分享帖有显著差异。** 旧 `fractal-audit` 已删除，`fractal-repo` / `fractal-context` 合并为 `fractal-sync`；决策的权威位置变为项目内 `.agents/skills/decision-*/`。比较当前能力时不能继续照搬原帖清单。[CHANGELOG](https://github.com/yaukwan/fractal-skills/blob/3dccdb8fa4e69d99ee5ae38f5d92b6116019f195/CHANGELOG.md)

它按根目录、模块目录、源文件合约组织当前上下文，再用决策 Skill、engineering、research、postmortem、specs 和 archive 区分材料职责。决策描述负责说明什么任务应加载这条约束；实质改变决定时建立后继，将旧决定退出自动发现，并保留历史及替代关系。[决策入口](https://github.com/yaukwan/fractal-skills/blob/3dccdb8fa4e69d99ee5ae38f5d92b6116019f195/skills/decision-capture/SKILL.md)、[归属规则](https://github.com/yaukwan/fractal-skills/blob/3dccdb8fa4e69d99ee5ae38f5d92b6116019f195/skills/decision-capture/references/authority-rules.md)、[退役与同步](https://github.com/yaukwan/fractal-skills/blob/3dccdb8fa4e69d99ee5ae38f5d92b6116019f195/skills/decision-capture/references/skill-sync-rules.md)

这是“当前应该遵守什么”的组织方式。Dev Memory 的 D 还承担保存小设计、硬编码取舍和历史理由的任务，不需要将每一条都提升为自动发现的 Skill。

其 Node scope checker 决定哪些路径匹配允许范围，Python validator 检查 Skill 结构。语义同步仍由 agent 执行；这些脚本不构成任意文件写入的权限隔离，也不能证明决定正确。[scope checker](https://github.com/yaukwan/fractal-skills/blob/3dccdb8fa4e69d99ee5ae38f5d92b6116019f195/skills/fractal-setup/assets/fractal-scope/scripts/check-scope.js)、[结构校验](https://github.com/yaukwan/fractal-skills/blob/3dccdb8fa4e69d99ee5ae38f5d92b6116019f195/skills/skill-design-guidelines/scripts/validate_skill.py)

对我们最有价值的是其对**代码现状与批准意图**的区分：代码变了可能是合理的新决定，也可能是实现偏离旧约束。直接让“最新代码覆盖旧设计文档”会丢失这个区别。

## Codex 交接 Skill：快照发现和保存策略

作者描述了不可覆盖的时间戳交接、latest/index 入口和恢复时的 Git 核对；共享入口通过锁协调更新。其 [ZIP 附件](https://linux.do/uploads/short-url/mRTI32uWtLQGTpFyM0YsWAukEzB.zip)本次直接下载返回 403，网页读取也未取得文件。因此我们确认的是这些公开设计主张，无法确认锁、原子写入或跨平台代码实际如何实现。[原说明](https://linux.do/t/topic/2230307/3)

Dev Memory 已有手动输出防覆盖；自动 PreCompact 快照则会刷新同 session 的路径。它没有跨 session 的 latest/index，新会话通常需要用户提供交接路径。不同 session 的状态隔离，但同 session 的 JSON 读改写没有锁；不能宣称支持任意并发写入。

可以吸收的重点是明确两种寿命：可刷新的恢复状态，以及明确命名保存的阶段快照。若日后用户经常找不到交接文件，先考虑只读列出快照，再决定是否需要共享索引和锁。时间最新的快照不一定属于当前任务。

## 值得借鉴什么

以下是 2026-10-04 的建议；其中前三项于 2026-10-05 采纳为 Skill 规则，其余仍按需评估。Python 运行协议没有改变。

| 优先级 | 借鉴点 | Dev Memory 已有基础 | 最小改进与成本 |
|---|---|---|---|
| 优先 | 决策写清适用范围和读取时机（Fractal） | D 已记录位置和重审条件；改设计前要求查 D | 增加可选的模块/行为范围，让 agent 更容易在改动前找到它；无需一条 D 一个 Skill |
| 优先 | 区分实现事实与批准意图（Fractal） | 已区分来源、推测和决策替代 | 遇到冲突先分类，再更正文档或实现；证据不足时保留冲突，而非自动承认新代码就是新决定 |
| 优先 | 分开表示证据入口、执行结果与适用版本（OwnMem） | H 已要求真实命令与验证范围，接手区分历史证据 | 用实际例子明确“文件存在但未运行”“旧版本通过”；暂不增加凭据和索引系统 |
| 按需 | 替代决定后检查相关引用（Fractal） | 稳定编号、旧决定保留、后继链接 | 局部查找受影响编号，历史引用保留，当前约束入口更新；无需全仓重写 |
| 按需 | 区分自动恢复快照与阶段存档（交接方案） | 手动输出防覆盖，自动状态按 session 刷新 | 在使用说明中讲清两者；真实找不到文件时再增加只读列出入口 |
| 出现故障后 | 客观的记录结构检查（OwnMem） | 条目已有约定格式 | 检查重复编号、断链和缺失锚点；需承担格式兼容和误报成本，不能声称检测理由真伪 |

暂不建议引入：向量检索/常驻服务、独立信任凭据、每条决策一个 Skill、完整三层代码合约、硬性经验数量配额、共享快照索引与跨平台锁。这些能力服务于各自场景；当前的需求和使用证据还不足以抵消维护成本。

## 发布定位与取舍

Dev Memory 可以继续服务“agent 写得快，维护者需要回头理解为什么”的个人开发场景。优势候选是少量文件、可读记录、默认任务级版本保存和明确的接手流程；它们仍需要真实使用证明，不能写成已测量的竞争优势。

相应代价也应公开：三份文档会增长，没有专用检索或语义审计，自动记录依赖 agent 判断，Hook 仅适配 Codex，多人并发与其他宿主未验证。选择更完整的工程经验治理或架构约束系统时，上述项目值得优先试用。

## 复用与归属

OwnMem 固定版本提供 [Apache-2.0 LICENSE](https://github.com/grpcer/ownmem/blob/01346322f22e87c04fe1dcecc7117f32589aa208/LICENSE) 与 [NOTICE](https://github.com/grpcer/ownmem/blob/01346322f22e87c04fe1dcecc7117f32589aa208/NOTICE)。Fractal 的源码 Skill 声明 Apache-2.0，但此次固定树未见根 LICENSE/NOTICE；生成决策的模板另有 Proprietary 字段。交接附件的许可证未知。

本轮仅独立总结设计、链接来源，没有复制上述项目的代码、Skill 正文或模板。后续若直接复用具体文件，应先核对其授权和归属要求，不能将上游材料一概重新标成 MIT。
