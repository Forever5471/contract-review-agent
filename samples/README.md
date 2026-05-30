# Contract Review Test Samples

这些文件用于本地上传测试。建议逐份上传，观察合同类型、审核策略、命中规则、条款判定和流转策略是否符合预期。

- `sales_contract_bad_5_rules.txt`：问题样本，业务语义上预计命中 5 条规则：
  - `SL-GEN-003` 首页与签章页主体完整性
  - `SL-GEN-004` 我方主体名称与角色一致性
  - `SL-GEN-010` 付款方式和付款条件完整性
  - `SL-GEN-012` 付款不得早于合同生效/审批
  - `SL-GEN-014` 签章与生效条款校验
- `sales_contract_good_compliant.txt`：合规样本，业务语义上应满足当前销售合同相关规则。

## 新增场景样本

- `sales_need_revision_early_payment.txt`
  - 目标策略：`strategy-sales` 销售合同审核策略
  - 目标流转：`flow-standard-contracts` 标准合同流转策略
  - 预期状态：`NeedRevision`，原因是命中 P0 或需退回规则
  - 重点命中：`SL-GEN-012` 付款不得早于合同生效/审批，兼有主体不完整、我方主体异常、金额流程等风险

- `sales_human_confirm_p1_subject.txt`
  - 目标策略：`strategy-sales`
  - 目标流转：`flow-standard-contracts`
  - 预期状态：`NeedHumanConfirm`
  - 重点命中：`SL-GEN-004` 我方主体名称与角色一致性。合同主体完整，但没有出现盛龙矿业相关我方主体名称。

- `sales_human_confirm_amount_threshold.txt`
  - 目标策略：`strategy-sales`
  - 目标流转：`flow-standard-contracts`
  - 预期状态：`NeedHumanConfirm`
  - 重点触发：合同金额 120,000 元达到标准流转策略的人工确认金额阈值，内容本身尽量保持合规。

- `engineering_need_revision_missing_safety.txt`
  - 目标策略：`strategy-engineering` 工程合同审核策略
  - 目标流转：`flow-high-risk-contracts` 高风险合同流转策略
  - 预期状态：`NeedRevision`
  - 重点命中：`SL-TYPE-ENG-002` 工程安全管理协议触发。合同是工程/施工类，但未出现安全生产、安全管理、事故、环保等条款。

- `engineering_human_confirm_amount_threshold.txt`
  - 目标策略：`strategy-engineering`
  - 目标流转：`flow-high-risk-contracts`
  - 预期状态：`NeedHumanConfirm`
  - 重点触发：工程合同金额 60,000 元达到高风险流转策略的人工确认金额阈值，同时保留安全生产与环保条款，避免命中工程安全缺失 P0。

## 注意

当前系统中 `SL-GEN-010` 和 `SL-ROLE-LEGAL-002` 是指令模式规则，结果依赖大模型配置和额度。如果 LLM 未配置或限流，这两条会显示为“未完成”，并可能让流转进入人工确认；这属于运行环境状态，不代表样本合同内容一定不合规。
