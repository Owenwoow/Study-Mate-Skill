#!/usr/bin/env python3
"""按 schemas/curriculum.schema.json 校验 curriculum.yaml。

用法:
    python3 scripts/check_curriculum.py <curriculum.yaml> [更多.yaml ...]

除了 JSON Schema 校验，还额外检查 schema 管不到的结构性问题：
  - id 重复
  - prerequisites / edges 引用了不存在的节点
  - 实验课 (kind: 实验) 的 prerequisites 是否列了它要验收的普通课
  - 依赖指到了排在它后面的节点（nodes 顺序即教学位次，倒挂会让学生学到还没讲的课）
  - 有向图存在环（prerequisites + edges 合成；DAG 是硬要求）
  - 存在未被任何后续节点依赖的孤儿节点（提示，不算错误）

退出码：全部通过 0；有问题 1；没给参数 2。
（本脚本由课程设计角色在一次实测会话里写出，经总控复核后收编：只读、无副作用。）
"""
import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("缺少 PyYAML，请先 pip install pyyaml")
try:
    import jsonschema
except ImportError:
    jsonschema = None

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "schemas" / "curriculum.schema.json"

sys.path.insert(0, str(ROOT / "scripts"))
import statuses  # noqa: E402  旧六档 → 三档的映射只有一份


RESOURCE_SECTIONS = ("## Knowledge", "## 易变内容的官方核对来源")   # 只有这两节是知识来源
SERVES_RE = re.compile(r"·\s*服务\s+(.+?)\s*$")


def resource_coverage(resources_path, node_ids):
    """RESOURCES.md 对大纲节点的覆盖率 → 提示列表（不阻断）。

    每条知识来源在行末写 `· 服务 <节点 id>`（多条用「、」分隔）；社区与 Gaps 不算。
    报三件事：指不出一处来源的节点、条数超过节点数 × 2、标记里写了大纲里没有的节点 id。
    """
    if not resources_path.is_file() or not node_ids:
        return []
    try:
        lines = resources_path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError):
        return [f"{resources_path.name} 读不出来，跳过资源覆盖率"]
    section, entries, served, unknown = None, 0, set(), set()
    for line in lines:
        if line.startswith("## "):
            section = line.strip()
            continue
        if section not in RESOURCE_SECTIONS or not re.match(r"^\s*- \[", line):
            continue
        entries += 1
        match = SERVES_RE.search(line)
        if not match:
            continue
        for node_id in re.split(r"[、,，]\s*", match.group(1)):
            node_id = node_id.strip()
            if node_id in node_ids:
                served.add(node_id)
            elif node_id:
                unknown.add(node_id)
    notes = []
    if entries and not served:
        notes.append(f"{resources_path.name} 的 {entries} 条来源都还没标 `· 服务 <节点 id>`"
                     "（按课设的「资源 ↔ 节点对照」补上，才算得出覆盖率）")
        return notes
    missing = [n for n in node_ids if n not in served]
    if missing:
        sample = "、".join(missing[:5]) + ("…" if len(missing) > 5 else "")
        notes.append(f"还有 {len(missing)} 个节点在 {resources_path.name} 里指不出一处来源：{sample}"
                     "（稳定基础知识可以不凑；易变内容要补收集）")
    if entries > 2 * len(node_ids):
        notes.append(f"{resources_path.name} 有 {entries} 条来源，超过节点数 × 2（{len(node_ids)} × 2）"
                     "——每条都该服务到节点，别拿条目充长度")
    if unknown:
        notes.append(f"「服务」标记里有大纲里没有的节点 id：{'、'.join(sorted(unknown))}")
    return notes


def normalized_for_schema(data):
    """只给 schema 校验用的副本：节点状态按旧六档映射成三档、去掉已取消的 mastery。"""
    copy = dict(data)
    nodes = data.get("nodes")
    if isinstance(nodes, list):
        fixed = []
        for node in nodes:
            if isinstance(node, dict):
                node = {key: value for key, value in node.items() if key != "mastery"}
                if isinstance(node.get("status"), str):
                    node["status"] = statuses.normalize_status(node["status"])
            fixed.append(node)
        copy["nodes"] = fixed
    return copy


def legacy_notes(data):
    """旧大纲里还留着的旧写法 → 不阻断的提示（写回时改掉）。"""
    nodes = data.get("nodes") if isinstance(data.get("nodes"), list) else []
    with_mastery = [n.get("id") for n in nodes if isinstance(n, dict) and "mastery" in n]
    legacy_status = sorted({n["status"] for n in nodes if isinstance(n, dict)
                            and isinstance(n.get("status"), str) and n["status"] in statuses.LEGACY_TIER_MAP})
    notes = []
    if with_mastery:
        notes.append(f"{len(with_mastery)} 个节点还带已取消的 mastery 字段（读时忽略；下次写回大纲时删掉）")
    if legacy_status:
        mapped = "、".join(f"{s}→{statuses.LEGACY_TIER_MAP[s]}" for s in legacy_status)
        notes.append(f"节点状态用了旧六档（按 {mapped} 读；写回时用三档）")
    return notes


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    failed = False
    schema_skipped = []

    for arg in argv[1:]:
        path = Path(arg).resolve()
        print(f"=== {path} ===")
        if not path.is_file():
            print(f"  [ERROR] 文件不存在")
            failed = True
            continue

        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, yaml.YAMLError) as exc:
            print(f"  [ERROR] 无法读取 YAML：{exc}")
            failed = True
            continue
        if not isinstance(data, dict):
            print("  [ERROR] 顶层不是 mapping")
            failed = True
            continue

        errors: list[str] = []
        # 旧大纲兼容（不阻断）：六档状态读侧映射成三档、已取消的 mastery 忽略——
        # 学习档案是学生的积累，词表改了不该让旧文件一下子过不了检查；写回时才用新词表。
        legacy = legacy_notes(data)
        for note in legacy:
            print(f"  [WARN] {note}")
        schema_checked = jsonschema is not None
        if schema_checked:
            validator = jsonschema.Draft7Validator(schema)
            for err in sorted(validator.iter_errors(normalized_for_schema(data)), key=lambda e: list(e.path)):
                loc = "/".join(str(p) for p in err.path) or "<root>"
                errors.append(f"schema  {loc}: {err.message}")
        else:
            schema_skipped.append(path)
            print("  [WARN] 未安装 jsonschema，跳过 schema 校验")

        # 结构检查仍会遍历这些字段；schema 报错后不能继续把错误类型当列表/字符串用。
        # 没装 jsonschema 时也保留这道检查，避免 TypeError 中断其余文件。
        structure_errors = []
        for field in ("nodes", "edges"):
            if not isinstance(data.get(field, []), list):
                structure_errors.append(f"{field} 必须是数组")
        if not structure_errors:
            for n in data.get("nodes", []):
                if not isinstance(n, dict) or not isinstance(n.get("id"), str):
                    structure_errors.append("nodes 中每项必须是含字符串 id 的对象")
                    continue
                prerequisites = n.get("prerequisites", [])
                if not isinstance(prerequisites, list) or not all(isinstance(p, str) for p in prerequisites):
                    structure_errors.append(f"{n['id']}: prerequisites 必须是字符串数组")
                if n.get("kind") is not None and not isinstance(n["kind"], str):
                    structure_errors.append(f"{n['id']}: kind 必须是字符串")
            for e in data.get("edges", []):
                if not isinstance(e, dict) or not all(isinstance(e.get(k), str) for k in ("from", "to")):
                    structure_errors.append("edges 中每项必须是含字符串 from/to 的对象")
        if structure_errors:
            failed = True
            print(f"  [FAIL] {len(errors + structure_errors)} 个问题：")
            for msg in errors + structure_errors:
                print(f"    - {msg}")
            continue

        nodes = data.get("nodes") or []
        ids = [n.get("id") for n in nodes if isinstance(n, dict)]
        seen: set[str] = set()
        for nid in ids:
            if nid in seen:
                errors.append(f"重复 id: {nid}")
            seen.add(nid)
        ids = list(dict.fromkeys(ids))

        for n in nodes:
            if not isinstance(n, dict):
                continue
            nid = n.get("id")
            for pre in n.get("prerequisites") or []:
                if pre not in seen:
                    errors.append(f"{nid}: prerequisites 引用了不存在的节点 {pre}")

        for e in data.get("edges") or []:
            if not isinstance(e, dict):
                continue
            for key in ("from", "to"):
                if e.get(key) not in seen:
                    errors.append(f"edge {e.get('from')} -> {e.get('to')}: {key} 指向不存在的节点 {e.get(key)}")

        # 位次倒挂：nodes 的书写顺序就是教学位次（课件文件名 `<序号>-<节点id>.md` 的序号按它算），
        # 所以依赖只能指向前面的节点；指向后面 = 学生还没学就被要求用它。
        pos = {nid: i for i, nid in enumerate(ids)}
        inverted: dict[tuple[str, str], None] = {}
        for n in nodes:
            if not isinstance(n, dict) or n.get("id") not in pos:
                continue
            for pre in n.get("prerequisites") or []:
                if pre in pos and pos[pre] > pos[n["id"]]:
                    inverted.setdefault((n["id"], pre), None)
        for e in data.get("edges") or []:
            if isinstance(e, dict) and e.get("from") in pos and e.get("to") in pos:
                if pos[e["from"]] > pos[e["to"]]:
                    inverted.setdefault((e["to"], e["from"]), None)
        for dep, pre in inverted:
            errors.append(f"{dep}（第 {pos[dep] + 1} 位）依赖 {pre}（第 {pos[pre] + 1} 位）——"
                          f"nodes 顺序即教学位次，依赖只能指向前面的节点")

        # 实验课必须有非空 prerequisites
        for n in nodes:
            if isinstance(n, dict) and n.get("kind") == "实验":
                if not n.get("prerequisites"):
                    errors.append(f"{n.get('id')}: 实验课必须有 prerequisites（列出验收哪些节点）")

        # 环检测（Kahn 拓扑排序）：prerequisites 与 edges 合成一张有向图，DAG 是硬要求。
        # 排序不掉的节点就是环上的节点——比手写 DFS 的颜色标记稳，不存在递归深度问题。
        graph: dict[str, set[str]] = {i: set() for i in ids}
        for n in nodes:
            if isinstance(n, dict) and n.get("id") in graph:
                for pre in n.get("prerequisites") or []:
                    if pre in graph:
                        graph[pre].add(n["id"])
        for e in data.get("edges") or []:
            if isinstance(e, dict) and e.get("from") in graph and e.get("to") in graph:
                graph[e["from"]].add(e["to"])
        indegree = {node: 0 for node in ids}
        for outs in graph.values():
            for nxt in outs:
                indegree[nxt] += 1
        ready = [node for node in ids if indegree[node] == 0]
        settled = 0
        while ready:
            node = ready.pop()
            settled += 1
            for nxt in graph[node]:
                indegree[nxt] -= 1
                if indegree[nxt] == 0:
                    ready.append(nxt)
        if settled < len(ids):
            stuck = [node for node in ids if indegree[node] > 0]
            errors.append(f"存在环：{len(stuck)} 个节点排不出拓扑序（{', '.join(stuck[:6])}"
                          + ("…" if len(stuck) > 6 else "") + "）")

        # 统计
        kinds: dict[str, int] = {}
        for n in nodes:
            if isinstance(n, dict):
                kinds[n.get("kind")] = kinds.get(n.get("kind"), 0) + 1
        print(f"  节点 {len(nodes)} 个： " + "，".join(f"{k} {v}" for k, v in kinds.items()))
        print(f"  边 {len(data.get('edges') or [])} 条")

        # 孤儿提示
        referenced = {p for n in nodes if isinstance(n, dict) for p in (n.get("prerequisites") or [])}
        referenced |= {e.get("from") for e in (data.get("edges") or []) if isinstance(e, dict)}
        orphans = [i for i in ids if i not in referenced]
        if orphans:
            print(f"  [提示] 没有被任何节点依赖的末端节点: {', '.join(orphans)}")

        # 资源清单覆盖率（只提示）：同目录有 RESOURCES.md 才查
        node_ids = [n.get("id") for n in nodes if isinstance(n, dict) and isinstance(n.get("id"), str)]
        for note in resource_coverage(path.parent / "RESOURCES.md", node_ids):
            print(f"  [提示] {note}")

        if errors:
            failed = True
            print(f"  [FAIL] {len(errors)} 个问题：")
            for msg in errors:
                print(f"    - {msg}")
        else:
            if schema_checked:
                print("  [PASS] schema 校验通过，引用完整")
            else:
                print("  [PASS] 结构检查通过，引用完整（schema 未校验，见末尾汇总）")

    if schema_skipped:
        names = "、".join(p.name for p in schema_skipped)
        print(f"[WARN] {len(schema_skipped)} 份文件的 schema 未校验，只过了结构检查与引用检查：{names}")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
