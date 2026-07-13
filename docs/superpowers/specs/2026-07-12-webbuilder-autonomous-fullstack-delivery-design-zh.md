# WebBuilder 自主全栈交付设计规格

日期：2026-07-12

状态：修订草案，等待用户审核

## 1. 摘要

WebBuilder 将继续定位为通用全栈 Web 系统交付 Skill，不会变成 WebGIS、数据标注、电商或其他垂直领域的专用生成器。

目标使用体验为：

```text
用户需求
-> AI 生成解决方案契约
-> 用户进行一次常规的统一确认
-> 在宿主能力范围内自主完成设计、开发、验证、修复和交付
-> 交付，或在声明的停止条件下保存可恢复检查点
-> 产出带可验证证据、可运行的生产级 MVP 工程
```

对于所有具有用户界面的项目，UI/UX 设计属于必选核心能力。特殊领域知识可以在相关需求出现时渐进加载，但不能拥有工作流、创建独立状态机，也不能作为需要用户选择的产品模式。

WebBuilder 本身就是最终产品：一个可移植 Skill、本地可读状态文件和小型确定性 Python 工具。子代理、浏览器、Git、Worktree、Docker 和终端由宿主提供。核心产品不需要后台服务。

本设计扩展 WebBuilder 现有的阶段、状态文件、任务契约、风险控制、Worktree 交接、验收门禁、集成门禁、修复预算和交付报告，不替换它们。

## 2. 目标

1. 接收用户对新 Web 系统的简短需求。
2. 由 AI 推断生产级 MVP 产品定义，不要求用户自己编写 PRD。
3. 将需求、范围、UI 方向、技术选型、架构、风险和验收标准合并为一个审核包。
4. 自主实现前只要求一次常规用户确认，之后仅在声明的停止条件或新的高影响授权场景下暂停。
5. 交付覆盖批准契约中所有适用 UI、后端、数据、测试、启动和文档能力的完整可运行工程。
6. 在相应质量域适用时，通过可机器验证的功能、UI、无障碍、性能、安全和交付证据证明完成状态。
7. 将 WebBuilder 的最终产品形态保持为一个轻量、宿主驱动的 Skill，加本地文件和小型确定性 Python 工具，不增加后台服务、Worker 池、插件运行时或强制外部 AI 服务。
8. 保留现有引导模式，用于需要渐进式需求发现或多次高影响决策的项目。
9. 任何自主停止都可以恢复，不重复有效的已完成任务，也不信任只写入一半的状态。

## 3. 非目标

- 不保证任何 Web 产品都能仅凭一句话且没有任何不确定性地完成。
- 不取消凭据、付费资源、外部账户、破坏性操作或不可逆生产操作所需的用户授权。
- 不把完整的 WebGIS、标注、电商、医疗或其他垂直系统运行时嵌入 WebBuilder。
- 不替代宿主提供的 Agent、浏览器、Git、Worktree 或部署能力。
- 不引入常驻调度器、数据库 Worker 池或无人值守远程合并服务。
- 不在宿主会话结束后继续后台运行；WebBuilder 会保存检查点，供下次会话恢复。
- 不用漂亮截图代替功能正确性、无障碍、安全或性能验证。
- 不对真正的纯 API 项目强制执行 UI 门禁；这类项目必须记录明确的 `not_applicable` 原因。
- 不把 Agent 写入的 `passed` 文本当作证明，而不验证命令结果和引用产物。

## 4. 与现有工作流的兼容性

现有顶层流程保持权威地位：

```text
Project Rules
-> User Discovery Gate
-> First-Principles Analysis
-> Requirement Baseline
-> Technology Strategy
-> Interface Design Baseline
-> System Design
-> Task Breakdown
-> Task Execution Loop
-> Integration Validation
-> Delivery
```

自主模式只改变执行前各阶段向用户展示和确认的方式，不改变它们的职责。

在引导模式中，WebBuilder 可以继续每次询问一个高影响问题。在自主模式中，WebBuilder 内部生成执行前产物草案，然后将一份汇总后的 Solution Contract 提交用户确认一次。

以下现有执行机制保持不变：

- `single`、`delegated` 和 `parallel` 执行模式；
- Git 可用时使用任务分支和 Worktree；
- Orchestrator 拥有验收和集成决定权；
- Developer、Tester、Reviewer 和 Repairer 职责；
- 串行集成；
- 主工作区复验；
- 任务和集成修复限制；
- 只有证据闭环后才能交付。

schema 1.4 引入本设计的自主状态和证据语义。现有 schema 1.3 项目通过幂等迁移保留内容，并默认使用 `guided`，直到用户明确批准自主模式。

## 5. 交付模式

增加项目级交付模式：

```yaml
delivery_mode: guided | autonomous
```

### 5.1 引导模式 `guided`

保留当前 User Discovery 行为，适用于：

- 用户希望参与产品塑造；
- 已有项目存在重要但未记录的约束；
- 需求仍包含未解决的高影响选择；
- 工作涉及关键迁移、生产环境、合规或外部系统风险。

### 5.2 自主模式 `autonomous`

面向新建生产级 MVP Web 系统：

1. 阅读用户需求和项目规则。
2. 推断产品、用户、流程、范围、UI 方向、技术栈、架构、风险和验收标准。
3. 生成需求基线、系统设计和任务计划草案。
4. 展示一份统一的 Solution Contract。
5. 用户批准后，将基线标记为可执行并持续推进，直到交付或触发明确停止条件。

只有宿主能够提供已批准契约要求的全部能力时，自主模式才可执行。缺少可选能力时可以记录降级，例如从 `parallel` 降为 `single`。缺少必需能力时进入 `environment_blocked` 或切换到 `guided`，绝不能降低交付声明标准。

现有项目和迁移项目默认使用 `guided`。新项目可以在确认前选择 `autonomous`，但只有批准当前契约 revision 且宿主能力门禁通过后才能执行。

## 6. 一次确认契约

不新增独立的 `solution-contract.md`。在 `requirements-baseline.md` 中增加简洁的 `## Solution Contract` 章节，使现有状态文件继续作为唯一事实来源。

确认包必须包含：

- 问题和预期结果；
- 目标用户和主要任务；
- 核心能力；
- 明确的非目标；
- 主要业务流程；
- 页面和导航摘要；
- UI 方向和信息密度；
- 选定的技术配置和主要架构决定；
- 数据、权限、安全和集成假设；
- 重要风险和排除项；
- 交付内容；
- 验收标准和验证方式。

确认元数据由 `requirements-baseline.md` 独占：

```yaml
confirmation_status: pending | approved | changes_requested
contract_revision: 1
approved_contract_revision: null | 1
approval_digest: null | sha256:<digest>
approval_scope: requirements_design_stack_ui_execution
approval_evidence: null | user_message_reference
approved_by: null | user
approved_at: null | ISO-8601 timestamp
discovery_method: interactive | inferred_contract
```

审批摘要只覆盖实质性契约：产品范围、非目标、验收信号、所选技术 profile、公共接口、数据与权限边界、交付假设和声明风险。它不冻结普通任务拆分、低风险实现细节或有界修复。只要这些内部调整继续满足已批准的契约 revision，就不需要重新确认。

Digest 输入使用文档化的规范序列化：UTF-8、LF 换行、稳定字段顺序、归一化无意义空白，并且只包含上述实质性契约字段。审批时间、审批者元数据、证据引用、任务运行状态和生成的 digest 本身不参与 digest 输入。

`system-design.md` 和 `task-plan.md` 记录 `based_on_contract_revision`。实质性契约变化会递增 `contract_revision`，使旧批准失效，并把派生设计、计划和证据标记为 stale，直到新 revision 获批并完成协调。

批准意味着 WebBuilder 可以在确认范围内做出正常、可逆的实现决策，但不授权：

- 使用未提供的真实凭据；
- 创建付费资源；
- 执行破坏性或不可逆的外部操作；
- 执行未明确包含在确认范围内的生产部署或域名变更；
- 实质性扩大或替换已确认的产品范围。

批准后，普通技术细节、UI 细节、低风险依赖、测试修复和预算内修复不再触发额外确认。

确认包包含工作量包络，依据任务数、受影响浏览器流程、外部依赖、必需质量门禁、修复预算和宿主可用并发能力估算。宿主无法可靠计量时，不得虚构固定 token、API 调用次数、耗时或预计中断次数。

## 7. 内部能力架构

WebBuilder 继续作为一个面向用户的 Skill，内部包含七项由 LLM 承担的职责和两个确定性支撑内核。它们是同一个产品内部的逻辑职责，不是后台服务、常驻进程或独立部署组件。

### 7.1 Solution Compiler

将用户需求编译为：

- 结果、用户、任务和流程；
- 功能和非目标；
- 页面和操作；
- 假设、约束和风险；
- 验收信号；
- 一次确认摘要。

### 7.2 Technology and Architecture Planner

- 新项目优先采用版本化的黄金技术配置。
- 只有需求提供具体理由时才选择其他技术配置。
- 在确认包中记录所选配置及其权衡。
- 确认后冻结技术选择，除非证据表明它无法满足契约。
- 不引入确认范围不需要的服务、框架或基础设施。

### 7.3 UI/UX Design Engine

对所有用户可见项目强制执行，负责：

- 信息架构；
- 用户流程和页面层级；
- 视觉方向和信息密度；
- 设计令牌；
- 布局和导航约定；
- 组件行为；
- loading、empty、error、disabled、success、validation 和 permission 状态；
- 响应式和键盘交互；
- 无障碍要求；
- 真实渲染、视觉验证和修复。

### 7.4 Full-Stack Task Planner

使用混合拆分：

1. 先冻结共享契约和基础设施。
2. 再交付包含 UI、API、数据、权限和测试的纵向业务切片。
3. 只在确认产品确实需要时增加管理、审计和全局质量工作。
4. 最后执行完整系统验证和交付。

### 7.5 Execution Controller

继续使用现有的自适应执行、Worker 边界、Worktree、独立检查、串行集成和状态更新规则。

### 7.6 Quality Gate

要求以下方面分别提供证据：

- 功能行为；
- UI 和响应式渲染；
- 无障碍；
- 工程健康；
- 安全；
- 性能；
- 部署和启动冒烟验证。

### 7.7 Delivery Controller

产出可运行工程、需求到证据的追踪关系、运行说明、已知风险和明确的未完成项。

### 7.8 State Kernel

一个小型确定性 Python 状态转换工具负责机器可检查的生命周期变化。它在替换状态文件前验证合法转换、revision 一致性和跨文件不变量，并使用临时文件加转换日志，使宿主中断可以在下次会话中被检测并幂等恢复。

人和 Agent 仍可编辑 Markdown 中的描述性内容。就绪、批准、停止、恢复、验收、集成和交付状态必须通过 State Kernel 转换，不能只靠手工修改状态值来声明成功。

### 7.9 Evidence Kernel

一个小型确定性证据工具执行或导入声明的验证，捕获退出状态和产物元数据，进行秘密脱敏，对产物计算 hash，并生成 manifest。Markdown 文件只索引证据摘要，不能自行制造通过结果。

Evidence Kernel 不是测试框架或远程制品服务。它包装项目选择的命令以及宿主提供的浏览器或安全工具，使交付门禁能够验证证据真实存在、匹配当前契约 revision 和 commit，并代表最新有效尝试。

## 8. 能力适用性与通用质量底线

不要把整个项目划分为 `lite`、`standard` 或 `full`。认证、数据库、UI、无障碍、Docker、审计、性能等关注点相互正交。Solution Contract 按能力记录适用性：

```yaml
capabilities:
  ui:
    status: required | not_applicable
    reason: 项目专属原因
  database:
    status: required | not_applicable
    reason: 项目专属原因
  authentication:
    status: required | not_applicable
    reason: 项目专属原因
  rbac:
    status: required | not_applicable
    reason: 项目专属原因
  audit:
    status: required | not_applicable
    reason: 项目专属原因
  docker:
    status: required | not_applicable
    reason: 项目专属原因
  accessibility:
    status: required | not_applicable
    reason: 项目专属原因
  performance:
    status: required
    profile: baseline | product-specific
  security:
    status: required
    profile: baseline | elevated
```

`not_applicable` 必须提供逐能力理由，并根据项目事实验证。运行环境无法执行不等于 `not_applicable`，而是 `environment_blocked`。门禁级 waiver 独立于能力适用性记录，并且属于例外：必须有明确用户证据、责任人、到期或复核条件以及残余风险。Agent 不能自行创建 waiver，基础安全也不能整体豁免。

所有项目都必须满足通用质量底线：

- 可复现安装，或明确记录无需安装的启动方式；
- 与所选技术栈相适应的构建或语法验证；
- 对主要行为的确定性验证；
- 存在用户界面时提供用户可见错误处理；
- 不提交凭据，并满足基础依赖与安全卫生要求；
- 准确的运行说明和已知限制；
- 需求到证据的可追踪性。

其他义务由能力适用性触发：

- 面向用户的 UI 必须覆盖响应式、键盘操作、可见焦点、相关状态和无障碍检查；
- 持久化数据必须覆盖 schema、迁移或初始化、恢复和干净状态验证；
- 身份认证必须覆盖会话生命周期和授权边界测试；
- 多角色系统必须覆盖 RBAC 和权限拒绝测试；
- 重要状态变化可能需要审计证据；
- 只有批准的交付契约包含容器启动时才要求 Docker；
- 端到端、性能和安全检查深度随批准流程与风险扩展，但基础安全永远不能整体标记为不适用。

## 9. 特殊领域知识

特殊领域知识是渐进加载的参考资料，不是核心工作流的可选版本。

示例：

```text
references/domains/
|-- geospatial.md
|-- annotation.md
|-- ecommerce.md
`-- realtime.md
```

领域参考可以贡献：

- 术语和不变量；
- 需求和非目标；
- 架构决定；
- 任务模式；
- 风险修正；
- 测试场景；
- 互操作和交付检查。

领域参考不得：

- 替换 WebBuilder 状态机；
- 拥有确认或交付流程；
- 让 UI、测试、安全或部署变成可选项；
- 要求用户选择或理解某个能力包；
- 在需求无关时加载。

## 10. 状态文件扩展

本设计将状态 schema 从 1.3 升级到 1.4。初始化创建 1.4 状态。1.3 到 1.4 的迁移必须无破坏、幂等、保留项目内容、创建可恢复备份，并将 `delivery_mode` 默认设为 `guided`。

### 10.1 `requirements-baseline.md`

增加：

- `confirmation_status`；
- `contract_revision`；
- `approved_contract_revision`；
- `approval_digest`；
- `approval_scope`；
- 审批者、时间和证据；
- `discovery_method`；
- 项目能力适用性及理由；
- `## Solution Contract`。

`requirements-baseline.md` 是确认状态和批准证据的唯一拥有者。

保留现有 User Discovery 和 First-Principles 章节。在自主模式中，它们记录 AI 推断的事实、假设和用户的统一批准。

Solution Contract 是面向用户的实质性决定投影。它可以摘要系统设计，但规范架构细节仍由 `system-design.md` 拥有。该投影和派生文件必须引用同一个已批准契约 revision，不能维护相互独立的确认状态。

### 10.2 `system-design.md`

强化现有设计章节，加入：

- `based_on_contract_revision`；
- 选定的技术配置；
- 架构决定和被拒绝的方案；
- 页面和用户流程；
- 数据模型和 API；
- 权限和安全；
- UI Design Lock；
- 组件和状态矩阵；
- 响应式和无障碍要求；
- 验证策略。

UI Design Lock 至少记录：

- 界面类型和信息密度；
- 语义化颜色角色；
- 字体角色；
- 间距、圆角、层级和图标约定；
- 导航和应用外壳；
- 组件规则；
- 动效策略；
- 明确的反模式和合理例外。

### 10.3 `task-plan.md`

增加 `based_on_contract_revision` 和任务质量域：

```yaml
quality_domains:
  - functional
  - ui
  - accessibility
  - performance
  - security
```

只要求适用的质量域。每个用户可见的纵向切片必须包含 `ui` 和 `accessibility`，除非记录具体的不适用原因。

能力适用性由已批准契约在项目级拥有。任务选择自己必须证明的适用质量域，但不能降低项目必需能力。

### 10.4 `loop-state.md`

增加：

```yaml
delivery_mode: guided | autonomous
autonomy_scope: unconfirmed | confirmed_plan
stop_reason: none | verification_failed | needs_user_action | needs_decision | repair_exhausted | environment_blocked
resume_checkpoint: none | specification | initialization | task:<TASK-ID> | integration | delivery
active_run_id: null | RUN-ID
state_revision: 1
pending_transition: null | TRANSITION-ID
```

`loop-state.md` 拥有运行模式和停止原因，但不重复保存确认状态。现有阶段、任务、执行模式、Agent 能力、Checker、Worktree 和交接状态继续保持权威。

增加宿主能力记录，覆盖子代理、空闲槽位、浏览器、Git、Worktree、Docker、网络和会话持久性。每项能力记录 `available`、`unavailable` 或 `unknown`，以及证据或检查方法。运行时降级必须遵循明确规则，不能静默削弱已批准门禁。

### 10.5 `validation-log.md`

保留任务 acceptance 和 integration 记录，增加项目级证据记录：

```text
PROJECT / functional
PROJECT / ui
PROJECT / accessibility
PROJECT / performance
PROJECT / security
PROJECT / delivery-smoke
```

UI 证据包括：

- 截图路径；
- 视口；
- 页面和状态；
- 结果；
- 发现项规则 ID 和严重级别；
- 修复记录；
- 复验结果。

每条证据记录还包括：

- evidence record ID、run ID、attempt 和时间；
- 已批准契约 revision，以及 Git commit 或 `direct_apply` 工作区 fingerprint；
- 命令或方法、工作目录、退出码和工具版本；
- artifact manifest 路径和 SHA-256；
- 脱敏状态；
- 后续修复替换旧尝试时的 superseded record ID。

证据选择使用当前契约 revision 和实现 fingerprint 下，最新、有效且未被替换的尝试。旧契约、旧 commit、旧 Worktree 或失败尝试的记录无效。

Git 项目的实现 fingerprint 是已验证 commit hash 加 dirty-worktree 状态。对于 `direct_apply` 或非 Git 工作，实现 fingerprint 是允许路径中项目相对文件名及 SHA-256 的确定性 manifest。生成的 artifact 目录和明确排除的易变文件不参与该 fingerprint。

### 10.6 `delivery-report.md`

增加覆盖所有适用质量域的最终矩阵：

| Requirement | Implementation | Functional | UI | Accessibility | Performance | Security | Delivery Smoke | Status |
|---|---|---|---|---|---|---|---|---|

### 10.7 证据目录

将大体积生成产物存放在 Markdown 状态文件之外：

```text
.webbuilder-artifacts/
`-- <run-id>/
    `-- <task-id-or-project>/
        `-- <attempt>/
            |-- manifest.json
            |-- command-output.txt
            |-- screenshots/
            `-- reports/
```

状态文件只保存项目相对的稳定路径、摘要和结论，不嵌入完整原始输出。Worker 可以在各自 Worktree 写入本次尝试的本地产物。在删除 Worktree 前，Orchestrator 必须把已接受证据复制到主工作区规范产物目录并验证 hash。

原始证据默认由 Git 忽略，除非项目规则要求提交长期保存的证据。`validation-log.md` 和 `delivery-report.md` 必须始终保留命令、结论、稳定规则 ID、hash，以及用于审计的产物路径或外部引用。

证据捕获必须脱敏凭据、cookie、authorization header、秘密环境变量、真实用户数据和不必要的本地绝对路径。截图和浏览器 trace 默认使用 seed 或合成数据。批准契约记录产物保留策略、大小限制，以及证据是随交付提供、仅本地保留，还是替换为外部持久引用。

### 10.8 状态转换与不变量

State Kernel 实现并测试以下转换：

```text
draft contract -> pending confirmation -> approved contract
approved contract -> ready design and plan -> active execution
active execution -> declared stop -> resumable checkpoint -> active execution
active execution -> task acceptance -> serial integration -> next task
active execution -> final validation -> delivered
material contract change -> approval invalidated -> pending confirmation
```

跨文件不变量：

- 执行要求 `approved_contract_revision == contract_revision`，且 approval digest 匹配；
- ready 的设计和计划必须引用该已批准契约 revision；
- 证据必须引用已批准契约 revision 和当前实现 fingerprint；
- 存在 pending transition 时，必须先由 State Kernel 完成或回滚，才能继续工作；
- `status: delivered` 要求不存在 pending transition、未解决 stop reason，并且所有适用证据完整；
- 恢复时不会重复有效的已完成任务，除非契约 revision、依赖、实现 fingerprint 或证据已过期；
- 手工修改成功状态不能绕过失败的转换或门禁。

## 11. 阶段与门禁行为

### 11.1 规格门禁

确认前检查：

- 每项需求都有验收信号；
- 页面、数据、API 和权限覆盖已声明流程；
- 各项决定不存在矛盾；
- 错误状态和非目标明确；
- 所选技术可以满足确认范围；
- 已定义验证命令或场景。
- 每项能力都已标记为 `required`，或具有合理的 `not_applicable` 决定；
- 契约 revision 和 approval digest 输入是确定性的。

### 11.2 宿主能力门禁

自主执行前：

- 检查并记录子代理、浏览器、Git、Worktree、Docker、网络和会话持久性能力；
- 对照已批准契约和验证策略检查必需能力；
- 只有相关能力可选且保持等价门禁时，才允许执行模式降级；
- 必需能力不可用时，以 `environment_blocked` 停止；
- 宿主未实际执行时，不得声称浏览器、容器、部署或独立审查结果。

### 11.3 初始化门禁

业务开发前，只运行已批准能力矩阵要求的检查：

- 依赖可以安装；
- 需要持久化数据时，数据库可以启动；
- 适用时，迁移或确定性数据初始化可以运行；
- 开发服务器可以启动；
- 类型检查和构建可以执行；
- 测试框架可以执行；
- 需要容器交付时，Docker 配置在语法和运行上有效；
- 在适用时通过健康检查和初始认证冒烟检查。

### 11.4 任务门禁

每个纵向切片必须具备：

- 需求 ID；
- 有边界的实现范围；
- 行为验证；
- 适用的 UI 状态覆盖；
- Developer 提交证据；
- 独立检查；
- 集成策略；
- 主工作区复验。
- 与当前契约 revision 和实现 fingerprint 匹配的 evidence manifest。

普通委派任务允许一个 fresh 独立 Checker 同时执行 Tester 和 Reviewer 职责。对于 `checker_strategy: independent_checker`，验收检查器要求 Developer 身份与 Checker 不同，但允许 Tester 和 Reviewer 身份相同。对于 `checker_strategy: separate_tester_reviewer`，Developer、Tester 和 Reviewer 身份必须全部不同。`single_session` 仅用于符合条件的低风险任务，不能表示为独立审查。

高风险和关键任务继续要求 Developer、Tester 和 Reviewer 三个身份不同。

### 11.5 UI 与浏览器门禁

任务执行期间，对受影响的用户可见流程：

- 运行相关 Playwright 场景；
- 只渲染受影响的页面和状态；
- 捕获足以验证变更布局的视口；
- 记录控制台、网络、溢出和交互错误；
- 在任务预算内修复并重跑。

任务门禁只记录由变更影响的流程、页面、状态和代表性 viewport，不运行所有页面、状态与 viewport 的笛卡尔积。

最终集成验证执行完整支持矩阵：

- 基准视口：390、768 和 1440 CSS 像素；
- 主要页面和流程；
- 适用的 loading、empty、error、disabled、validation、success 和 permission 状态；
- 键盘导航和可见焦点；
- 自动无障碍检查；
- 在稳定、接近生产的环境中执行技术配置定义的性能检查；
- 控制台和失败请求检查。

没有真实渲染证据和有效 artifact manifest，不得声明视觉验证通过。浏览器工作量用受影响流程、状态和 viewport 表达，不使用缺乏依据的固定耗时或 API 调用次数。

### 11.6 最终交付门禁

必须证明：

- 文档中的标准命令或 Docker 命令可以启动系统；
- 可以从干净状态执行迁移和种子数据；
- 在适用时，认证、权限和核心业务流程通过端到端测试；
- 构建、类型检查、单元测试和集成测试通过；
- 最终 UI 证据矩阵完整；
- 没有阻断级无障碍、安全、性能或运行时问题；
- 每项确认需求都映射到实现和证据；
- 运行说明、风险和未完成项明确。
- 每个 evidence manifest 都存在，通过 hash 和脱敏检查，并匹配已批准契约 revision 和交付实现 fingerprint；
- 每个合理的 `not_applicable` 决定仍与实际交付产品一致；
- 不存在 pending state transition 或未解决 stop reason。

## 12. UI 质量闭环

必须执行以下 UI 闭环：

```text
产品与 UX 分析
-> UI Design Lock
-> UI 实现
-> 确定性源码检查
-> Agent 设计审查
-> 真实截图矩阵
-> 无障碍和性能检查
-> 有限修复
-> 重新渲染和重新测试
```

审美发现与客观质量发现必须分开。高审美评分不能抵消无障碍、运行时或性能失败。

任务级 UI 检查只覆盖变更流程。最终检查覆盖所有主要批准流程、代表性移动端/平板/桌面布局、必需状态、无障碍和选定性能 profile。矩阵必须基于风险，不能膨胀为无限截图笛卡尔积。

每个发现项必须包含稳定 ID、严重级别、受影响页面或组件、证据路径、修复方式和复验状态。

实现时借鉴第三方机制，但未经许可证检查不得直接复制第三方文本或代码。主要参考包括：StyleSeed 的持久设计锁和截图循环、Impeccable 的路由操作和确定性发现注册表、Web Quality Skills 的客观无障碍和性能门禁。

## 13. 修复与停止策略

保留相互独立的有限预算：

- 任务修复最多 3 次；
- 集成修复最多 5 次；
- 同一错误指纹在同一修复范围内出现 3 次后停止。

每次修复必须：

1. 引用失败证据；
2. 确定一个主要原因；
3. 只修改解决该原因所需的内容；
4. 重跑失败验证；
5. 更新验证记录；
6. 只有门禁通过后才继续。

`task_repair_attempt` 和 `integration_repair_attempt` 使用不同计数器、失败 fingerprint 和 recovery point。任务级成功不会重置未解决的集成失败。

现有任务和工作流状态保持不变。自主执行停止时，由 `loop-state.md` 记录 `stop_reason` 和 `resume_checkpoint`：

| Stop reason 或现有任务状态 | 含义 |
|---|---|
| `needs_repair` | 现有任务状态：存在预算内自动修复方案。 |
| `verification_failed` | 验证证据失败，需要诊断。 |
| `needs_user_action` | 需要凭据、付费资源或用户拥有的外部操作。 |
| `needs_decision` | 必须改变确认范围或重要架构决定。 |
| `repair_exhausted` | 已耗尽声明的修复预算。 |
| `environment_blocked` | 所需本地或外部环境不可用。 |

当终止原因无法安全解除时，现有工作流状态变为 `blocked`；只有需求和证据全部闭环后才变为 `delivered`。

普通编码错误、测试失败、UI 缺陷和低风险实现选择，在自动修复前不询问用户。

### 13.1 检查点与恢复协议

每次自主停止时：

1. 完成或回滚所有 pending State Kernel transition；
2. 记录 active run、当前任务、attempt 计数、停止证据和恢复检查点；
3. Worktree 或未集成分支包含诊断或可恢复工作时予以保留；
4. 保持已完成和已接受任务不变；
5. 清理 Worktree 前，把已接受证据复制到规范产物目录；
6. 只提供安全恢复选项：解除阻塞后继续、切换到 guided，或在明确批准后放弃/重启。

恢复时先读取状态和证据，再执行操作。除非 staleness 规则使任务失效，否则不重复已完成任务。数据库或外部写入恢复遵循任务已批准的 rollback 或 forward-fix 方案；WebBuilder 不会盲目逆转不可逆迁移。

### 13.2 授权边界

Solution Contract 批准只授权确认范围内、可逆的本地实现工作。它不替代宿主工具权限，也不授权凭据、付费服务、生产部署、破坏性外部写入、不可逆迁移、高风险安装脚本、秘密传输，或对范围、数据、权限和公共接口的实质性改变。

关键操作如果在确认时已知，契约可以记录预期方案，但真正执行仍需宿主和 critical 任务契约要求的明确批准证据。证据收集遵循第 10.7 节的脱敏与保留规则。

## 14. WebBuilder 自身测试策略

### 14.1 确定性状态测试

提交测试套件，并在启用自主模式前通过 CI 运行。先为 schema 1.3 增加 characterization tests，再在实现前为每项 1.4 行为编写失败测试：

- 自主模式草案状态；
- 一次确认后的批准转换；
- approval digest 和契约 revision 失效；
- 确认前拒绝执行；
- 引导模式兼容；
- 从 1.3 到 1.4 的幂等无损迁移；
- 多文件状态写入中断及确定性恢复；
- 恢复时不重复有效的已完成任务；
- 质量域验证；
- 能力适用性和无效 `not_applicable` 决定；
- 项目级证据记录；
- evidence artifact 存在性、hash、revision、实现 fingerprint、脱敏、supersession 和篡改检测；
- UI 证据完整性；
- 缺少必需证据时拒绝交付；
- 按策略验证独立 Checker 身份；
- 分离任务和集成修复预算。

### 14.2 Skill 行为评测

使用代表性需求评测：

- 常见 SaaS 或管理系统；
- 内容密集型业务应用；
- 数据密集型运营应用；
- 纯 API 服务；
- 地理空间或标注等特殊需求。

验证 WebBuilder 是否：

- 生成可用的 Solution Contract；
- 在自主模式中只要求一次正常确认；
- 对用户可见系统始终强制 UI；
- 不强制加载无关特殊领域知识；
- 生成有边界的纵向任务；
- 记录可执行验证；
- 只因明确停止条件而停止；
- 生成完整交付证据。
- 宿主能力不可用时安全降级；
- 拒绝 stale、手写、缺失或被篡改的证据；
- 从声明的检查点恢复且不重复已完成工作。

### 14.3 端到端示例

维护一个从初始化运行到交付的示例项目，必须覆盖：

- 自主确认；
- 至少一个完整纵向业务切片；
- 身份认证，或明确记录不需要认证的原因；
- 数据库迁移和种子数据；
- 响应式 UI 状态；
- 端到端测试；
- 证据采集；
- 最终交付报告。
- 一次声明的停止和成功恢复；
- 至少一个合理的 `not_applicable` 能力；
- 证据捕获、篡改拒绝和规范产物保留。

首个维护示例只使用一个经过验证的黄金技术 profile，并保留 existing/custom-stack escape hatch。只有其他 profile 具备同等端到端兼容性和证据覆盖后才可以加入。Profile 记录兼容版本范围、最近验证日期、支持宿主、选择标准、升级和废弃策略，而不是在本设计中永久固定短期框架版本示例。

## 15. 推进阶段

在阶段 4 的退出标准通过前，自主执行始终由 opt-in feature flag 控制。

### 阶段 0：发布基础

- 提交现有和新增测试，不再忽略 tests 目录。
- 为支持的 Python 和操作系统环境增加 CI。
- 让文档中的验证命令具备 UTF-8 安全性。
- 记录 schema 1.3 characterization baseline。

### 阶段 1：State Kernel 与兼容性

- 增加 schema 1.4、转换表、revision 所有权、journaled recovery 和幂等迁移。
- 修正按策略验证的独立 Checker 身份语义。
- 分离任务和集成修复状态。
- 保留 guided，并让迁移项目默认使用 guided。

### 阶段 2：契约与能力适用性

- 增加 delivery mode、Solution Contract、approval digest、contract revision 和 discovery method。
- 增加能力适用性和通用质量底线。
- 实现批准失效和派生产物 staleness。
- 在自主模式生成契约，但继续禁用自主执行。

### 阶段 3：证据与宿主能力

- 增加 Evidence Kernel、manifest、脱敏、artifact hash、保留策略和规范 Worktree 证据交接。
- 增加宿主能力检查和明确降级/阻塞规则。
- 扩展任务、UI、无障碍、性能、安全、集成和交付门禁。

### 阶段 4：窄范围端到端自主闭环

- 支持一个经过验证的黄金技术 profile，以及 existing/custom-stack 路径。
- 维护一个从契约批准到停止/恢复再到交付的示例。
- 运行 Prompt、状态、证据篡改、宿主降级和端到端评测。
- 只有完整闭环通过后，才以明确 opt-in 方式启用自主模式。

### 阶段 5：受控扩展

- 只有具备同等端到端证据时才增加更多技术 profile。
- 只有通用流程稳定后才增加特殊领域参考。
- 验证无关参考不会被加载。
- 保持领域知识与核心状态机分离。

## 16. 风险与缓解措施

### 过度自动化选择了错误产品方向

缓解：统一确认包在实现前展示假设、排除项、架构、UI 方向和验收标准。

### 一次确认被误解为无限授权

缓解：批准范围明确排除凭据、付费资源、不可逆外部操作和未确认的生产变更。

### 宿主能力被误解为产品能力

缓解：执行前检查宿主能力并记录证据；只有保持等价门禁时才降级；需要不可用工具的完成声明必须阻止。

### Agent 编写证据导致虚假通过

缓解：确定性 evidence manifest 记录退出码、当前 revision 和实现 fingerprint、artifact hash、脱敏状态和最新尝试规则。交付拒绝缺失、stale、手写或被篡改的证据。

### 宿主中断导致状态矛盾

缓解：State Kernel 使用带 revision 的 journaled transition；恢复时先检查 pending transition，并在派发更多工作前完成或回滚。

### UI 验证耗时过长

缓解：任务门禁只渲染受影响页面和状态；最终集成验证才执行完整视口和状态矩阵。

### Lighthouse 或浏览器检查不稳定

缓解：所选技术配置记录性能预算；最终性能门禁在有文档说明、稳定且接近生产的环境中运行，保留原始证据并区分环境失败和产品失败。

### Skill 体积过大

缓解：主 `SKILL.md` 只负责路由和策略；详细通用与特殊指导放入渐进加载的 references。

### 特殊领域知识压过通用工作流

缓解：领域参考只贡献约束和检查。核心产品、UI、执行和交付职责始终保持强制。

### 状态 schema 变得脆弱

缓解：保留现有文件，在 State Kernel 中集中管理 schema 1.4 和转换不变量，提供幂等迁移和备份，并在改变执行行为前提交确定性测试。

## 17. 本设计的验收标准

基于本设计的实现必须满足：

1. 已提交的测试套件和 CI 保留 schema 1.3 characterization baseline。
2. 现有 guided 项目可以幂等迁移到 schema 1.4，不丢失内容，并默认保持 guided。
3. 自主模式可以从简短需求生成完整确认包、能力适用性矩阵和工作量包络。
4. 只有当前契约 revision 已批准、派生设计和计划引用它、必需宿主能力可用时才能执行。
5. 实质性契约变化会使批准和 stale 证据失效，但不会冻结普通内部实现决定。
6. 中断的状态转换和自主停止都能确定性恢复，且不会重复有效的已完成任务。
7. 用户可见项目没有真实 UI 证据和适用无障碍检查时不能交付。
8. 纯 API 等特殊形态可以合理记录 `not_applicable` 能力，但不能绕过通用安全、行为或交付底线。
9. 普通委派任务允许一个 fresh 独立 Checker 同时完成测试和审查；高风险和关键任务要求 Developer、Tester 和 Reviewer 三者分离。
10. 交付拒绝手写、缺失、stale、已被替换、revision 错误、实现错误、未脱敏或被篡改的证据。
11. 最终交付能够证明启动、适用数据初始化、核心业务流程、需求覆盖和所有适用质量域。
12. 缺少宿主能力时，必须明确降级、交给 guided 或阻塞，不能降低完成声明标准。
13. WebBuilder 继续作为可移植的最终产品 Skill，使用本地文件和小型确定性 Python 工具，不强制依赖后台运行时或外部 Agent 服务。
