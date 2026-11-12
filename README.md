# 消保评价 Skill（Consumer Protection Evaluation）

> 年度金融消保评价（消保监管评价自评）全流程指导技能 · 作者：八大权益 · 版本：v1.0.0

## 简介

指导金融消费者权益保护从业者有效开展年度金融消保评价（消保监管评价自评）：指标解读、台账分工、证据链整理、自评报告撰写、失分诊断与模拟打分，覆盖银行/保险法人及分支机构。核心理念：消保监管评价是「材料 + 逻辑」的双重博弈——把年度评价表翻译成一张可执行的工作地图，并在每个环节提示"监管会怎么想"。

## 适用场景

- 消保监管评价自评从零开始的流程指导（银行/保险，法人机构/一级分支机构/分支机构）
- 评价指标解读：总分 100 分、七要素权重下限、三层指标结构、三类给分方式（有无型/比率分档型/扣分型）、1-5 级等级线
- 指标台账生成与责任部门分工建议
- 证明材料整理、材料体检（证据链审计）
- 自评报告撰写与失分诊断、模拟打分测算

## 内置脚本

```bash
# 生成指标台账（内置银行版/保险版评价表全部指标）
python3 scripts/build_ledger.py --type insurance --format csv --out 指标台账.csv
python3 scripts/build_ledger.py --type bank --format md --out 指标台账.md

# 证明材料体检
python3 scripts/evidence_audit.py

# 模拟打分测算
python3 scripts/scoring.py
```

## 目录结构

```
├── SKILL.md                     # 技能主文件
├── scripts/                     # build_ledger.py / evidence_audit.py / scoring.py 及银行、保险指标数据
├── references/                  # 法规与分级、指标与权益映射、证据链、报告撰写、失分诊断等 9 份参考文件
└── assets/                      # 指标台账模板、证明材料目录、自评报告模板、失分诊断表
```

## 安装使用

将本目录复制到 WorkBuddy 用户级技能目录：

```
~/.workbuddy/skills/consumer-protection-annual-evaluation/
```

在对话中直接使用触发词即可，例如"帮我生成 2025 年度消保评价指标台账""帮我做一次材料体检并模拟打分，看离 2 级还差几分"。

## 关联技能（八大权益 · 金融消保系列）

- [投诉管理](https://github.com/openfcp/complaint-management)
- [消保审查](https://github.com/openfcp/consumer-protection-review)
- [消保检查](https://github.com/openfcp/consumer-protection-inspection)
- [合规销售](https://github.com/openfcp/compliance-sales)
- [金融消保专家](https://github.com/openfcp/consumer-protection-expert)
