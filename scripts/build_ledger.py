#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成消保监管评价指标台账。

内置 2025 年度银行/保险法人版评价表全部二级指标，输出可直接分发给责任部门填写的台账。

用法：
    python3 build_ledger.py --type insurance --format csv --out 指标台账.csv
    python3 build_ledger.py --type bank --format md
    python3 build_ledger.py --type insurance --list-elements   # 只看要素与分值分布
"""
import argparse
import csv
import json
import os
import sys

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
FILES = {"insurance": "insurance.json", "bank": "bank.json"}

HEADER = [
    "序号", "要素", "要素权重", "一级指标", "二级指标", "分值",
    "三级指标要求", "评分要点", "建议证明材料",
    "责任部门", "现有材料", "自评得分", "差距与整改(动作+时间+交付物)",
]


def load(kind):
    path = os.path.join(DATA_DIR, FILES[kind])
    if not os.path.exists(path):
        sys.exit(f"找不到指标数据文件：{path}")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def rows_of(data):
    for r in data["rows"]:
        yield [
            r["seq"], r["element"], r["element_weight"], r["l1"], r["l2"],
            r["l2_score"] if r["l2_score"] is not None else "",
            r["l3"], r["scoring"], r["materials"], "", "", "", "",
        ]


def write_csv(data, out):
    f = sys.stdout if out == "-" else open(out, "w", encoding="utf-8-sig", newline="")
    w = csv.writer(f)
    w.writerow([f"消保监管评价指标台账（{data['type']} / {data['version']}）"])
    w.writerow(HEADER)
    for row in rows_of(data):
        w.writerow(row)
    if f is not sys.stdout:
        f.close()


def write_md(data, out):
    lines = [f"# 消保监管评价指标台账（{data['type']} / {data['version']}）", ""]
    cur = None
    for r in data["rows"]:
        if r["element"] != cur:
            cur = r["element"]
            lines.append(f"\n## {cur}（权重 {r['element_weight']}）\n")
            lines.append("| 序号 | 一级指标 | 二级指标 | 分值 | 责任部门 | 自评得分 |")
            lines.append("|---|---|---|---|---|---|")
        lines.append(
            f"| {r['seq']} | {r['l1']} | {r['l2']} | {r['l2_score']} |  |  |"
        )
    lines.append("\n> 三级指标要求、评分要点、建议证明材料见同目录 CSV 版；逐条填写后请与 `scoring.py` 联动测算等级。")
    text = "\n".join(lines)
    if out == "-":
        print(text)
    else:
        with open(out, "w", encoding="utf-8") as f:
            f.write(text)


def list_elements(data):
    order = []
    agg = {}
    for r in data["rows"]:
        if r["element"] not in agg:
            order.append(r["element"])
            agg[r["element"]] = {"w": r["element_weight"], "s": 0.0, "n": 0}
        agg[r["element"]]["s"] += r["l2_score"] or 0
        agg[r["element"]]["n"] += 1
    print(f"{data['type']} / {data['version']}")
    total = 0.0
    for e in order:
        v = agg[e]
        total += v["s"]
        print(f"  {e:<8} 权重 {v['w']:>4}  分值合计 {v['s']:>5.1f}  二级指标 {v['n']} 条")
    print(f"  {'合计':<8} 权重 100%  分值合计 {total:>5.1f}")


def main():
    ap = argparse.ArgumentParser(description="生成消保监管评价指标台账")
    ap.add_argument("--type", choices=["insurance", "bank"], default="insurance",
                    help="insurance=保险法人版, bank=银行法人版")
    ap.add_argument("--format", choices=["csv", "md"], default="csv")
    ap.add_argument("--out", default="-", help="输出路径，默认打印到标准输出")
    ap.add_argument("--list-elements", action="store_true", help="只打印要素与分值分布")
    a = ap.parse_args()

    data = load(a.type)
    if a.list_elements:
        list_elements(data)
        return
    if a.format == "csv":
        write_csv(data, a.out)
    else:
        write_md(data, a.out)
    if a.out != "-":
        print(f"已生成：{a.out}（{len(data['rows'])} 条二级指标）", file=sys.stderr)


if __name__ == "__main__":
    main()
