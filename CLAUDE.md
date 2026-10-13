# study-mate-skill（引擎开发仓库）

在本目录开的会话 = **改 skill 引擎**：SKILL.md、角色/协议规格、脚本、模板、前端资源（Sayo / Prism / 样式与交互），以及从上游同步（`.claude/skills/study-mate-sync/`）。

## 仓库与学习项目

- **本仓库**（`E:\Code\Study-Mate-Skill`，GitHub `Owenwoow/Study-Mate-Skill`）：只放引擎，**不放任何学习内容**
- **学习项目**：本机 `studymate.config.yaml`（不入库）的 `workspace:` 指向的那个项目——现在是 `E:\Code\AI_drive_learning` 的 `workspace/`。学习项目通过目录联接使用本仓库：它的 `.claude/skills/study-mate-skill` → 本仓库，`.claude/skills/study-mate-sync` → 本仓库的 `.claude/skills/study-mate-sync`
- 用户平时在学习项目的会话里改引擎也行（经联接改的就是本仓库的文件）；提交一律在本仓库做
- 这里的会话**不做学习**（不讲课、不出课件、不改进度）

## 改动规则

- 前端（页面样式、交互、组件）：先查成熟产品（VitePress、GitHub、Obsidian 等）的真实实现再照搬，优先现成库与官方插件，不自己设计；后端/脚本可按需求定制
- 改了 SKILL.md、角色或协议规格 → 跑 `python scripts/check_skill.py`
- 改了脚本、模板、`templates/assets/` 或本包文档 → 再跑回归测试 `bash scripts/tests/run_tests.sh`
  - 本机没有 `python3` 命令：先在 scratchpad 建一个指向 `python` 的 `python3` 包装脚本并放进 `PATH`，同时设 `PYTHONUTF8=1`（否则子进程按 GBK 解码输出，测试会误报）
- 新增/改名共享前端文件：拷贝清单只有一份——`scripts/lessonfile.py` 的 `SHARED_DIRS`/`SHARED_FILES`（`gen_home.py`、`preview_templates.py` 都照它拷）；再同步 `templates/assets/README.md` 与 `references/工程约束.md` 的说明
- 看效果：`python scripts/preview_templates.py` 生成到 `.preview/`（已忽略），不要拿真实工作区试

## 同步到学习工作区

引擎改完、要让现有课件用上时：

1. 跑 `python scripts/gen_home.py`（按本机配置把共享资源拷进学习工作区并刷新主页）；课件层资源（`style.css`/`quiz.js`/`lesson-toc.js`）改了还要拷进各科目 `assets/`；需要时对已有课件跑 `render_lesson.py` 重渲
2. 这些落在学习工作区里的变化属于**学习项目的仓库**：在那边单独提交，提交信息写「同步 skill 资源：<改了什么>」
3. 本仓库的提交与学习项目的提交**绝不合并成一次**

## Git（本仓库）

- 直接在 `main` 上提交；每个独立小改动提交一次；提交前 `git status` + `git diff`，只 `git add` 相关文件
- 提交信息中文，一行说清做了什么，必要时空一行写原因，末尾带 Claude 署名行
- 不提交：`__pycache__/`、`.preview/`、`workspace/`（本包默认工作区）、`studymate.config.yaml`（本机配置；示例见 `studymate.config.example.yaml`）
- 禁止：`git push --force`、`git reset --hard`、`git clean -f`、`--amend`/`rebase` 改写已有提交、`--no-verify`
- 远程是 GitHub `origin`（公开仓库）：提交后 `git push` 保持同步；**绝不 force**，推送前确认没有本机配置、个人数据混进来
