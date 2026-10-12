#!/usr/bin/env python3
"""图片库校验器 `scripts/check_pool.py` 的回归测试，10 个场景。

图片库的落点是硬口径（R15）：图片在 `<subject>/assets/img/pool/`、索引是图片库目录的**兄弟**
`<subject>/assets/img/pool.md`、表头七列逐字固定。每个场景自造一个临时科目，只改该场景要测的
那一处偏差（必要时分散在两行），断言「该拦的拦住、该放行的放行」——校验器是"命名必须能检索"
的保险，坏图片库必须过不去。

`尺寸` 列是「宽×高」像素，**不参与**体积判定（体积看磁盘上的文件字节），但要与**文件头**里的真实
宽高一致（⑥）：造图时写真的 PNG/JPEG/GIF/WebP 文件头，合格场景给大像素值、超体积场景给小像素值。

用法：python3 scripts/tests/test_pool.py
"""
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fixtures  # noqa: E402

HEADER = '| 文件 | 主题标签 | 一句话说明 | 来源 URL | 许可 | 尺寸 | 抓取日期 |'
SEPARATOR = '| --- | --- | --- | --- | --- | --- | --- |'
GAPS = '\n## Gaps\n\n- 缺「指针运算」的图：站点上没有宽度 ≥400px 的现成图\n'

IMG_A = '数组-内存布局-连续存储-cppreference-01.png'
IMG_B = '哈希表-冲突处理-链地址法-oi-wiki-02.png'
# 形状合规但超过 60 字符：字符集、分段、`<NN>` 都对，只有长度超——必须按长度拦
LONG_NAME = ('数组-内存布局-连续存储-'
             + '越界访问与指针算术的边界情况' * 3 + '-cppreference-01.png')
SHORT_HEADER = HEADER.replace('| 许可 ', '')          # 少一列：用来测「索引缺列」


def row(name, topic='数组 · 内存布局', note='连续存储的内存布局', url='https://example.com/page',
        license_='CC BY-SA 4.0', size='640×360', date='2026-09-19'):
    """拼一行索引（七格，与表头同序）。"""
    return f'| {name} | {topic} | {note} | {url} | {license_} | {size} | {date} |'


def short_row(name):
    """少一格的索引行：没有「许可」那格（与 SHORT_HEADER 配对）。"""
    return f'| {name} | 数组 · 内存布局 | 连续存储的内存布局 | https://example.com/page | 640×360 | 2026-09-19 |'


def index(text, header=HEADER):
    """索引全文：表头 + 分隔行 + 数据行 + 末尾 Gaps。"""
    return header + '\n' + SEPARATOR + '\n' + text.rstrip('\n') + '\n' + GAPS


SCENARIOS = []


def scenario(label, text, files, want_fail, must=None, must_not=None):
    SCENARIOS.append({'label': label, 'text': text, 'files': files,
                      'want_fail': want_fail, 'must': must or [], 'must_not': must_not or []})


# 1 合格：分隔行要跳过（当成数据行就会报 文件名不合规）、`尺寸` 是大像素值而文件很小
scenario('合格图片库通过（含分隔行与 Gaps）',
         index(row(IMG_A, size='4000×3000') + '\n' + row(IMG_B, size='800×600')),
         {IMG_A: (400, 4000, 3000), IMG_B: (900, 800, 600)}, False, must=['OK', '（2 张）'],
         must_not=['文件名不合规', '文件缺失', '为空', '超体积'])

# 2 文件名：`图1.png` 看不出主题、`LONG_NAME` 超过 60 字符——两条都要报，且带行号
scenario('文件名不合规拦（含超长）',
         index(row('图1.png') + '\n' + row(LONG_NAME)),
         {'图1.png': 400, LONG_NAME: 400}, True,
         must=['文件名不合规', 'pool.md:3', 'pool.md:4', f'{len(LONG_NAME)} 字符'],
         must_not=['文件缺失', '超体积'])

# 3 缺列：表头与数据行都没有「许可」这一列
scenario('缺列拦（表头少「许可」）',
         index(short_row(IMG_A), header=SHORT_HEADER),
         {IMG_A: 400}, True, must=['索引缺列', '许可'],
         must_not=['文件名不合规', '文件缺失', '超体积'])

# 4 文件缺失：索引里写了，图片库里没有
scenario('文件缺失拦',
         index(row(IMG_A)),
         {}, True, must=['文件缺失', IMG_A],
         must_not=['文件名不合规', '超体积'])

# 5 许可空：`许可` 那格是空的（页面没标注也要写「未标注」）。同一场景的第二行省掉 `抓取日期`：
# 收口后 ④ 是三列齐查，两行各缺一格、各报一条（行号证明两行都被查过）
scenario('许可空拦',
         index(row(IMG_A, license_='') + '\n' + row(IMG_B, date='')),
         {IMG_A: 400, IMG_B: 400}, True,
         must=['pool.md:3', '`许可` 为空', 'pool.md:4', '`抓取日期` 为空'],
         must_not=['文件名不合规', '文件缺失', '超体积'])

# 6 超体积：201 KB（`尺寸` 写 100×100 也救不了——体积只看文件字节）；消息报字节，不四舍五入。
# 上限 500 KB 与课件硬约束（`lesson-design`「配图」行、`image-scout` 过滤步）同一个数：
# 过了这道闸门的图必然也过得了课件那一关。
scenario('超体积拦（上限 500 KB）',
         index(row(IMG_B, size='100×100')),
         {IMG_B: (501 * 1024, 100, 100)}, True, must=['超体积', f'{501 * 1024} B > {500 * 1024} B'],
         must_not=['文件名不合规', '文件缺失'])


# 7 文件头：尺寸照文件头写；JPEG/GIF/WebP 也认；扩展名与真实格式不符要拦
scenario('尺寸与文件头对不上拦（页面标注被缩放过）',
         index(row(IMG_A, size='640×360')), {IMG_A: (400, 1280, 720)}, True,
         must=['`尺寸` 与文件头对不上', '1280×720'], must_not=['文件名不合规', '超体积'])
scenario('JPEG / GIF / WebP 文件头都认（尺寸一致放行）',
         index(row('数组-内存布局-连续存储-cppreference-03.jpg', size='800×450') + '\n'
               + row('数组-内存布局-连续存储-cppreference-04.gif', size='500×300') + '\n'
               + row('数组-内存布局-连续存储-cppreference-05.webp', size='600×400')),
         {'数组-内存布局-连续存储-cppreference-03.jpg': (400, 800, 450, 'jpeg'),
          '数组-内存布局-连续存储-cppreference-04.gif': (400, 500, 300, 'gif'),
          '数组-内存布局-连续存储-cppreference-05.webp': (400, 600, 400, 'webp')},
         False, must=['OK', '（3 张）'])
scenario('扩展名与真实格式不符拦（.png 里装的是 JPEG）',
         index(row(IMG_A, size='640×360')), {IMG_A: (400, 640, 360, 'jpeg')}, True,
         must=['格式与扩展名不符', 'jpeg'])
scenario('尺寸写法不对拦（要 宽×高）',
         index(row(IMG_A, size='640 宽')), {IMG_A: (400, 640, 360)}, True,
         must=['`尺寸` 要写成 宽×高'])


def image_bytes(size, width=640, height=360, fmt='png'):
    '''合成一个只有文件头的图片（够 check_pool 读出格式与宽高），再补零到 size 字节。'''
    if fmt == 'png':
        head = (b'\x89PNG\r\n\x1a\n' + (13).to_bytes(4, 'big') + b'IHDR'
                + width.to_bytes(4, 'big') + height.to_bytes(4, 'big') + b'\x08\x02\x00\x00\x00')
    elif fmt == 'jpeg':
        head = (b'\xff\xd8' + b'\xff\xe0' + (16).to_bytes(2, 'big') + b'JFIF\x00' + b'\x00' * 9
                + b'\xff\xc0' + (17).to_bytes(2, 'big') + b'\x08'
                + height.to_bytes(2, 'big') + width.to_bytes(2, 'big') + b'\x03' + b'\x00' * 9)
    elif fmt == 'gif':
        head = b'GIF89a' + width.to_bytes(2, 'little') + height.to_bytes(2, 'little')
    else:  # webp（VP8X：画布宽高减一、各 3 字节小端）
        head = (b'RIFF' + b'\x00' * 4 + b'WEBPVP8X' + b'\x00' * 8
                + (width - 1).to_bytes(3, 'little') + (height - 1).to_bytes(3, 'little'))
    return head + b'\x00' * max(size - len(head), 0)


def build(subject, item):
    """按场景重建图片库与索引：清空目录、写图片文件、写 pool.md。"""
    pool = os.path.join(subject, 'assets', 'img', 'pool')
    index_path = os.path.join(subject, 'assets', 'img', 'pool.md')
    shutil.rmtree(pool, ignore_errors=True)
    os.makedirs(pool, exist_ok=True)
    if os.path.exists(index_path):
        os.remove(index_path)
    for name, spec in item['files'].items():
        spec = spec if isinstance(spec, tuple) else (spec,)
        with open(os.path.join(pool, name), 'wb') as handle:
            handle.write(image_bytes(*spec))
    with open(index_path, 'w', encoding='utf-8') as handle:
        handle.write(item['text'])


def main():
    tmp = tempfile.mkdtemp(prefix='smtest-pool-')
    subject = fixtures.write_subject(tmp)
    failures = 0
    for item in SCENARIOS:
        build(subject, item)
        code, out = fixtures.run_pool(subject)
        ok = (code != 0) == item['want_fail']
        ok = ok and all(phrase in out for phrase in item['must'])
        ok = ok and all(phrase not in out for phrase in item['must_not'])
        failures += not ok
        fixtures.check(item['label'], ok, out if not ok else f'校验器={"FAIL" if code else "OK"}')
    total = len(SCENARIOS)
    print(f'\n{total - failures}/{total} 通过')
    shutil.rmtree(tmp, ignore_errors=True)
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
