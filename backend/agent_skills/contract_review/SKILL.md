---
name: contract-review
description: 基于合同画像和条款对象执行风险审查，完成规则选择、条款片段匹配、脚本模式规则执行、指令模式规则执行、轻量 RAG 证据检索和风险项生成。适用于合同理解完成后，需要输出可溯源风险列表、规则命中过程和人工确认标记的场景。
---

# Contract Review Skill

## 目标

根据合同类型、条款对象、字段和全文执行合同审查。该 Skill 代表“风险审查”这个业务能力，规则引擎、条款片段匹配、RAG 检索和脚本执行都只是它内部的工具。

## 输入

- `text`：合同全文。
- `contract_type`：合同类型。
- `clauses`：条款对象列表。
- `fields`：合同结构化字段。

## 输出

- `executed_rules`：执行规则数量。
- `rule_events`：每条规则的通过、未通过、证据和建议。
- `risks`：未通过规则形成的风险项。
- `evidence`：条款片段、制度、模板、历史合同或字段证据。

## 内部工具

- `RuleEngineTool`：执行规则配置。
- `LocalRagTool`：从规章制度、合同模板、历史合同中检索证据。

## 大模型配置

当环境变量 `LLM_PROVIDER=glm` 且 `GLM_API_KEY` 存在时，指令模式规则优先调用 GLM Chat Completion。默认模型为 `glm-5`，默认接口为 `https://api.z.ai/api/paas/v4/chat/completions`。

可配置项：

- `GLM_MODEL`：默认 `glm-5`。
- `GLM_BASE_URL`：默认 `https://api.z.ai/api/paas/v4`。
- `GLM_TEMPERATURE`：默认 `0.1`。
- `GLM_MAX_TOKENS`：默认 `900`。
- `GLM_TIMEOUT_SECONDS`：默认 `30`。
- `GLM_THINKING`：默认 `disabled`，避免在规则执行结果中引入推理过程。

## 规则模式

- 脚本模式：使用确定性 Python 判断，适合金额阈值、字段存在性、关键词模式等稳定规则；运行时会注入 `clauses` 和 `rule_inputs`。
- 指令模式：优先使用 GLM 指令执行器，要求模型只返回 JSON；规则相关条款和 RAG 证据会一起进入模型上下文。

## 约束

- 每个风险项必须绑定规则 ID、优先级、问题、建议和证据。
- P0/P1 风险默认需要人工确认。
- RAG 只负责找依据，不直接给最终审查结论。
- 不在日志、接口和前端中输出 API Key。
