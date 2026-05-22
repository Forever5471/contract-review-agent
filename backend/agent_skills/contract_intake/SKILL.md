---
name: contract-intake
description: 将上传文件或外部 API 同步来的合同纳入合同库，生成合同记录、文件版本、来源元数据和待审核任务。适用于合同进入审核链路前的入库、版本登记、来源归一和状态初始化。
---

# Contract Intake Skill

## 目标

把合同文件和业务元数据转成一个可被 Agent Loop 消费的合同记录。该 Skill 只负责入库和任务初始化，不做合同内容理解和风险判断。

## 输入

- `file_obj`：上传文件流或 API 同步得到的文件流。
- `file_name`：原始文件名。
- `source`：来源，如 `upload`、`oa`、`erp`、`api`。
- `business_dept`：经办或发起部门。
- `initiator`：经办人或发起人。

## 输出

- `contract.id`：合同记录 ID。
- `contract.file_path`：本地归档路径。
- `contract.source`：归一后的来源。
- `contract.status`：初始为 `Pending`。
- `contract.review.events`：首个入库事件。

## 内部工具

- 文件持久化工具：保存上传文件，生成安全文件名。
- 状态写入工具：写入合同库 JSON Store。
- 元数据归一工具：补齐来源、部门、经办人和创建时间。

## 约束

- 不解析合同正文。
- 不调用 RAG、规则引擎或大模型。
- 不覆盖已有文件；每次入库生成新的合同 ID 和文件版本。

