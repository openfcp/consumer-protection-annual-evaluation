#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""证明材料体检：按七要素归类、找出零材料与弱证据、检查命名与结构。

用法：
    python3 evidence_audit.py --dir ./证明材料 --type insurance
    python3 evidence_audit.py --dir ./证明材料 --type bank --out 材料体检报告.md

设计思路：评审人先看目录、再看数据报表、最后翻底稿。因此体检不只看"有没有"，
还看"结构是否像一份能被快速读懂的证据集"。
"""
import argparse
import os
import re
import sys
from collections import Counter, defaultdict

ELEMENTS = ["体制机制", "适当性管理", "营销行为管理", "纠纷化解", "金融教育", "消费者服务", "个人信息保护"]

KEYWORDS = {
    "体制机制": ["制度", "董事会", "监事会", "高管", "委员会", "治理", "审查制度", "审计", "考核", "培训",
             "职责", "架构", "编制", "预算", "议事规则", "纪要", "章程"],
    "适当性管理": ["适当性", "风险等级", "风险评级", "分类分级", "测评", "评估问卷", "风险承受", "匹配",
              "合格投资者", "双录", "告知", "65", "老年"],
    "营销行为管理": ["营销", "宣传", "话术", "海报", "信息披露", "披露", "格式条款", "条款", "可回溯",
               "双录", "质检", "互联网", "销售页面", "合作机构", "准入", "协议", "代理", "拒收", "退订"],
    "纠纷化解": ["投诉", "工单", "纠纷", "调解", "应调", "和解", "溯源", "办结", "转办", "信访", "12378"],
    "金融教育": ["教育", "宣教", "宣传月", "3·15", "315", "投资者", "风险提示", "金融知识", "活动方案",
             "原创", "折页", "短视频", "专区"],
    "消费者服务": ["服务", "适老", "无障碍", "残障", "军人", "涉外", "便民", "为民办实事", "舆情",
              "应急", "突发事件", "演练", "服务质量"],
    "个人信息保护": ["个人信息", "隐私", "授权", "信息收集", "数据安全", "权限", "客户信息", "信息安全"],
}

IMG_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp", ".heic"}
DOC_EXT = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".csv", ".ppt", ".pptx", ".txt", ".md"}
AV_EXT = {".mp4", ".avi", ".mov", ".mp3", ".wav", ".mkv"}

BAD_WORDS = ["新建", "副本", "最终版", "未命名", "copy", "最终", "修改版", "临时"]


def walk(root):
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        for fn in filenames:
            if fn.startswith(".") or fn.startswith("~$"):
                continue
            full = os.path.join(dirpath, fn)
            out.append((full, os.path.relpath(full, root)))
    return out


def classify(relpath):
    """文件归入要素：优先看路径，再看文件名。"""
    text = relpath.replace(os.sep, " ")
    scores = defaultdict(int)
    for el, kws in KEYWORDS.items():
        for kw in kws:
            if kw in text:
                scores[el] += 1
    if not scores:
        return "未归类"
    return max(scores.items(), key=lambda kv: kv[1])[0]


def audit(files):
    by_el = defaultdict(list)
    ext_counter = Counter()
    for full, rel in files:
        ext = os.path.splitext(full)[1].lower()
        ext_counter[ext] += 1
        by_el[classify(rel)].append(rel)
    return by_el, ext_counter


def check_names(files):
    issues = []
    for full, rel in files:
        name = os.path.basename(rel)
        stem = os.path.splitext(name)[0]
        problems = []
        if len(name) > 80:
            problems.append("文件名过长")
        if " " in name:
            problems.append("含空格")
        if not re.search(r"(20\d{2})[-_.年]?\d{1,2}", stem):
            problems.append("无日期")
        for w in BAD_WORDS:
            if w in name:
                problems.append(f"含「{w}」")
                break
        if not re.match(r"^\d+[-_]\d+", stem) and not re.match(r"^[1-7][-_]", stem):
            problems.append("无要素/指标编号前缀")
        if problems:
            issues.append((rel, problems))
    return issues


def main():
    ap = argparse.ArgumentParser(description="消保评价证明材料体检")
    ap.add_argument("--dir", required=True, help="证明材料根目录")
    ap.add_argument("--type", choices=["insurance", "bank"], default="insurance")
    ap.add_argument("--out", default="-", help="报告输出路径，默认打印")
    a = ap.parse_args()

    if not os.path.isdir(a.dir):
        sys.exit(f"目录不存在：{a.dir}")

    files = walk(a.dir)
    if not files:
        sys.exit(f"目录为空：{a.dir}")

    by_el, ext_counter = audit(files)
    name_issues = check_names(files)
    total = len(files)

    has_catalog = any(("目录" in r or "catalog" in r.lower() or "index" in r.lower()) for _, r in files)

    img = sum(v for k, v in ext_counter.items() if k in IMG_EXT)
    doc = sum(v for k, v in ext_counter.items() if k in DOC_EXT)
    av = sum(v for k, v in ext_counter.items() if k in AV_EXT)
    other = total - img - doc - av

    L = []
    L.append(f"# 证明材料体检报告（{a.type}）\n")
    L.append(f"- 扫描目录：`{a.dir}`")
    L.append(f"- 文件总数：**{total}**（文档 {doc} / 图片 {img} / 音视频 {av} / 其他 {other}）")
    L.append(f"- 目录文件：{'已提供' if has_catalog else '**未发现（评审人无法快速索引，记为高风险）**'}")
    L.append("")

    L.append("## 一、按要素分布\n")
    L.append("| 要素 | 文件数 | 占比 | 状态 |")
    L.append("|---|---|---|---|")
    for el in ELEMENTS + ["未归类"]:
        n = len(by_el.get(el, []))
        pct = f"{n / total * 100:.1f}%" if total else "0%"
        if el == "未归类":
            status = "建议在文件名中补要素/指标编号前缀" if n else "—"
        elif n == 0:
            status = "**零材料，必须补件**"
        elif n < 5:
            status = "偏少，核对是否有指标被漏掉"
        else:
            status = "有材料，需逐条核对证据链是否闭环"
        L.append(f"| {el} | {n} | {pct} | {status} |")
    L.append("")

    empty = [el for el in ELEMENTS if not by_el.get(el)]
    issues = []
    if empty:
        issues.append(f"**零材料要素**：{'、'.join(empty)}。七项要素任一为空，等于该要素整体放弃得分。")
    if not has_catalog:
        issues.append("**缺证明材料目录**：通知明确要求制作证明材料目录；没有目录的成堆材料，评审通常按低效处理。")
    if total and img / total > 0.7:
        issues.append(f"**图片占比过高（{img / total * 100:.0f}%）**：截图只能证明「看到了」，不能证明「持续在运行」。建议补结构化报表（Excel/CSV）与过程底稿（纪要、台账、检查报告）。")
    if total and doc / total < 0.3:
        issues.append(f"**文档类占比偏低（{doc / total * 100:.0f}%）**：制度、台账、报告是主力证据，图片是辅助。")
    if total and len(name_issues) > total * 0.3:
        issues.append(f"**命名不规范 {len(name_issues)} 份**：建议统一为 `要素号-指标号_材料名称_形成日期_版本`。")

    L.append("## 二、需要立即处理的问题\n")
    if issues:
        for i, s in enumerate(issues, 1):
            L.append(f"{i}. {s}")
    else:
        L.append("未发现结构性问题。仍需逐条核对证据链是否闭环（制度—执行—效果）。")
    L.append("")

    L.append("## 三、命名与结构问题（前 30 条）\n")
    if name_issues:
        L.append("| 文件 | 问题 |")
        L.append("|---|---|")
        for rel, problems in name_issues[:30]:
            L.append(f"| {rel} | {'、'.join(problems)} |")
        if len(name_issues) > 30:
            L.append(f"\n> 共 {len(name_issues)} 份存在命名问题，此处仅列前 30 条。")
    else:
        L.append("未发现明显命名问题。")
    L.append("")

    L.append("## 四、下一步动作（按优先级）\n")
    L.append("1. **补零材料要素**（归零型风险最高）：按 `references/03-evidence-playbook.md` 的分要素清单逐项补齐。")
    L.append("2. **建立统一目录**：字段为 序号/要素/指标/材料名称/文号或版本/形成日期/页码/证明目的/责任部门/备注。")
    L.append("3. **每条指标补一份执行台账**：只有制度没有台账的指标，几乎都会被认定「机制未运行」。")
    L.append("4. **统一命名并重排版**：拆分超大 PDF，每个文件首页加索引页。")
    L.append("5. **做一次闭环抽查**：随机抽 10 条指标，看能否只用目录在 3 分钟内走完「制度—执行—效果」。")
    L.append("")

    text = "\n".join(L)
    if a.out == "-":
        print(text)
    else:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"已生成：{a.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
