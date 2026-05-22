# 合同智审 Agent MVP

这是一个从 0 到 1 的最小可运行版本，目标是先跑通：

- 合同上传或 API 入库
- 自动创建审核任务
- 后台 Agent Loop 调用 Skill
- 规则引擎输出风险
- 轻量 RAG 返回依据
- 前端三栏展示合同库、合同预览、审核过程和结果

## 启动

```powershell
cd D:\飞书下载\洛阳盛龙矿业AI合同智审文件\contract-review-agent-mvp
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8123
```

浏览器访问：

```text
http://127.0.0.1:8123
```

如果本机 Python 环境没有把 `python` 加入 PATH，也可以使用项目提供的启动脚本：

```powershell
python run_local_server.py
```

## 配置 GLM

当前支持把指令模式规则接到 GLM Chat Completion。复制 `.env.example` 为 `.env.local`，并填写本地密钥：

```powershell
Copy-Item .env.example .env.local
```

`.env.local` 示例：

```text
LLM_PROVIDER=glm
GLM_API_KEY=replace-with-your-glm-api-key
GLM_MODEL=glm-5
GLM_BASE_URL=https://api.z.ai/api/paas/v4
```

接口 `/api/llm/status` 可查看是否已配置模型，不会返回 API Key。

## 当前实现边界

当前版本已支持配置 GLM 处理指令模式规则，生产向量库、OCR 服务、外部资信接口仍保留替换点：

- `backend/agent.py`：主审查 Agent Loop
- `backend/agent_skills/`：粗粒度业务 Skill，每个目录包含 `SKILL.md`
- `backend/tools/`：Skill 内部调用的确定性工具，如解析、抽取、规则执行和轻量 RAG
- `backend/tools/execute_rules.py`：规则执行工具，指令模式可调用 GLM
- `backend/tools/local_rag.py`：轻量 RAG 检索工具
- `backend/llm.py`：GLM 配置读取、请求封装和 JSON 响应解析
- `backend/rules.py`：规则配置样例

后续可以逐步替换为生产级向量数据库、OCR 服务、外部资信接口和完整规则库。

## 当前 Skill 划分

Agent Loop 只编排四个粗粒度 Skill：

- `ContractIntakeSkill`：合同上传/API 同步入库，生成合同记录和审核任务。
- `ContractUnderstandingSkill`：文档解析、类型识别、字段抽取、模板匹配。
- `ContractReviewSkill`：规则选择、规则执行、轻量 RAG 证据检索、风险生成。
- `ReviewReportingSkill`：风险汇总、角色意见、人工确认状态和前端摘要。

解析器、抽取器、规则引擎和 RAG 都作为 Skill 内部工具存在，不再作为 Agent Loop 中的独立 Skill 暴露。
