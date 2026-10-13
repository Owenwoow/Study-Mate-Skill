"""按块解决 merge-file 冲突。
用法：python resolve.py <文件> <选择...>
选择逐块对应：o=本地 t=上游新版 ot=先本地后上游 to=先上游后本地 k=保留冲突标记（之后手改）
"""
import sys

path, choices = sys.argv[1], sys.argv[2:]
with open(path, encoding='utf-8', newline='') as f:
    lines = f.read().split('\n')

out, i, n = [], 0, 0
while i < len(lines):
    line = lines[i]
    if not line.startswith('<<<<<<< '):
        out.append(line); i += 1; continue
    ours, theirs, j = [], [], i + 1
    while not lines[j].startswith('======='):
        ours.append(lines[j]); j += 1
    j += 1
    while not lines[j].startswith('>>>>>>> '):
        theirs.append(lines[j]); j += 1
    c = choices[n] if n < len(choices) else 'k'
    if c == 'k':
        out.extend(lines[i:j + 1])
    else:
        for side in c:
            out.extend(ours if side == 'o' else theirs)
    n += 1; i = j + 1

with open(path, 'w', encoding='utf-8', newline='') as f:
    f.write('\n'.join(out))
left = sum(1 for l in out if l.startswith('<<<<<<< '))
print(f'{path}: {n} 块，剩余冲突 {left}')
