#!/usr/bin/env python3
"""校验技能包文档的 frontmatter：解析、name 与文件（或目录）名一致、description 非空。

用法：
  python3 scripts/check_skill.py                    # 校验默认范围：SKILL.md + references/{roles,protocols}/*.md
  python3 scripts/check_skill.py SKILL.md           # 校验单个文件
  python3 scripts/check_skill.py references/roles   # 校验目录下全部 .md

技能入口是 `<root>/SKILL.md`（`name` 必须等于技能目录名）；
角色与协议是 `references/roles/<名字>.md`、`references/protocols/<名字>.md`（`name` 必须等于文件名主干）。
这些是**参考规格文档**，由 SKILL.md 按路径读取，不作为独立技能注册——所以只有 name / description 两项要求。
"""
import glob
import os
import re
import sys

import yaml

FRONTMATTER = re.compile(r'^---\r?\n(.*?)\r?\n---\r?\n', re.S)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read_frontmatter(path):
    with open(path, encoding='utf-8-sig') as handle:
        text = handle.read()
    match = FRONTMATTER.match(text)
    if not match:
        raise ValueError('frontmatter 缺失或格式不对（需以 --- 开头并闭合）')
    meta = yaml.safe_load(match.group(1))
    if not isinstance(meta, dict):
        raise ValueError('frontmatter 必须是 YAML 映射')
    return meta


def default_paths():
    paths = [os.path.join(ROOT, 'SKILL.md')]
    for group in ('roles', 'protocols'):
        paths.extend(sorted(glob.glob(os.path.join(ROOT, 'references', group, '*.md'))))
    return [p for p in paths if os.path.isfile(p)]


def expand(argument):
    """把参数展开成待校验的 .md 文件列表（目录取其下全部 .md）。"""
    if os.path.isdir(argument):
        return sorted(glob.glob(os.path.join(argument, '*.md')))
    return [argument]


def expected_name(path):
    """技能入口用所在目录名；参考规格用文件名主干。"""
    if os.path.basename(path) == 'SKILL.md':
        return os.path.basename(os.path.dirname(os.path.normpath(path)))
    return os.path.splitext(os.path.basename(path))[0]


def normalize(name):
    """比较前归一：小写、下划线与空格都当短横线（目录名可能带大写，frontmatter 走小写短横线约定）。"""
    return str(name).strip().lower().replace('_', '-').replace(' ', '-')


def main(argv):
    if any(a in ('-h', '--help') for a in argv):
        print(__doc__)
        return 0
    arguments = [a for a in argv if not a.startswith('-')]
    paths = default_paths() if not arguments else [p for a in arguments for p in expand(a)]
    if not paths:
        raise SystemExit('没有可校验的文档（检查路径是否写对）\n\n' + __doc__)

    failed = 0
    for path in paths:
        try:
            meta = read_frontmatter(path)
        except (OSError, UnicodeDecodeError, yaml.YAMLError, ValueError) as exc:
            failed += 1
            print(f'FAIL {path}: {exc}')
            continue
        want = expected_name(path)
        problems = []
        if normalize(meta.get('name')) != normalize(want):
            problems.append(f"name={meta.get('name')!r} 与 {want!r} 不一致")
        if not meta.get('description'):
            problems.append('description 缺失')
        if problems:
            failed += 1
            print(f'FAIL {path}: ' + '；'.join(problems))
        else:
            print(f'OK   {path}')
    print(f'\n{len(paths) - failed}/{len(paths)} 份文档通过')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
