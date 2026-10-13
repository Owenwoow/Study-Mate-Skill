# StudyMate · 通用 Agent Skill

把「自学一门科目」这件事交给 Agent：**定计划、讲知识、做项目、验收成果**。

> **原项目**：[Miaotofu01/Study-Mate](https://github.com/Miaotofu01/Study-Mate)（MIT，© Cattofu）。
> 本仓库是它的**蒸馏版**：去掉 DeepSeek Harness（DSH）宿主绑定，整理成一个标准的 Agent Skill（一个目录、一个 `SKILL.md`），Claude Code 等支持 Agent Skills 的宿主都能直接用。
> 上游的新改动会持续按语义移植过来，当前同步到上游 `63db27a`（v2.0.1 之后），记录见 [`UPSTREAM.md`](UPSTREAM.md)。

```
你说「我想学 Python 写爬虫」
  → 先盘问目的 / 程度 / 前置基础 / 配套项目 / 实操载体
  → 产出知识点路线图（DAG）+ 科目主页
  → 逐节点产出 HTML 课件（讲解 + 页内练习）+ 引导式实操（lab）
  → 实验课用可运行证据验收；进度落在文件里，下次会话直接接着学
```

## 它和「直接跟 AI 聊天学」的区别

| 常见做法 | 卡在哪 | StudyMate 的做法 |
|---|---|---|
| 直接跟 AI 聊天学 | 会话一长上下文就吃不下；聊完不留痕，下次从零开始 | 状态全部落在文件里；每次会话只带相关记忆、上下文短；课件是教科书式的讲解与配图 |
| 看视频课 / 网课 | 质量参差不齐；付费；跟不上前沿节奏 | 讲解方式定制化；按需检索最新的资料与标准；完全开源、完全本地 |

## 安装（Claude Code）

**依赖**：Python 3.9+ 与 `pyyaml`；可选 `jsonschema`（大纲 schema 校验，缺了降级为提示）、`node`（跑两套 DOM 测试）。

```bash
python -m pip install pyyaml jsonschema
```

Claude Code 从 `~/.claude/skills/`（所有项目可用）或 `<项目>/.claude/skills/`（只在这个项目可用）里找 skill，**一个目录一个 `SKILL.md`**。三种装法任选其一：

**① 直接克隆到用户级 skill 目录**（最简单）

```bash
git clone https://github.com/Owenwoow/Study-Mate-Skill.git ~/.claude/skills/study-mate-skill
```

**② 只给某个学习项目用**

```bash
git clone https://github.com/Owenwoow/Study-Mate-Skill.git <你的学习项目>/.claude/skills/study-mate-skill
```

**③ 仓库放在别处，用链接接进 skill 目录**（想单独维护、给多个项目共用时）

```bash
git clone https://github.com/Owenwoow/Study-Mate-Skill.git D:/Code/Study-Mate-Skill
```

```powershell
# Windows：目录联接（不需要管理员权限）
New-Item -ItemType Junction -Path "$HOME\.claude\skills\study-mate-skill" -Target "D:\Code\Study-Mate-Skill"
```

```bash
# macOS / Linux：符号链接
ln -s ~/Code/Study-Mate-Skill ~/.claude/skills/study-mate-skill
```

装好后**新开一个会话**（skill 列表在会话开始时加载），问一句「你有哪些可用的 skill」能看到 `study-mate-skill`，或直接说「我想学 X」，就说明识别到了。目录名不必和 skill 名完全一致（大小写、`_` 与 `-` 视为相同）。

其他宿主（如 WorkBuddy AI 的 `~/.workbuddy-ai/skills/`）同理：把整个目录放进它的 skill 目录即可。

## 配置学习工作区（可选）

学习数据（科目、课件、进度、记忆）放在**学习工作区**里，按下面的顺序定位：

1. 环境变量 `LEARN_WORKSPACE`
2. 本机配置 `studymate.config.yaml` 的 `workspace:`（相对路径按本仓库目录解析，也可写绝对路径）
3. 默认：本仓库下的 `workspace/`

`studymate.config.yaml` 是**本机配置、不入库**。想把学习数据放到别处（比如放进你自己的笔记仓库、跟着它一起备份），从示例复制一份再改：

```bash
cp studymate.config.example.yaml studymate.config.yaml
```

```yaml
workspace: D:/Learning/workspace
```

引擎与学习数据分开放，更新引擎（`git pull`）不会碰到你的学习记录。

## 用法

装好后在任意目录开会话，直接说：

| 你说 | 会发生什么 |
|---|---|
| 「我想学 X」 | 总控亲自盘问（目的、程度、前置基础、配套项目、实操载体），然后建课：资料清单 → 图片库 → 知识点路线图 → 第一课 |
| 「我不知道学什么，帮我选方向」 | 进入方向探索：一次问一个问题，通常 5 问、最多 8 问，给出候选方向，你确认后才建课 |
| 「继续学 X」 | 恢复上次的进度，报告学到哪、建议这次学什么 |
| 「这段没看懂」+ 贴原文 | 就地讲清那一段，必要时记一条误解，答完回到原处 |
| 「考考我」 | 按当前节点出一份练习 |
| 「学完了」 | 普通节点按页内自测与实操结果推进；实验课由出题角色按可运行证据验收 |

**课件在哪**：学习工作区的 `index.html` 是课程总览，从那里点进科目主页和每一节课件（静态 HTML，用浏览器直接打开，离线可用）。

**课件里有什么**：

- 教科书式讲解与配图（图片库里的现成图、脚本出的图、内联 SVG）；数学式用离线 KaTeX 排版
- 代码块语法高亮（PrismJS）+ 语言角标 + 一键复制；`::: code` 可以在代码框里加一句解释
- 页内练习四种题型：**客观题**（即时判）、**开放题**（展开参考答案与判分要点自评）、**预测验证**（先写下预测才能看实际结果）、**交付物**（要做出什么 + 用来验收的测试命令）
- 实操课附带 `lab/`：留白任务 + 断言 + 参考解，学生自己写、自己跑测试

**进度**：每个节点三档（未开始 / 学习中 / 已学完）；实验课是里程碑验收，通过时连同它验收的前置节点一起置为已学完。

想先看看页面长什么样（不用建真课程）：

```bash
python scripts/preview_templates.py --open   # 用假数据渲染到 .preview/
```

更完整的日常用法见 [`references/使用说明.md`](references/使用说明.md)，图解版见 [`docs/skill-tutorial.html`](docs/skill-tutorial.html)（下载后用浏览器打开）。

## 更新

```bash
git -C ~/.claude/skills/study-mate-skill pull   # 路径换成你的安装位置
```

更新后在学习项目里跑一次 `python <安装位置>/scripts/gen_home.py`，把新的共享前端资源铺进工作区。

## 包里有什么

| 路径 | 是什么 |
|---|---|
| `SKILL.md` | **唯一入口**：学习系统总控——开场、盘问、学习循环、角色派发、脚本清单、边界 |
| `references/roles/*.md` | 5 个角色规格：`resource-scout`（找资料）、`image-scout`（采图）、`curriculum-designer`（拟大纲）、`learning-coach`（写课件内容）、`practice-evaluator`（出题与实验课验收） |
| `references/protocols/*.md` | 6 份协议：`learning-discovery`（方向探索）、`lesson-design`（课件内核）、`layered-practice`（题目规范）、`evidence-check`（实验课验收）、`local-qa`（局部答疑）、`record-keeping`（状态读写） |
| `references/*.md` | 课件内容格式（渲染器的唯一输入规格）、工程约束、使用说明、设计方案、安装与迁移、Agent 交接协议 |
| `scripts/` | 渲染器、主页生成、四道校验（大纲 / 课件 / 图片库 / skill 文档）、角色交接门禁、批处理，以及 `tests/` 回归测试 |
| `schemas/` | 大纲、进度、误解记录、题目、科目、会话摘要、角色交接等 JSON Schema |
| `templates/` | 页面骨架（主页、科目页、课件壳）、工作区文件模板、前端资源（Sayo UI、主题、PrismJS、KaTeX） |
| `UPSTREAM.md` | 与原项目的同步状态：基线、本地定制清单、故意不跟的方向、同步记录 |
| `.claude/skills/study-mate-sync/` | 维护者用：把上游新改动移植过来的流程与合并工具（在本仓库目录开 Claude Code 会话，说「同步上游」即可） |

**核心口径**：模型**一个字 HTML 都不写**。讲解角色写内容文件（`.md`），出题角色写题库（`.quiz.json`），HTML 由渲染器一次产出；所有校验都是确定性脚本，带行号报错。

## 脚本

只依赖标准库 + `pyyaml`。用法 `python scripts/<名字> --help`。

```bash
python scripts/gen_home.py [<workspace>]                 # 生成根主页 + 全部科目主页（含链接自检）
python scripts/render_lesson.py <科目目录> <节点id>       # 内容文件 + 题库 → 课件 HTML（--check 只校验）
python scripts/check_lesson.py <页面> --subject <科目> --node <节点id>
python scripts/check_curriculum.py <curriculum.yaml>     # 同目录有 RESOURCES.md 时顺带报资源覆盖率
python scripts/check_pool.py <科目目录>                   # 图片库：命名、来源许可、体积、按文件头复算尺寸
python scripts/check_handoff.py <stage_dir> --role <角色> [--node <节点id>]
python scripts/check_skill.py                            # 校验本包文档的 frontmatter
python scripts/renumber_lessons.py <科目目录> [--dry-run] [--render]
```

## 测试

```bash
python scripts/check_skill.py
bash scripts/tests/run_tests.sh             # 19 套回归测试（自己造临时科目，不碰工作区）
bash scripts/tests/run_tests.sh --browser   # 再加 3 套真实 Chrome 测试（需要 google-chrome）
```

Windows 上若没有 `python3` 命令，先让 `python3` 指向 `python`，并设 `PYTHONUTF8=1`（否则子进程按 GBK 解码输出）。

## 与原项目的差异

原项目后来演进成 DSH 插件：TypeScript 引擎注册为宿主原生工具、课件在 DSH 内嵌阅读端里看。本仓库保持宿主无关：

| 方面 | 原项目（Study-Mate） | 本仓库 |
|---|---|---|
| 形态 | npm 插件包 `@yunmiao/studymate`，12 个子 skill + 学习模式预设 | 1 个 `SKILL.md` 入口 + `references/` 下 11 份参考规格 |
| 引擎 | TypeScript，注册为宿主原生工具（v1.1 起） | Python 脚本，Agent 用命令行调用 |
| 看课件 | DSH 内嵌阅读端；静态页只作导出 | 静态 HTML 课件就是主体验，浏览器直接打开 |
| 工作区 | 读 `~/.dsh/studymate-config.yaml` | `LEARN_WORKSPACE` → `studymate.config.yaml` → `<root>/workspace` |
| 角色派发 | DSH 的 `subagent` | 宿主有子代理就派出去；没有就由总控按角色规格自己串行做 |
| 本地增补 | — | PrismJS 代码高亮；在 Python 渲染器与 `quiz.js` 里实现了原项目只在 TS 阅读端做的部分（四种题型、`::: code`、三档进度映射、资源覆盖率、图片文件头复算） |

学习方法本身（盘问 → 路线图 → 课件 + 练习 → 实验课验收 → 状态落盘）与原项目一致；哪些改动跟了、哪些故意没跟、为什么，逐条记在 [`UPSTREAM.md`](UPSTREAM.md)。

## License

MIT，见 [LICENSE](LICENSE)（版权 Cattofu）。原项目：[Miaotofu01/Study-Mate](https://github.com/Miaotofu01/Study-Mate)。
