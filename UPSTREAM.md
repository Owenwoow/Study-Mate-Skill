# 上游同步状态

本包从 [Miaotofu01/Study-Mate](https://github.com/Miaotofu01/Study-Mate) 蒸馏而来（去宿主化的通用 skill）。
同步流程见主仓库 `.claude/skills/study-mate-sync/SKILL.md`；本文件是它的状态：开工先读，收工必更新。

## 基线

- 上游仓库：https://github.com/Miaotofu01/Study-Mate（分支 `main`）
- **基线提交**：`f8a6204`（v0.3.0，2026-09-30）
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
| 示例科目（线性代数、计算机网络）整套重跑 | 本地 examples 是删减过的示意，只同步共享层副本 | 2026-10-12 |

（后续批次要核实的：ADR-0002 引擎改用 TypeScript、ADR-0003 阅读端只嵌 DSH、ADR-0005 静态页面降为导出——本地仍是 Python 脚本 + 静态 HTML 课件。）

## 同步记录

| 日期 | 上游区间 | 采纳 | 跳过 / 不跟 | 未完成 |
|---|---|---|---|---|
| 2026-10-12 | —（建立基线 `3d2a31f`） | — | — | — |
| 2026-10-12 | `3d2a31f..v0.3.0`（51 提交） | 检查项 10 本地引用可达；图注编号交渲染器；主页未生成不拦课件；Py3.12+ 非法转义；围栏语言白名单；KaTeX 公式排版（课件 + 题库）；学习方向探索协议；讲解先读来源原文、讲法以来源为准、教科书语体兜底；去掉强制中英对照；配图不指定画法；本地教材 → `reference/`、在线来源 → `sources/`；角色草稿 `/tmp` → `.stage/`；等子代理不轮询；脚本重构（curriculum/lessonfile/lessonfmt/statuses/pagetpl）+ 共享清单单源；术语表模板「待掌握/已掌握」；`build_examples.py`；新增 7 套测试 | 见「故意不跟的方向」 | 3 套浏览器测试本机没有 google-chrome，未跑 |
