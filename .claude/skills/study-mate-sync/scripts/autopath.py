"""自动解决「只差文档路径写法」的冲突块：上游侧把 docs/{规范,使用,设计}/X.md 换成本地写法后与本地侧相同 → 取本地。
用法：python autopath.py <文件...>
"""
import re
import sys

SUBS = [
    (re.compile(r'docs/(?:规范|使用|设计)/(课件内容格式|工程约束|使用说明|设计方案)\.md'), r'references/\1.md'),
    (re.compile(r'docs/(课件内容格式|工程约束|使用说明|设计方案)\.md'), r'references/\1.md'),
]


def norm(text):
    for pattern, repl in SUBS:
        text = pattern.sub(repl, text)
    return text


for path in sys.argv[1:]:
    lines = open(path, encoding='utf-8').read().split('\n')
    out, i, solved, left = [], 0, 0, 0
    while i < len(lines):
        if not lines[i].startswith('<<<<<<< '):
            out.append(lines[i]); i += 1; continue
        j = i + 1
        while not lines[j].startswith('======='):
            j += 1
        k = j + 1
        while not lines[k].startswith('>>>>>>> '):
            k += 1
        ours, theirs = lines[i + 1:j], lines[j + 1:k]
        if '\n'.join(ours) == norm('\n'.join(theirs)):
            out.extend(ours); solved += 1
        else:
            out.extend(lines[i:k + 1]); left += 1
        i = k + 1
    open(path, 'w', encoding='utf-8', newline='').write('\n'.join(out))
    print(f'{path}: 自动解决 {solved}，剩 {left}')
