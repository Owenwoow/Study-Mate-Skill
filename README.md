# StudyMate · 通用 Agent Skill

把「自学一门科目」这件事交给 Agent：**定计划、讲知识、做项目、验收成果**。

这是从 [Study-Mate](https://github.com/Miaotofu01/Study-Mate)（DSH 学习模式预设）整理出来的**通用技能包**——不再绑定任何特定 Agent 框架，任何支持 Agent Skills 约定的宿主都能用。

```
你说「我想学 C++ 打竞赛」
  → 先盘问目的 / 程度 / 前置基础 / 配套项目 / 实操载体
  → 产出知识点路线图（DAG）+ 科目主页
  → 逐节点产出 HTML 课件（讲解 + 检索练习）+ 引导式实操（lab）
  → 用可运行证据验收，进度落在文件里、下次会话直接继承
```

## 它和「直接跟 AI 聊天学」的区别

| 常见做法 | 卡在哪 | StudyMate 的做法 |
|---|---|---|
| 直接跟 AI 聊天学 | 会话一长上下文就吃不下；聊完不留痕，下次从零开始 | 状态全部落在文件里；每次会话只带相关记忆、上下文短；课件是教科书式的讲解与配图 |
| 看视频课 / 网课 | 质量参差不齐；付费；跟不上前沿节奏 | 讲解方式定制化；按需检索最新的资料与标准；完全开源、完全本地 |

## 安装

**依赖**：Python 3.9+、`pyyaml`。可选：`jsonschema`（大纲 schema 校验，缺了降级为 WARN）、`bash`（跑回归测试）、`node`（跑两套 JS DOM 测试）。

```bash
python3 -m pip install pyyaml jsonschema
```

**装法**：把**整个目录**（本目录，含 `scripts/`、`templates/`、`schemas/`、`references/`）复制到宿主的技能目录：

| 宿主 | 技能目录（用户级） |
|---|---|
| WorkBuddy AI | `~/.workbuddy-ai/skills/`（项目级：`<项目>/.workbuddy-ai/skills/`） |
| Claude Code | `~/.claude/skills/`（项目级：`<项目>/.claude/skills/`） |
| 其他宿主 | 按它自己的约定——只要是「一个目录一个 `SKILL.md`」的扫描方式即可 |

```bash
# 例：装到 WorkBuddy AI 的用户级技能目录
cp -r Study-Mate-Skill ~/.workbuddy-ai/skills/
```

装好后目录长这样（`name` 与目录名不一致时改一下 `SKILL.md` 的 frontmatter）：

```text
~/.workbuddy-ai/skills/Study-Mate-Skill/
├── SKILL.md               # 唯一入口（总控）
├── studymate.config.yaml  # 工作区定位
├── README.md
├── references/            # 角色与协议规格 + 约束文档
├── schemas/  templates/  scripts/
└── workspace/             # 你的学习数据（默认位置）
```

细节与迁移见 [`references/安装与迁移.md`](references/安装与迁移.md)。

## 快速开始

装好后，在任意目录开会话：

> 我想学「线性代数」，目标是能看懂机器学习论文里的矩阵推导。

总控会先解析工作区、读共享记忆，然后盘问清楚再建课程。后续每次会话开场自动恢复进度。

**第一次生成课程后**，课程总览页在工作区 `<LEARN_WORKSPACE>/index.html`——那是未来所有课件的入口。

想先看看长什么样（不用建真课程）：

```bash
python3 scripts/preview_templates.py --open   # 用假数据渲染到 .preview/，只看样式与交互
```

## 工作区在哪

三级定位，前者优先：

1. 环境变量 `LEARN_WORKSPACE`；
2. `studymate.config.yaml` 里的 `workspace:`（可写相对本包的路径）；
3. 默认 `<root>/workspace`。

想换位置（比如放到 `D:\study`）：改 `studymate.config.yaml`，或每次开会话前 `export LEARN_WORKSPACE=/path/to/study`。学习数据全在工作区里，**换机器把整个包（含工作区）拷走即可**。

## 包里有什么

| 路径 | 是什么 |
|---|---|
| `SKILL.md` | **唯一入口**：学习系统总控——开场、盘问、学习循环、角色派发、脚本清单、边界 |
| `references/roles/*.md` | 5 个角色规格：`resource-scout`（找资料）、`image-scout`（采图）、`curriculum-designer`（拟大纲）、`learning-coach`（写课件内容）、`practice-evaluator`（出题与实验课验收） |
| `references/protocols/*.md` | 6 份协议：`learning-discovery`（可选方向探索）、`lesson-design`（课件内核）、`layered-practice`（题目规范）、`evidence-check`（实验课验收）、`local-qa`（局部答疑）、`record-keeping`（状态读写） |
| `references/Agent交接协议.md` | 角色暂存交接（`handoff.json`）的唯一口径 |
| `references/课件内容格式.md` | 内容文件与题目位置的语法——**渲染器的唯一输入规格** |
| `references/工程约束.md` | 目录约定、占位符契约、前端技术选型 |
| `references/使用说明.md` | 面向学生的日常用法 |
| `references/设计方案.md` | 产品视角的设计意图 |
| `scripts/` | 渲染器 + 4 道校验 + 主页生成 + 批处理（见下） |
| `schemas/` | 5 份 JSON Schema：大纲 / 进度 / 评估 / 会话摘要 / 科目 |
| `templates/` | 页面骨架（主页、科目页、课件壳）+ 工作区文件模板 + 前端资源源（Sayo UI + 主题层） |

**规则归属**：一处定义、别处只给指针。课件内核看 `lesson-design`，题目看 `layered-practice`，配图规范在 `learning-coach` 的「配图」，状态读写看 `record-keeping`。

## 脚本

只依赖标准库 + `pyyaml`，全部是确定性的、带行号报错。用法 `python3 scripts/<名字> --help`。

```bash
python3 scripts/gen_home.py [<workspace>]                # 生成根主页 + 全部科目主页（含链接自检）
python3 scripts/render_lesson.py <科目目录> <节点id>      # 内容文件 + 题库 → 课件 HTML（--check 只校验）
python3 scripts/check_lesson.py <页面> --subject <科目> --node <节点id>
python3 scripts/check_curriculum.py <curriculum.yaml> ...
python3 scripts/check_pool.py <科目目录>
python3 scripts/check_skill.py                          # 校验本包文档的 frontmatter
python3 scripts/preview_templates.py [--open]
python3 scripts/apply_empty_reasons.py <科目目录> <节点id> <tsv>
python3 scripts/renumber_lessons.py <科目目录> [--dry-run] [--render]
```

**退出码**：`check_lesson.py` / `check_curriculum.py` / `check_pool.py` 有阻断项即 1；`gen_home.py` 占位符缺失或产物断链即 1；`render_lesson.py` 有问题即 1、用法错误即 2。

**核心口径**：模型**一个字 HTML 都不写**。讲解角色写内容文件（`.md`），出题角色写题库（`.quiz.json`），HTML 由渲染器一次产出。内容文件里出现块级 HTML 标签会被渲染器拦下。

## 验证

```bash
# ① 文档 frontmatter
python3 scripts/check_skill.py

# ② 拿一份真实工作区跑一遍引擎（复制一份，别改原数据）
cp -r <你的学习工作区> /tmp/sm-check && python3 scripts/gen_home.py /tmp/sm-check
python3 scripts/check_curriculum.py /tmp/sm-check/.learning/subjects/*/curriculum.yaml
python3 scripts/check_pool.py /tmp/sm-check/.learning/subjects/<slug>

# ③ 回归测试（自己造临时科目，不碰工作区）
bash scripts/tests/run_tests.sh
```

## 与 DSH 原版的差异

整理成通用技能包时做了这些改动（引擎逻辑与约束文档的实质内容保持不变）：

| 方面 | DSH 原版 | 本通用版 |
|---|---|---|
| 技能组织 | 11 个平级 `SKILL.md`（1 总控 + 5 角色 + 6 协议） | 1 个入口 `SKILL.md` + `references/` 下 11 份参考规格（不会被注册成独立技能） |
| 安装 | `install.sh` / `install.ps1` 装预设到 `~/.dsh/` + npm 包 `@yunmiao/studymate` | 把目录复制到宿主的技能目录；无安装脚本、无 npm 依赖 |
| 工作区定位 | 读 `~/.dsh/studymate-config.yaml` | 三级定位：`LEARN_WORKSPACE` 环境变量 → `studymate.config.yaml` → `<root>/workspace` |
| 角色派发 | 只用 DSH 的 `subagent` | **两条路**：宿主有子代理能力就派出去；没有就由总控按角色规格自己串行做（角色边界仍然有效） |
| 用户交互 / 呈现 | `ask_user_question` / `present` / `xdg-open` | 用宿主自带的提问与呈现能力；**至少必须在回复里给出绝对路径** |
| 文档位置 | `docs/` | `references/`（保留 `课件内容格式.md` 等文件名，测试与脚本的引用同步更新） |
| 已剔除 | 预设、npm 打包、发布流水线、DSH 专有的安装器测试 | — |

`scripts/check_skill.py` 重写为校验本包的文档 frontmatter（`name` + `description`）；`gen_home.py` 的工作区定位改为三级；其余脚本只做了路径引用同步。

## License

MIT（见 [LICENSE](LICENSE)，版权 Cattofu）。上游项目：[Miaotofu01/Study-Mate](https://github.com/Miaotofu01/Study-Mate)。
