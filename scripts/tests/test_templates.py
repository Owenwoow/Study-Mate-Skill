#!/usr/bin/env python3
"""模板与规格一致：`templates/` 的分节名与键，必须和提示词/schema 写的一致。

为什么单独有这道：规格是散文（写在 SKILL 与 `docs/` 里），模板是另一份文件，两者之间没有测试
连着。真出过事——`templates/GLOSSARY.md` 一直写 `## Terms`，而规格（`SKILL.md`）、
`learning-system`、`image-scout` 三处都按 `## 待掌握`／`## 已掌握` 两节读词：照模板建出来的术语表，
「采图」查不到主题词、主页也没有那两节可读。这类漂移不会有任何报错，只能靠交叉阅读发现。

所以这道**两边一起钉**：规格里写着的分节，模板里必须真有；模板的键，schema 里必须真有。
规格那边改了名而模板没跟、或者模板自创了键，都会红。

用法：python3 scripts/tests/test_templates.py
"""
import json
import re
import sys
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
REPO = TESTS_DIR.parents[1]
TEMPLATES = REPO / 'templates'

failures = 0
total = 0


def check(label, ok, detail=''):
    global failures, total
    total += 1
    print(f"{'PASS' if ok else 'FAIL'}  {label}" + (f'  — {detail}' if detail and not ok else ''))
    failures += not ok


def read(path):
    return (REPO / path).read_text(encoding='utf-8')


def has_all(text, needles):
    """返回 (全都在, 缺哪些)。"""
    missing = [needle for needle in needles if needle not in text]
    return not missing, missing


def main():
    # ── 一、规格侧：这些分节名是规格定的（改规格要先改这里，再同步模板）────────
    ok, missing = has_all(read('SKILL.md'), ['## 待掌握', '## 已掌握'])
    check('规格仍要求术语表两节（SKILL.md）', ok, f'缺 {missing}')

    ok, missing = has_all(read('SKILL.md'),
                          ['## Why', '## Success looks like', '## Constraints', '## Out of scope'])
    check('规格仍要求使命四节（SKILL.md 建课顺序）', ok, f'缺 {missing}')

    # 总控点名的落点必须在模板里有家：说「共享记忆」的某个条目，模板里就得真有那串字，
    # 否则学生按指示去找、找不到（「各领域当前水平」是「我是谁」下面的一个条目，不是小节）。
    system = read('SKILL.md')
    memory_tpl = read('templates/MEMORY.md')
    for term in ['各领域当前水平']:
        check(f'总控点名的「{term}」在 templates/MEMORY.md 里有家',
              term in system and term in memory_tpl,
              f'总控{"有" if term in system else "没有"}、模板{"有" if term in memory_tpl else "没有"}')

    ok, missing = has_all(read('references/使用说明.md'),
                          ['我是谁 / 教学偏好 / 学习习惯 / 跨科目观察'])
    check('规格仍列出共享记忆四节（references/使用说明.md §六）', ok, f'缺 {missing}')

    # ── 二、模板侧：照着上面的规格逐条对 ──────────────────────────────────
    ok, missing = has_all(read('templates/GLOSSARY.md'), ['## 待掌握', '## 已掌握'])
    check('templates/GLOSSARY.md 有「待掌握 / 已掌握」两节', ok, f'缺 {missing}')

    ok, missing = has_all(read('templates/MISSION.md'),
                          ['## Why', '## Success looks like', '## Constraints'])
    check('templates/MISSION.md 有使命三节', ok, f'缺 {missing}')

    ok, missing = has_all(read('templates/MEMORY.md'),
                          ['## 我是谁', '## 教学偏好', '## 学习习惯', '## 跨科目观察'])
    check('templates/MEMORY.md 有共享记忆四节', ok, f'缺 {missing}')

    # 科目档案的键：模板与 schema 必须完全一致（模板自创键 = schema 校验会拦下来，
    # schema 加了键而模板没跟 = 学生新建科目时少写一个必填字段）
    schema = json.loads(read('schemas/subject.schema.json'))
    schema_keys = set(schema.get('properties', {}))
    try:
        import yaml
    except ImportError:      # pragma: no cover - 环境缺 pyyaml 时只跳过这一条
        check('templates/subject.yaml 的键与 subject.schema.json 一致（跳过：没有 pyyaml）', True)
    else:
        template_keys = set(yaml.safe_load(read('templates/subject.yaml')) or {})
        check('templates/subject.yaml 的键与 subject.schema.json 完全一致',
              template_keys == schema_keys,
              f'模板多 {sorted(template_keys - schema_keys)} / 模板缺 {sorted(schema_keys - template_keys)}')

    # status 的取值：模板里那个值必须是 schema enum 里的一员（写错的话建课第一步就过不了校验）
    status = (yaml.safe_load(read('templates/subject.yaml')) or {}).get('status')
    check(f'templates/subject.yaml 的 status 取值合法（{status}）',
          status in (schema['properties']['status'].get('enum') or []),
          f'不在 {schema["properties"]["status"].get("enum")} 里')

    # ── 三、围栏语言：语法模块认可的着色标签必须与前端配色表一一对应 ──────────
    # 真出过事——`python` 在渲染器里畅通无阻（原样写进 data-lang），而 learn-theme.js
    # 的 LANGS 没有这个键：Python 课件的 36 个代码块全部不上色，且没有任何报错。
    # 白名单现在住在 scripts/lessonfmt.py（围栏判定的唯一口径）。
    source = read('scripts/lessonfmt.py')
    match = re.search(r'^COLORED_LANGS = \(([^)]*)\)', source, re.M)
    check('语法模块仍有 COLORED_LANGS 白名单', match is not None)
    colored = re.findall(r"'([a-z][a-z0-9_]*)'", match.group(1)) if match else []

    js = read('templates/assets/learn-theme.js')
    # 用带守卫的 search 取块：锚点漂成 `const LANGS = {` 时给出标签化的 FAIL，而不是 IndexError。
    match_js = re.search(r'var LANGS = \{([\s\S]*?)\n  \};', js)
    check('前端仍有 var LANGS 定义', match_js is not None)
    keys = re.findall(r'^    ([a-z][a-z0-9_]*): function', match_js.group(1), re.M) if match_js else []

    check('前端配色表与语法模块的白名单逐个相等',
          sorted(keys) == sorted(colored),
          f'前端={sorted(keys)} 语法模块={sorted(colored)}')
    check('python 两边都有', 'python' in keys and 'python' in colored)

    # ── 四、题型：quiz.js 认的题型与 question.schema.json 的词表逐个相等 ──────────────
    # 词表多一种而前端不认 = 出题人照规格出的题在页面上全走「数据不完整」兜底，且没有任何报错。
    schema_kinds = json.loads(read('schemas/question.schema.json'))['properties']['kind']['enum']
    quiz = read('templates/assets/quiz.js')
    match_kinds = re.search(r'var FIELD_GROUPS = \{([\s\S]*?)\n  \};', quiz)
    check('quiz.js 仍有 FIELD_GROUPS 题型表', match_kinds is not None)
    quiz_kinds = re.findall(r"^    '([^']+)':", match_kinds.group(1), re.M) if match_kinds else []
    check('quiz.js 的题型与 question.schema.json 逐个相等',
          sorted(quiz_kinds) == sorted(schema_kinds), f'前端={quiz_kinds} schema={schema_kinds}')

    # ── 五、templates/assets 顶层只放清单里的东西（清单只有一份：scripts/lessonfile.py）──
    sys.path.insert(0, str(REPO / 'scripts'))
    import lessonfile

    listed = (set(lessonfile.SHARED_DIRS) | set(lessonfile.SHARED_FILES)
              | set(lessonfile.SUBJECT_FILES) | {lessonfile.ASSET_DOC})
    present = {entry.name for entry in (REPO / 'templates' / 'assets').iterdir()}
    check('templates/assets 顶层每一项都登记在清单里（新文件不登记就没人拷也没人守）',
          present == listed,
          f'清单外 {sorted(present - listed)} / 清单里却没有 {sorted(listed - present)}')

    print(f'\n{total - failures}/{total} 通过')
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
