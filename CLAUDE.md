# study-mate-skill（引擎开发仓库）

在本目录开的会话 = **改 skill 引擎**：SKILL.md、角色/协议规格、脚本、模板、前端资源（Sayo / Prism / 样式与交互）。
上级目录 `E:\Project\AI_drive_learning\CLAUDE.md` 也会被读到：它的语言、命令格式、git 禁令照样适用；
但其中「在本目录开会话只做学习」说的是主项目目录，**不适用于这里**——本文件与它冲突时以本文件为准。

## 两个仓库

- **本仓库**（`.claude/skills/study-mate-skill/`）：独立 git 仓库，只放引擎；主仓库的 `.gitignore` 忽略本目录
- **主仓库**（`E:\Project\AI_drive_learning`）：学习内容，`workspace/` 下的科目、课件、题库、lab、进度
- 这里的会话**不做学习**（不讲课、不出课件、不改进度）；要学习回主目录开会话

## 改动规则

- 前端（页面样式、交互、组件）：先查成熟产品（VitePress、GitHub、Obsidian 等）的真实实现再照搬，优先现成库与官方插件，不自己设计；后端/脚本可按需求定制
- 改了 SKILL.md、角色或协议规格 → 跑 `python scripts/check_skill.py`
- 改了脚本、模板、`templates/assets/` 或本包文档 → 再跑回归测试 `bash scripts/tests/run_tests.sh`
  - 本机没有 `python3` 命令：先在 scratchpad 建一个指向 `python` 的 `python3` 包装脚本并放进 `PATH`，同时设 `PYTHONUTF8=1`（否则子进程按 GBK 解码输出，测试会误报）
- 新增/改名共享前端文件：清单分散在三处，必须同时改——`templates/assets/README.md`、`scripts/preview_templates.py` 的 `shared_dirs/shared_files`、`scripts/gen_home.py` 的 `ensure_shared_assets`
- 看效果：`python scripts/preview_templates.py` 生成到 `.preview/`（已忽略），不要拿真实工作区试

## 同步到学习工作区

引擎改完、要让现有课件用上时：

1. 跑 `python scripts/gen_home.py`（把共享资源拷进工作区并刷新主页）；课件层资源（`style.css`/`quiz.js`/`lesson-toc.js`）改了还要拷进各科目 `assets/`；需要时对已有课件跑 `render_lesson.py` 重渲
2. 这些落在 `workspace/` 里的变化属于**主仓库**：在主仓库单独提交，提交信息写「同步 skill 资源：<改了什么>」
3. 本仓库的提交与主仓库的提交**绝不合并成一次**

## Git（本仓库）

- 直接在 `main` 上提交；每个独立小改动提交一次；提交前 `git status` + `git diff`，只 `git add` 相关文件
- 提交信息中文，一行说清做了什么，必要时空一行写原因，末尾带 Claude 署名行
- 不提交：`__pycache__/`、`.preview/`、`workspace/`（本包默认工作区，真实学习数据在主仓库）
- 禁止：`git push --force`、`git reset --hard`、`git clean -f`、`--amend`/`rebase` 改写已有提交、`--no-verify`
- 暂无远程仓库，不推送
