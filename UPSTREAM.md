# 上游同步状态

本包从 [Miaotofu01/Study-Mate](https://github.com/Miaotofu01/Study-Mate) 蒸馏而来（去宿主化的通用 skill）。
同步流程见主仓库 `.claude/skills/study-mate-sync/SKILL.md`；本文件是它的状态：开工先读，收工必更新。

## 基线

- 上游仓库：https://github.com/Miaotofu01/Study-Mate（分支 `main`）
- **基线提交**：`3d2a31f`（2026-09-24「chore(示例): 生成示例工作区的页面与共享层」，介于 v0.2.0 与 v0.3.0 之间）
- 本地安装提交：`20352a2`（2026-09-25）

> 基线怎么来的：本地包没记录蒸馏版本，2026-10-12 用 `scripts/`、`schemas/`、`templates/lesson.html` 逐个比对上游 first-parent 历史，
> `0e343ce`…`3d2a31f` 这一段与本地最接近（剩余差异是蒸馏改写），下一个上游提交 `29aeabb`/`629ad38` 起本地就没有了。
> 设计方案仍是 v1.3、没有 KaTeX 和 learning-discovery，也印证了这一点。

## 本地定制清单（同步时保留，冲突先问用户）

| 定制 | 涉及文件 | 来源提交 |
|---|---|---|
| 工作区指向主仓库根目录 `workspace/` | `studymate.config.yaml` | `20352a2` |
| 课件代码块用 PrismJS 上色 + VitePress 式语言角标、图标复制按钮 | `templates/lesson.html`、`templates/assets/prism/`、`templates/assets/learn-theme.{css,js}`、`templates/assets/README.md`、`scripts/gen_home.py`、`scripts/preview_templates.py`、`references/工程约束.md` | `c16c57a` |
| 引擎开发会话的 CLAUDE.md 与权限配置 | `CLAUDE.md`、`.claude/settings.json`、`.gitignore` | `048d86a` |
| 同步状态文件 | `UPSTREAM.md` | — |
| 去宿主化：不依赖 DSH/Cordis，单个 skill、角色/协议放 `references/` | 全包 | 蒸馏时 |

前端改动原则（来自用户）：照搬成熟产品（VitePress、GitHub 等）的实现、用现成库，不自己设计。

## 故意不跟的方向

上游做了、本地决定不跟的事。写在这里的，以后同步直接跳过，不再重复讨论。

（首次同步时按上游 ADR 核实并填写。初判可能涉及：ADR-0002 引擎改用 TypeScript、ADR-0003 阅读端只嵌 DSH、ADR-0005 静态页面降为导出——本地仍是 Python 脚本 + 静态 HTML 课件。）

## 同步记录

| 日期 | 上游区间 | 采纳 | 跳过 / 不跟 | 未完成 |
|---|---|---|---|---|
| 2026-10-12 | —（建立基线 `3d2a31f`） | — | — | 上游已到 v2.0.1（`63db27a`），尚未同步 |
