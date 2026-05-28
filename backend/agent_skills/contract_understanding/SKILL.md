---
name: contract-understanding
description: 对已入库合同做内容理解，完成文档解析、合同类型识别、条款对象抽取、核心字段抽取和模板结构匹配。适用于合同进入风险审查前，需要生成结构化合同画像、预览文本、条款、字段和模板偏差信息的场景。
---

# Contract Understanding Skill

## 目标

把一份合同从“文件”变成“结构化合同画像”。该 Skill 是一个粗粒度业务 Skill，内部可以调用多个确定性工具，但 Agent Loop 只把它视为一次合同理解动作。

## 输入

- `contract.file_path`：合同文件路径。
- `contract.file_name`：合同原始文件名。
- `contract.source`：合同来源。

## 输出

- `text`：解析后的全文。
- `preview`：前端预览文本。
- `contract_type`：合同类型。
- `clauses`：条款对象，包含条款编号、标题、类型、原文、所属合同和位置。
- `fields`：金额、主体、付款、发票、生效、签章、违约、安全等核心字段。
- `template_match`：模板匹配结果、命中条款、缺失条款和相似度。
- `tool_runs`：内部工具执行摘要。

## 内部工具

- `DocumentParseTool`：解析 docx、pdf、doc、md、txt。
- `ContractClassifyTool`：基于关键词和文件名识别合同类型。
- `ClauseExtractTool`：切分合同条款并识别条款类型与位置。
- `FieldExtractTool`：抽取审查所需字段。
- `TemplateMatchTool`：根据合同类型做轻量模板匹配。

## 约束

- 不做风险结论。
- 不直接调用规则引擎。
- 低置信度的分类和模板匹配只输出 warning，交由后续审查和人工确认处理。
