#!/usr/bin/env python3
"""生成 docs/skill-tutorial.html：StudyMate Skill 的工作流与架构教程。

- 流程图用下面的小工具按坐标生成 SVG（不依赖外部库）
- 技能包里的 MD / YAML 原文逐字嵌进页面（JSON），页内「原文抽屉」按原样逐行呈现
- 原文改了就重跑：python docs/build_tutorial.py
"""
from __future__ import annotations

import html
import json
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "skill-tutorial.html"

# ───────────────────────── 要嵌入的原文 ─────────────────────────
DOCS = [
    ("入口", "SKILL.md", "唯一入口：总控流程（宿主注册的就是它）"),
    ("入口", "README.md", "包说明、安装、与 DSH 原版的差异"),
    ("入口", "studymate.config.yaml", "工作区定位配置"),
    ("角色规格", "references/roles/resource-scout.md", "找资料"),
    ("角色规格", "references/roles/image-scout.md", "采图"),
    ("角色规格", "references/roles/curriculum-designer.md", "拟大纲与实验课"),
    ("角色规格", "references/roles/learning-coach.md", "写课件内容与配图"),
    ("角色规格", "references/roles/practice-evaluator.md", "出题与评估"),
    ("协议", "references/protocols/record-keeping.md", "状态读写（所有落盘口径）"),
    ("协议", "references/protocols/lesson-design.md", "课件内核"),
    ("协议", "references/protocols/layered-practice.md", "题目规范（四层四型）"),
    ("协议", "references/protocols/evidence-check.md", "证据核验"),
    ("协议", "references/protocols/local-qa.md", "局部答疑"),
    ("约束文档", "references/课件内容格式.md", "渲染器的唯一输入规格"),
    ("约束文档", "references/工程约束.md", "目录、占位符契约、前端选型"),
    ("约束文档", "references/使用说明.md", "面向学生的日常用法"),
    ("约束文档", "references/设计方案.md", "产品视角的设计意图"),
    ("约束文档", "references/安装与迁移.md", "安装、工作区与迁移"),
    ("工作区模板", "templates/MEMORY.md", "跨科目共享记忆模板"),
    ("工作区模板", "templates/MISSION.md", "科目使命模板"),
    ("工作区模板", "templates/GLOSSARY.md", "术语表模板"),
    ("工作区模板", "templates/RESOURCES.md", "资源清单模板"),
    ("工作区模板", "templates/subject.yaml", "科目元数据模板"),
    ("工作区模板", "templates/README.md", "模板目录说明"),
]


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def href(path: str) -> str:
    return "../" + quote(path)


def d(path: str, label: str | None = None, find: str | None = None) -> str:
    """正文里的文档链接：点击打开原文抽屉；href 指向本地文件（Ctrl+点击 / 无 JS 时直接打开）。"""
    label = label or path.rsplit("/", 1)[-1]
    f = f' data-find="{esc(find)}"' if find else ""
    return f'<a class="doc" href="{href(path)}" data-doc="{esc(path)}"{f}>{esc(label)}</a>'


# ───────────────────────── SVG 小工具 ─────────────────────────
def text_w(s: str, cjk: float = 12.6, asc: float = 7.0) -> float:
    return sum(cjk if ord(c) > 255 else asc for c in s)


class Fig:
    def __init__(self, key: str, w: int, h: int, title: str):
        self.key, self.w, self.h, self.title = key, w, h, title
        self.bg: list[str] = []
        self.edges: list[str] = []
        self.labels: list[str] = []
        self.nodes: list[str] = []
        self.B: dict[str, tuple[float, float, float, float]] = {}

    def lane(self, x, w, title, cls):
        self.bg.append(
            f'<rect class="lane {cls}" x="{x}" y="0" width="{w}" height="{self.h}" rx="12"/>'
            f'<text class="lane-t" x="{x + w / 2}" y="28" text-anchor="middle">{esc(title)}</text>'
        )

    def raw(self, s: str):
        self.bg.append(s)

    def box(self, id, x, y, w, h, lines, cls="", doc=None, find=None, shape="rect"):
        self.B[id] = (x, y, w, h)
        attrs = ""
        if doc:
            attrs = f' class="clk" data-doc="{esc(doc)}" tabindex="0" role="button"'
            if find:
                attrs += f' data-find="{esc(find)}"'
        g = [f"<g{attrs}>"]
        if shape == "diamond":
            cx, cy = x + w / 2, y + h / 2
            g.append(f'<polygon class="nd {cls}" points="{cx},{y} {x + w},{cy} {cx},{y + h} {x},{cy}"/>')
        else:
            g.append(f'<rect class="nd {cls}" x="{x}" y="{y}" width="{w}" height="{h}" rx="9"/>')
        lh = 17
        y0 = y + h / 2 - (len(lines) - 1) * lh / 2
        for i, line in enumerate(lines):
            c = "t"
            if line.startswith("*"):
                line, c = line[1:], "t tb"
            elif line.startswith("~"):
                line, c = line[1:], "t tm"
            g.append(
                f'<text class="{c}" x="{x + w / 2}" y="{y0 + i * lh:.1f}" text-anchor="middle" '
                f'dominant-baseline="central">{esc(line)}</text>'
            )
        if doc and shape != "diamond":
            g.append(f'<text class="t-doc" x="{x + w - 8}" y="{y + 11}" text-anchor="end">↗</text>')
        g.append("</g>")
        self.nodes.append("".join(g))

    def pt(self, id, side, off=0.0):
        x, y, w, h = self.B[id]
        return {
            "n": (x + w / 2 + off, y),
            "s": (x + w / 2 + off, y + h),
            "e": (x + w, y + h / 2 + off),
            "w": (x, y + h / 2 + off),
        }[side]

    def path(self, pts, label=None, cls="", both=False, lpos=None):
        d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        ms = f' marker-start="url(#ahs-{self.key})"' if both else ""
        self.edges.append(f'<path class="e {cls}" d="{d}" marker-end="url(#ah-{self.key})"{ms}/>')
        if label:
            if lpos is None:
                best, seg = -1.0, None
                for a, b in zip(pts, pts[1:]):
                    ln = abs(a[0] - b[0]) + abs(a[1] - b[1])
                    if ln > best:
                        best, seg = ln, (a, b)
                (ax, ay), (bx, by) = seg
                lpos = ((ax + bx) / 2, (ay + by) / 2)
            lx, ly = lpos
            tw = text_w(label, 12, 6.6) + 10
            self.labels.append(
                f'<rect class="elb" x="{lx - tw / 2:.1f}" y="{ly - 10:.1f}" width="{tw:.1f}" height="20" rx="4"/>'
                f'<text class="el {cls}" x="{lx:.1f}" y="{ly:.1f}" text-anchor="middle" dominant-baseline="central">{esc(label)}</text>'
            )

    def arrow(self, a, b, sa="s", sb="n", label=None, cls="", via=None, oa=0, ob=0, both=False, lpos=None):
        A, B = self.pt(a, sa, oa), self.pt(b, sb, ob)
        pts = [A]
        if via:
            pts += via
        else:
            va, vb = sa in "ns", sb in "ns"
            if va and vb and abs(A[0] - B[0]) > 0.5:
                my = (A[1] + B[1]) / 2
                pts += [(A[0], my), (B[0], my)]
            elif not va and not vb and abs(A[1] - B[1]) > 0.5:
                mx = (A[0] + B[0]) / 2
                pts += [(mx, A[1]), (mx, B[1])]
            elif va and not vb:
                pts.append((A[0], B[1]))
            elif not va and vb:
                pts.append((B[0], A[1]))
        pts.append(B)
        self.path(pts, label, cls, both, lpos)

    def svg(self) -> str:
        k = self.key
        defs = (
            f'<defs><marker id="ah-{k}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
            f'<path d="M0,0 L10,5 L0,10 z" class="ahp"/></marker>'
            f'<marker id="ahs-{k}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
            f'<path d="M0,0 L10,5 L0,10 z" class="ahp"/></marker></defs>'
        )
        body = "".join(self.bg + self.edges + self.nodes + self.labels)
        return (
            f'<svg class="fig" viewBox="0 0 {self.w} {self.h}" role="img" aria-label="{esc(self.title)}" '
            f'style="min-width:{int(self.w * 0.72)}px">{defs}{body}</svg>'
        )


# ───────────────────────── 图 1：Skill 调用总工作流（泳道） ─────────────────────────
def fig_invoke() -> str:
    f = Fig("f1", 1060, 1590, "图 1：Claude Code 调用 StudyMate 技能的总工作流")
    f.lane(0, 180, "学生（用户）", "u")
    f.lane(190, 400, "Claude 主会话 = 总控（SKILL.md）", "c")
    f.lane(600, 220, "子代理（Agent 工具）", "a")
    f.lane(830, 230, "文件系统 / 脚本", "f")
    UX, UW = 12, 156
    CX, CW = 270, 280
    AX, AW = 612, 196
    FX, FW = 842, 206
    SK = "SKILL.md"

    f.box("U1", UX, 56, UW, 58, ["“我想学线性代数”", "~或 /study-mate-skill"], "u")
    f.box("C1", CX, 56, CW, 58, ["*宿主匹配 description", "~→ 调用 Skill 工具加载技能"], "c", SK)
    f.box("F1", FX, 56, FW, 58, ["*SKILL.md 正文注入上下文", "~附带 Base directory = <root>"], "f", SK)
    f.arrow("U1", "C1", "e", "w")
    f.arrow("C1", "F1", "e", "w", "加载")

    f.box("C2", CX, 140, CW, 58, ["*① 定位 <root> 与工作区", "~读写一律用绝对路径，不用 cwd"], "c", SK, "## 一、开场")
    f.box("F2", FX, 137, FW, 64, ["env LEARN_WORKSPACE", "→ studymate.config.yaml", "→ <root>/workspace"], "f", "studymate.config.yaml")
    f.arrow("C1", "C2")
    f.arrow("C2", "F2", "e", "w", "三级定位", "dash")

    f.box("C3", CX, 224, CW, 58, ["*② 加载 record-keeping", "~按「恢复视图」切片读状态"], "c",
          "references/protocols/record-keeping.md", "## 读写规则")
    f.box("F3", FX, 224, FW, 58, ["MEMORY.md · progress.yaml", "~最近 5 误解 / 3 记录 / 3 评估"], "f", "templates/MEMORY.md")
    f.arrow("C2", "C3")
    f.arrow("C3", "F3", "e", "w", "只读需要的部分", "dash")

    f.box("D4", 330, 306, 160, 76, ["有科目？"], "d", shape="diamond")
    f.arrow("C3", "D4")

    f.box("C5", CX, 408, CW, 58, ["*③ 新科目盘问（总控亲自）", "~按决策树 frontier 分轮问"], "c", SK, "## 二、新科目盘问")
    f.box("U5", UX, 408, UW, 58, ["逐张卡片作答", "~目的·程度·前置·项目·载体"], "u")
    f.arrow("D4", "C5", label="新科目 / 首次")
    f.arrow("C5", "U5", "w", "e", "AskUserQuestion", both=True)

    f.box("C6", CX, 492, CW, 58, ["*④ 写 MISSION.md · subject.yaml", "~建 subjects/<slug>/ 目录"], "c", SK, "4. **新科目**")
    f.box("F6", FX, 492, FW, 58, ["subjects/<slug>/", "~MISSION · subject.yaml · assessments/"], "f", "templates/MISSION.md")
    f.arrow("C5", "C6")
    f.arrow("C6", "F6", "e", "w", "写")

    f.box("C7", CX, 576, CW, 58, ["*⑤ 派 resource-scout", "~值：subject_path + 盘问摘要"], "c", SK, "### 怎么派")
    f.box("A7", AX, 576, AW, 58, ["*resource-scout", "~检索权威教材 / 官方文档"], "a", "references/roles/resource-scout.md")
    f.box("F7", FX, 576, FW, 58, ["/tmp/resource-scout-<slug>/", "~deliver/RESOURCES.md"], "f")
    f.arrow("C6", "C7")
    f.arrow("C7", "A7", "e", "w", "Agent")
    f.arrow("A7", "F7", "e", "w", "写")

    f.box("C8", CX, 660, CW, 58, ["*cp 落 RESOURCES.md", "~写 GLOSSARY.md（5-15 个主题词）"], "c", "templates/GLOSSARY.md")
    f.arrow("C7", "C8")
    f.arrow("F7", "C8", "s", "e", "cp（不读进上下文）")

    f.box("C9", CX, 752, CW, 58, ["*⑥ 同时派两个（并行）", "~同一条消息里两次 Agent 调用"], "c", SK, "3. 派 `resource-scout`")
    f.box("A9a", AX, 736, AW, 46, ["*image-scout", "~采图 → pool/ + pool.md"], "a", "references/roles/image-scout.md")
    f.box("A9b", AX, 792, AW, 46, ["*curriculum-designer", "~设计课程 DAG"], "a", "references/roles/curriculum-designer.md")
    f.box("F9", FX, 736, FW, 46, ["assets/img/pool.md", "~check_pool.py 自检"], "f")
    f.arrow("C8", "C9")
    f.arrow("C9", "A9a", "e", "w", oa=-18)
    f.arrow("C9", "A9b", "e", "w", oa=18)
    f.arrow("A9a", "F9", "e", "w", "写")

    f.box("C10", CX, 872, CW, 64, ["*⑦ 落 curriculum.yaml / progress.yaml", "~check_curriculum · check_pool", "~gen_home 刷新主页"], "c",
          "references/protocols/record-keeping.md", "## 主页刷新")
    f.box("F10", FX, 872, FW, 64, ["curriculum.yaml", "progress.yaml", "~index.html（主页）"], "f",
          "references/protocols/record-keeping.md")
    f.arrow("C9", "C10")
    f.arrow("A9b", "C10", "s", "e", "回大纲内容", ob=-14)
    f.arrow("C10", "F10", "e", "w", oa=14, ob=14)

    f.box("C11", CX, 962, CW, 58, ["*⑧ 报告 + 「下一步」", "~几个节点 / 第一课 / 课型 → 开始吗？"], "c", SK, "## 三、对话节奏")
    f.box("U11", UX, 962, UW, 58, ["“开始吧”"], "u")
    f.arrow("C10", "C11")
    f.arrow("D4", "C11", "w", "n", "已有科目：学生选", "accent", via=[(214, 344), (214, 944), (340, 944)], ob=-70,
            lpos=(214, 520))
    f.arrow("C11", "U11", "w", "e", "下一步")

    f.box("C12", CX, 1050, CW, 64, ["*⑨ 学习循环（一个节点）", "~详见图 1-B"], "c strong", SK, "## 四、学习循环")
    f.box("A12", AX, 1050, AW, 64, ["*learning-coach", "~→ practice-evaluator", "~串行两段，不并发"], "a",
          "references/roles/learning-coach.md")
    f.box("F12", FX, 1050, FW, 64, ["lessons/NNNN-<id>.md", ".quiz.json", "~render → .html"], "f", "references/课件内容格式.md")
    f.arrow("U11", "C12", "s", "w", ob=-14)
    f.arrow("C12", "A12", "e", "w", "Agent")
    f.arrow("A12", "F12", "e", "w", "写")

    f.box("C13", CX, 1142, CW, 58, ["*⑩ check_lesson 通过 → 呈上课件", "~回复里写绝对路径 / 预览面板"], "c", SK, "4. **过检查**")
    f.box("U13", UX, 1142, UW, 58, ["读课件 · 页内自测", "~跑 lab 断言"], "u")
    f.arrow("C12", "C13")
    f.arrow("C13", "U13", "w", "e")

    f.box("C14", CX, 1226, CW, 58, ["*局部提问：总控亲自答", "~local-qa：≤200 字 + 送回原位"], "c",
          "references/protocols/local-qa.md")
    f.box("U14", UX, 1226, UW, 58, ["贴回看不懂的一段"], "u")
    f.box("F14", FX, 1226, FW, 58, ["misconceptions.yaml", "~+ progress.yaml（双落点）"], "f")
    f.arrow("C13", "C14", label="随时", cls="dash")
    f.arrow("U14", "C14", "e", "w")
    f.arrow("C14", "F14", "e", "w", "记误解")

    f.box("D15", 330, 1310, 160, 76, ["评估点？"], "d", SK, "5. 学生说\"学完了\"", shape="diamond")
    f.box("U15", UX, 1319, UW, 58, ["“学完了 / 考考我”"], "u")
    f.box("A15", AX, 1319, AW, 58, ["*practice-evaluator", "~时机二 · 评估（作答原文）"], "a",
          "references/roles/practice-evaluator.md", "## 时机二")
    f.box("F15", FX, 1319, FW, 58, ["assessments/", "~NNNN-<id>.md"], "f", "references/protocols/evidence-check.md")
    f.arrow("C14", "D15")
    f.arrow("U15", "D15", "e", "w")
    f.arrow("D15", "A15", "e", "w", "是")
    f.arrow("A15", "F15", "e", "w", "写")

    f.box("C16", CX, 1412, CW, 58, ["*⑪ 更新 progress.yaml · 学习记录", "~实验通过 → 置「已通过项目验证」"], "c",
          "references/protocols/record-keeping.md", "## 项目与实验课")
    f.arrow("D15", "C16", label="否：保守更新")
    f.arrow("A15", "C16", "s", "e", "结论")
    f.arrow("C16", "C12", "w", "w", "下一节点", "accent", via=[(232, 1441), (232, 1096)], ob=14, lpos=(232, 1300))

    f.box("C17", CX, 1500, CW, 58, ["*⑫ 会话结束", "~会话摘要 + memory_updates，刷新主页"], "c", SK, "## 八、会话结束")
    f.box("U17", UX, 1500, UW, 58, ["“今天到这”"], "u")
    f.box("F17", FX, 1500, FW, 58, ["sessions/YYYY-MM-DD.md", "~MEMORY.md · index.html"], "f")
    f.arrow("C16", "C17", label="或结束")
    f.arrow("U17", "C17", "e", "w")
    f.arrow("C17", "F17", "e", "w", "写")
    return f.svg()


# ───────────────────────── 图 1-B：一个节点的产出管线 ─────────────────────────
def fig_loop() -> str:
    f = Fig("f1b", 900, 1030, "图 1-B：学习循环中一个节点从派工到呈上页面")
    SK = "SKILL.md"
    f.box("S", 300, 14, 300, 50, ["*学生同意学当前节点", "~总控把状态置为「学习中」"], "c")
    f.box("D", 365, 92, 170, 70, ["节点 kind？"], "d", "references/protocols/layered-practice.md", "## 四", shape="diamond")
    f.arrow("S", "D")

    LX, LW, RX, RW = 90, 320, 520, 320
    f.box("L1", LX, 200, LW, 66, ["*① 派 learning-coach", "~值：subject_path + 节点 id（不规定怎么写）",
                                   "~→ lessons/NNNN-<id>.md，留 ::: quiz 锚点"], "a", "references/roles/learning-coach.md")
    f.box("R1", RX, 200, RW, 66, ["*① 派 practice-evaluator", "~时机一 · 实验任务（+ 被验收节点 id）",
                                   "~→ deliver/lessons/…md + lab/NNNN-…/"], "a", "references/roles/practice-evaluator.md", "## 时机一")
    f.arrow("D", "L1", "w", "n", "概念 / 实操")
    f.arrow("D", "R1", "e", "n", "实验")

    f.box("L2", LX, 296, LW, 66, ["*② 内容落盘后，再派 practice-evaluator", "~时机一 · 出题（+ 内容文件路径 + 载体）",
                                   "~→ /tmp/practice-evaluator-<id>/deliver/"], "a", "references/roles/practice-evaluator.md", "## 时机一")
    f.box("L3", LX, 392, LW, 66, ["*③ 总控搬入（一个字都不改）", "~cp -r deliver/. <subject_path>/",
                                   "~empty_reason → apply_empty_reasons.py"], "c", SK, "- **你搬入**")
    f.box("L4", LX, 488, LW, 56, ["*④ 自查 lab 交付态（实操课）", "~参考解全绿 · 留白态非零退出"], "c", SK, "- **自查 lab 交付态**")
    f.arrow("L1", "L2")
    f.arrow("L2", "L3")
    f.arrow("L3", "L4")

    f.box("R2", RX, 296, RW, 66, ["*② 总控 cp 原样搬入", "~说明页 → lessons/ · 任务树 → lab/", "~缺东西打回出题人，不代写"], "c", SK,
          "3. **实验课")
    f.arrow("R1", "R2")

    f.box("M1", 270, 580, 360, 62, ["*⑤ render_lesson.py <subject> <id>", "~内容 .md + .quiz.json + curriculum.yaml → .html"],
          "s", "references/课件内容格式.md")
    f.arrow("L4", "M1", ob=-80)
    f.arrow("R2", "M1", ob=80)

    f.box("D2", 365, 672, 170, 70, ["带行号报错？"], "d", shape="diamond")
    f.arrow("M1", "D2")
    f.box("X1", 30, 672, 270, 70, ["*按 <文件>:<行> 打回作者", "~内容 → learning-coach", "~题库 / 锚点 → practice-evaluator"], "x",
          SK, "- **验收不过")
    f.arrow("D2", "X1", "w", "e", "是")
    f.arrow("X1", "L1", "n", "w", "改完重渲", "accent", via=[(56, 672), (56, 233)], oa=-109, lpos=(56, 460))

    f.box("M2", 270, 772, 360, 58, ["*⑥ check_lesson.py 过检查", "~版式 · 配图 · 题目结构 · 上下节指针 · lab"], "s", SK, "4. **过检查**")
    f.arrow("D2", "M2", label="否")
    f.box("D3", 365, 858, 170, 66, ["FAIL？"], "d", shape="diamond")
    f.arrow("M2", "D3")
    f.arrow("D3", "X1", "w", "s", "是")
    f.box("M3", 270, 954, 360, 58, ["*⑦ 呈上页面（绝对路径）+「下一步」", "~实操 / 实验课顺带给 lab/NNNN-… 路径"], "c", SK, "## 三、对话节奏")
    f.arrow("D3", "M3", label="PASS（WARN 心里有数）")
    return f.svg()


# ───────────────────────── 图 1-C：派工协议时序 ─────────────────────────
def fig_seq() -> str:
    W, H = 1080, 520
    f = Fig("f1c", W, H, "图 1-C：总控派一次活的完整往返")
    P = [
        ("总控（主会话）", 110, "c"),
        ("子代理（全新上下文）", 360, "a"),
        ("/tmp/<角色>-<id>/deliver/", 600, "f"),
        ("科目目录", 820, "f"),
        ("校验脚本", 990, "s"),
    ]
    for name, x, cls in P:
        w = max(150, text_w(name, 12.6, 7.2) + 26)
        f.raw(f'<line class="life" x1="{x}" y1="56" x2="{x}" y2="{H - 14}"/>')
        f.box(name, x - w / 2, 10, w, 46, ["*" + name], cls)

    def msg(y, a, b, label, cls=""):
        xa, xb = P[a][1], P[b][1]
        pad = 6 if xb > xa else -6
        f.path([(xa + pad, y), (xb - pad, y)], None, cls)
        lx = (xa + xb) / 2
        tw = text_w(label, 12, 6.6) + 12
        f.labels.append(
            f'<rect class="elb" x="{lx - tw / 2:.1f}" y="{y - 26:.1f}" width="{tw:.1f}" height="20" rx="4"/>'
            f'<text class="el strong {cls}" x="{lx:.1f}" y="{y - 16:.1f}" text-anchor="middle" dominant-baseline="central">{esc(label)}</text>'
        )

    msg(104, 0, 1, "① 三样：规格路径 · 值 · 边界")
    x = P[1][1]
    f.path([(x + 6, 140), (x + 70, 140), (x + 70, 172), (x + 6, 172)], None)
    f.labels.append(f'<text class="el strong" x="{x + 80}" y="156" dominant-baseline="central">② 自己 Read 角色规格与协议</text>')
    msg(226, 1, 2, "③ 按最终相对路径写产物")
    msg(276, 1, 0, "④ 只回摘要 + 可复算规模", "dash")
    msg(326, 2, 3, "⑤ 总控执行 cp / cp -r")
    msg(376, 0, 4, "⑥ render_lesson / check_*")
    msg(426, 4, 0, "⑦ 通过，或 <文件>:<行> 报错", "dash")
    msg(476, 0, 1, "⑧ 不过：带原文证据退回作者", "warn")
    return f.svg()


# ───────────────────────── 图 2-B：文件关系与数据流 ─────────────────────────
def fig_files() -> str:
    f = Fig("f2b", 1080, 840, "图 2-B：学习工作区里的文件由谁写、被谁读、生成什么")
    f.raw('<text class="lane-t" x="205" y="28" text-anchor="middle">源文件（✎ = 作者）</text>')
    f.raw('<text class="lane-t" x="565" y="28" text-anchor="middle">引擎：脚本 / 模板 / schema</text>')
    f.raw('<text class="lane-t" x="910" y="28" text-anchor="middle">生成产物（谁也不手改）</text>')
    FX, FW = 40, 330
    files = [
        ("f1", "MEMORY.md", "✎ 总控（跨科目共享）", "templates/MEMORY.md"),
        ("f2", "subject.yaml · MISSION.md · GLOSSARY.md", "✎ 总控（元数据，改前跟学生确认）", "templates/MISSION.md"),
        ("f3", "RESOURCES.md", "✎ resource-scout → deliver → 总控 cp", "references/roles/resource-scout.md"),
        ("f4", "assets/img/pool/ + pool.md", "✎ image-scout（learning-coach 可追加自产图）", "references/roles/image-scout.md"),
        ("f5", "curriculum.yaml（课程 DAG）", "✎ curriculum-designer 设计 → 总控落盘", "references/roles/curriculum-designer.md"),
        ("f6", "lessons/NNNN-<id>.md（内容文件）", "✎ learning-coach（实验说明页：practice-evaluator）", "references/课件内容格式.md"),
        ("f7", "lessons/NNNN-<id>.quiz.json（题库）", "✎ practice-evaluator → deliver → cp", "references/protocols/layered-practice.md"),
        ("f8", "lab/NNNN-…/ + solutions/ + README.md", "✎ practice-evaluator → deliver → cp", "references/protocols/layered-practice.md"),
        ("f9", "progress.yaml · misconceptions.yaml", "✎ 总控（运行期进度只认 progress.yaml）", "references/protocols/record-keeping.md"),
        ("f10", "assessments/ · learning-records/ · sessions/", "✎ 评估：practice-evaluator；其余：总控", "references/protocols/record-keeping.md"),
    ]
    for i, (id, name, owner, doc) in enumerate(files):
        f.box(id, FX, 50 + i * 60, FW, 48, ["*" + name, "~" + owner], "f", doc)

    MX, MW = 450, 230
    f.box("sc", MX, 110, MW, 48, ["*schemas/*.json（5 份）", "~结构化文件写后校验"], "ref", "references/protocols/record-keeping.md",
          "## 读写规则")
    f.box("s4", MX, 230, MW, 48, ["*check_pool.py", "~七列索引 · 命名 · ≤500 KB"], "s", "references/roles/image-scout.md")
    f.box("s3", MX, 290, MW, 48, ["*check_curriculum.py", "~重复 id · 悬空 · 环 · 孤儿"], "s", "SKILL.md", "## 十、脚本清单")
    f.box("s1", MX, 380, MW, 62, ["*render_lesson.py", "~内容 + 题库 + 大纲 → 页面", "~认不出就报错，不静默降级"], "s",
          "references/课件内容格式.md")
    f.box("t1", MX, 470, MW, 46, ["*templates/lesson.html", "~占位符外壳 @LEARN:*"], "ref", "references/工程约束.md",
          "## 三、模板与生成器的占位符契约")
    f.box("s5", MX, 676, MW, 58, ["*gen_home.py", "~模板 + 科目数据 → 主页", "~含链接自检"], "s", "references/工程约束.md",
          "## 三、模板与生成器的占位符契约")
    f.box("t2", MX, 764, MW, 46, ["*home-index / subject-index.html", "~主页模板"], "ref", "references/工程约束.md",
          "## 三、模板与生成器的占位符契约")

    OX, OW = 780, 260
    f.box("o1", OX, 380, OW, 62, ["*lessons/NNNN-<id>.html", "~学生看的课件页"], "o")
    f.box("s2", OX, 480, OW, 58, ["*check_lesson.py", "~版式 · 题目结构 · 指针 · lab 齐全"], "s", "SKILL.md", "4. **过检查**")
    f.box("o2", OX, 626, OW, 46, ["*subjects/<slug>/index.html", "~科目主页（路线图）"], "o")
    f.box("o3", OX, 684, OW, 46, ["*<LEARN_WORKSPACE>/index.html", "~根主页（全部科目）"], "o")
    f.box("o4", OX, 742, OW, 46, ["*GLOSSARY.html · RESOURCES.html", "~附件静态页"], "o")

    f.arrow("f4", "s4", "e", "w")
    f.arrow("f5", "s3", "e", "w")
    f.arrow("sc", "s3", "e", "e", "schema", "dash", via=[(705, 134), (705, 314)])
    f.arrow("f5", "s1", "e", "w", oa=12, ob=-20, via=[(425, 326), (425, 391)])
    f.arrow("f6", "s1", "e", "w", ob=-2, via=[(405, 374), (405, 409)])
    f.arrow("f7", "s1", "e", "w", ob=16)
    f.arrow("t1", "s1", "n", "s")
    f.arrow("s1", "o1", "e", "w", "写盘")
    f.arrow("o1", "s2", "s", "n", "检查", "dash")
    # 左侧总线：元数据、大纲、进度与记录 → gen_home
    bus_x, bus_y = 20, 705
    for fid in ("f2", "f3", "f5", "f9", "f10"):
        x, y, w, h = f.B[fid]
        f.raw(f'<path class="e bus" d="M{x},{y + h / 2} L{bus_x},{y + h / 2}"/><circle class="busdot" cx="{bus_x}" cy="{y + h / 2}" r="3"/>')
    f.path([(bus_x, 134), (bus_x, bus_y), (MX, bus_y)], "gen_home 读取", "bus", lpos=(235, bus_y))
    f.arrow("t2", "s5", "n", "s")
    f.arrow("s5", "o2", "e", "w", oa=-14)
    f.arrow("s5", "o3", "e", "w", oa=2)
    f.arrow("s5", "o4", "e", "w", oa=16)
    return f.svg()


# ───────────────────────── 页面 ─────────────────────────
PAGE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>StudyMate Skill 原理教程</title>
<meta name="description" content="StudyMate 自学技能包在 Claude Code 里如何被调用、如何派工、文件之间什么关系——流程图 + 原文对照。">
<style>
:root{
  --bg:#f6f5f1; --panel:#ffffff; --panel2:#f0eee8; --ink:#1d1f24; --muted:#5d636e; --line:#d9d6cd;
  --accent:#2f6fde; --accent-bg:#e8f0ff;
  --u:#c9702a; --u-bg:#fdf1e6; --c:#2f6fde; --c-bg:#eaf1ff; --a:#7b4fc9; --a-bg:#f2ecfd;
  --f:#2d8a5a; --f-bg:#e8f6ee; --s:#0f8a8f; --s-bg:#e3f5f5; --d:#b8860b; --d-bg:#fdf6dd;
  --x:#c63d3d; --x-bg:#fdecec; --o:#566070; --o-bg:#eef0f3;
  --lane-u:#fbf4ec; --lane-c:#eff4fd; --lane-a:#f6f1fd; --lane-f:#eef8f2;
  --edge:#7c828d; --code-bg:#fbfaf7; --hl:#fff4c2; --shadow:0 1px 2px rgba(0,0,0,.05),0 6px 24px rgba(0,0,0,.06);
}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){
  --bg:#15171b; --panel:#1d2026; --panel2:#23272e; --ink:#e6e8ec; --muted:#9aa2ae; --line:#343944;
  --accent:#7aa7ff; --accent-bg:#1f2b44;
  --u:#f0a060; --u-bg:#3a2a1c; --c:#7aa7ff; --c-bg:#1d2a44; --a:#b18cf5; --a-bg:#2c2340;
  --f:#5fcf93; --f-bg:#1b3327; --s:#4fd0d4; --s-bg:#173335; --d:#e6bd4a; --d-bg:#3a3218;
  --x:#f07a7a; --x-bg:#402222; --o:#aab3c0; --o-bg:#2a2f37;
  --lane-u:#211d19; --lane-c:#1a1f29; --lane-a:#1f1b27; --lane-f:#18221d;
  --edge:#8a919c; --code-bg:#181a1f; --hl:#3d3717; --shadow:0 1px 2px rgba(0,0,0,.3),0 6px 24px rgba(0,0,0,.3);
}}
:root[data-theme="dark"]{
  --bg:#15171b; --panel:#1d2026; --panel2:#23272e; --ink:#e6e8ec; --muted:#9aa2ae; --line:#343944;
  --accent:#7aa7ff; --accent-bg:#1f2b44;
  --u:#f0a060; --u-bg:#3a2a1c; --c:#7aa7ff; --c-bg:#1d2a44; --a:#b18cf5; --a-bg:#2c2340;
  --f:#5fcf93; --f-bg:#1b3327; --s:#4fd0d4; --s-bg:#173335; --d:#e6bd4a; --d-bg:#3a3218;
  --x:#f07a7a; --x-bg:#402222; --o:#aab3c0; --o-bg:#2a2f37;
  --lane-u:#211d19; --lane-c:#1a1f29; --lane-a:#1f1b27; --lane-f:#18221d;
  --edge:#8a919c; --code-bg:#181a1f; --hl:#3d3717; --shadow:0 1px 2px rgba(0,0,0,.3),0 6px 24px rgba(0,0,0,.3);
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.75 -apple-system,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif}
code,pre,.mono{font-family:"Cascadia Code",Consolas,"SFMono-Regular",Menlo,monospace}
a{color:var(--accent)}
.layout{display:grid;grid-template-columns:240px minmax(0,1fr);gap:40px;max-width:1280px;margin:0 auto;padding:0 24px}
nav.toc{position:sticky;top:0;align-self:start;max-height:100vh;overflow:auto;padding:28px 0;font-size:13.5px}
nav.toc .brand{font-weight:700;font-size:15px;margin-bottom:14px}
nav.toc a{display:block;color:var(--muted);text-decoration:none;padding:3px 10px;border-left:2px solid transparent}
nav.toc a.sub{padding-left:22px;font-size:13px}
nav.toc a:hover,nav.toc a.on{color:var(--ink);border-left-color:var(--accent)}
main{padding:28px 0 120px;min-width:0}
header.hero{padding:26px 0 8px}
.eyebrow{color:var(--accent);font-weight:600;font-size:13px;letter-spacing:.06em}
h1{font-size:32px;line-height:1.3;margin:6px 0 12px}
h2{font-size:23px;margin:56px 0 12px;padding-top:8px;border-top:1px solid var(--line)}
h3{font-size:17.5px;margin:32px 0 8px}
p{margin:10px 0}
.lead{font-size:16.5px;color:var(--muted);max-width:780px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:16px 20px;box-shadow:var(--shadow)}
.grid{display:grid;gap:14px}
.g3{grid-template-columns:repeat(3,minmax(0,1fr))}
.g2{grid-template-columns:repeat(2,minmax(0,1fr))}
.g5{grid-template-columns:repeat(5,minmax(0,1fr))}
table{border-collapse:collapse;width:100%;font-size:14px;margin:12px 0}
th,td{border:1px solid var(--line);padding:7px 10px;text-align:left;vertical-align:top}
th{background:var(--panel2);font-weight:600}
td code,p code,li code{background:var(--panel2);padding:1px 5px;border-radius:4px;font-size:.9em}
.tablewrap{overflow-x:auto}
pre.cmd{background:var(--code-bg);border:1px solid var(--line);border-radius:8px;padding:10px 14px;overflow-x:auto;font-size:13.5px;margin:8px 0}
a.doc{text-decoration:none;border-bottom:1px dashed var(--accent);font-family:"Cascadia Code",Consolas,monospace;font-size:.88em;background:var(--accent-bg);padding:1px 5px;border-radius:4px;white-space:nowrap}
a.doc::after{content:" ↗";font-size:.8em}
.figure{margin:18px 0 8px;background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:14px;box-shadow:var(--shadow)}
.figure .scroll{overflow-x:auto}
.figcap{font-size:13.5px;color:var(--muted);margin:10px 4px 0}
.figcap b{color:var(--ink)}
svg.fig{width:100%;height:auto;display:block;font-family:-apple-system,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif}
.lane{stroke:none}.lane.u{fill:var(--lane-u)}.lane.c{fill:var(--lane-c)}.lane.a{fill:var(--lane-a)}.lane.f{fill:var(--lane-f)}
.lane-t{font-size:14px;font-weight:700;fill:var(--muted)}
.nd{fill:var(--panel);stroke:var(--line);stroke-width:1.4}
.nd.u{fill:var(--u-bg);stroke:var(--u)}.nd.c{fill:var(--c-bg);stroke:var(--c)}.nd.a{fill:var(--a-bg);stroke:var(--a)}
.nd.f{fill:var(--f-bg);stroke:var(--f)}.nd.s{fill:var(--s-bg);stroke:var(--s)}.nd.d{fill:var(--d-bg);stroke:var(--d)}
.nd.x{fill:var(--x-bg);stroke:var(--x)}.nd.o{fill:var(--o-bg);stroke:var(--o);stroke-dasharray:0}
.nd.ref{fill:var(--panel);stroke:var(--edge);stroke-dasharray:5 3}
.nd.strong{stroke-width:2.6}
.t{font-size:13px;fill:var(--ink)}.tb{font-weight:700}.tm{fill:var(--muted);font-size:12px}
.t-doc{font-size:11px;fill:var(--accent);opacity:.7}
g.clk{cursor:pointer}g.clk:hover .nd,g.clk:focus .nd{filter:brightness(1.05);stroke-width:2.4}
g.clk:focus{outline:none}
.e{fill:none;stroke:var(--edge);stroke-width:1.6}
.e.dash{stroke-dasharray:6 4}.e.accent{stroke:var(--accent);stroke-width:1.8;stroke-dasharray:7 4}
.e.warn{stroke:var(--x)}.e.bus{stroke:var(--f);stroke-dasharray:3 3}
.busdot{fill:var(--f)}
.ahp{fill:var(--edge)}
.elb{fill:var(--bg);opacity:.92}
.el{font-size:12px;fill:var(--muted)}.el.strong{fill:var(--ink)}.el.accent{fill:var(--accent)}.el.warn{fill:var(--x)}
.life{stroke:var(--line);stroke-width:1.4;stroke-dasharray:4 4}
.legend{display:flex;flex-wrap:wrap;gap:8px 16px;font-size:13px;color:var(--muted);margin:8px 4px 0}
.legend i{display:inline-block;width:14px;height:14px;border-radius:4px;vertical-align:-2px;margin-right:6px;border:1.5px solid}
.stack{display:flex;flex-direction:column;gap:0}
.layer{display:grid;grid-template-columns:150px minmax(0,1fr);gap:16px;align-items:center;background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px 16px}
.layer .ln{font-weight:700}
.layer .ln small{display:block;font-weight:400;color:var(--muted);font-size:12.5px;line-height:1.4}
.chips{display:flex;flex-wrap:wrap;gap:6px}
.chip{font-size:13px;padding:3px 9px;border-radius:999px;border:1px solid var(--line);background:var(--panel2);white-space:nowrap}
.chip.c{border-color:var(--c);background:var(--c-bg)}.chip.a{border-color:var(--a);background:var(--a-bg)}
.chip.s{border-color:var(--s);background:var(--s-bg)}.chip.f{border-color:var(--f);background:var(--f-bg)}
.conn{align-self:center;font-size:12.5px;color:var(--muted);padding:4px 0 4px 170px;position:relative}
.conn::before{content:"";position:absolute;left:74px;top:0;bottom:0;border-left:2px dashed var(--line)}
.lvl{border-left:4px solid var(--accent)}
.lvl h4{margin:0 0 4px;font-size:15px}.lvl p{margin:4px 0;font-size:14px;color:var(--muted)}
.note{border-left:4px solid var(--d);background:var(--d-bg);padding:10px 14px;border-radius:8px;margin:14px 0;font-size:14.5px}
.warnbox{border-left:4px solid var(--x);background:var(--x-bg);padding:10px 14px;border-radius:8px;margin:14px 0;font-size:14.5px}
.principle{counter-increment:pr}
.principle h4{margin:0 0 4px;font-size:15.5px}
.principle h4::before{content:counter(pr) ". ";color:var(--accent)}
.principles{counter-reset:pr}
.principle p{font-size:14px;margin:4px 0;color:var(--muted)}
.principle .src{font-size:12.5px}
.doclib{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:10px}
.doclib button{all:unset;cursor:pointer;display:block;background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:9px 12px}
.doclib button:hover{border-color:var(--accent)}
.doclib .p{font-family:"Cascadia Code",Consolas,monospace;font-size:12.5px;word-break:break-all}
.doclib .s{font-size:12.5px;color:var(--muted)}
.doclib h4{grid-column:1/-1;margin:14px 0 0;font-size:14px;color:var(--muted)}
/* 原文抽屉 */
.drawer{position:fixed;top:0;right:0;height:100vh;width:min(860px,100vw);background:var(--panel);border-left:1px solid var(--line);box-shadow:-10px 0 40px rgba(0,0,0,.18);transform:translateX(102%);transition:transform .22s ease;z-index:50;display:flex;flex-direction:column}
.drawer.open{transform:none}
.dhead{display:flex;flex-wrap:wrap;align-items:center;gap:8px;padding:12px 16px;border-bottom:1px solid var(--line);background:var(--panel2)}
.dhead .path{font-family:"Cascadia Code",Consolas,monospace;font-size:13.5px;font-weight:600;flex:1;min-width:180px;word-break:break-all}
.dhead .desc{width:100%;font-size:12.5px;color:var(--muted);order:5}
.btn{font:inherit;font-size:13px;padding:4px 10px;border-radius:7px;border:1px solid var(--line);background:var(--panel);color:var(--ink);cursor:pointer;text-decoration:none}
.btn:hover{border-color:var(--accent)}
.btn.on{background:var(--accent);color:#fff;border-color:var(--accent)}
.dbody{flex:1;overflow:auto;background:var(--code-bg)}
.src{font-family:"Cascadia Code",Consolas,monospace;font-size:13px;line-height:1.65;padding:8px 0;min-width:max-content}
.src .r{display:flex;padding-right:18px}
.src .r.hl{background:var(--hl)}
.src .n{flex:0 0 52px;text-align:right;padding-right:14px;color:var(--muted);opacity:.6;user-select:none}
.src .c{white-space:pre}
.src .h{color:var(--accent);font-weight:700}.src .fm{color:var(--a)}.src .fence{color:var(--s)}.src .dir{color:var(--u);font-weight:600}
.src .tbl{color:var(--ink)}.src .cm{color:var(--muted)}
.rendered{padding:18px 26px;font-size:14.5px;line-height:1.75}
.rendered pre{background:var(--panel2);padding:10px;border-radius:6px;overflow:auto}
.rendered table{font-size:13px}
.scrim{position:fixed;inset:0;background:rgba(0,0,0,.25);opacity:0;pointer-events:none;transition:opacity .2s;z-index:40}
.scrim.open{opacity:1;pointer-events:auto}
.themebtn{position:fixed;right:16px;bottom:16px;z-index:30}
@media (max-width:980px){
  .layout{grid-template-columns:1fr;padding:0 16px}
  nav.toc{display:none}
  .g3,.g5{grid-template-columns:1fr 1fr}
}
@media (max-width:620px){
  .g3,.g2,.g5{grid-template-columns:1fr}
  .layer{grid-template-columns:1fr}
  .conn{padding-left:16px}.conn::before{left:6px}
  h1{font-size:25px}
}
</style>
</head>
<body>
<div class="layout">
<nav class="toc" id="toc">
  <div class="brand">StudyMate Skill 教程</div>
  <a href="#s0">0. 一页看懂</a>
  <a href="#s1">1. 装进 Claude Code</a>
  <a href="#s2">2. Claude Code 怎么加载它</a>
  <a href="#s3">3. 图一：调用工作流</a>
  <a class="sub" href="#s3a">总工作流（泳道）</a>
  <a class="sub" href="#s3b">一个节点的产出管线</a>
  <a class="sub" href="#s3c">派一次活的往返</a>
  <a class="sub" href="#s3d">抽象能力 → 具体工具</a>
  <a href="#s4">4. 图二：架构拆解</a>
  <a class="sub" href="#s4a">分层架构</a>
  <a class="sub" href="#s4b">文件关系与数据流</a>
  <a class="sub" href="#s4c">课件三件与归属</a>
  <a href="#s5">5. 设计原理</a>
  <a href="#s6">6. Windows 注意事项</a>
  <a href="#s7">7. 原文档库</a>
</nav>
<main>
<header class="hero">
  <div class="eyebrow">STUDY-MATE-SKILL · 工作流与架构</div>
  <h1>一个 SKILL.md 怎样驱动一整套自学系统</h1>
  <p class="lead">这份教程拆解 <code>E:\Code\Study-Mate-Skill</code>：它装进 Claude Code 之后，AI 怎样被触发、怎样当好「总控」、怎样把活派给 5 个子代理，以及磁盘上每个文件由谁写、被谁读。所有带 <span class="mono" style="color:var(--accent)">↗</span> 的文件名和流程图方框都能点开，<b>点开后逐行显示该文件的原文</b>，并定位到相关段落。</p>
</header>

<h2 id="s0">0. 一页看懂</h2>
<div class="grid g3">
  <div class="card"><b>它是什么</b><p>一个<b>编排型</b>技能：%SKILL% 本身不教知识，只规定流程。AI 读了它之后扮演「总控」，负责定流程、和学生对话、记档案，把检索、写课件、出题这些重活派给子代理。</p></div>
  <div class="card"><b>为什么能跨会话</b><p>学习状态全部写在文件里（%MEMORY%、<code>progress.yaml</code>……）。每次开场按「恢复视图」只切片读取相关部分，所以上下文一直很短，下次会话也能从上次停下的地方接着学。</p></div>
  <div class="card"><b>为什么质量可控</b><p><b>模型一个字 HTML 都不写</b>：讲解角色写内容 .md，出题角色写 .quiz.json，页面由 Python 渲染器一次生成，再过 4 道带行号报错的确定性校验。</p></div>
</div>

<h2 id="s1">1. 装进 Claude Code</h2>
<p>README 的做法是把整个目录复制到宿主的技能目录（%README_INSTALL%）。要注意一点：技能名以 frontmatter 的 <code>name: study-mate-skill</code> 为准，把目录名也改成一样，<code>/study-mate-skill</code> 的触发名和目录才对得上。在 PowerShell 里：</p>
<pre class="cmd">Copy-Item -Recurse E:\Code\Study-Mate-Skill "$HOME\.claude\skills\study-mate-skill"</pre>
<pre class="cmd">python -m pip install pyyaml jsonschema</pre>
<p>装好之后，在任意目录开一个 Claude Code 会话，说一句「我想学 X」或输入 <code>/study-mate-skill</code> 就能触发。学习数据默认写到 <code>&lt;root&gt;/workspace</code>；想换位置，改 %CONFIG%，或者设置环境变量 <code>LEARN_WORKSPACE</code>。</p>

<h2 id="s2">2. Claude Code 怎么加载它：三层渐进式披露</h2>
<p>Claude Code 不会把整个技能包一次性塞进上下文，而是分三层、按需加载。StudyMate 在第三层又加了一条硬规矩：「需要哪份就读哪份，别一次全读进来」（见 %SKILL_TABLE%）。</p>
<div class="grid g3">
  <div class="card lvl"><h4>第 1 层 · 元数据（常驻）</h4><p>会话启动时，Claude Code 扫描 <code>~/.claude/skills/*/SKILL.md</code>，只把 frontmatter 里的 <code>name</code>、<code>description</code>、<code>argument-hint</code> 放进技能列表，占用的 token 很少。</p><p>description 里写好了触发语：「我想学 X」「继续学 X」「考考我」「这段没看懂」。</p></div>
  <div class="card lvl"><h4>第 2 层 · SKILL.md 正文（触发时）</h4><p>用户的话和 description 匹配上，或者用户手动输入 <code>/study-mate-skill</code>，模型就调用 <b>Skill 工具</b>。Claude Code 把 SKILL.md 正文和它所在目录的绝对路径（<b>Base directory</b>）一起注入上下文，这个路径就是文档里反复出现的 <code>&lt;root&gt;</code>。</p></div>
  <div class="card lvl"><h4>第 3 层 · references / scripts（按需）</h4><p>SKILL.md 开头有一张「什么时候读」的表，总控只在需要时用 Read 读对应的规格。派活时，它只把规格的<b>绝对路径</b>交给子代理，由子代理自己去读。脚本则通过 Bash 执行，脚本源码不进上下文。</p></div>
</div>

<h2 id="s3">3. 图一：AI 调用这个 Skill 时的工作流</h2>
<h3 id="s3a">3.1 总工作流（四条泳道）</h3>
<p>图里从上到下是一次完整会话：开场、新科目盘问、并行建课、学习循环、局部提问、评估，最后结束会话。<b>方框可以点</b>，会打开 SKILL.md（或对应规格）的原文，并定位到那一节。</p>
<div class="figure"><div class="scroll">%FIG1%</div>
<div class="legend"><span><i style="border-color:var(--u);background:var(--u-bg)"></i>学生动作</span><span><i style="border-color:var(--c);background:var(--c-bg)"></i>总控亲自做</span><span><i style="border-color:var(--a);background:var(--a-bg)"></i>子代理</span><span><i style="border-color:var(--f);background:var(--f-bg)"></i>文件</span><span><i style="border-color:var(--d);background:var(--d-bg)"></i>判断</span><span style="color:var(--accent)">- - 蓝色虚线：分支 / 回路</span></div>
<p class="figcap"><b>图 1</b>　几个关键点：① 开场第一步永远是定位 <code>&lt;root&gt;</code> 和工作区，<b>不在会话 cwd 里读写</b>；② 盘问由总控亲自做，用 AskUserQuestion 一次一张卡片，推荐项放第一个；③ <code>image-scout</code> 和 <code>curriculum-designer</code> 是全流程里<b>唯一</b>允许并行的一段，因为两者不写同一个文件；④ 每轮回复都以「下一步」收尾，这是硬规则。</p></div>

<h3 id="s3b">3.2 图 1-B：学习循环里，一个节点怎样从派工走到呈上页面</h3>
<p>对应 %LOOP%。节点按 <code>kind</code> 分两条路：概念课和实操课<b>串行两段</b>，先由讲解角色写正文和锚点，再由出题人出题；实验课只派出题人，产出实验说明页和验收任务。两条路最后合流，统一经过渲染器和检查。</p>
<div class="figure"><div class="scroll">%FIG1B%</div>
<p class="figcap"><b>图 1-B</b>　为什么必须串行：题库和内容文件之间靠 <code>::: quiz</code> 的<b>锚点文本</b>逐字对位。锚点是讲解的产物，内容文件还没落盘时出题人无从对齐，所以「两边同时开工必然对不上」。报错按归属打回：内容问题退给 <code>learning-coach</code>，题库或锚点问题退给 <code>practice-evaluator</code>，总控<b>不代改</b>。</p></div>

<h3 id="s3c">3.3 图 1-C：总控派一次活的完整往返</h3>
<p>对应 %DISPATCH%。这张时序图适用于全部 5 个角色。</p>
<div class="figure"><div class="scroll">%FIG1C%</div>
<p class="figcap"><b>图 1-C</b>　派工 prompt <b>只写三样</b>：① 角色规格的绝对路径（「先读它、照它执行」）；② 值（路径、节点 id、载体……），不复述要求和格式；③ 一句三条边界（不自行委派子代理、不直接向用户提问、不建也不改环境）。子代理的长产出不放在回复正文里（回复会被压缩），而是落到 <code>/tmp/&lt;角色&gt;-&lt;id&gt;/deliver/</code>，由总控 <code>cp</code> 原样搬进科目目录。这样<b>一份产物只经过作者一个人的手</b>。</p></div>

<h3 id="s3d">3.4 SKILL.md 里的抽象能力，对应 Claude Code 的哪个工具</h3>
<p>这个技能包写成了「宿主无关」的形式（%DISPATCH9%），在 Claude Code 里的落点如下：</p>
<div class="tablewrap"><table>
<tr><th>SKILL.md 的说法</th><th>Claude Code 里的工具</th><th>说明</th></tr>
<tr><td>唯一入口 / 技能注册</td><td>技能目录扫描 + <b>Skill</b> 工具</td><td>只有 SKILL.md 被注册；<code>references/</code> 下的角色和协议都是普通 .md，不会被识别成独立技能</td></tr>
<tr><td>宿主的「用户提问能力」</td><td><b>AskUserQuestion</b></td><td>「一次一条卡片，推荐项放第一并标 (Recommended)」和这个工具的约定一致</td></tr>
<tr><td>子代理 / 任务委派</td><td><b>Agent</b>（general-purpose）</td><td>必须是<b>全新上下文</b>，不能用会继承上下文的 fork 模式，否则角色会以为自己是总控。并行时在同一条消息里发两次 Agent 调用</td></tr>
<tr><td>读规格 / 读状态</td><td><b>Read</b>（offset/limit）、<b>Grep</b></td><td>恢复视图要求只读需要的部分</td></tr>
<tr><td>搬运、跑渲染器和校验</td><td><b>Bash</b> / PowerShell</td><td><code>cp -r</code>、<code>python … render_lesson.py</code>、<code>check_*.py</code>、<code>gen_home.py</code></td></tr>
<tr><td>外部检索（仅子代理）</td><td><b>WebSearch / WebFetch</b></td><td><code>resource-scout</code> 查权威来源；<code>image-scout</code> 只在允许的站点内抓图</td></tr>
<tr><td>结果呈现</td><td>预览面板 / 发送文件 / 回复里的绝对路径</td><td>硬规则：<b>至少要在回复里写出绝对路径</b>，这样学生点得开</td></tr>
<tr><td>没有子代理能力的宿主</td><td>—</td><td>总控按角色规格<b>自己串行执行</b>；「prompt 只写三样」不再适用，但角色边界仍然有效</td></tr>
</table></div>

<h2 id="s4">4. 图二：项目架构拆解与运行逻辑</h2>
<h3 id="s4a">4.1 分层架构：引擎只读，工作区读写</h3>
<p>整个包分成两个<b>互不混用</b>的区域（%ENG%）：<b>引擎</b> <code>&lt;root&gt;/</code> 在学习时只读；<b>学习工作区</b> <code>&lt;LEARN_WORKSPACE&gt;/</code> 存放全部学习数据，换机器时连同工作区整体拷走即可。</p>
<div class="stack">
  <div class="layer"><div class="ln">宿主层<small>Claude Code</small></div><div class="chips"><span class="chip">Skill 工具</span><span class="chip">Agent</span><span class="chip">AskUserQuestion</span><span class="chip">Read / Grep</span><span class="chip">Bash</span><span class="chip">WebSearch / WebFetch</span><span class="chip">预览 / 呈现</span></div></div>
  <div class="conn">Skill 工具注入 SKILL.md 正文 + Base directory</div>
  <div class="layer"><div class="ln">编排层<small>唯一入口，流程归它</small></div><div class="chips"><span class="chip c">%SKILL% = 总控</span><span class="chip c">开场 · 盘问 · 学习循环 · 使命变更 · 会话结束</span><span class="chip c">亲自做：答疑 / 元数据 / 全部档案 / 跑脚本</span></div></div>
  <div class="conn">按路径派工（只给规格路径 + 值 + 边界）</div>
  <div class="layer"><div class="ln">角色层<small>references/roles/ · 子代理</small></div><div class="chips">%ROLES%</div></div>
  <div class="conn">角色和总控都要遵守的规则：一处定义，别处只给指针</div>
  <div class="layer"><div class="ln">规格层<small>references/</small></div><div class="chips">%PROTOCOLS%</div></div>
  <div class="conn">契约：字段结构、占位符、内容语法</div>
  <div class="layer"><div class="ln">确定性层<small>scripts / schemas / templates</small></div><div class="chips"><span class="chip s">render_lesson.py</span><span class="chip s">check_lesson.py</span><span class="chip s">check_curriculum.py</span><span class="chip s">check_pool.py</span><span class="chip s">check_skill.py</span><span class="chip s">gen_home.py</span><span class="chip s">renumber_lessons.py</span><span class="chip s">apply_empty_reasons.py</span><span class="chip">schemas/ ×5</span><span class="chip">templates/（lesson / home / subject 模板 + Sayo UI）</span></div></div>
  <div class="conn">写入 / 生成</div>
  <div class="layer"><div class="ln">数据层<small>&lt;LEARN_WORKSPACE&gt;/</small></div><div class="chips"><span class="chip f">index.html</span><span class="chip f">.learning/MEMORY.md</span><span class="chip f">.learning/assets/（共享层）</span><span class="chip f">subjects/&lt;slug&gt;/…</span></div></div>
</div>
<p>运行逻辑可以概括成一句话：<b>LLM 负责判断和生成内容，Python 负责格式和一致性。</b>模型产出的是 Markdown、YAML、JSON 这类「源文件」；凡是可以机械判定的部分（HTML 结构、上下节指针、锚点对账、DAG 有没有环、图片命名），都交给带行号报错的脚本。</p>

<h3 id="s4b">4.2 图 2-B：文件关系与数据流</h3>
<p>下图左列是科目目录里的源文件，每个方框第二行写着作者；中列是引擎里的脚本、模板和 schema；右列是生成出来的页面。方框可以点开看对应规格的原文。</p>
<div class="figure"><div class="scroll">%FIG2B%</div>
<div class="legend"><span><i style="border-color:var(--f);background:var(--f-bg)"></i>源文件</span><span><i style="border-color:var(--s);background:var(--s-bg)"></i>脚本</span><span><i style="border-color:var(--edge);border-style:dashed"></i>模板 / schema</span><span><i style="border-color:var(--o);background:var(--o-bg)"></i>生成产物</span><span style="color:var(--f)">··· 绿色点线：gen_home 的输入总线</span></div>
<p class="figcap"><b>图 2-B</b>　两条关键规则：① <b>进度只认 <code>progress.yaml</code></b>。<code>curriculum.yaml</code> 里的 <code>status/mastery</code> 只是建课时的初始快照，<code>progress.yaml</code> 只记录有变化的节点，<code>gen_home.py</code> 负责把两者合并。② <b>同一科目同一时间只有一个写入者</b>，只有「不写同一个文件」的两支允许并行。</p></div>

<h3 id="s4c">4.3 课件三件与归属：改课件就是改源文件再重渲</h3>
<div class="tablewrap"><table>
<tr><th>文件</th><th>谁写</th><th>内容</th><th>约束来源</th></tr>
<tr><td><code>lessons/NNNN-&lt;id&gt;.md</code></td><td>learning-coach（实验说明页由 practice-evaluator 写，总控 cp）</td><td>front matter（仅 title/goal）、<code>##</code>/<code>###</code>、列表、管道表、代码围栏、<code>::: quiz</code>/<code>::: practice</code>/<code>::: figure</code>…</td><td>%FMT%、%LD%</td></tr>
<tr><td><code>lessons/NNNN-&lt;id&gt;.quiz.json</code></td><td>practice-evaluator → deliver → 总控 cp（<b>一个字不改</b>）</td><td>键 = 锚点文本（逐字）；题面、选项、why、criteria</td><td>%LP%</td></tr>
<tr><td><code>lessons/NNNN-&lt;id&gt;.html</code></td><td><code>render_lesson.py</code></td><td>学生看的页面，<b>谁也不手改</b>，下次渲染会覆盖</td><td>%ENG3%</td></tr>
</table></div>
<p>渲染器的铁律是「<b>认不出就报错</b>」：碰到未知指令、锚点缺题又没写 <code>empty_reason</code>、题库里有孤儿键、同一锚点被引用两次、配图文件不存在，都会带 <code>&lt;文件&gt;:&lt;行&gt;</code> 报错，绝不静默降级。所以总控<b>不用手工核对「题目位置 ↔ 题目」</b>，这件事交给检查脚本。</p>

<h2 id="s5">5. 设计原理：为什么这样拆</h2>
<div class="grid g2 principles">
  <div class="card principle"><h4>状态外置，上下文保持很短</h4><p>聊天式学习的死穴是会话一长上下文就装不下，关掉之后什么都不留。这里把所有状态写成文件，开场只切片读「恢复视图」。</p><p class="src">%RK%</p></div>
  <div class="card principle"><h4>总控和工人分离，只派五类活</h4><p>判断标准是：这件事需要<b>外部检索、大量生成或独立验证</b>吗？不需要就别派。信息源已经在总控上下文里的活（答疑、盘问、元数据、档案），派出去还得先转述，更慢也更费。</p><p class="src">%DISPATCH%</p></div>
  <div class="card principle"><h4>传路径，不转述</h4><p>上游产出只给绝对路径和节点 id，由下游自己去读。转述会失真，还会让总控上下文膨胀：一份题库 15 KB，一套 lab 20 KB，一份大纲 46 KB。</p><p class="src">%HANDOFF%</p></div>
  <div class="card principle"><h4>模型不写 HTML，页面交给确定性渲染</h4><p>内容格式只允许一小套块语法，块级 HTML 标签会被拦下。版式统一、可以回归测试，同时把模型最容易出错的部分挪到了代码里。</p><p class="src">%FMT%</p></div>
  <div class="card principle"><h4>靠锚点对位，不靠序号</h4><p><code>::: quiz</code> 的锚点文本是内容和题库之间唯一的接头。按序号对位，一旦两边不一致就会静默错位；按锚点对位，对不上就直接报错。</p><p class="src">%FMT%</p></div>
  <div class="card principle"><h4>一处定义，别处只给指针</h4><p>课件内核归 lesson-design，题目归 layered-practice，配图归 learning-coach 的「配图」一节，状态读写归 record-keeping。规则不会出现两份，也就不会漂移。</p><p class="src">%ENG2%</p></div>
  <div class="card principle"><h4>证据分级，出题人的防线</h4><p>出题和批改是同一个角色，所以口头确认<b>单独出现时不足以判过</b>。证据可信度从高到低：运行结果、学生自己写的测试、解释能力、口头确认。</p><p class="src">%EV%</p></div>
  <div class="card principle"><h4>验收不过，退回作者本人</h4><p>带上失败的原文证据退回，总控不代改，也不另开新角色。这样每份产物只有一个 owner，出了问题能追到人。</p><p class="src">%HANDOFF%</p></div>
</div>

<h2 id="s6">6. 在 Windows + Claude Code 上跑的注意事项</h2>
<div class="warnbox"><b>实测：这台机器上的 <code>python3</code> 是 Windows 商店的占位别名。</b>执行 <code>python3 -c "print(1)"</code> 没有任何输出，退出码是 49。可 SKILL.md 里所有脚本命令都写的是 <code>python3</code>。可选的处理方法：到「设置 → 应用 → 高级应用设置 → 应用执行别名」里关掉 python3 的别名；或者在 <code>~/.claude/CLAUDE.md</code> 里写一句「运行 StudyMate 脚本时用 <code>python</code> 代替 <code>python3</code>」。另外 <code>jsonschema</code> 目前没装，缺了它 <code>check_curriculum.py</code> 的 schema 校验会降级成 WARN。</div>
<pre class="cmd">python -m pip install jsonschema</pre>
<div class="note"><b>/tmp 暂存路径（可能踩坑）：</b>派工约定把产物落到 <code>/tmp/&lt;角色&gt;-&lt;id&gt;/deliver/</code>。在 Git Bash 里 <code>/tmp</code> 会被映射到一个 Windows 临时目录，<code>cp</code> 能正常工作；但原生 Windows 的 Python 不认识 <code>/tmp/…</code> 这种路径。如果 <code>apply_empty_reasons.py</code> 拿到的 TSV 路径是 <code>/tmp/…</code>，就可能报找不到文件。遇到这种情况，可以先用 <code>cygpath -w</code> 转换路径，或者把暂存根目录换成一个 Windows 绝对路径。</div>
<div class="note"><b>名字对齐：</b>frontmatter 里是 <code>name: study-mate-skill</code>，仓库目录却叫 <code>Study-Mate-Skill</code>。装到 <code>~/.claude/skills/</code> 时，建议把目录名也改成 <code>study-mate-skill</code>，这一点 README 里也提到了。</div>

<h2 id="s7">7. 原文档库（逐字嵌入）</h2>
<p>下面是技能包里全部约束文档、模板和示例的<b>原文</b>，在生成本页时逐字嵌入。点一下就在右侧抽屉里逐行显示，支持「原文 / 渲染」两种视图，也可以「打开本地文件」。原文有改动时重跑下面这条命令即可同步（嵌入时间：%BUILT%）：</p>
<pre class="cmd">python E:\Code\Study-Mate-Skill\docs\build_tutorial.py</pre>
<div class="doclib" id="doclib"></div>
</main>
</div>

<div class="scrim" id="scrim"></div>
<aside class="drawer" id="drawer" aria-label="原文查看器">
  <div class="dhead">
    <span class="path" id="dpath"></span>
    <button class="btn on" id="vraw">原文</button>
    <button class="btn" id="vren">渲染</button>
    <button class="btn" id="dcopy">复制</button>
    <a class="btn" id="dlocal" target="_blank">打开本地文件 ↗</a>
    <button class="btn" id="dclose">关闭 ✕</button>
    <span class="desc" id="ddesc"></span>
  </div>
  <div class="dbody" id="dbody"></div>
</aside>
<button class="btn themebtn" id="themebtn" title="切换亮 / 暗">◐ 主题</button>

<script type="application/json" id="docs-data">%DOCS_JSON%</script>
<script>
(function(){
  var DATA = JSON.parse(document.getElementById('docs-data').textContent);
  var drawer = document.getElementById('drawer'), scrim = document.getElementById('scrim');
  var body = document.getElementById('dbody'), cur = null, mode = 'raw';

  function escapeHtml(s){return s.replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}

  function renderRaw(text){
    var lines = text.split('\n'), out = [], inFence = false, inFm = false;
    for (var i=0;i<lines.length;i++){
      var l = lines[i], cls = '';
      if (i===0 && l.trim()==='---'){inFm = true; cls='fm';}
      else if (inFm){cls='fm'; if (l.trim()==='---') inFm=false;}
      else if (/^\s*(```|~~~)/.test(l)){cls='fence'; inFence=!inFence;}
      else if (inFence){cls='fence';}
      else if (/^#{1,6}\s/.test(l)){cls='h';}
      else if (/^\s*:::/.test(l)){cls='dir';}
      else if (/^\s*\|/.test(l)){cls='tbl';}
      else if (/^\s*#/.test(l)){cls='cm';}
      out.push('<div class="r" data-i="'+i+'"><span class="n">'+(i+1)+'</span><span class="c '+cls+'">'+(escapeHtml(l)||' ')+'</span></div>');
    }
    return '<div class="src">'+out.join('')+'</div>';
  }

  function highlight(find){
    if (!find || !cur) return;
    var lines = cur.text.split('\n'), start = -1;
    for (var i=0;i<lines.length;i++){ if (lines[i].indexOf(find)!==-1){start=i;break;} }
    if (start<0) return;
    var m = /^(#{1,6})\s/.exec(lines[start]), lvl = m ? m[1].length : 0, end = start;
    var inF = false;
    for (var j=start+1;j<lines.length;j++){
      if (/^\s*(```|~~~)/.test(lines[j])) inF=!inF;
      if (inF) { end=j; continue; }
      var mm = /^(#{1,6})\s/.exec(lines[j]);
      if (lvl && mm && mm[1].length<=lvl) break;
      if (!lvl && (mm || (lines[j].trim()==='' && j-start>14))) break;
      end=j;
    }
    if (!lvl) end = Math.min(end, start+30);
    for (var k=start;k<=end;k++){var r=body.querySelector('.r[data-i="'+k+'"]'); if(r) r.classList.add('hl');}
    var first = body.querySelector('.r[data-i="'+start+'"]');
    if (first) body.scrollTop = Math.max(0, first.getBoundingClientRect().top - body.getBoundingClientRect().top + body.scrollTop - 40);
  }

  function show(){
    if (!cur) return;
    document.getElementById('vraw').classList.toggle('on', mode==='raw');
    document.getElementById('vren').classList.toggle('on', mode==='ren');
    if (mode==='raw'){ body.innerHTML = renderRaw(cur.text); highlight(cur.find); }
    else {
      var t = cur.text, fm = '';
      var m = /^---\n([\s\S]*?)\n---\n/.exec(t);
      if (m){ fm = '<pre>'+escapeHtml(m[0])+'</pre>'; t = t.slice(m[0].length); }
      if (/\.ya?ml$/.test(cur.path)) { body.innerHTML = '<div class="rendered"><pre>'+escapeHtml(cur.text)+'</pre></div>'; return; }
      if (window.marked){ body.innerHTML = '<div class="rendered">'+fm+window.marked.parse(t)+'</div>'; body.scrollTop=0; }
      else body.innerHTML = '<div class="rendered"><p>渲染视图需要联网加载 marked.js（当前不可用），已回退为原文。</p></div>' + renderRaw(cur.text);
    }
  }

  function open(path, find){
    var entry = DATA[path];
    if (!entry){ window.open('../'+encodeURI(path)); return; }
    cur = {path:path, text:entry.text, find:find};
    document.getElementById('dpath').textContent = path;
    document.getElementById('ddesc').textContent = entry.desc + (find ? '　·　已定位：' + find : '');
    document.getElementById('dlocal').href = '../' + path.split('/').map(encodeURIComponent).join('/');
    drawer.classList.add('open'); scrim.classList.add('open');
    show();
  }
  function close(){ drawer.classList.remove('open'); scrim.classList.remove('open'); }

  document.addEventListener('click', function(ev){
    var t = ev.target.closest('[data-doc]');
    if (!t) return;
    if (t.tagName==='A' && (ev.ctrlKey || ev.metaKey)) return; // Ctrl+点击：直接打开本地文件
    ev.preventDefault();
    open(t.getAttribute('data-doc'), t.getAttribute('data-find'));
  });
  document.addEventListener('keydown', function(ev){
    if (ev.key==='Escape') close();
    if ((ev.key==='Enter'||ev.key===' ') && ev.target.matches && ev.target.matches('g.clk')){ ev.preventDefault(); ev.target.dispatchEvent(new MouseEvent('click',{bubbles:true})); }
  });
  scrim.onclick = close;
  document.getElementById('dclose').onclick = close;
  document.getElementById('vraw').onclick = function(){mode='raw';show();};
  document.getElementById('vren').onclick = function(){mode='ren';show();};
  document.getElementById('dcopy').onclick = function(){
    if (!cur) return;
    try { navigator.clipboard.writeText(cur.text); this.textContent='已复制'; var b=this; setTimeout(function(){b.textContent='复制'},1200);} catch(e){}
  };

  // 文档库
  var lib = document.getElementById('doclib'), group = null;
  Object.keys(DATA).forEach(function(p){
    var e = DATA[p];
    if (e.group!==group){ group=e.group; var h=document.createElement('h4'); h.textContent=group; lib.appendChild(h); }
    var b = document.createElement('button'); b.setAttribute('data-doc', p);
    b.innerHTML = '<div class="p">'+escapeHtml(p)+'</div><div class="s">'+escapeHtml(e.desc)+' · '+e.text.split('\n').length+' 行</div>';
    lib.appendChild(b);
  });

  // 主题
  var root = document.documentElement;
  try { var saved = localStorage.getItem('smt-theme'); if (saved) root.setAttribute('data-theme', saved); } catch(e){}
  document.getElementById('themebtn').onclick = function(){
    var dark = root.getAttribute('data-theme') ? root.getAttribute('data-theme')==='dark' : matchMedia('(prefers-color-scheme: dark)').matches;
    var next = dark ? 'light' : 'dark'; root.setAttribute('data-theme', next);
    try { localStorage.setItem('smt-theme', next); } catch(e){}
  };

  // 目录高亮
  var links = [].slice.call(document.querySelectorAll('nav.toc a'));
  var io = new IntersectionObserver(function(es){
    es.forEach(function(e){ if (e.isIntersecting){ links.forEach(function(a){ a.classList.toggle('on', a.getAttribute('href')==='#'+e.target.id); }); } });
  }, {rootMargin:'-10% 0px -80% 0px'});
  links.forEach(function(a){ var s=document.querySelector(a.getAttribute('href')); if(s) io.observe(s); });
})();
</script>
<script src="https://cdn.jsdelivr.net/npm/marked@12/marked.min.js" async></script>
</body>
</html>
"""


def main() -> None:
    import datetime

    data = {}
    for group, path, desc in DOCS:
        p = ROOT / path
        if not p.exists():
            print(f"跳过（不存在）：{path}")
            continue
        data[path] = {"group": group, "desc": desc, "text": p.read_text(encoding="utf-8").replace("\r\n", "\n")}

    roles = "".join(
        f'<span class="chip a">{d("references/roles/" + r + ".md", r)}</span>'
        for r in ["resource-scout", "image-scout", "curriculum-designer", "learning-coach", "practice-evaluator"]
    )
    protos = "".join(
        f'<span class="chip">{d("references/protocols/" + r + ".md", r)}</span>'
        for r in ["record-keeping", "lesson-design", "layered-practice", "evidence-check", "local-qa"]
    ) + "".join(f'<span class="chip">{d("references/" + r + ".md", r)}</span>' for r in ["课件内容格式", "工程约束"])

    rep = {
        "%SKILL%": d("SKILL.md"),
        "%SKILL_TABLE%": d("SKILL.md", "SKILL.md 开头的索引表", "| 路径 |"),
        "%MEMORY%": d("templates/MEMORY.md", "MEMORY.md"),
        "%README_INSTALL%": d("README.md", "README · 安装", "## 安装"),
        "%CONFIG%": d("studymate.config.yaml"),
        "%LOOP%": d("SKILL.md", "SKILL.md §四 学习循环", "## 四、学习循环"),
        "%DISPATCH%": d("SKILL.md", "SKILL.md §九 角色派发", "### 怎么派"),
        "%DISPATCH9%": d("SKILL.md", "SKILL.md §九", "## 九、角色派发"),
        "%HANDOFF%": d("SKILL.md", "SKILL.md · 交接与返回", "### 交接与返回"),
        "%ENG%": d("references/工程约束.md", "工程约束 §一", "## 一、两个区域"),
        "%ENG2%": d("references/工程约束.md", "工程约束 §二", "## 二、目录与规则归属"),
        "%ENG3%": d("references/protocols/record-keeping.md", "record-keeping · 课件三件", "## 课件三件与归属"),
        "%FMT%": d("references/课件内容格式.md", "课件内容格式.md"),
        "%LD%": d("references/protocols/lesson-design.md", "lesson-design"),
        "%LP%": d("references/protocols/layered-practice.md", "layered-practice"),
        "%RK%": d("references/protocols/record-keeping.md", "record-keeping · 读写规则", "## 读写规则"),
        "%EV%": d("references/protocols/evidence-check.md", "evidence-check"),
        "%ROLES%": roles,
        "%PROTOCOLS%": protos,
        "%FIG1%": fig_invoke(),
        "%FIG1B%": fig_loop(),
        "%FIG1C%": fig_seq(),
        "%FIG2B%": fig_files(),
        "%BUILT%": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    page = PAGE
    for k, v in rep.items():
        page = page.replace(k, v)
    page = page.replace("%DOCS_JSON%", json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))
    OUT.write_text(page, encoding="utf-8")
    print(f"已生成 {OUT}（嵌入 {len(data)} 份原文，{OUT.stat().st_size // 1024} KB）")


if __name__ == "__main__":
    main()
