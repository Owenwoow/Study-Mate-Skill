"""把冲突块逐块替换成给定文本。
用法：python fill.py <文件> <块文本文件>
块文本文件里各块用一行 `%%%%` 分隔，按顺序对应文件里的冲突块；某块写 `@@KEEP` 则保留冲突标记。
"""
import sys

path, blocks_path = sys.argv[1], sys.argv[2]
blocks = open(blocks_path, encoding='utf-8').read().split('\n%%%%\n')
blocks = [b.strip('\n') for b in blocks]
lines = open(path, encoding='utf-8').read().split('\n')
out, i, n = [], 0, 0
while i < len(lines):
    if not lines[i].startswith('<<<<<<< '):
        out.append(lines[i]); i += 1; continue
    j = i
    while not lines[j].startswith('>>>>>>> '):
        j += 1
    if n >= len(blocks):
        raise SystemExit(f'{path}: 冲突块 {n + 1} 没有给替换文本')
    if blocks[n] == '@@KEEP':
        out.extend(lines[i:j + 1])
    else:
        out.extend(blocks[n].split('\n'))
    n += 1; i = j + 1
if n != len(blocks):
    raise SystemExit(f'{path}: 冲突块 {n} 个，给了 {len(blocks)} 段替换文本')
open(path, 'w', encoding='utf-8', newline='').write('\n'.join(out))
print(f'{path}: 替换 {n} 块')
