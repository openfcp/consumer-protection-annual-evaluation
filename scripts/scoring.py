#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""自评得分测算：要素得分 → 总分 → 等级档位 → 距上一档差多少、差在哪。

用法：
    python3 scoring.py --type insurance --template --out 自评打分表.csv   # 生成待填模板
    python3 scoring.py --type insurance --input 自评打分表.csv              # 测算
    python3 scoring.py --type insurance --input 自评打分表.csv --branch 86.2  # 含一级分支机构平均分

输入 CSV 只需两列：序号,自评得分（缺省视为满分，便于先看天花板）。
"""
import argparse
import csv
import json
import os
import sys

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
FILES = {"insurance": "insurance.json", "bank": "bank.json"}

GRADES = [
    (90, "1级"), (85, "2A"), (80, "2B"), (75, "2C"),
    (70, "3A"), (65, "3B"), (60, "3C"), (45, "4级"), (0, "5级"),
]


def load(kind):
    with open(os.path.join(DATA_DIR, FILES[kind]), encoding="utf-8") as f:
        return json.load(f)


def grade(score):
    for line, name in GRADES:
        if score >= line:
            return name, line
    return "5级", 0


def next_grade(score):
    """返回上一档名称与所需分数。"""
    for line, name in reversed(GRADES):
        if score < line:
            return name, line
    return None, None


def write_template(data, out):
    f = sys.stdout if out == "-" else open(out, "w", encoding="utf-8-sig", newline="")
    w = csv.writer(f)
    w.writerow(["序号", "要素", "一级指标", "二级指标", "分值", "自评得分", "扣分理由/依据"])
    for r in data["rows"]:
        w.writerow([r["seq"], r["element"], r["l1"], r["l2"], r["l2_score"], "", ""])
    if f is not sys.stdout:
        f.close()
        print(f"已生成模板：{out}（{len(data['rows'])} 条，分值列不可改，得分留空待填）", file=sys.stderr)


def read_scores(path):
    scores = {}
    with open(path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            seq = (row.get("序号") or "").strip()
            if not seq.isdigit():
                continue
            raw = (row.get("自评得分") or "").strip()
            scores[int(seq)] = None if raw == "" else float(raw)
    return scores


def main():
    ap = argparse.ArgumentParser(description="消保评价自评得分测算")
    ap.add_argument("--type", choices=["insurance", "bank"], default="insurance")
    ap.add_argument("--input", help="自评打分表 CSV")
    ap.add_argument("--template", action="store_true", help="生成待填模板")
    ap.add_argument("--out", default="-", help="模板输出路径")
    ap.add_argument("--branch", type=float, default=None, help="一级分支机构平均得分")
    a = ap.parse_args()

    data = load(a.type)
    if a.template:
        write_template(data, a.out)
        return
    if not a.input:
        sys.exit("请用 --input 指定打分表，或先用 --template 生成模板")

    scores = read_scores(a.input)

    lines = [f"# 自评得分测算（{data['type']} / {data['version']}）\n"]
    lines.append("| 序号 | 要素 | 二级指标 | 分值 | 自评 | 失分 |")
    lines.append("|---|---|---|---|---|---|")
    el_agg, lost = {}, []
    total_score = total_full = 0.0
    for r in data["rows"]:
        full = r["l2_score"] or 0
        s = scores.get(r["seq"], None)
        if s is None:
            s = full
        s = max(0.0, min(s, full))
        gap = full - s
        el_agg.setdefault(r["element"], [0.0, 0.0])
        el_agg[r["element"]][0] += full
        el_agg[r["element"]][1] += s
        total_full += full
        total_score += s
        if gap > 0:
            lost.append((gap, r["seq"], r["element"], r["l2"], full, s))
        lines.append(f"| {r['seq']} | {r['element']} | {r['l2']} | {full} | {s:g} | {gap:g} |")

    lines.append("\n## 要素得分\n")
    lines.append("| 要素 | 满分 | 自评 | 得分率 | 评价 |")
    lines.append("|---|---|---|---|---|")
    for el, (full, s) in el_agg.items():
        rate = s / full * 100 if full else 0
        flag = "✅ 达标" if rate >= 95 else ("⚠️ 有缺口" if rate >= 85 else "❌ 短板")
        lines.append(f"| {el} | {full:g} | {s:g} | {rate:.1f}% | {flag} |")

    legal = round(total_score, 1)
    g, line = grade(legal)
    ng, need = next_grade(legal)

    lines.append(f"\n## 结论\n")
    lines.append(f"- 法人自评总分：**{legal} / {total_full:g}**")
    lines.append(f"- 对应等级：**{g}**（档位线 {line} 分）")
    if ng and need:
        lines.append(f"- 距上一档「{ng}」还差 **{round(need - legal, 1)} 分**")
    if a.branch is not None:
        combined = round((legal + a.branch) / 2, 1)
        cg, _ = grade(combined)
        lines.append(f"- 一级分支机构平均分：{a.branch}")
        lines.append(f"- 综合得分（法人 50% + 分支平均 50%）：**{combined}**，对应等级 **{cg}**")
        if cg != g:
            lines.append(f"  - 注意：分支机构拉低了结果（相差 {round(legal - combined, 1)} 分），整改重心应下沉到分支机构。")

    lost.sort(reverse=True)
    if lost:
        lines.append("\n## 失分最集中的 8 条（优先整改）\n")
        lines.append("| 失分 | 序号 | 要素 | 二级指标 | 满分 | 自评 |")
        lines.append("|---|---|---|---|---|---|")
        for gap, seq, el, l2, full, s in lost[:8]:
            lines.append(f"| {gap:g} | {seq} | {el} | {l2} | {full} | {s:g} |")
        lines.append("\n> 整改顺序建议：归零型（有/无判定）→ 分档型（比率类）→ 扣减型（已发生事实，认账并写整改）。")
    else:
        lines.append("\n未记录失分项。若全项满分，请复核是否存在“自评虚高”——参照 references/05-loss-points.md 的六个高估项。")

    print("\n".join(lines))


if __name__ == "__main__":
    main()
