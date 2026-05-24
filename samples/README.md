# Sales Contract Test Samples

这两个文件用于本地上传测试：

- `sales_contract_bad_5_rules.txt`：问题样本，业务语义上预计命中 5 条规则：
  - `SL-GEN-003` 首页与签章页主体完整性
  - `SL-GEN-004` 我方主体名称与角色一致性
  - `SL-GEN-010` 付款方式和付款条件完整性
  - `SL-GEN-012` 付款不得早于合同生效/审批
  - `SL-GEN-014` 签章与生效条款校验
- `sales_contract_good_compliant.txt`：合规样本，业务语义上应满足当前销售合同相关规则。

注意：当前本机 `/api/llm/status` 显示 LLM 未配置。未配置 LLM 时，指令模式规则会提示模型不可用；这属于运行环境状态，不代表合规样本合同内容不合规。
