#!/usr/bin/env python3
"""技能包结构闸门：入口与参考规格齐全、SKILL.md 的关键规则在位、交叉引用不断链、无宿主专有残留。

这是把 DSH 原版的「提示词压缩回归」换成**宿主无关**版本后的产物：
原版钉的是 11 个 `SKILL.md` 里的 417 条措辞；通用版只有 1 个入口 + 11 份参考规格，
所以这里钉三类东西——

  ① 包结构：入口、5 个角色、6 个协议、4 份约束文档、8 份 schema、15 个脚本、模板齐全；
  ② 规则在位：SKILL.md 里承载可执行规则的片段（阈值、字段名、文件名、命令、时机、禁止项）
     逐条必须在（压缩/改写时不许丢规则）；
  ③ 一致性与洁净：SKILL.md 提到的每个 `references/*.md` 与 `scripts/*.py` 都真实存在；
     包内不再出现宿主专有标记（`~/.dsh`、`disable-model-invocation`、`ask_user_question`、
     `subagent_fork`、`install.sh` 等），避免把原宿主的安装方式带进通用包。

用法：python3 scripts/tests/test_package.py
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ROLES = ('resource-scout', 'image-scout', 'curriculum-designer', 'learning-coach', 'practice-evaluator')
PROTOCOLS = ('learning-discovery', 'lesson-design', 'layered-practice', 'evidence-check', 'local-qa',
             'record-keeping')
DOCS = ('课件内容格式.md', '工程约束.md', '使用说明.md', '设计方案.md', '安装与迁移.md', 'Agent交接协议.md')
SCHEMAS = ('curriculum.schema.json', 'progress.schema.json', 'assessment.schema.json',
           'session-summary.schema.json', 'subject.schema.json', 'agent-handoff.schema.json',
           'misconceptions.schema.json', 'question.schema.json')
SCRIPTS = ('gen_home.py', 'render_lesson.py', 'check_lesson.py', 'check_curriculum.py',
           'check_pool.py', 'check_skill.py', 'preview_templates.py',
           'apply_empty_reasons.py', 'renumber_lessons.py',
           'curriculum.py', 'lessonfile.py', 'lessonfmt.py', 'pagetpl.py', 'statuses.py', 'check_handoff.py')
TEMPLATES = ('lesson.html', 'home-index.html', 'subject-index.html',
             'MEMORY.md', 'MISSION.md', 'RESOURCES.md', 'GLOSSARY.md', 'subject.yaml')

# SKILL.md 里承载规则的片段（不是文风词：阈值 / 字段名 / 文件名 / 命令 / 时机 / 禁止项）
SKILL_RULES = [
    # 开场与工作区
    ('开场先定位工作区（三级定位）', 'LEARN_WORKSPACE'),
    ('工作区配置文件', 'studymate.config.yaml'),
    ('按恢复视图读状态', '恢复视图'),
    ('首次使用问三件事', '想学什么'),
    ('新科目落地：lab/ 与 sources/ 不预建', '`lab/` 与 `sources/` 不预建'),
    ('MISSION 两节来自盘问第一问', 'Success looks like'),
    ('先派 resource-scout 收集资料', '`resource-scout` 收集资料'),
    ('资源清单：角色落 deliver/、总控 cp 落位', '<subject_path>/.stage/resource-scout-<slug>/deliver/RESOURCES.md'),
    ('建池与拟大纲并行', '建池与拟大纲并行'),
    ('图片库为空不阻塞', '图片库为空不阻塞'),
    ('progress 初始值', 'misconceptions: []'),
    ('project 只写 current', 'project` 只写 `current'),
    ('过 progress schema', 'progress.schema.json'),
    ('报告要给下一步', '不许只报告就停'),
    # 盘问
    ('盘问画设计树/分轮', 'frontier'),
    ('推荐项第一', '(Recommended)'),
    ('必问：目的追问到具体', '追问到具体'),
    ('必问：目标层级（档位）', '能独立做项目 / 精通'),
    ('必问：前置基础按科目问具体项', '**按科目问具体项**'),
    ('必问：项目给 3 个以上候选', '3 个以上候选'),
    ('必问：实验载体先随派工交给 practice-evaluator', '先随派工 prompt 交给 `practice-evaluator`'),
    ('前置基础落 Constraints 与共享记忆', '`MISSION.md` 的 `## Constraints`'),
    ('事实不问学生，自评必须问', '**前置基础是学生自评、不是事实**'),
    ('结束标准 frontier 空', 'frontier 空'),
    # 对话节奏
    ('每轮以「下一步」收尾', '**下一步**：<谁做什么> —— <怎么触发>'),
    ('不重复问同一个问题', '不重复问同一个问题'),
    ('学生说今天到这别再推', '今天到这'),
    # 学习循环
    ('节点状态置学习中', '学习中'),
    ('出题串行交接：内容文件落盘后才派出题人', '锚点是讲解的产物，内容文件没落盘就先别派出题人'),
    ('写盘时题面与答案一个字都不改', '题面与答案一个字都不改'),
    ('empty_reason 由总控用脚本打进内容文件', 'scripts/apply_empty_reasons.py'),
    ('lab 交付态自查（参考解全绿、留白态非零退出）', '参考解全绿、任务/留白态非零退出'),
    ('总控跑渲染器出页面', 'python3 <root>/scripts/render_lesson.py <subject_path> <节点id>'),
    ('渲染失败按 <文件>:<行> 打回', '按 `<文件>:<行>` 打回'),
    ('实验课说明页 cp 到位后走渲染器', '`cp` 说明页到 `lessons/<序号>-<节点id>.md`'),
    ('实验课与概念课同一条路', '跟概念课同一条路'),
    ('实验课输入带被验收节点', '被验收节点'),
    ('过检查命令', 'check_lesson.py'),
    ('FAIL 按归属打回', '`FAIL` 按归属打回'),
    ('通过后给出可点页面 + 绝对路径', '绝对路径'),
    ('验收只在实验课', '只在 `kind: 实验` 的课派'),
    ('阶段评估已删', '阶段评估已删'),
    ('考考我补一份练习', '考考我'),
    ('非验收点给保守进度（最多到学习中）', '状态最多到「学习中」'),
    ('通过则置已学完、结论写学习记录', '该节点置为「已学完」'),
    ('实验课置位规则', '`record-keeping` 置位'),
    ('部分通过记误解（只记一处）', '只记 `misconceptions.yaml` 一处'),
    ('两次无效降一档', '降一档'),
    ('局部提问你亲自答', 'local-qa'),
    # 元数据与使命
    ('四份元数据表', 'GLOSSARY.md'),
    ('使命变更', '使命变更'),
    ('会话结束写摘要', 'session-summary'),
    # 派发
    ('只派五类活', '只派五类活'),
    ('派工只写三样（规格是权威、只给值）', 'prompt 只写三样'),
    ('三条边界一句', '三条边界'),
    ('上游产出给路径不转述', '上游产出给路径，不转述'),
    ('搬运用 shell，不转抄', '搬运用 shell，不转抄'),
    ('对位靠锚点，不靠序号', '对位靠锚点，不靠序号'),
    ('同一科目同时只有一个写入者', '同一科目同时只有一个写入者'),
    ('交付带可复算的规模', '可复算的规模'),
    ('验收不过退回原产出者', '退回给产出它的那个角色自己改'),
    # 宿主无关的两条路
    ('无子代理能力时自己串行做', '没有子代理能力'),
    ('用宿主的提问能力', '用户提问能力'),
    ('用宿主的结果呈现能力', '结果呈现能力'),
    # 边界
    ('只在工作区写学习文件', '只在 `<LEARN_WORKSPACE>/` 下写学习文件'),
    ('刷新主页一条命令', 'python3 <root>/scripts/gen_home.py'),
]

# 宿主专有标记：通用包里不该再出现
FORBIDDEN = (
    '~/.dsh',
    'disable-model-invocation',
    'user-invocable',
    'ask_user_question',
    'subagent_fork',
    'install.sh',
    'install.ps1',
    'cordis',
    '@yunmiao',
    'agent-presets',
)

# 扫描范围（README.md 不扫：它有一节专门对照 DSH 原版，会合法地提到这些词；
# 本文件不扫：FORBIDDEN 的字面量就写在下面）
SCAN_DIRS = ('references', 'scripts', 'templates')
SCAN_FILES = ('SKILL.md',)
SCAN_SKIP = {'scripts/tests/test_package.py'}


class Reporter:
    def __init__(self):
        self.failed = 0
        self.total = 0

    def ok(self, label, passed, detail=''):
        self.total += 1
        if passed:
            print(f'  PASS {label}')
        else:
            self.failed += 1
            print(f'  FAIL {label}' + (f'  —— {detail}' if detail else ''))


def read(relative):
    with open(os.path.join(ROOT, relative), encoding='utf-8') as handle:
        return handle.read()


def walk_scanned():
    for name in SCAN_FILES:
        yield name, read(name)
    for base in SCAN_DIRS:
        for dirpath, dirnames, filenames in os.walk(os.path.join(ROOT, base)):
            dirnames[:] = [d for d in dirnames if d != '__pycache__']
            for filename in filenames:
                if not filename.endswith(('.md', '.py', '.js', '.mjs', '.html', '.yaml', '.yml', '.sh')):
                    continue
                full = os.path.join(dirpath, filename)
                relative = os.path.relpath(full, ROOT).replace('\\', '/')
                if relative in SCAN_SKIP:
                    continue
                with open(full, encoding='utf-8', errors='replace') as handle:
                    yield relative, handle.read()


def main():
    r = Reporter()
    print('① 包结构')
    for name, text in (('SKILL.md', read('SKILL.md')),):
        match = re.match(r'^---\r?\n(.*?)\r?\n---\r?\n', text, re.S)
        r.ok('入口 SKILL.md 有 frontmatter', bool(match))
        front = match.group(1) if match else ''
        r.ok('入口有 name', bool(re.search(r'^name:\s*\S', front, re.M)))
        r.ok('入口有 description', bool(re.search(r'^description:\s*\S', front, re.M)))
    for group, names in (('references/roles', ROLES), ('references/protocols', PROTOCOLS)):
        for name in names:
            r.ok(f'{group}/{name}.md 在', os.path.isfile(os.path.join(ROOT, group, f'{name}.md')))
    for name in DOCS:
        r.ok(f'references/{name} 在', os.path.isfile(os.path.join(ROOT, 'references', name)))
    for name in SCHEMAS:
        r.ok(f'schemas/{name} 在', os.path.isfile(os.path.join(ROOT, 'schemas', name)))
    for name in SCRIPTS:
        r.ok(f'scripts/{name} 在', os.path.isfile(os.path.join(ROOT, 'scripts', name)))
    for name in TEMPLATES:
        r.ok(f'templates/{name} 在', os.path.isfile(os.path.join(ROOT, 'templates', name)))
    r.ok('studymate.config.yaml 在', os.path.isfile(os.path.join(ROOT, 'studymate.config.yaml')))
    r.ok('LICENSE 在', os.path.isfile(os.path.join(ROOT, 'LICENSE')))

    print('\n② SKILL.md 规则在位')
    skill = read('SKILL.md')
    missing = [(label, frag) for label, frag in SKILL_RULES if frag not in skill]
    for label, frag in SKILL_RULES:
        r.ok(label, frag in skill, f'找的是 {frag!r}')
    print(f'  —— {len(SKILL_RULES) - len(missing)}/{len(SKILL_RULES)} 条规则在位')

    print('\n③ 交叉引用与洁净度')
    for ref in sorted(set(re.findall(r'references/[A-Za-z0-9_\u4e00-\u9fa5./-]+\.md', skill))):
        r.ok(f'SKILL.md 引用 {ref} 存在', os.path.isfile(os.path.join(ROOT, ref)))
    for ref in sorted(set(re.findall(r'scripts/[A-Za-z0-9_.]+\.py', skill))):
        r.ok(f'SKILL.md 引用 {ref} 存在', os.path.isfile(os.path.join(ROOT, ref)))
    hits = []
    for relative, text in walk_scanned():
        for marker in FORBIDDEN:
            if marker in text:
                hits.append(f'{relative}: {marker}')
    r.ok('包内无宿主专有残留', not hits, '；'.join(hits[:8]))

    print('\n' + '─' * 30)
    print(f'{r.total - r.failed}/{r.total} 项通过')
    return 1 if r.failed else 0


if __name__ == '__main__':
    sys.exit(main())
