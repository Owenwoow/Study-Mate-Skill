# 上游同步状态

本包从 [Miaotofu01/Study-Mate](https://github.com/Miaotofu01/Study-Mate) 蒸馏而来（去宿主化的通用 skill）。
同步流程见主仓库 `.claude/skills/study-mate-sync/SKILL.md`；本文件是它的状态：开工先读，收工必更新。

## 基线

- 上游仓库：https://github.com/Miaotofu01/Study-Mate（分支 `main`）
- **基线提交**：`63db27a`（上游 main，v2.0.1 之后，2026-10-11）
- 上游删除 Python 引擎前的最后一版：`535e063`（2026-10-05）——之后上游已没有 Python 脚本/HTML 模板可合，只能移植提示词、规格与思路
- 蒸馏起点：`3d2a31f`（2026-09-24，介于 v0.2.0 与 v0.3.0 之间）
- 本地安装提交：`20352a2`（2026-09-25）

> 蒸馏起点怎么来的：本地包没记录蒸馏版本，2026-10-12 用 `scripts/`、`schemas/`、`templates/lesson.html` 逐个比对上游 first-parent 历史，
> `0e343ce`…`3d2a31f` 这一段与本地最接近（剩余差异是蒸馏改写），下一个上游提交 `29aeabb`/`629ad38` 起本地就没有了。
> 设计方案仍是 v1.3、没有 KaTeX 和 learning-discovery，也印证了这一点。

## 本地定制清单（同步时保留，冲突先问用户）

| 定制 | 涉及文件 | 来源提交 |
|---|---|---|
| 工作区指向主仓库根目录 `workspace/` | `studymate.config.yaml` | `20352a2` |
| 课件代码块用 PrismJS 上色 + VitePress 式语言角标、图标复制按钮（上游的自研正则高亮只作 Prism 未加载时的退路） | `templates/lesson.html`、`templates/assets/prism/`、`templates/assets/learn-theme.{css,js}`、`templates/assets/README.md`、`scripts/lessonfile.py` 的 `SHARED_DIRS`（含 `prism`）、`scripts/tests/fixtures.py` 的 `SHARED_STUBS`、`references/工程约束.md` | `c16c57a` |
| 工作区三级定位（`LEARN_WORKSPACE` → `studymate.config.yaml` → `<root>/workspace`）；上游改成读 DSH 配置，不跟 | `scripts/gen_home.py` 的 `learn_workspace()` 与 `main()` | 蒸馏时 |
| 测试入口用本地 `run_tests.sh` 逐套列出（上游改成 `npm test`）；结构闸门 `test_package.py` 是本地独有 | `scripts/tests/run_tests.sh`、`scripts/tests/test_package.py`、`scripts/tests/README.md` | 蒸馏时 |
| 示例科目是删减过的（没有课件），`build_examples.py` 额外给每个科目装课件层组件 | `examples/`、`scripts/build_examples.py` | 2026-10-12 |
| 检查项 10 的引用取值改成只认真标签上的 href/src（上游正则扫全文，会把转义后的示例代码当链接；上游 Python 版已删、不会再修） | `scripts/check_lesson.py` 的 `ref_values`、`scripts/tests/test_lesson_links.py` | 2026-10-12 |
| 示例科目 `examples/` 与 `build_examples.py` 已删（随上游 ADR-0009）；测试用 `fixtures.py` 临时现造 | — | 2026-10-12 |
| 三档进度的读侧映射与「完成度」：上游在 TS 端映射，本地在 `statuses.py`（`LEGACY_TIER_MAP`/`normalize_status`/`TIER_FILL`）；主页「掌握度」改成按三档折算的「完成度」 | `scripts/statuses.py`、`scripts/gen_home.py`、`templates/home-index.html`、`templates/subject-index.html` | 2026-10-12 |
| `check_curriculum.py` 对旧大纲（mastery、旧六档）只提示不阻断 | `scripts/check_curriculum.py`、`scripts/tests/test_curriculum.py` | 2026-10-12 |
| 预测验证 / 交付物两种新题型的页面实现（上游只在 TS 阅读端实现）；检查器与 `quiz.js` 共用一张字段表、按字段推断题型并拦混写 | `templates/assets/quiz.js`、`templates/assets/style.css`、`scripts/check_lesson.py`、`scripts/tests/{quiz_dom_test.js,test_quiz_code.py,test_templates.py}` | 2026-10-12 |
| 保留会话摘要（上游已退役：它有开场摘要工具，本地没有） | `SKILL.md`、`references/protocols/record-keeping.md`、`schemas/session-summary.schema.json` | 2026-10-12 |
| 题目层级保留 L1-L4 叫法（上游改名读懂/改对/查错/造出），语义照上游：深度看 `objective` 不看课型 | `references/protocols/layered-practice.md` 等 | 2026-10-12 |
| 误解记录 `source` 用「局部提问」代替上游的「问答面板」 | `schemas/misconceptions.schema.json`、`references/protocols/local-qa.md` | 2026-10-12 |
| `::: code` 框内解释槽的渲染实现（上游只在 TS 阅读端）：`build_code`/`render_code` + `.lesson-code` 样式 | `scripts/render_lesson.py`、`templates/assets/style.css`、`references/课件内容格式.md`、`scripts/tests/test_render_lesson.py` | 2026-10-13 |
| 资源清单「服务」标记的分工：上游让资料收集直接标节点 id，但那时大纲还没出来——本地改为课设报「资源 ↔ 节点对照」、总控落大纲后补标记 | `references/roles/{resource-scout,curriculum-designer}.md`、`SKILL.md`（新科目第 4b 步） | 2026-10-13 |
| 资源覆盖率提示与图片库文件头复算（上游在 TS 校验器里）：`check_curriculum.py` 读同目录 `RESOURCES.md`；`check_pool.py` 纯标准库读 png/jpeg/gif/webp 文件头 | `scripts/check_curriculum.py`、`scripts/check_pool.py`、`scripts/tests/{test_curriculum,test_pool}.py` | 2026-10-13 |
| 资料收集交稿前「自己核一遍链接」（上游是 `studymate_verify_sources` 工具） | `references/roles/resource-scout.md` | 2026-10-13 |
| 角色不再派子代理（Claude Code 的子代理不能再派）：resource-scout 自己转换本地教材 | `references/roles/resource-scout.md`、`SKILL.md` 派工边界 | 2026-10-12 |
| 引擎开发会话的 CLAUDE.md 与权限配置 | `CLAUDE.md`、`.claude/settings.json`、`.gitignore` | `048d86a` |
| 同步状态文件 | `UPSTREAM.md` | — |
| 去宿主化：不依赖 DSH/Cordis，单个 skill、角色/协议放 `references/` | 全包 | 蒸馏时 |

前端改动原则（来自用户）：照搬成熟产品（VitePress、GitHub 等）的实现、用现成库，不自己设计。

## 故意不跟的方向

上游做了、本地决定不跟的事。写在这里的，以后同步直接跳过，不再重复讨论。

| 上游做法 | 不跟的原因 | 定于 |
|---|---|---|
| DSH 沙箱的「会话目录暂存工作区 + 收尾问落点搬运 + `prefs.md` 记落点 + 提权」整套（5d537cf 等） | 为 DSH `workspace-write` 沙箱设计；本地工作区由配置定位、直接写。只采纳了其中「角色草稿放 `<subject_path>/.stage/`」 | 2026-10-12 |
| 工作区读 `~/.dsh/studymate-config.yaml` / `STUDYMATE_*` 环境变量 | 本地用三级定位（见定制清单） | 2026-10-12 |
| Codex/ChatGPT、Antigravity 插件，npm 安装器与发布、CI、`interaction_state.py` | 宿主/发布专属 | 2026-10-12 |
| 提示词改用「代称」+ `docs/文件归属.md` 索引 | 本地规格一直直接写真实文件名，单个 skill 用不着再加一层索引 | 2026-10-12 |
| 引擎脚本一律 `python3 -B`（v1.0） | 为 DSH 只读引擎目录准备；本地引擎目录可写、`__pycache__/` 已忽略 |  2026-10-12 |
| 派工值从总控的映射表搬进各角色规格「输入」节（bce408d） | 纯结构重构；本地保留总控里的值映射表 | 2026-10-12 |
| 提示词规则归属声明表 `rule-owners.json` + `test_skill_rules.py`、技能调用面 frontmatter（`disable-model-invocation` 等）与其测试、`check_skill.py` 的调用面检查、`工程约束 §四` 参数形态契约测试 | 针对上游 12 个 SKILL.md 的结构；本地是 1 个入口 + 参考规格，由 `test_package.py` 守 | 2026-10-12 |
| `docs/` 按用途分 `使用/规范/设计/adr/agents`、AGENTS.md、GLOSSARY.md、贡献契约、issue 模板 | 上游开源协作用；本地文档都在 `references/` | 2026-10-12 |
| ADR-0002 引擎改 TypeScript、DSH 原生工具（`studymate_*`）、ADR-0003 阅读端只嵌 DSH、ADR-0005 静态页降为导出、ADR-0010 阅读端写参考资料、ADR-0011 三栏、ADR-0012 答疑会话（问答面板）、ADR-0013 Web 运行时 | 本地是 Python 脚本 + 静态 HTML 课件，宿主无关 | 2026-10-12 |
| ADR-0007 作答数据 `attempts/` 与 `attempts.schema.json` | 前提是阅读端能写盘；本地静态页不写盘（预测只留在页面里） | 2026-10-12 |
| 会话摘要退役 | 见定制清单（本地保留） | 2026-10-12 |
| 上游 v1.1 的 TS 端测试（`test_core_*`/`test_host_*`/`test_client_*`/`test_tools_*`/`test_watch_*` 等）与浏览器测试框架 `harness.mjs`；DOM 测试改名 `.cjs` | TS 引擎/阅读端专属 | 2026-10-12 |
| v1.2+ 的 DSH 阅读端改动：路线图去掉连线（3fdaae7）、代码块/终端块换文档站骨架与行首三档着色、答疑会话的课件指针（e3db252）、原生工具注册面、核链接工具 `studymate_verify_sources` 与按节冻结的内容指纹 | 阅读端/TS 工具专属；本地只取了规格层（term 口径、::: code、服务标记、Gaps 子节） | 2026-10-13 |
| 安装器、npm 发布、无头宿主版本声明、README 架构图与英文版、编排纪律文档 | 宿主/发布/上游协作专属 | 2026-10-13 |
| 示例科目（线性代数、计算机网络）整套重跑 | 本地 examples 是删减过的示意，只同步共享层副本 | 2026-10-12 |


## 同步记录

| 日期 | 上游区间 | 采纳 | 跳过 / 不跟 | 未完成 |
|---|---|---|---|---|
| 2026-10-12 | —（建立基线 `3d2a31f`） | — | — | — |
| 2026-10-12 | `3d2a31f..v0.3.0`（51 提交） | 检查项 10 本地引用可达；图注编号交渲染器；主页未生成不拦课件；Py3.12+ 非法转义；围栏语言白名单；KaTeX 公式排版（课件 + 题库）；学习方向探索协议；讲解先读来源原文、讲法以来源为准、教科书语体兜底；去掉强制中英对照；配图不指定画法；本地教材 → `reference/`、在线来源 → `sources/`；角色草稿 `/tmp` → `.stage/`；等子代理不轮询；脚本重构（curriculum/lessonfile/lessonfmt/statuses/pagetpl）+ 共享清单单源；术语表模板「待掌握/已掌握」；`build_examples.py`；新增 7 套测试 | 见「故意不跟的方向」 | 3 套浏览器测试本机没有 google-chrome，未跑 |
| 2026-10-12 | `v0.3.0..v1.0.0`（20 提交） | 角色暂存交接门禁（`handoff.json` + `check_handoff.py` + `agent-handoff.schema.json` + `references/Agent交接协议.md`，三个 staged 角色交稿最后写 manifest、总控搬入前先验）；题目数据异常导致后续题组不显示（quiz.js）；使命新增 `## Out of scope`；image-scout 不用系统临时目录；脚本若干修复（大纲校验、渲染器、主页生成、附件渲染）；`test_templates` 补「使命四节」「共享记忆条目有家」；新增 `test_handoff.py` | 见「故意不跟的方向」（-B、派工值重构、规则归属/调用面测试、docs 重组；VitePress 阅读端提案留到 v1.1 一起评估） | 浏览器测试同上 |
| 2026-10-12 | `v1.0.0..v1.1.0`（249 提交；脚本到 `535e063`） | 用户决定：进度三档（未开始/学习中/已学完）+ 去掉掌握度、误解单一落点（`misconceptions.schema.json`）、评估记录退役、删阶段评估、引入预测验证/交付物题型（`question.schema.json` + 本地实现 quiz.js）、删 examples；另采纳：证据资格（延迟重测、四类不算证据、全部核心点、范围为空不通过）、课型不决定题深度、L2 先预测再验证、已引用的图不删、位次会挪、转不动的资料别硬造 | 见「故意不跟的方向」（TS 引擎与 DSH 阅读端整套、作答数据、会话摘要退役） | 浏览器测试同上；工作区里旧格式的 `curriculum.yaml`（32 个节点带 mastery）与 `progress.yaml`（mastery、misconceptions 数组）未改写，读侧兼容，下次写回时自然收敛 |
| 2026-10-13 | `v1.1.0..63db27a`（v1.2.0、v2.0.0、v2.0.1 与之后 10 个提交） | 课件语体不再跟着来源走（来源只定讲法与内容，语体归教材式行文）+ 「行文禁忌」改为带错误/正确/保留的「行文要求」；`term` 是终端/运行结果摘录的口径；`::: code` 框内解释槽（本地实现渲染）；资源清单：每条来源标服务节点、`## 易变内容的官方核对来源` 独立成节、`## Gaps` 拆两个子节、分节固定；资料收集的取回失败判据与抓取预算；大纲覆盖率提示（本地实现）；图片库按文件头复算格式与尺寸（本地实现） | 见「故意不跟的方向」（DSH 阅读端与 TS 工具、安装发布） | 浏览器测试同上；你现有 `RESOURCES.md` 的 46 条来源还没有「服务」标记（检查只提示），下次总控维护资源清单时补 |
