const state = {
  contracts: [],
  rules: [],
  agents: [],
  availableSkills: [],
  availableTools: [],
  agentSkillIds: [],
  agentToolIds: [],
  selectedAgentSkillId: null,
  selectedAgentToolId: null,
  agentSkillSearch: "",
  agentToolSearch: "",
  strategies: [],
  strategyRules: [],
  flowStrategies: [],
  flowReviewStrategies: [],
  flowRules: [],
  knowledge: null,
  knowledgeItems: [],
  knowledgeSearchResults: [],
  feedbackItems: [],
  feedbackSummary: null,
  selectedKnowledgeCategory: "全部",
  selectedFeedbackId: null,
  knowledgeQuery: "",
  knowledgeUploadCategory: "",
  ruleStats: null,
  selectedId: null,
  selectedRuleId: null,
  selectedAgentId: null,
  selectedStrategyId: null,
  selectedFlowStrategyId: null,
  editingRuleOriginalId: null,
  editingAgentOriginalId: null,
  editingStrategyOriginalId: null,
  editingFlowStrategyOriginalId: null,
  currentRuleMode: "脚本模式",
  activeEvidenceTab: "clauses",
  inputParams: [],
  outputParams: [],
  debugFile: null,
  contractListTab: "todo",
  resultFilter: "all",
  pollTimer: null,
  pollStableTicks: 0,
  agentSaveResetTimer: null,
};

const $ = (selector) => document.querySelector(selector);

const els = {
  uploadBtn: $("#uploadBtn"),
  uploadStatus: $("#uploadStatus"),
  knowledgeBtn: $("#knowledgeBtn"),
  feedbackBtn: $("#feedbackBtn"),
  agentsBtn: $("#agentsBtn"),
  flowStrategiesBtn: $("#flowStrategiesBtn"),
  strategiesBtn: $("#strategiesBtn"),
  rulesBtn: $("#rulesBtn"),
  fileInput: $("#fileInput"),
  dropZone: $("#dropZone"),
  refreshBtn: $("#refreshBtn"),
  rerunBtn: $("#rerunBtn"),
  contractList: $("#contractList"),
  contractCount: $("#contractCount"),
  todoCount: $("#todoCount"),
  doneCount: $("#doneCount"),
  previewTitle: $("#previewTitle"),
  previewSub: $("#previewSub"),
  emptyPreview: $("#emptyPreview"),
  previewContent: $("#previewContent"),
  contractType: $("#contractType"),
  reviewStatus: $("#reviewStatus"),
  maxAmount: $("#maxAmount"),
  strategyName: $("#strategyName"),
  textTab: $("#textTab"),
  evidenceTabBtns: document.querySelectorAll("[data-evidence-tab]"),
  evidencePanels: document.querySelectorAll("[data-evidence-panel]"),
  clausesEvidenceCount: $("#clausesEvidenceCount"),
  fieldsEvidenceCount: $("#fieldsEvidenceCount"),
  templateEvidenceCount: $("#templateEvidenceCount"),
  strategyEvidenceCount: $("#strategyEvidenceCount"),
  clausesTab: $("#clausesTab"),
  fieldsTab: $("#fieldsTab"),
  templateTab: $("#templateTab"),
  strategyTab: $("#strategyTab"),
  timeline: $("#timeline"),
  riskList: $("#riskList"),
  resultSummary: $("#resultSummary"),
  resultTabs: $("#resultTabs"),
  riskTotal: $("#riskTotal"),
  agentPromptVersion: $("#agentPromptVersion"),
  businessDept: $("#businessDept"),
  initiator: $("#initiator"),
  statTotal: $("#statTotal"),
  statPassed: $("#statPassed"),
  statNeedConfirm: $("#statNeedConfirm"),
  statHighRisk: $("#statHighRisk"),
  statGeneralRisk: $("#statGeneralRisk"),
  statTotalRisk: $("#statTotalRisk"),
  knowledgeModal: $("#knowledgeModal"),
  closeKnowledgeBtn: $("#closeKnowledgeBtn"),
  refreshKnowledgeBtn: $("#refreshKnowledgeBtn"),
  knowledgeCount: $("#knowledgeCount"),
  knowledgeRoot: $("#knowledgeRoot"),
  knowledgeCategories: $("#knowledgeCategories"),
  knowledgeFileInput: $("#knowledgeFileInput"),
  knowledgeSearchInput: $("#knowledgeSearchInput"),
  knowledgeSearchBtn: $("#knowledgeSearchBtn"),
  knowledgeClearSearchBtn: $("#knowledgeClearSearchBtn"),
  knowledgeStats: $("#knowledgeStats"),
  knowledgeList: $("#knowledgeList"),
  feedbackModal: $("#feedbackModal"),
  closeFeedbackBtn: $("#closeFeedbackBtn"),
  refreshFeedbackBtn: $("#refreshFeedbackBtn"),
  feedbackTotal: $("#feedbackTotal"),
  feedbackRejectCount: $("#feedbackRejectCount"),
  feedbackApproveCount: $("#feedbackApproveCount"),
  feedbackOpinionCount: $("#feedbackOpinionCount"),
  feedbackTopRules: $("#feedbackTopRules"),
  feedbackList: $("#feedbackList"),
  feedbackOverview: $("#feedbackOverview"),
  feedbackDetail: $("#feedbackDetail"),
  rulesModal: $("#rulesModal"),
  closeRulesBtn: $("#closeRulesBtn"),
  newRuleBtn: $("#newRuleBtn"),
  resetRulesBtn: $("#resetRulesBtn"),
  rulesList: $("#rulesList"),
  rulesCount: $("#rulesCount"),
  ruleForm: $("#ruleForm"),
  ruleEditorTitle: $("#ruleEditorTitle"),
  ruleEditorSub: $("#ruleEditorSub"),
  ruleEnabled: $("#ruleEnabled"),
  ruleId: $("#ruleId"),
  ruleName: $("#ruleName"),
  rulePriority: $("#rulePriority"),
  ruleRiskLevel: $("#ruleRiskLevel"),
  ruleScope: $("#ruleScope"),
  ruleDescription: $("#ruleDescription"),
  scriptConfigPanel: $("#scriptConfigPanel"),
  ruleScript: $("#ruleScript"),
  ruleScriptLines: $("#ruleScriptLines"),
  instructionField: $("#instructionField"),
  ruleInstruction: $("#ruleInstruction"),
  inputParamsList: $("#inputParamsList"),
  outputParamsList: $("#outputParamsList"),
  addInputParamBtn: $("#addInputParamBtn"),
  addOutputParamBtn: $("#addOutputParamBtn"),
  debugFileInput: $("#debugFileInput"),
  chooseDebugFileBtn: $("#chooseDebugFileBtn"),
  runRuleDebugBtn: $("#runRuleDebugBtn"),
  debugFileName: $("#debugFileName"),
  debugResult: $("#debugResult"),
  deleteRuleBtn: $("#deleteRuleBtn"),
  strategiesModal: $("#strategiesModal"),
  closeStrategiesBtn: $("#closeStrategiesBtn"),
  newStrategyBtn: $("#newStrategyBtn"),
  resetStrategiesBtn: $("#resetStrategiesBtn"),
  strategiesList: $("#strategiesList"),
  strategiesCount: $("#strategiesCount"),
  strategyForm: $("#strategyForm"),
  strategyEditorTitle: $("#strategyEditorTitle"),
  strategyEditorSub: $("#strategyEditorSub"),
  strategyEnabled: $("#strategyEnabled"),
  strategyId: $("#strategyId"),
  strategyNameInput: $("#strategyNameInput"),
  strategyTemplateType: $("#strategyTemplateType"),
  strategyRuleCount: $("#strategyRuleCount"),
  strategyDescription: $("#strategyDescription"),
  strategyInstruction: $("#strategyInstruction"),
  strategyRulesList: $("#strategyRulesList"),
  createRuleFromStrategyBtn: $("#createRuleFromStrategyBtn"),
  deleteStrategyBtn: $("#deleteStrategyBtn"),
  flowStrategiesModal: $("#flowStrategiesModal"),
  closeFlowStrategiesBtn: $("#closeFlowStrategiesBtn"),
  newFlowStrategyBtn: $("#newFlowStrategyBtn"),
  resetFlowStrategiesBtn: $("#resetFlowStrategiesBtn"),
  flowStrategiesList: $("#flowStrategiesList"),
  flowStrategiesCount: $("#flowStrategiesCount"),
  flowStrategyForm: $("#flowStrategyForm"),
  flowStrategyEditorTitle: $("#flowStrategyEditorTitle"),
  flowStrategyEditorSub: $("#flowStrategyEditorSub"),
  flowStrategyEnabled: $("#flowStrategyEnabled"),
  flowStrategyId: $("#flowStrategyId"),
  flowStrategyName: $("#flowStrategyName"),
  flowStrategyDescription: $("#flowStrategyDescription"),
  flowReviewStrategyCount: $("#flowReviewStrategyCount"),
  flowReviewStrategiesList: $("#flowReviewStrategiesList"),
  autoPassMaxP0: $("#autoPassMaxP0"),
  autoPassMaxP1: $("#autoPassMaxP1"),
  autoPassMaxGeneral: $("#autoPassMaxGeneral"),
  autoPassMaxAmount: $("#autoPassMaxAmount"),
  humanConfirmMinAmount: $("#humanConfirmMinAmount"),
  humanConfirmMinP1: $("#humanConfirmMinP1"),
  humanConfirmMinGeneral: $("#humanConfirmMinGeneral"),
  needRevisionMinP0: $("#needRevisionMinP0"),
  needRevisionRuleIds: $("#needRevisionRuleIds"),
  blockedRuleIds: $("#blockedRuleIds"),
  deleteFlowStrategyBtn: $("#deleteFlowStrategyBtn"),
  agentsModal: $("#agentsModal"),
  closeAgentsBtn: $("#closeAgentsBtn"),
  newAgentBtn: $("#newAgentBtn"),
  resetAgentsBtn: $("#resetAgentsBtn"),
  agentsList: $("#agentsList"),
  agentsCount: $("#agentsCount"),
  agentForm: $("#agentForm"),
  agentEditorTitle: $("#agentEditorTitle"),
  agentEditorSub: $("#agentEditorSub"),
  agentEnabled: $("#agentEnabled"),
  agentId: $("#agentId"),
  agentName: $("#agentName"),
  agentDescription: $("#agentDescription"),
  agentSystemPrompt: $("#agentSystemPrompt"),
  agentUserPrompt: $("#agentUserPrompt"),
  agentSkillCount: $("#agentSkillCount"),
  agentSelectedSkills: $("#agentSelectedSkills"),
  agentSkillCatalog: $("#agentSkillCatalog"),
  agentSkillDetail: $("#agentSkillDetail"),
  agentSkillSearch: $("#agentSkillSearch"),
  agentToolCount: $("#agentToolCount"),
  agentSelectedTools: $("#agentSelectedTools"),
  agentToolCatalog: $("#agentToolCatalog"),
  agentToolDetail: $("#agentToolDetail"),
  agentToolSearch: $("#agentToolSearch"),
  agentModelProvider: $("#agentModelProvider"),
  agentModelName: $("#agentModelName"),
  agentModelBaseUrl: $("#agentModelBaseUrl"),
  agentTemperature: $("#agentTemperature"),
  agentModelApiKey: $("#agentModelApiKey"),
  agentModelApiKeyStatus: $("#agentModelApiKeyStatus"),
  agentModelEnabled: $("#agentModelEnabled"),
  agentModelTestBtn: $("#agentModelTestBtn"),
  agentModelTestStatus: $("#agentModelTestStatus"),
  agentSaveStatus: $("#agentSaveStatus"),
  agentSaveBtn: $("#agentSaveBtn"),
  deleteAgentBtn: $("#deleteAgentBtn"),
};

async function api(path, options = {}) {
  const response = await fetch(path, options);
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `HTTP ${response.status}`);
  }
  return response.json();
}

function normalizeErrorMessage(error) {
  return parseApiError(error).message;
}

function parseApiError(error) {
  const raw = error?.message || String(error || "未知错误");
  try {
    const parsed = JSON.parse(raw);
    const detail = parsed.detail || parsed.message || parsed;
    if (typeof detail === "string") return { message: detail };
    if (detail && typeof detail === "object") {
      return {
        ...detail,
        message: detail.message || detail.detail || raw,
      };
    }
    return { message: raw };
  } catch {
    return { message: raw };
  }
}

async function loadContracts() {
  const [data, ruleStats] = await Promise.all([
    api("/api/contracts"),
    api("/api/rules/stats"),
  ]);
  state.contracts = data.items || [];
  state.ruleStats = ruleStats;
  els.contractCount.textContent = state.contracts.length;
  renderStats();
  renderContractList();
  const visibleContracts = getVisibleContracts();
  if (!state.selectedId && visibleContracts[0]) {
    selectContract(visibleContracts[0].id);
  }
}

async function refreshContractListState() {
  const [data, ruleStats] = await Promise.all([
    api("/api/contracts"),
    api("/api/rules/stats"),
  ]);
  state.contracts = data.items || [];
  state.ruleStats = ruleStats;
  els.contractCount.textContent = state.contracts.length;
  renderStats();
  renderContractList();
}

function renderStats() {
  const total = state.contracts.length;
  const passed = state.contracts.filter((item) => item.status === "Completed").length;
  const needConfirm = state.contracts.filter((item) => ["NeedHumanConfirm", "NeedRevision", "Blocked"].includes(item.status)).length;
  const highRisk = state.ruleStats?.high_risk_rules ?? 0;
  const generalRisk = state.ruleStats?.general_risk_rules ?? 0;
  const totalRisk = state.ruleStats?.total_rules ?? 0;
  els.statTotal.textContent = total;
  els.statPassed.textContent = passed;
  els.statNeedConfirm.textContent = needConfirm;
  els.statHighRisk.textContent = highRisk;
  els.statGeneralRisk.textContent = generalRisk;
  els.statTotalRisk.textContent = totalRisk;
}

async function openKnowledgeModal() {
  els.knowledgeModal.classList.remove("hidden");
  await loadKnowledge();
}

async function loadKnowledge(refresh = false) {
  const data = await api(`/api/knowledge${refresh ? "?refresh=true" : ""}`);
  state.knowledge = data;
  state.knowledgeItems = data.items || [];
  if (!state.selectedKnowledgeCategory) state.selectedKnowledgeCategory = "全部";
  renderKnowledge();
}

async function searchKnowledge() {
  const query = els.knowledgeSearchInput.value.trim();
  state.knowledgeQuery = query;
  if (!query) {
    state.knowledgeSearchResults = [];
    renderKnowledge();
    return;
  }
  const data = await api(`/api/knowledge/search?q=${encodeURIComponent(query)}&top_k=10`);
  state.knowledgeSearchResults = data.items || [];
  renderKnowledgeSearchStats(data);
  renderKnowledgeList();
}

function renderKnowledge() {
  const items = state.knowledgeItems || [];
  els.knowledgeCount.textContent = items.length;
  els.knowledgeRoot.innerHTML = `
    <b>索引根目录</b>
    <span>${escapeHtml(state.knowledge?.workspace_root || "-")}</span>
  `;
  renderKnowledgeCategories();
  renderKnowledgeSearchStats();
  renderKnowledgeList();
}

function renderKnowledgeCategories() {
  const categories = state.knowledge?.categories || [];
  const totalChunks = state.knowledge?.chunk_count || 0;
  const categoryButtons = [
    { name: "全部", documents: state.knowledgeItems.length, chunks: totalChunks, exists: true },
    ...categories,
  ];
  els.knowledgeCategories.innerHTML = categoryButtons.map((category) => `
    <article class="knowledge-category ${state.selectedKnowledgeCategory === category.name ? "active" : ""}">
      <button class="knowledge-category-main" type="button" data-knowledge-category="${escapeHtml(category.name)}">
        <span>
          <b>${escapeHtml(category.name)}</b>
          <small>${category.exists ? "可用" : "目录未创建"}</small>
        </span>
        <em>${category.documents || 0} 文档 · ${category.chunks || 0} 片段</em>
      </button>
      ${category.name === "全部" ? "" : `<button class="ghost-btn knowledge-upload-btn" type="button" data-knowledge-upload="${escapeHtml(category.name)}">上传</button>`}
    </article>
  `).join("");
  els.knowledgeCategories.querySelectorAll("[data-knowledge-category]").forEach((button) => {
    button.addEventListener("click", () => {
      state.selectedKnowledgeCategory = button.dataset.knowledgeCategory || "全部";
      state.knowledgeQuery = "";
      state.knowledgeSearchResults = [];
      els.knowledgeSearchInput.value = "";
      renderKnowledge();
    });
  });
  els.knowledgeCategories.querySelectorAll("[data-knowledge-upload]").forEach((button) => {
    button.addEventListener("click", () => {
      state.knowledgeUploadCategory = button.dataset.knowledgeUpload || "";
      els.knowledgeFileInput.value = "";
      els.knowledgeFileInput.click();
    });
  });
}

async function uploadKnowledgeFile(file) {
  if (!file || !state.knowledgeUploadCategory) return;
  const formData = new FormData();
  formData.append("category", state.knowledgeUploadCategory);
  formData.append("file", file);
  const data = await api("/api/knowledge/upload", {
    method: "POST",
    body: formData,
  });
  state.knowledge = data.knowledge;
  state.knowledgeItems = data.knowledge?.items || [];
  state.selectedKnowledgeCategory = data.item?.category || state.knowledgeUploadCategory;
  state.knowledgeQuery = "";
  state.knowledgeSearchResults = [];
  els.knowledgeSearchInput.value = "";
  renderKnowledge();
  toast(`已上传到${state.selectedKnowledgeCategory}。`);
}

function renderKnowledgeSearchStats(data = null) {
  const activeCategory = state.selectedKnowledgeCategory || "全部";
  const query = state.knowledgeQuery;
  const confidence = data?.confidence ?? null;
  const warning = (data?.warnings || [])[0] || "";
  els.knowledgeStats.innerHTML = `
    <span>当前分类：<b>${escapeHtml(activeCategory)}</b></span>
    <span>索引片段：<b>${state.knowledge?.chunk_count || 0}</b></span>
    ${query ? `<span>检索词：<b>${escapeHtml(query)}</b></span>` : ""}
    ${confidence !== null ? `<span>置信度：<b>${Math.round(confidence * 100)}%</b></span>` : ""}
    ${warning ? `<span class="knowledge-warning">${escapeHtml(warning)}</span>` : ""}
  `;
}

function renderKnowledgeList() {
  const query = state.knowledgeQuery;
  const items = query ? filterKnowledgeSearchResults() : filterKnowledgeItems();
  if (!items.length) {
    els.knowledgeList.innerHTML = `
      <div class="empty-state compact-empty">
        <strong>${query ? "未检索到知识片段" : "暂无知识文档"}</strong>
        <span>${query ? "换一个关键词试试。" : "在索引根目录下创建规章制度、合同模板或历史合同目录后刷新索引。"}</span>
      </div>
    `;
    return;
  }
  els.knowledgeList.innerHTML = items.map((item) => query ? renderKnowledgeSearchItem(item) : renderKnowledgeDocumentItem(item)).join("");
}

function filterKnowledgeItems() {
  if (state.selectedKnowledgeCategory === "全部") return state.knowledgeItems;
  return state.knowledgeItems.filter((item) => item.category === state.selectedKnowledgeCategory);
}

function filterKnowledgeSearchResults() {
  if (state.selectedKnowledgeCategory === "全部") return state.knowledgeSearchResults;
  return state.knowledgeSearchResults.filter((item) => item.category === state.selectedKnowledgeCategory);
}

function renderKnowledgeDocumentItem(item) {
  return `
    <article class="knowledge-card">
      <div class="knowledge-card-head">
        <div>
          <b>${escapeHtml(item.title || item.source || "-")}</b>
          <span>${escapeHtml(item.source || "-")}</span>
        </div>
        <em>${escapeHtml(item.category || "-")} · ${item.chunks || 0} 片段</em>
      </div>
      <p>${escapeHtml(item.preview || "暂无可预览内容。")}</p>
    </article>
  `;
}

function renderKnowledgeSearchItem(item) {
  return `
    <article class="knowledge-card search-result-card">
      <div class="knowledge-card-head">
        <div>
          <b>${escapeHtml(item.source || "-")}</b>
          <span>${escapeHtml(item.category || "-")}</span>
        </div>
        <em>相关性 ${escapeHtml(String(item.score ?? "-"))}</em>
      </div>
      <p>${escapeHtml(item.snippet || "暂无片段内容。")}</p>
    </article>
  `;
}

async function openFeedbackModal() {
  els.feedbackModal.classList.remove("hidden");
  await loadHumanFeedback();
}

async function loadHumanFeedback() {
  const data = await api("/api/human-feedback");
  state.feedbackItems = data.items || [];
  state.feedbackSummary = data.summary || {};
  if (!state.selectedFeedbackId && state.feedbackItems[0]) {
    state.selectedFeedbackId = state.feedbackItems[0].id;
  }
  if (state.selectedFeedbackId && !state.feedbackItems.some((item) => item.id === state.selectedFeedbackId)) {
    state.selectedFeedbackId = state.feedbackItems[0]?.id || null;
  }
  renderFeedback();
}

function renderFeedback() {
  renderFeedbackSummary();
  renderFeedbackList();
  renderFeedbackDetail();
}

function renderFeedbackSummary() {
  const summary = state.feedbackSummary || {};
  els.feedbackTotal.textContent = summary.total || 0;
  els.feedbackRejectCount.textContent = summary.reject_count || 0;
  els.feedbackApproveCount.textContent = summary.approve_count || 0;
  els.feedbackOpinionCount.textContent = summary.with_opinion_count || 0;
  const topRules = summary.top_rules || [];
  if (!topRules.length) {
    els.feedbackTopRules.innerHTML = `<div class="feedback-top-empty">暂无高频关联规则</div>`;
    return;
  }
  els.feedbackTopRules.innerHTML = `
    <b>高频关联规则</b>
    ${topRules.map((rule) => `
      <span>${escapeHtml(rule.rule_id)} · ${escapeHtml(rule.rule_name)}<em>${rule.count}</em></span>
    `).join("")}
  `;
}

function renderFeedbackList() {
  const items = state.feedbackItems || [];
  if (!items.length) {
    els.feedbackList.innerHTML = `
      <div class="empty-state compact-empty">
        <strong>暂无人工反馈</strong>
        <span>人工审核提交意见后，会在这里形成可学习的反馈样本。</span>
      </div>
    `;
    return;
  }
  els.feedbackList.innerHTML = items.map((item) => `
    <article class="rule-list-item feedback-list-item ${item.id === state.selectedFeedbackId ? "active" : ""}" data-feedback-id="${escapeHtml(item.id)}">
      <div>
        <b>${escapeHtml(item.contract_name || "未命名合同")}</b>
        <span>${escapeHtml(item.contract_type || "未识别合同类型")} · ${escapeHtml(item.time || "-")}</span>
      </div>
      <div class="rule-list-meta">
        <em class="feedback-action ${escapeHtml(feedbackActionClass(item.action))}">${escapeHtml(feedbackActionLabel(item.action, item.decision))}</em>
        <em class="priority-pill priority-P${item.risk_summary?.p0 ? "0" : item.risk_summary?.p1 ? "1" : "2"}">风险 ${item.risk_summary?.total || 0}</em>
      </div>
    </article>
  `).join("");
  els.feedbackList.querySelectorAll("[data-feedback-id]").forEach((node) => {
    node.addEventListener("click", () => {
      state.selectedFeedbackId = node.dataset.feedbackId;
      renderFeedback();
    });
  });
}

function renderFeedbackDetail() {
  const item = state.feedbackItems.find((entry) => entry.id === state.selectedFeedbackId);
  if (!item) {
    els.feedbackOverview.innerHTML = `
      <div class="feedback-detail-head">
        <div>
          <h3>反馈样本池</h3>
          <p>人工审核提交意见后，系统会把意见、风险、命中条款和规则上下文汇总到这里。</p>
        </div>
      </div>
      <div class="feedback-metrics">
        <span><b>${state.feedbackSummary?.total || 0}</b>反馈</span>
        <span><b>${state.feedbackSummary?.reject_count || 0}</b>退回</span>
        <span><b>${state.feedbackSummary?.approve_count || 0}</b>通过</span>
        <span><b>${state.feedbackSummary?.contract_count || 0}</b>合同</span>
      </div>
    `;
    els.feedbackDetail.innerHTML = `
      <div class="empty-state">
        <strong>暂无反馈详情</strong>
        <span>选择左侧反馈后查看人工意见、关联风险和规则上下文。</span>
      </div>
    `;
    return;
  }
  els.feedbackOverview.innerHTML = `
    <div class="feedback-detail-head">
      <div>
        <h3>${escapeHtml(item.contract_name || "未命名合同")}</h3>
        <p>${escapeHtml(item.contract_type || "-")} · ${escapeHtml(item.review_strategy?.name || "未关联审核策略")}</p>
      </div>
      <div class="feedback-head-actions">
        <span class="feedback-action ${escapeHtml(feedbackActionClass(item.action))}">${escapeHtml(feedbackActionLabel(item.action, item.decision))}</span>
        <button class="ghost-btn" type="button" data-feedback-contract-id="${escapeHtml(item.contract_id || "")}">查看合同</button>
      </div>
    </div>
    <div class="feedback-metrics">
      <span><b>${item.risk_summary?.total || 0}</b>风险</span>
      <span><b>${item.risk_summary?.p0 || 0}</b>P0</span>
      <span><b>${item.risk_summary?.p1 || 0}</b>P1</span>
      <span><b>${formatAmount(item.max_amount)}</b>金额</span>
    </div>
  `;
  els.feedbackDetail.innerHTML = `
    <section class="feedback-card">
      <div class="feedback-card-title">
        <b>人工反馈意见</b>
        <span>${escapeHtml(item.reviewer || "人工审核人")} · ${escapeHtml(item.time || "-")}</span>
      </div>
      <p>${escapeHtml(item.opinion || "未填写补充意见。")}</p>
    </section>
    <section class="feedback-card">
      <div class="feedback-card-title">
        <b>审核上下文</b>
        <span>${escapeHtml(item.status_text || "-")}</span>
      </div>
      <div class="feedback-context-grid">
        <span><b>审核策略</b>${escapeHtml(item.review_strategy?.name || "-")}</span>
        <span><b>流转策略</b>${escapeHtml(item.flow_decision?.flow_strategy || "-")}</span>
        <span><b>流转结论</b>${escapeHtml(item.flow_decision?.status_text || item.flow_decision?.decision || "-")}</span>
        <span><b>经办部门</b>${escapeHtml(item.business_dept || "-")}</span>
      </div>
      ${item.report_summary ? `<p class="feedback-report-summary">${escapeHtml(item.report_summary)}</p>` : ""}
    </section>
    ${renderFeedbackRiskSection(item)}
    ${renderFeedbackPassedRules(item)}
    ${renderFeedbackClauseSection(item)}
  `;
  const openContractBtn = els.feedbackOverview.querySelector("[data-feedback-contract-id]");
  openContractBtn?.addEventListener("click", async () => {
    const contractId = openContractBtn.dataset.feedbackContractId;
    if (!contractId) return;
    els.feedbackModal.classList.add("hidden");
    await selectContract(contractId);
  });
}

function renderFeedbackRiskSection(item) {
  const risks = item.risks || [];
  if (!risks.length) {
    return `
      <section class="feedback-card">
        <div class="feedback-card-title"><b>关联风险</b><span>0 项</span></div>
        <div class="empty-state compact-empty"><strong>该反馈未关联风险项</strong><span>通常发生在人工通过或无风险合同。</span></div>
      </section>
    `;
  }
  return `
    <section class="feedback-card">
      <div class="feedback-card-title"><b>关联风险</b><span>${risks.length} 项</span></div>
      <div class="feedback-risk-list">
        ${risks.map((risk) => `
          <article>
            <div>
              <b>${escapeHtml(risk.rule_id || "-")} · ${escapeHtml(risk.rule_name || "-")}</b>
              <span>${escapeHtml(risk.mode || "-")} · ${escapeHtml(risk.risk_level || "-")} · ${escapeHtml(risk.priority || "-")}</span>
            </div>
            <p>${escapeHtml(risk.issue || "-")}</p>
            <small>${escapeHtml(risk.source_excerpt || risk.suggestion || "")}</small>
          </article>
        `).join("")}
      </div>
    </section>
  `;
}

function renderFeedbackPassedRules(item) {
  const passedRules = item.passed_rules || [];
  if (!passedRules.length) return "";
  return `
    <section class="feedback-card">
      <div class="feedback-card-title"><b>当次通过规则</b><span>${passedRules.length} 条</span></div>
      <div class="feedback-pill-list">
        ${passedRules.map((rule) => `<span>${escapeHtml(rule.rule_id || "-")} · ${escapeHtml(rule.rule_name || "-")}</span>`).join("")}
      </div>
    </section>
  `;
}

function renderFeedbackClauseSection(item) {
  const clauses = item.matched_clauses || [];
  if (!clauses.length) return "";
  return `
    <section class="feedback-card">
      <div class="feedback-card-title"><b>命中条款样本</b><span>${clauses.length} 条</span></div>
      <div class="feedback-clause-list">
        ${clauses.map((clause) => `
          <article>
            <b>${escapeHtml(clause.number || "")}${escapeHtml(clause.title || "未命名条款")}</b>
            <span>${escapeHtml(clause.type || "-")} · ${escapeHtml(clause.location || "-")}</span>
            <p>${escapeHtml(clause.text || "")}</p>
          </article>
        `).join("")}
      </div>
    </section>
  `;
}

function feedbackActionLabel(action, decision) {
  if (decision) return decision;
  if (action === "approve") return "确认通过";
  if (action === "reject") return "确认不通过";
  return "人工反馈";
}

function feedbackActionClass(action) {
  if (action === "approve") return "feedback-action-approve";
  if (action === "reject") return "feedback-action-reject";
  return "feedback-action-neutral";
}

async function openAgentsModal() {
  els.agentsModal.classList.remove("hidden");
  await loadAgents();
}

async function loadAgents() {
  const data = await api("/api/agents");
  state.agents = data.items || [];
  state.availableSkills = data.available_skills || [];
  state.availableTools = data.available_tools || [];
  renderAgentsList();
  const next = state.agents.find((agent) => agent.id === state.selectedAgentId) || state.agents[0];
  if (next) selectAgent(next.id);
  else startNewAgent();
}

function renderAgentsList() {
  els.agentsCount.textContent = state.agents.length;
  if (!state.agents.length) {
    els.agentsList.innerHTML = `<div class="empty-state compact-empty"><strong>暂无智能体</strong><span>恢复默认后开始配置。</span></div>`;
    return;
  }
  els.agentsList.innerHTML = state.agents.map((agent) => `
    <article class="rule-list-item ${agent.id === state.selectedAgentId ? "active" : ""}" data-agent-id="${escapeHtml(agent.id)}">
      <div>
        <b>${escapeHtml(agent.name)}</b>
        <span>${escapeHtml(agent.id)}</span>
      </div>
      <div class="rule-list-meta">
        <em class="mode-pill">${escapeHtml(agent.model?.provider || "-")}</em>
        <em class="priority-pill">${escapeHtml(agent.model?.model || "-")}</em>
        ${agent.enabled ? "" : `<em class="disabled-pill">停用</em>`}
      </div>
    </article>
  `).join("");
  els.agentsList.querySelectorAll("[data-agent-id]").forEach((node) => {
    node.addEventListener("click", () => selectAgent(node.dataset.agentId));
  });
}

function selectAgent(agentId) {
  const agent = state.agents.find((item) => item.id === agentId);
  if (!agent) return;
  state.selectedAgentId = agent.id;
  state.editingAgentOriginalId = agent.id;
  renderAgentsList();
  els.agentEditorTitle.textContent = agent.name;
  els.agentEditorSub.textContent = `智能体编号：${agent.id}`;
  els.agentEnabled.checked = agent.enabled !== false;
  els.agentId.value = agent.id || "";
  els.agentName.value = agent.name || "";
  els.agentDescription.value = agent.description || "";
  els.agentSystemPrompt.value = agent.system_prompt || "";
  els.agentUserPrompt.value = agent.user_prompt || "";
  state.agentSkillIds = [...(agent.skills || [])];
  state.selectedAgentSkillId = state.agentSkillIds[0] || state.availableSkills[0]?.id || null;
  renderAgentSkills();
  state.agentToolIds = [...(agent.tools || [])];
  state.selectedAgentToolId = state.agentToolIds[0] || state.availableTools[0]?.id || null;
  renderAgentTools();
  els.agentModelProvider.value = agent.model?.provider || "openai-compatible";
  els.agentModelName.value = agent.model?.model || "";
  els.agentModelBaseUrl.value = agent.model?.base_url || "";
  els.agentTemperature.value = agent.model?.temperature ?? 0.2;
  els.agentModelApiKey.value = "";
  renderAgentApiKeyStatus(agent);
  els.agentModelEnabled.checked = !!agent.model?.enabled;
  els.deleteAgentBtn.disabled = false;
  setAgentSaveStatus("", "");
  setAgentModelTestStatus("", "");
}

function startNewAgent() {
  state.selectedAgentId = null;
  state.editingAgentOriginalId = null;
  renderAgentsList();
  els.agentEditorTitle.textContent = "新建智能体";
  els.agentEditorSub.textContent = "尚未保存";
  els.agentEnabled.checked = true;
  els.agentId.value = "";
  els.agentName.value = "";
  els.agentDescription.value = "";
  els.agentSystemPrompt.value = "";
  els.agentUserPrompt.value = "";
  state.agentSkillIds = [];
  state.selectedAgentSkillId = state.availableSkills[0]?.id || null;
  renderAgentSkills();
  state.agentToolIds = [];
  state.selectedAgentToolId = state.availableTools[0]?.id || null;
  renderAgentTools();
  els.agentModelProvider.value = "openai-compatible";
  els.agentModelName.value = "";
  els.agentModelBaseUrl.value = "";
  els.agentTemperature.value = 0.2;
  els.agentModelApiKey.value = "";
  renderAgentApiKeyStatus(null);
  els.agentModelEnabled.checked = false;
  els.deleteAgentBtn.disabled = true;
  setAgentSaveStatus("", "");
  setAgentModelTestStatus("", "");
}

function renderAgentApiKeyStatus(agent) {
  const mask = agent?.model?.api_key_mask || "";
  const configured = !!agent?.model?.api_key_configured;
  els.agentModelApiKeyStatus.textContent = configured ? `已配置：${mask}` : "未配置";
}

function renderAgentSkills() {
  const selected = new Set(state.agentSkillIds);
  const catalog = filterResources(state.availableSkills, state.agentSkillSearch);
  els.agentSkillCount.textContent = `已选 ${state.agentSkillIds.length} 个`;
  els.agentSelectedSkills.innerHTML = state.agentSkillIds.length
    ? state.agentSkillIds.map((skillId) => renderAgentSkillItem(skillId, "selected")).join("")
    : `<div class="agent-skill-empty">尚未选择技能</div>`;
  els.agentSkillCatalog.innerHTML = catalog.length ? catalog.map((skill) => `
    <article class="agent-skill-card ${selected.has(skill.id) ? "disabled" : ""} ${skill.id === state.selectedAgentSkillId ? "active" : ""}" data-skill-id="${escapeHtml(skill.id)}">
      <div>
        <b>${escapeHtml(skill.name || skill.id)}</b>
        <small>${escapeHtml(skill.id)}</small>
      </div>
      <button class="ghost-btn skill-add-btn" type="button" ${selected.has(skill.id) ? "disabled" : ""}>添加</button>
    </article>
  `).join("") : `<div class="agent-skill-empty">未找到匹配技能</div>`;
  els.agentSelectedSkills.querySelectorAll("[data-skill-id]").forEach((node) => {
    node.addEventListener("click", () => selectAgentSkill(node.dataset.skillId));
  });
  els.agentSelectedSkills.querySelectorAll(".skill-remove-btn").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      removeAgentSkill(button.closest("[data-skill-id]").dataset.skillId);
    });
  });
  els.agentSkillCatalog.querySelectorAll("[data-skill-id]").forEach((node) => {
    node.addEventListener("click", () => selectAgentSkill(node.dataset.skillId));
  });
  els.agentSkillCatalog.querySelectorAll(".skill-add-btn").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      addAgentSkill(button.closest("[data-skill-id]").dataset.skillId);
    });
  });
  renderAgentSkillDetail();
}

function renderAgentSkillItem(skillId, kind) {
  const skill = findSkill(skillId);
  return `
    <article class="agent-skill-card ${skillId === state.selectedAgentSkillId ? "active" : ""}" data-skill-id="${escapeHtml(skillId)}">
      <div>
        <b>${escapeHtml(skill?.name || skillId)}</b>
        <small>${escapeHtml(skillId)}</small>
      </div>
      ${kind === "selected" ? `<button class="danger-btn skill-remove-btn" type="button">移除</button>` : ""}
    </article>
  `;
}

function selectAgentSkill(skillId) {
  state.selectedAgentSkillId = skillId;
  renderAgentSkills();
}

function addAgentSkill(skillId) {
  if (!state.agentSkillIds.includes(skillId)) {
    state.agentSkillIds.push(skillId);
  }
  state.selectedAgentSkillId = skillId;
  renderAgentSkills();
}

function removeAgentSkill(skillId) {
  state.agentSkillIds = state.agentSkillIds.filter((item) => item !== skillId);
  if (state.selectedAgentSkillId === skillId) {
    state.selectedAgentSkillId = state.agentSkillIds[0] || state.availableSkills[0]?.id || null;
  }
  renderAgentSkills();
}

function renderAgentSkillDetail() {
  const skill = findSkill(state.selectedAgentSkillId);
  if (!skill) {
    els.agentSkillDetail.innerHTML = "点击左侧技能查看详情。";
    return;
  }
  const selectedFile = pickPreviewResourceFile(skill.file_tree, "SKILL.md");
  els.agentSkillDetail.innerHTML = `
    <div class="resource-detail-head">
      <div>
        <b>${escapeHtml(skill.name || skill.id)}</b>
        <span>${escapeHtml(skill.id)}</span>
      </div>
      <em>${escapeHtml(skill.package_path || "")}</em>
    </div>
    <p>${escapeHtml(skill.description || "暂无描述。")}</p>
    <div class="resource-detail-grid">
      <div><strong>输入</strong><small>${escapeHtml(formatValue(skill.inputs || []))}</small></div>
      <div><strong>输出</strong><small>${escapeHtml(formatValue(skill.outputs || []))}</small></div>
      <div><strong>工具</strong><small>${escapeHtml(formatValue(skill.tools || []))}</small></div>
    </div>
    <div class="resource-browser">
      <div class="resource-tree">${renderResourceTree(skill.file_tree, selectedFile?.path)}</div>
      <pre class="resource-file-preview" data-resource-preview>${escapeHtml(formatResourcePreview(selectedFile) || skill.readme || "暂无文件内容。")}</pre>
    </div>
  `;
  bindResourceTreePreview(els.agentSkillDetail, skill.file_tree);
}

function findSkill(skillId) {
  return state.availableSkills.find((skill) => skill.id === skillId);
}

function renderAgentTools() {
  const selected = new Set(state.agentToolIds);
  const catalog = filterResources(state.availableTools, state.agentToolSearch);
  els.agentToolCount.textContent = `已选 ${state.agentToolIds.length} 个`;
  els.agentSelectedTools.innerHTML = state.agentToolIds.length
    ? state.agentToolIds.map((toolId) => renderAgentToolItem(toolId, "selected")).join("")
    : `<div class="agent-skill-empty">尚未选择工具</div>`;
  els.agentToolCatalog.innerHTML = catalog.length ? catalog.map((tool) => `
    <article class="agent-skill-card ${selected.has(tool.id) ? "disabled" : ""} ${tool.id === state.selectedAgentToolId ? "active" : ""}" data-tool-id="${escapeHtml(tool.id)}">
      <div>
        <b>${escapeHtml(tool.name || tool.id)}</b>
        <small>${escapeHtml(tool.id)}</small>
      </div>
      <button class="ghost-btn tool-add-btn" type="button" ${selected.has(tool.id) ? "disabled" : ""}>添加</button>
    </article>
  `).join("") : `<div class="agent-skill-empty">未找到匹配工具</div>`;
  els.agentSelectedTools.querySelectorAll("[data-tool-id]").forEach((node) => {
    node.addEventListener("click", () => selectAgentTool(node.dataset.toolId));
  });
  els.agentSelectedTools.querySelectorAll(".tool-remove-btn").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      removeAgentTool(button.closest("[data-tool-id]").dataset.toolId);
    });
  });
  els.agentToolCatalog.querySelectorAll("[data-tool-id]").forEach((node) => {
    node.addEventListener("click", () => selectAgentTool(node.dataset.toolId));
  });
  els.agentToolCatalog.querySelectorAll(".tool-add-btn").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      addAgentTool(button.closest("[data-tool-id]").dataset.toolId);
    });
  });
  renderAgentToolDetail();
}

function renderAgentToolItem(toolId, kind) {
  const tool = findTool(toolId);
  return `
    <article class="agent-skill-card ${toolId === state.selectedAgentToolId ? "active" : ""}" data-tool-id="${escapeHtml(toolId)}">
      <div>
        <b>${escapeHtml(tool?.name || toolId)}</b>
        <small>${escapeHtml(toolId)}</small>
      </div>
      ${kind === "selected" ? `<button class="danger-btn tool-remove-btn" type="button">移除</button>` : ""}
    </article>
  `;
}

function selectAgentTool(toolId) {
  state.selectedAgentToolId = toolId;
  renderAgentTools();
}

function addAgentTool(toolId) {
  if (!state.agentToolIds.includes(toolId)) {
    state.agentToolIds.push(toolId);
  }
  state.selectedAgentToolId = toolId;
  renderAgentTools();
}

function removeAgentTool(toolId) {
  state.agentToolIds = state.agentToolIds.filter((item) => item !== toolId);
  if (state.selectedAgentToolId === toolId) {
    state.selectedAgentToolId = state.agentToolIds[0] || state.availableTools[0]?.id || null;
  }
  renderAgentTools();
}

function renderAgentToolDetail() {
  const tool = findTool(state.selectedAgentToolId);
  if (!tool) {
    els.agentToolDetail.innerHTML = "点击左侧工具查看详情。";
    return;
  }
  const selectedFile = pickPreviewResourceFile(tool.file_tree);
  els.agentToolDetail.innerHTML = `
    <div class="resource-detail-head">
      <div>
        <b>${escapeHtml(tool.name || tool.id)}</b>
        <span>${escapeHtml(tool.id)}</span>
      </div>
      <em>${escapeHtml(tool.package_path || "")}</em>
    </div>
    <p>${escapeHtml(tool.description || "暂无描述。")}</p>
    <div class="resource-detail-grid">
      <div><strong>被哪些 Skill 使用</strong><small>${escapeHtml(formatValue(tool.used_by || []))}</small></div>
    </div>
    <div class="resource-browser single">
      <div class="resource-tree">${renderResourceTree(tool.file_tree, selectedFile?.path)}</div>
      <pre class="resource-file-preview" data-resource-preview>${escapeHtml(formatResourcePreview(selectedFile) || tool.source || "暂无文件内容。")}</pre>
    </div>
  `;
  bindResourceTreePreview(els.agentToolDetail, tool.file_tree);
}

function findTool(toolId) {
  return state.availableTools.find((tool) => tool.id === toolId);
}

function filterResources(items, query) {
  const keyword = (query || "").trim().toLowerCase();
  if (!keyword) return items;
  return items.filter((item) => [item.id, item.name, item.description].some((value) => String(value || "").toLowerCase().includes(keyword)));
}

function renderResourceTree(node, selectedPath, depth = 0) {
  if (!node) return `<div class="resource-tree-empty">暂无文件结构</div>`;
  const icon = node.type === "dir" ? "▸" : "•";
  const path = node.path || node.name || "";
  const children = (node.children || []).map((child) => renderResourceTree(child, selectedPath, depth + 1)).join("");
  return `
    <button class="resource-tree-node resource-${escapeHtml(node.type)} ${selectedPath === path ? "active" : ""}" style="--depth:${depth}" type="button" data-resource-path="${escapeHtml(path)}" ${node.type === "file" ? "" : "disabled"}>
      <span>${icon}</span>
      <b>${escapeHtml(node.name)}</b>
      ${node.type === "file" ? `<small>${escapeHtml(node.path || "")}</small>` : ""}
    </button>
    ${children}
  `;
}

function pickPreviewResourceFile(node, preferredName) {
  const files = flattenResourceFiles(node);
  return files.find((file) => file.name === preferredName) || files.find((file) => file.name === "SKILL.md") || files[0] || null;
}

function formatResourcePreview(file) {
  if (!file) return "";
  return `# ${file.path || file.name}\n\n${file.content || "该文件暂无内容。"}`;
}

function bindResourceTreePreview(container, root) {
  const filesByPath = Object.fromEntries(flattenResourceFiles(root).map((file) => [file.path || file.name, file]));
  const preview = container.querySelector("[data-resource-preview]");
  container.querySelectorAll("[data-resource-path]").forEach((button) => {
    button.addEventListener("click", () => {
      const file = filesByPath[button.dataset.resourcePath];
      if (!file || !preview) return;
      container.querySelectorAll(".resource-tree-node.active").forEach((node) => node.classList.remove("active"));
      button.classList.add("active");
      preview.textContent = formatResourcePreview(file);
    });
  });
}

function flattenResourceFiles(node) {
  if (!node) return [];
  if (node.type === "file") return [node];
  return (node.children || []).flatMap((child) => flattenResourceFiles(child));
}

function collectAgentForm() {
  return {
    id: els.agentId.value.trim(),
    name: els.agentName.value.trim(),
    description: els.agentDescription.value.trim(),
    system_prompt: els.agentSystemPrompt.value.trim(),
    user_prompt: els.agentUserPrompt.value.trim(),
    skills: state.agentSkillIds,
    tools: state.agentToolIds,
    model: {
      provider: els.agentModelProvider.value.trim(),
      model: els.agentModelName.value.trim(),
      base_url: els.agentModelBaseUrl.value.trim(),
      temperature: Number(els.agentTemperature.value || 0.2),
      api_key: els.agentModelApiKey.value.trim(),
      enabled: els.agentModelEnabled.checked,
    },
    enabled: els.agentEnabled.checked,
  };
}

async function saveCurrentAgent(event) {
  event.preventDefault();
  const path = state.editingAgentOriginalId
    ? `/api/agents/${encodeURIComponent(state.editingAgentOriginalId)}`
    : "/api/agents";
  const method = state.editingAgentOriginalId ? "PUT" : "POST";
  window.clearTimeout(state.agentSaveResetTimer);
  setAgentSaveStatus("saving", "正在保存...");
  els.agentSaveBtn.disabled = true;
  els.agentSaveBtn.textContent = "保存中...";
  try {
    const data = await api(path, {
      method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(collectAgentForm()),
    });
    state.selectedAgentId = data.item.id;
    await loadAgents();
    setAgentSaveStatus("success", `保存成功：${data.item.name || data.item.id}`);
    els.agentSaveBtn.textContent = "已保存";
    toast(`保存成功：${data.item.name || data.item.id}，后续审核将使用该配置。`, "success");
    state.agentSaveResetTimer = window.setTimeout(() => {
      els.agentSaveBtn.textContent = "保存智能体";
    }, 1800);
  } catch (error) {
    const message = normalizeErrorMessage(error);
    setAgentSaveStatus("error", `保存失败：${message}`);
    els.agentSaveBtn.textContent = "保存失败";
    toast(`保存智能体失败：${message}`, "error");
    state.agentSaveResetTimer = window.setTimeout(() => {
      els.agentSaveBtn.textContent = "保存智能体";
    }, 2200);
  } finally {
    els.agentSaveBtn.disabled = false;
  }
}

function setAgentSaveStatus(type, message) {
  if (!els.agentSaveStatus) return;
  els.agentSaveStatus.textContent = message || "";
  els.agentSaveStatus.className = `save-status ${type ? `save-status-${type}` : ""}`;
}

async function testAgentModelConnection() {
  setAgentModelTestStatus("testing", "正在测试连接...");
  els.agentModelTestBtn.disabled = true;
  try {
    const data = await api("/api/agents/test-llm", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(collectAgentForm()),
    });
    if (data.ok) {
      const usageText = data.usage?.total_tokens ? `，消耗 ${data.usage.total_tokens} tokens` : "";
      setAgentModelTestStatus("success", `连接成功：${data.provider || "-"} / ${data.model || "-"}${usageText}`);
      toast("大模型连接测试成功。");
    } else {
      setAgentModelTestStatus("error", `连接失败：${data.error || "大模型调用失败"}`);
      toast(`大模型连接失败：${data.error || "调用失败"}`);
    }
  } catch (error) {
    const message = normalizeErrorMessage(error);
    setAgentModelTestStatus("error", `连接失败：${message}`);
    toast(`大模型连接失败：${message}`);
  } finally {
    els.agentModelTestBtn.disabled = false;
  }
}

function setAgentModelTestStatus(type, message) {
  if (!els.agentModelTestStatus) return;
  els.agentModelTestStatus.textContent = message || "";
  els.agentModelTestStatus.className = `model-test-status ${type ? `model-test-status-${type}` : ""}`;
}

async function deleteCurrentAgent() {
  if (!state.editingAgentOriginalId) return;
  if (!confirm(`确认删除智能体 ${state.editingAgentOriginalId}？`)) return;
  await api(`/api/agents/${encodeURIComponent(state.editingAgentOriginalId)}`, { method: "DELETE" });
  toast("智能体已删除。");
  state.selectedAgentId = null;
  state.editingAgentOriginalId = null;
  await loadAgents();
}

async function resetAgents() {
  if (!confirm("确认恢复默认智能体配置？当前智能体配置会被覆盖。")) return;
  const data = await api("/api/agents/reset", { method: "POST" });
  state.agents = data.items || [];
  state.selectedAgentId = state.agents[0]?.id || null;
  toast("已恢复默认智能体配置。");
  renderAgentsList();
  if (state.selectedAgentId) selectAgent(state.selectedAgentId);
}

async function openFlowStrategiesModal() {
  els.flowStrategiesModal.classList.remove("hidden");
  await loadFlowStrategies();
}

async function loadFlowStrategies() {
  const data = await api("/api/flow-strategies");
  state.flowStrategies = data.items || [];
  state.flowReviewStrategies = data.review_strategies || [];
  state.flowRules = data.rules || [];
  renderFlowStrategiesList();
  const next = state.flowStrategies.find((item) => item.id === state.selectedFlowStrategyId) || state.flowStrategies[0];
  if (next) selectFlowStrategy(next.id);
  else startNewFlowStrategy();
}

function renderFlowStrategiesList() {
  els.flowStrategiesCount.textContent = state.flowStrategies.length;
  if (!state.flowStrategies.length) {
    els.flowStrategiesList.innerHTML = `<div class="empty-state compact-empty"><strong>暂无流转策略</strong><span>新建后关联审核策略。</span></div>`;
    return;
  }
  els.flowStrategiesList.innerHTML = state.flowStrategies.map((item) => `
    <article class="rule-list-item ${item.id === state.selectedFlowStrategyId ? "active" : ""}" data-flow-strategy-id="${escapeHtml(item.id)}">
      <div>
        <b>${escapeHtml(item.name)}</b>
        <span>${escapeHtml(item.id)}</span>
      </div>
      <div class="rule-list-meta">
        <em class="mode-pill">${(item.review_strategy_ids || []).length} 套审核策略</em>
        ${item.enabled ? "" : `<em class="disabled-pill">停用</em>`}
      </div>
    </article>
  `).join("");
  els.flowStrategiesList.querySelectorAll("[data-flow-strategy-id]").forEach((node) => {
    node.addEventListener("click", () => selectFlowStrategy(node.dataset.flowStrategyId));
  });
}

function selectFlowStrategy(flowStrategyId) {
  const item = state.flowStrategies.find((strategy) => strategy.id === flowStrategyId);
  if (!item) return;
  state.selectedFlowStrategyId = item.id;
  state.editingFlowStrategyOriginalId = item.id;
  renderFlowStrategiesList();
  els.flowStrategyEditorTitle.textContent = item.name;
  els.flowStrategyEditorSub.textContent = `关联 ${(item.review_strategy_ids || []).length} 套审核策略`;
  els.flowStrategyEnabled.checked = item.enabled !== false;
  els.flowStrategyId.value = item.id || "";
  els.flowStrategyName.value = item.name || "";
  els.flowStrategyDescription.value = item.description || "";
  els.autoPassMaxP0.value = item.auto_pass_max_p0 ?? 0;
  els.autoPassMaxP1.value = item.auto_pass_max_p1 ?? 0;
  els.autoPassMaxGeneral.value = item.auto_pass_max_general ?? 2;
  els.autoPassMaxAmount.value = item.auto_pass_max_amount ?? 100000;
  els.humanConfirmMinAmount.value = item.human_confirm_min_amount ?? 100000;
  els.humanConfirmMinP1.value = item.human_confirm_min_p1 ?? 1;
  els.humanConfirmMinGeneral.value = item.human_confirm_min_general ?? 3;
  els.needRevisionMinP0.value = item.need_revision_min_p0 ?? 1;
  els.needRevisionRuleIds.value = (item.need_revision_rule_ids || []).join("，");
  els.blockedRuleIds.value = (item.blocked_rule_ids || []).join("，");
  els.deleteFlowStrategyBtn.disabled = false;
  renderFlowReviewStrategyChecklist(item.review_strategy_ids || []);
}

function startNewFlowStrategy() {
  state.selectedFlowStrategyId = null;
  state.editingFlowStrategyOriginalId = null;
  renderFlowStrategiesList();
  els.flowStrategyEditorTitle.textContent = "新建流转策略";
  els.flowStrategyEditorSub.textContent = "关联审核策略并配置流转条件";
  els.flowStrategyEnabled.checked = true;
  els.flowStrategyId.value = "";
  els.flowStrategyName.value = "";
  els.flowStrategyDescription.value = "";
  els.autoPassMaxP0.value = 0;
  els.autoPassMaxP1.value = 0;
  els.autoPassMaxGeneral.value = 2;
  els.autoPassMaxAmount.value = 100000;
  els.humanConfirmMinAmount.value = 100000;
  els.humanConfirmMinP1.value = 1;
  els.humanConfirmMinGeneral.value = 3;
  els.needRevisionMinP0.value = 1;
  els.needRevisionRuleIds.value = "";
  els.blockedRuleIds.value = "";
  els.deleteFlowStrategyBtn.disabled = true;
  renderFlowReviewStrategyChecklist([]);
}

function renderFlowReviewStrategyChecklist(selectedStrategyIds) {
  const selected = new Set(selectedStrategyIds || []);
  els.flowReviewStrategyCount.textContent = `已选 ${selected.size} 个`;
  if (!state.flowReviewStrategies.length) {
    els.flowReviewStrategiesList.innerHTML = `<div class="empty-state compact-empty"><strong>暂无审核策略</strong><span>请先配置审核策略。</span></div>`;
    return;
  }
  els.flowReviewStrategiesList.innerHTML = state.flowReviewStrategies.map((strategy) => `
    <label class="strategy-rule-item">
      <input type="checkbox" value="${escapeHtml(strategy.id)}" ${selected.has(strategy.id) ? "checked" : ""} />
      <span>
        <b>${escapeHtml(strategy.name)}</b>
        <small>${escapeHtml(strategy.id)} · ${escapeHtml(strategy.template_type)} · ${(strategy.rule_ids || []).length} 条规则</small>
      </span>
    </label>
  `).join("");
  els.flowReviewStrategiesList.querySelectorAll("input[type='checkbox']").forEach((checkbox) => {
    checkbox.addEventListener("change", () => {
      els.flowReviewStrategyCount.textContent = `已选 ${collectFlowReviewStrategyIds().length} 个`;
    });
  });
}

function collectFlowReviewStrategyIds() {
  return [...els.flowReviewStrategiesList.querySelectorAll("input[type='checkbox']:checked")].map((node) => node.value);
}

function collectFlowStrategyForm() {
  return {
    id: els.flowStrategyId.value.trim(),
    name: els.flowStrategyName.value.trim(),
    description: els.flowStrategyDescription.value.trim(),
    review_strategy_ids: collectFlowReviewStrategyIds(),
    auto_pass_max_p0: Number(els.autoPassMaxP0.value || 0),
    auto_pass_max_p1: Number(els.autoPassMaxP1.value || 0),
    auto_pass_max_general: Number(els.autoPassMaxGeneral.value || 0),
    auto_pass_max_amount: Number(els.autoPassMaxAmount.value || 0),
    human_confirm_min_amount: Number(els.humanConfirmMinAmount.value || 0),
    human_confirm_min_p1: Number(els.humanConfirmMinP1.value || 0),
    human_confirm_min_general: Number(els.humanConfirmMinGeneral.value || 0),
    need_revision_min_p0: Number(els.needRevisionMinP0.value || 0),
    need_revision_rule_ids: splitCommaList(els.needRevisionRuleIds.value),
    blocked_rule_ids: splitCommaList(els.blockedRuleIds.value),
    enabled: els.flowStrategyEnabled.checked,
  };
}

async function saveCurrentFlowStrategy(event) {
  event.preventDefault();
  const path = state.editingFlowStrategyOriginalId
    ? `/api/flow-strategies/${encodeURIComponent(state.editingFlowStrategyOriginalId)}`
    : "/api/flow-strategies";
  const method = state.editingFlowStrategyOriginalId ? "PUT" : "POST";
  const data = await api(path, {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(collectFlowStrategyForm()),
  });
  toast("审核流转策略已保存。");
  state.selectedFlowStrategyId = data.item.id;
  await loadFlowStrategies();
}

async function deleteCurrentFlowStrategy() {
  if (!state.editingFlowStrategyOriginalId) return;
  if (!confirm(`确认删除审核流转策略 ${state.editingFlowStrategyOriginalId}？`)) return;
  await api(`/api/flow-strategies/${encodeURIComponent(state.editingFlowStrategyOriginalId)}`, { method: "DELETE" });
  toast("审核流转策略已删除。");
  state.selectedFlowStrategyId = null;
  state.editingFlowStrategyOriginalId = null;
  await loadFlowStrategies();
}

async function resetFlowStrategies() {
  if (!confirm("确认恢复默认审核流转策略？当前流转策略配置会被覆盖。")) return;
  const data = await api("/api/flow-strategies/reset", { method: "POST" });
  state.flowStrategies = data.items || [];
  state.flowReviewStrategies = data.review_strategies || [];
  state.flowRules = data.rules || [];
  state.selectedFlowStrategyId = state.flowStrategies[0]?.id || null;
  toast("已恢复默认审核流转策略。");
  renderFlowStrategiesList();
  if (state.selectedFlowStrategyId) selectFlowStrategy(state.selectedFlowStrategyId);
}

async function openStrategiesModal() {
  els.strategiesModal.classList.remove("hidden");
  await loadStrategies();
}

async function loadStrategies() {
  const data = await api("/api/strategies");
  state.strategies = data.items || [];
  state.strategyRules = data.rules || [];
  renderStrategiesList();
  const next = state.strategies.find((strategy) => strategy.id === state.selectedStrategyId) || state.strategies[0];
  if (next) selectStrategy(next.id);
  else startNewStrategy();
}

function renderStrategiesList() {
  els.strategiesCount.textContent = state.strategies.length;
  if (!state.strategies.length) {
    els.strategiesList.innerHTML = `<div class="empty-state compact-empty"><strong>暂无策略</strong><span>新建一个模板策略开始配置。</span></div>`;
    return;
  }
  els.strategiesList.innerHTML = state.strategies.map((strategy) => `
    <article class="rule-list-item ${strategy.id === state.selectedStrategyId ? "active" : ""}" data-strategy-id="${escapeHtml(strategy.id)}">
      <div>
        <b>${escapeHtml(strategy.name)}</b>
        <span>${escapeHtml(strategy.template_type)} · ${escapeHtml(strategy.id)}</span>
      </div>
      <div class="rule-list-meta">
        <em class="mode-pill">${(strategy.rule_ids || []).length} 条规则</em>
        ${strategy.enabled ? "" : `<em class="disabled-pill">停用</em>`}
      </div>
    </article>
  `).join("");
  els.strategiesList.querySelectorAll("[data-strategy-id]").forEach((node) => {
    node.addEventListener("click", () => selectStrategy(node.dataset.strategyId));
  });
}

function selectStrategy(strategyId) {
  const strategy = state.strategies.find((item) => item.id === strategyId);
  if (!strategy) return;
  state.selectedStrategyId = strategy.id;
  state.editingStrategyOriginalId = strategy.id;
  renderStrategiesList();
  els.strategyEditorTitle.textContent = strategy.name;
  els.strategyEditorSub.textContent = `模板类型：${strategy.template_type}`;
  els.strategyEnabled.checked = strategy.enabled !== false;
  els.strategyId.value = strategy.id || "";
  els.strategyNameInput.value = strategy.name || "";
  els.strategyTemplateType.value = strategy.template_type || "";
  els.strategyDescription.value = strategy.description || "";
  els.strategyInstruction.value = strategy.agent_instruction || "";
  els.deleteStrategyBtn.disabled = false;
  renderStrategyRuleChecklist(strategy.rule_ids || []);
}

function startNewStrategy() {
  state.selectedStrategyId = null;
  state.editingStrategyOriginalId = null;
  renderStrategiesList();
  els.strategyEditorTitle.textContent = "新建审核策略";
  els.strategyEditorSub.textContent = "按合同模板类型关联规则";
  els.strategyEnabled.checked = true;
  els.strategyId.value = "";
  els.strategyNameInput.value = "";
  els.strategyTemplateType.value = "";
  els.strategyDescription.value = "";
  els.strategyInstruction.value = "";
  els.deleteStrategyBtn.disabled = true;
  renderStrategyRuleChecklist([]);
}

function renderStrategyRuleChecklist(selectedRuleIds) {
  const selected = new Set(selectedRuleIds || []);
  els.strategyRuleCount.value = selected.size ? `${selected.size} 条` : "未关联";
  if (!state.strategyRules.length) {
    els.strategyRulesList.innerHTML = `<div class="empty-state compact-empty"><strong>暂无规则</strong><span>请先在规则配置中新建规则。</span></div>`;
    return;
  }
  els.strategyRulesList.innerHTML = state.strategyRules.map((rule) => `
    <label class="strategy-rule-item">
      <input type="checkbox" value="${escapeHtml(rule.id)}" ${selected.has(rule.id) ? "checked" : ""} />
      <span>
        <b>${escapeHtml(rule.name)}</b>
        <small>${escapeHtml(rule.id)} · ${escapeHtml(rule.mode)} · ${escapeHtml(rule.priority)} · ${escapeHtml(rule.risk_level)}</small>
      </span>
    </label>
  `).join("");
  els.strategyRulesList.querySelectorAll("input[type='checkbox']").forEach((checkbox) => {
    checkbox.addEventListener("change", updateStrategyRuleCount);
  });
}

function updateStrategyRuleCount() {
  els.strategyRuleCount.value = `${collectStrategyRuleIds().length} 条`;
}

function collectStrategyRuleIds() {
  return [...els.strategyRulesList.querySelectorAll("input[type='checkbox']:checked")].map((node) => node.value);
}

function collectStrategyForm() {
  return {
    id: els.strategyId.value.trim(),
    name: els.strategyNameInput.value.trim(),
    template_type: els.strategyTemplateType.value.trim(),
    description: els.strategyDescription.value.trim(),
    agent_instruction: els.strategyInstruction.value.trim(),
    rule_ids: collectStrategyRuleIds(),
    enabled: els.strategyEnabled.checked,
  };
}

async function saveCurrentStrategy(event) {
  event.preventDefault();
  const path = state.editingStrategyOriginalId
    ? `/api/strategies/${encodeURIComponent(state.editingStrategyOriginalId)}`
    : "/api/strategies";
  const method = state.editingStrategyOriginalId ? "PUT" : "POST";
  const data = await api(path, {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(collectStrategyForm()),
  });
  toast("审核策略已保存。");
  state.selectedStrategyId = data.item.id;
  await loadStrategies();
}

async function deleteCurrentStrategy() {
  if (!state.editingStrategyOriginalId) return;
  if (!confirm(`确认删除审核策略 ${state.editingStrategyOriginalId}？`)) return;
  await api(`/api/strategies/${encodeURIComponent(state.editingStrategyOriginalId)}`, { method: "DELETE" });
  toast("审核策略已删除。");
  state.selectedStrategyId = null;
  state.editingStrategyOriginalId = null;
  await loadStrategies();
}

async function resetStrategies() {
  if (!confirm("确认恢复默认审核策略？当前策略配置会被覆盖。")) return;
  const data = await api("/api/strategies/reset", { method: "POST" });
  state.strategies = data.items || [];
  state.strategyRules = data.rules || [];
  state.selectedStrategyId = state.strategies[0]?.id || null;
  toast("已恢复默认审核策略。");
  renderStrategiesList();
  if (state.selectedStrategyId) selectStrategy(state.selectedStrategyId);
}

function createRuleFromStrategy() {
  els.strategiesModal.classList.add("hidden");
  openRulesModal().then(() => {
    startNewRule();
    const templateType = els.strategyTemplateType.value.trim();
    if (templateType) {
      els.ruleScope.value = `${templateType}，策略规则`;
    }
  }).catch((error) => toast(error.message));
}

function splitCommaList(value) {
  return value.split(/[,，]/).map((item) => item.trim()).filter(Boolean);
}

async function openRulesModal() {
  els.rulesModal.classList.remove("hidden");
  await loadRules();
}

async function loadRules() {
  const data = await api("/api/rules");
  state.rules = data.items || [];
  renderRulesList();
  if (!state.selectedRuleId && state.rules[0]) {
    selectRule(state.rules[0].id);
  } else if (state.selectedRuleId) {
    const next = state.rules.find((rule) => rule.id === state.selectedRuleId) || state.rules[0];
    if (next) selectRule(next.id);
    else startNewRule();
  } else {
    startNewRule();
  }
}

function renderRulesList() {
  els.rulesCount.textContent = state.rules.length;
  if (!state.rules.length) {
    els.rulesList.innerHTML = `<div class="empty-state compact-empty"><strong>暂无规则</strong><span>新建一条规则开始配置。</span></div>`;
    return;
  }
  els.rulesList.innerHTML = state.rules.map((rule) => `
    <article class="rule-list-item ${rule.id === state.selectedRuleId ? "active" : ""}" data-rule-id="${escapeHtml(rule.id)}">
      <div>
        <b>${escapeHtml(rule.name)}</b>
        <span>${escapeHtml(rule.id)}</span>
      </div>
      <div class="rule-list-meta">
        <em class="mode-pill">${escapeHtml(rule.mode)}</em>
        <em class="priority-pill priority-${escapeHtml(rule.priority)}">${escapeHtml(rule.priority)}</em>
        ${rule.enabled ? "" : `<em class="disabled-pill">停用</em>`}
      </div>
    </article>
  `).join("");
  els.rulesList.querySelectorAll(".rule-list-item").forEach((node) => {
    node.addEventListener("click", () => selectRule(node.dataset.ruleId));
  });
}

function selectRule(ruleId) {
  const rule = state.rules.find((item) => item.id === ruleId);
  if (!rule) return;
  state.selectedRuleId = rule.id;
  state.editingRuleOriginalId = rule.id;
  state.currentRuleMode = rule.mode || "脚本模式";
  renderRulesList();
  fillRuleForm(rule);
}

function fillRuleForm(rule) {
  els.ruleEditorTitle.textContent = rule.name || "新建规则";
  els.ruleEditorSub.textContent = rule.id ? `规则编号：${rule.id}` : "尚未保存";
  els.ruleEnabled.checked = rule.enabled !== false;
  els.ruleId.value = rule.id || "";
  els.ruleName.value = rule.name || "";
  els.rulePriority.value = rule.priority || "P2";
  els.ruleRiskLevel.value = rule.risk_level === "一般风险" ? "一般风险" : "高风险";
  els.ruleScope.value = (rule.scope || []).join("，");
  els.ruleDescription.value = rule.description || "";
  els.ruleScript.value = rule.script || defaultRuleScript();
  updateScriptLineNumbers();
  els.ruleInstruction.value = rule.instruction || "";
  state.inputParams = normalizeParamState(rule.input_params || defaultInputParams());
  state.outputParams = normalizeParamState(rule.output_params || defaultOutputParams());
  renderParamLists();
  clearDebugResult();
  els.deleteRuleBtn.disabled = !state.editingRuleOriginalId;
  renderRuleMode();
}

function startNewRule() {
  state.selectedRuleId = null;
  state.editingRuleOriginalId = null;
  state.currentRuleMode = "脚本模式";
  renderRulesList();
  fillRuleForm({
    id: "",
    name: "",
    mode: "脚本模式",
    priority: "P2",
    risk_level: "一般风险",
    scope: [],
    description: "",
    enabled: true,
    script: defaultRuleScript(),
    instruction: "",
    input_params: defaultInputParams(),
    output_params: defaultOutputParams(),
  });
}

function renderRuleMode() {
  document.querySelectorAll(".mode-tab").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.ruleMode === state.currentRuleMode);
  });
  els.scriptConfigPanel.classList.toggle("hidden", state.currentRuleMode !== "脚本模式");
  els.instructionField.classList.toggle("hidden", state.currentRuleMode !== "指令模式");
}

function collectRuleForm() {
  return {
    id: els.ruleId.value.trim(),
    name: els.ruleName.value.trim(),
    mode: state.currentRuleMode,
    priority: els.rulePriority.value,
    risk_level: els.ruleRiskLevel.value.trim(),
    scope: els.ruleScope.value.split(/[,，]/).map((item) => item.trim()).filter(Boolean),
    description: els.ruleDescription.value.trim(),
    enabled: els.ruleEnabled.checked,
    script: els.ruleScript.value.trim(),
    instruction: els.ruleInstruction.value.trim(),
    input_params: collectParams("input"),
    output_params: collectParams("output"),
  };
}

async function saveCurrentRule(event) {
  event.preventDefault();
  const payload = collectRuleForm();
  const path = state.editingRuleOriginalId
    ? `/api/rules/${encodeURIComponent(state.editingRuleOriginalId)}`
    : "/api/rules";
  const method = state.editingRuleOriginalId ? "PUT" : "POST";
  const data = await api(path, {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  toast("规则已保存。");
  state.selectedRuleId = data.item.id;
  await Promise.all([loadRules(), loadContracts()]);
}

async function deleteCurrentRule() {
  if (!state.editingRuleOriginalId) return;
  if (!confirm(`确认删除规则 ${state.editingRuleOriginalId}？`)) return;
  await api(`/api/rules/${encodeURIComponent(state.editingRuleOriginalId)}`, { method: "DELETE" });
  toast("规则已删除。");
  state.selectedRuleId = null;
  state.editingRuleOriginalId = null;
  await Promise.all([loadRules(), loadContracts()]);
}

async function resetRules() {
  if (!confirm("确认恢复默认规则？当前规则配置会被覆盖。")) return;
  const data = await api("/api/rules/reset", { method: "POST" });
  state.rules = data.items || [];
  state.selectedRuleId = state.rules[0]?.id || null;
  toast("已恢复默认规则。");
  renderRulesList();
  if (state.selectedRuleId) selectRule(state.selectedRuleId);
  await loadContracts();
}

function defaultRuleScript() {
  return `# 输入参数会按参数名注入为同名变量
# 系统上下文也可使用：text、contract_type、fields、rule_inputs
passed = True
issue = ""
suggestion = ""
evidence = []`;
}

function updateScriptLineNumbers() {
  if (!els.ruleScript || !els.ruleScriptLines) return;
  const lineCount = Math.max(1, els.ruleScript.value.split("\n").length);
  els.ruleScriptLines.textContent = Array.from({ length: lineCount }, (_, index) => index + 1).join("\n");
}

function syncScriptLineScroll() {
  if (!els.ruleScript || !els.ruleScriptLines) return;
  els.ruleScriptLines.scrollTop = els.ruleScript.scrollTop;
}

function defaultInputParams() {
  return [
    { display_name: "合同主体列表", name: "parties", type: "array", description: "从合同中抽取甲方、乙方、买方、卖方等签约主体名称。" },
  ];
}

function defaultOutputParams() {
  return [
    { display_name: "是否通过", name: "passed", type: "boolean", description: "规则判断是否通过。" },
    { display_name: "风险问题", name: "issue", type: "string", description: "未通过时的问题描述。" },
    { display_name: "修改建议", name: "suggestion", type: "string", description: "未通过时的修改建议。" },
    { display_name: "判断依据", name: "evidence", type: "array", description: "支撑判断的字段、关键词或制度依据。" },
  ];
}

function normalizeParamState(params) {
  return (params || []).map((param) => ({
    display_name: param.display_name || param.name || "",
    name: param.name || "",
    type: param.type || "string",
    description: param.description || "",
  }));
}

function renderParamLists() {
  els.inputParamsList.innerHTML = renderParamRows(state.inputParams, "input");
  els.outputParamsList.innerHTML = renderParamRows(state.outputParams, "output");
}

function renderParamRows(params, kind) {
  if (!params.length) {
    return `<div class="param-empty">暂无参数</div>`;
  }
  return params.map((param, index) => `
    <div class="param-row" data-param-kind="${kind}" data-param-index="${index}">
      <input class="param-display-name" placeholder="显示名" value="${escapeHtml(param.display_name)}" />
      <input class="param-name" placeholder="参数名" value="${escapeHtml(param.name)}" />
      <select class="param-type">
        ${["string", "number", "boolean", "array", "object"].map((type) => `
          <option value="${type}" ${param.type === type ? "selected" : ""}>${type}</option>
        `).join("")}
      </select>
      <input class="param-description" placeholder="参数描述" value="${escapeHtml(param.description)}" />
      <button class="ghost-btn param-remove-btn" type="button">删除</button>
    </div>
  `).join("");
}

function collectParams(kind) {
  return [...document.querySelectorAll(`.param-row[data-param-kind="${kind}"]`)]
    .map((row) => ({
      display_name: row.querySelector(".param-display-name")?.value.trim() || "",
      name: row.querySelector(".param-name")?.value.trim() || "",
      type: row.querySelector(".param-type")?.value || "string",
      description: row.querySelector(".param-description")?.value.trim() || "",
    }))
    .filter((param) => param.name);
}

function addParam(kind) {
  const target = kind === "input" ? state.inputParams : state.outputParams;
  target.push({ display_name: "", name: "", type: "string", description: "" });
  renderParamLists();
}

function removeParam(kind, index) {
  const target = kind === "input" ? state.inputParams : state.outputParams;
  target.splice(index, 1);
  renderParamLists();
}

function syncParamStateFromDom() {
  state.inputParams = collectParams("input");
  state.outputParams = collectParams("output");
}

function clearDebugResult() {
  state.debugFile = null;
  if (els.debugFileInput) els.debugFileInput.value = "";
  els.debugFileName.textContent = "未选择文件";
  els.runRuleDebugBtn.disabled = true;
  els.debugResult.classList.add("hidden");
  els.debugResult.innerHTML = "";
}

async function runRuleDebug() {
  if (!state.debugFile) return;
  const form = new FormData();
  form.append("file", state.debugFile);
  form.append("rule_json", JSON.stringify(collectRuleForm()));
  els.runRuleDebugBtn.disabled = true;
  els.debugResult.classList.remove("hidden");
  els.debugResult.innerHTML = `<b>调试中</b><p>正在解析文件并运行当前规则...</p>`;
  try {
    const data = await api("/api/rules/debug", { method: "POST", body: form });
    renderDebugResult(data);
  } finally {
    els.runRuleDebugBtn.disabled = false;
  }
}

function renderDebugResult(data) {
  const event = data.result?.data?.rule_event || {};
  const warnings = data.result?.warnings || [];
  els.debugResult.innerHTML = `
    <div class="debug-result-head">
      <b>${event.passed ? "通过" : "未通过"}</b>
      <span>${escapeHtml(data.understanding?.contract_type || "-")}</span>
    </div>
    <div class="debug-result-grid">
      <div><b>问题</b><span>${escapeHtml(event.issue || "无")}</span></div>
      <div><b>建议</b><span>${escapeHtml(event.suggestion || "无")}</span></div>
      <div><b>执行模式</b><span>${escapeHtml(event.mode || "-")}</span></div>
      <div><b>证据数量</b><span>${(event.evidence || []).length}</span></div>
    </div>
    ${warnings.length ? `<p class="debug-warning">${escapeHtml(warnings.join("；"))}</p>` : ""}
  `;
}

function renderContractList() {
  renderContractListTabs();
  if (!state.contracts.length) {
    els.contractList.innerHTML = `<div class="empty-state"><strong>合同库为空</strong><span>上传第一份合同开始审核。</span></div>`;
    return;
  }
  const visibleContracts = getVisibleContracts();
  if (!visibleContracts.length) {
    const title = state.contractListTab === "todo" ? "暂无待办合同" : "暂无已办合同";
    const tip = state.contractListTab === "todo" ? "需要人工确认的合同会显示在这里。" : "人工已确认或审核完成的合同会显示在这里。";
    els.contractList.innerHTML = `<div class="empty-state compact-empty"><strong>${title}</strong><span>${tip}</span></div>`;
    return;
  }
  els.contractList.innerHTML = visibleContracts.map((item) => `
    <article class="contract-item ${item.id === state.selectedId ? "active" : ""}" data-id="${item.id}">
      <div class="contract-item-head">
        <b>${escapeHtml(item.name)}</b>
        ${state.contractListTab === "done" ? `<button class="archive-contract-btn" type="button" data-archive-id="${escapeHtml(item.id)}">归档</button>` : ""}
      </div>
      <div class="contract-meta">
        <span class="status-pill status-${item.status}">${escapeHtml(item.status_text || item.status)}</span>
        <span>${escapeHtml(item.contract_type || "待识别")}</span>
        ${item.flow_strategy ? `<span>${escapeHtml(item.flow_strategy)}</span>` : ""}
        <span class="risk-pill">风险 ${item.risk_count || 0}</span>
        ${item.p0_count ? `<span class="risk-pill">P0 ${item.p0_count}</span>` : ""}
        ${item.p1_count ? `<span class="risk-pill">P1 ${item.p1_count}</span>` : ""}
      </div>
    </article>
  `).join("");
  document.querySelectorAll(".contract-item").forEach((node) => {
    node.addEventListener("click", () => selectContract(node.dataset.id));
  });
  document.querySelectorAll("[data-archive-id]").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      archiveContract(button.dataset.archiveId).catch((error) => toast(error.message));
    });
  });
}

function renderContractListTabs() {
  const todo = state.contracts.filter((item) => getContractListBucket(item) === "todo").length;
  const done = state.contracts.length - todo;
  els.todoCount.textContent = todo;
  els.doneCount.textContent = done;
  document.querySelectorAll(".contract-list-tab").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.contractTab === state.contractListTab);
  });
}

function getVisibleContracts() {
  return state.contracts.filter((item) => getContractListBucket(item) === state.contractListTab);
}

function getContractListBucket(item) {
  if (item.status === "Completed") return "done";
  if ((item.status_text || "").includes("人工已确认")) return "done";
  return "todo";
}

async function selectContract(id) {
  if (state.selectedId !== id) {
    state.resultFilter = "all";
  }
  state.selectedId = id;
  renderContractList();
  els.rerunBtn.disabled = false;
  await loadContractDetail(id);
  startPolling();
}

async function loadContractDetail(id) {
  await refreshContractListState();
  const data = await api(`/api/contracts/${id}`);
  renderContract(data.item);
  return data.item;
}

function clearContractSelection() {
  state.selectedId = null;
  state.resultFilter = "all";
  els.rerunBtn.disabled = true;
  els.previewTitle.textContent = "请选择一份合同";
  els.previewSub.textContent = "中间区域用于展示合同正文和审核依据。";
  els.emptyPreview.classList.remove("hidden");
  els.previewContent.classList.add("hidden");
  els.timeline.innerHTML = "";
  els.riskList.innerHTML = "";
  els.resultSummary.classList.add("empty-state");
  els.resultSummary.innerHTML = `<strong>等待选择合同</strong><span>从左侧合同库选择一份合同查看审核结果。</span>`;
  renderContractList();
}

async function archiveContract(contractId) {
  if (!contractId) return;
  if (!confirm("归档后该合同会从前台合同库移除，后台记录仍会保留。确认归档？")) return;
  await api(`/api/contracts/${contractId}/archive`, { method: "POST" });
  toast("合同已归档，前台列表不再展示。");
  if (state.selectedId === contractId) {
    state.selectedId = null;
  }
  await loadContracts();
  if (!getVisibleContracts().length) {
    clearContractSelection();
  }
}

function renderContract(contract) {
  els.emptyPreview.classList.add("hidden");
  els.previewContent.classList.remove("hidden");
  els.previewTitle.textContent = contract.name;
  els.previewSub.textContent = `来源：${contract.source || "-"} · 创建时间：${contract.created_at || "-"}`;
  els.contractType.textContent = contract.contract_type || "识别中";
  els.reviewStatus.textContent = contract.status_text || contract.status || "-";
  els.maxAmount.textContent = formatAmount(contract.fields?.max_amount);
  els.strategyName.textContent = contract.review_strategy?.name || "待匹配";
  els.textTab.textContent = contract.parsed_text || "正在等待文档解析结果...";
  els.clausesTab.innerHTML = renderClauses(contract.clauses || []);
  els.fieldsTab.innerHTML = renderObjectTable(contract.fields || {});
  els.templateTab.innerHTML = renderObjectTable(contract.template_match || {});
  els.strategyTab.innerHTML = renderObjectTable(formatStrategyEvidence(contract.review_strategy || {}));
  renderEvidenceTabCounts(contract);
  setEvidenceTab(state.activeEvidenceTab || "clauses");
  els.agentPromptVersion.textContent = contract.agent_prompt_version || "-";
  renderTimeline(contract.review?.events || []);
  renderResult(contract);
}

function renderEvidenceTabCounts(contract) {
  const strategy = contract.review_strategy || {};
  const strategyEvidence = formatStrategyEvidence(strategy);
  els.clausesEvidenceCount.textContent = String((contract.clauses || []).length);
  els.fieldsEvidenceCount.textContent = String(Object.keys(contract.fields || {}).length);
  els.templateEvidenceCount.textContent = String(Object.keys(contract.template_match || {}).length);
  els.strategyEvidenceCount.textContent = String(
    Object.values(strategyEvidence).filter((value) => Array.isArray(value) ? value.length : value).length
  );
}

function setEvidenceTab(tab) {
  state.activeEvidenceTab = tab || "clauses";
  els.evidenceTabBtns.forEach((button) => {
    const active = button.dataset.evidenceTab === state.activeEvidenceTab;
    button.classList.toggle("active", active);
    button.setAttribute("aria-selected", active ? "true" : "false");
  });
  els.evidencePanels.forEach((panel) => {
    const active = panel.dataset.evidencePanel === state.activeEvidenceTab;
    panel.classList.toggle("active", active);
    panel.hidden = !active;
  });
}

function renderClauses(clauses) {
  if (!clauses.length) {
    return `<div class="empty-state"><strong>暂无条款对象</strong><span>等待合同理解 Skill 输出。</span></div>`;
  }
  return `
    <div class="clause-list">
      ${clauses.map((clause) => `
        <article class="clause-card">
          <div class="clause-card-head">
            <b>${escapeHtml(clause.number || clause.id || "-")} ${escapeHtml(clause.title || "未命名条款")}</b>
            <em>${escapeHtml(formatClauseType(clause.type))}</em>
          </div>
          <span>${escapeHtml(clause.location || formatClausePosition(clause.position) || "-")}</span>
          <p>${escapeHtml(clause.text || "")}</p>
        </article>
      `).join("")}
    </div>
  `;
}

function formatClauseType(type) {
  const map = {
    parties: "主体",
    subject: "标的",
    payment: "付款",
    invoice: "发票",
    delivery: "交付",
    acceptance: "验收",
    effective: "签章生效",
    breach: "违约",
    dispute: "争议",
    safety: "安全",
    confidentiality: "保密",
    termination: "解除终止",
    other: "其他",
  };
  return map[type] || type || "-";
}

function formatClausePosition(position) {
  if (!position) return "";
  if (position.line_start && position.line_end) return `第${position.line_start}-${position.line_end}行`;
  if (position.char_start !== undefined && position.char_end !== undefined) return `${position.char_start}-${position.char_end}`;
  return "";
}

function formatStrategyEvidence(strategy) {
  if (!strategy || !Object.keys(strategy).length) return {};
  return {
    strategy_id: strategy.id,
    strategy_name: strategy.name,
    template_type: strategy.template_type,
    linked_rules: (strategy.rules || []).map((rule) => `${rule.id} ${rule.name}`),
    agent_instruction: strategy.agent_instruction,
  };
}

function renderTimeline(events) {
  const visible = events.filter((event) => event.visible_to_user !== false);
  if (!visible.length) {
    els.timeline.innerHTML = `<div class="empty-state"><strong>尚无执行轨迹</strong><span>Agent Loop 启动后会记录步骤。</span></div>`;
    return;
  }
  els.timeline.innerHTML = visible.map((event) => `
    <article class="event">
      <div class="event-top">
        <b>${escapeHtml(event.phase || event.event_type)}</b>
        <span>${escapeHtml(event.time || "")}</span>
      </div>
      <p>${escapeHtml(event.message || "")}</p>
      ${renderConfidenceDetail(event.confidence_detail)}
    </article>
  `).join("");
  els.timeline.scrollTop = els.timeline.scrollHeight;
}

function renderConfidenceDetail(detail) {
  const metrics = flattenConfidenceDetail(detail);
  if (!metrics.length) return "";
  return `
    <div class="confidence-detail">
      ${metrics.map((item) => `
        <span>${escapeHtml(item.label)}：${escapeHtml(formatMetricDegree(item.value))}</span>
      `).join("")}
    </div>
  `;
}

function flattenConfidenceDetail(detail) {
  if (!detail || typeof detail !== "object") return [];
  const labelMap = {
    overall: "总体置信度",
    document_parse: "文档解析",
    contract_classify: "合同类型识别",
    clause_extract: "条款抽取",
    field_extract: "字段抽取",
    template_match: "模板匹配",
    method: "计算方法",
    file_size_signal: "文件大小信号",
    suffix_support: "格式支持度",
    metadata_completeness: "元数据完整度",
    persistence_check: "入库持久化校验",
    text_length: "文本长度",
    chunk_coverage: "分块覆盖",
    preview_available: "预览可用性",
    keyword_strength: "关键词强度",
    file_name_signal: "文件名信号",
    type_ambiguity: "类型区分度",
    text_available: "文本可用性",
    party_extraction: "主体抽取",
    amount_extraction: "金额抽取",
    clause_signal: "条款信号",
    clause_coverage: "条款覆盖",
    clause_type_coverage: "条款类型覆盖",
    location_coverage: "位置覆盖",
    contract_type_confidence: "合同类型置信度",
    section_coverage: "模板章节覆盖",
    matched_section_volume: "匹配章节数量",
    field_completeness: "字段完整度",
    rule_determinism: "规则确定性",
    evidence_support: "证据支撑",
    llm_quality: "大模型判断质量",
    warning_penalty: "告警惩罚",
    risk_penalty: "风险惩罚",
    risk_structure: "风险结构完整度",
    role_coverage: "角色意见覆盖",
    count_consistency: "数量一致性",
    summary_quality: "摘要质量",
    human_confirm_consistency: "人工确认一致性",
    llm_summary_quality: "大模型润色质量",
    index_coverage: "知识索引覆盖",
    recall_count: "检索召回数量",
    top_score_strength: "最高相关性",
    source_diversity: "来源多样性",
  };
  const preferredOrder = [
    "overall",
    "document_parse",
    "contract_classify",
    "clause_extract",
    "field_extract",
    "template_match",
    "field_completeness",
    "rule_determinism",
    "evidence_support",
    "llm_quality",
    "risk_structure",
    "role_coverage",
    "count_consistency",
    "summary_quality",
    "human_confirm_consistency",
    "llm_summary_quality",
    "warning_penalty",
    "risk_penalty",
    "method",
  ];
  const keys = [
    ...preferredOrder.filter((key) => Object.prototype.hasOwnProperty.call(detail, key)),
    ...Object.keys(detail).filter((key) => !preferredOrder.includes(key)),
  ];
  return keys
    .filter((key) => key !== "tool_details" && detail[key] !== null && detail[key] !== undefined)
    .map((key) => ({
      label: labelMap[key] || key,
      value: detail[key],
    }));
}

function formatMetricDegree(value) {
  if (typeof value === "number" && Number.isFinite(value)) {
    if (value >= 0 && value <= 1) {
      return `${Math.round(value * 100)}%`;
    }
    return String(value);
  }
  const methodMap = {
    minimum_tool_confidence: "取工具最低置信度",
  };
  return methodMap[value] || String(value);
}

function renderResult(contract) {
  const risks = contract.risks || [];
  els.riskTotal.textContent = risks.length;
  els.resultTabs.classList.add("hidden");
  els.resultTabs.innerHTML = "";
  if (!contract.report) {
    els.resultSummary.classList.add("empty-state");
    els.resultSummary.innerHTML = `<strong>等待审核结果</strong><span>Agent Loop 完成后会在这里展示结论。</span>`;
    els.riskList.innerHTML = "";
  } else {
    els.resultSummary.classList.remove("empty-state");
    const counts = contract.report.risk_counts || {};
    const high = (counts.P0 || 0) + (counts.P1 || 0);
    const general = (counts.P2 || 0) + (counts.P3 || 0);
    const passedRuleEvents = getPassedRuleEvents(contract);
    const executedRuleCount = getExecutedRuleCount(contract, risks);
    const incompleteRuleEvents = getIncompleteRuleEvents(contract);
    const hasIncompleteRules = incompleteRuleEvents.length > 0;
    const passed = Math.max(0, Number(contract.report.passed_rules ?? passedRuleEvents.length) || (executedRuleCount - risks.length - incompleteRuleEvents.length));
    const filterCounts = {
      all: risks.length,
      high,
      general,
      ...(incompleteRuleEvents.length ? { incomplete: incompleteRuleEvents.length } : {}),
      passed,
    };
    if (!Object.prototype.hasOwnProperty.call(filterCounts, state.resultFilter)) {
      state.resultFilter = "all";
    }
    const filteredRisks = filterRisksByResultTab(risks, state.resultFilter);
    const reviewMeta = getReviewMeta(contract, risks);
    const resultTabs = [
      { key: "all", label: "全部", count: risks.length },
      { key: "high", label: "重大风险", count: high },
      { key: "general", label: "一般风险", count: general },
      ...(incompleteRuleEvents.length ? [{ key: "incomplete", label: "未完成", count: incompleteRuleEvents.length }] : []),
      { key: "passed", label: "通过", count: passed },
    ];
    const boardRejected = risks.length > 0 || hasIncompleteRules;
    const statusLabel = risks.length ? "不通过" : hasIncompleteRules ? "待确认" : "通过";
    els.resultSummary.innerHTML = `
      <div class="review-board ${boardRejected ? "review-board-rejected" : "review-board-passed"}">
        <div class="review-board-head">
          <div class="review-title-block">
            <div class="review-title-line">
              <h3>审查结果</h3>
              <span class="review-status-badge ${boardRejected ? "status-fail" : "status-pass"}">${statusLabel}</span>
            </div>
            <b>审核结论：</b>
          </div>
        </div>
        <p class="review-summary">${escapeHtml(contract.report.summary)}</p>
        <div class="review-tabs">
          ${resultTabs.map((tab) => `
            <button class="review-tab ${state.resultFilter === tab.key ? "active" : ""}" data-result-filter="${tab.key}" type="button">
              ${tab.label} <b>${tab.count}</b>
            </button>
          `).join("")}
        </div>
        <div class="review-contract-row">
          <span class="contract-icon">策</span>
          <b>${escapeHtml(reviewMeta)}</b>
        </div>
        ${renderFlowDecisionLine(contract.report.flow_decision || contract.flow_decision)}
      </div>
    `;
    els.riskList.innerHTML = renderRiskCardsForFilter(filteredRisks, state.resultFilter, risks, contract) + renderHumanReviewPanel(contract);
    bindResultFilterActions(contract);
    bindHumanReviewActions(contract);
  }
}

function filterRisksByResultTab(risks, filter) {
  if (filter === "high") return risks.filter((risk) => ["P0", "P1"].includes(risk.priority));
  if (filter === "general") return risks.filter((risk) => ["P2", "P3"].includes(risk.priority));
  if (["passed", "incomplete"].includes(filter)) return [];
  return risks;
}

function renderFlowDecisionLine(flowDecision) {
  if (!flowDecision) return "";
  return `
    <div class="review-contract-row flow-decision-row">
      <span class="contract-icon">流</span>
      <b>${escapeHtml(flowDecision.flow_strategy?.name || "审核流转策略")} · ${escapeHtml(flowDecision.status_text || flowDecision.decision || "-")}：${escapeHtml(flowDecision.reason || "")}</b>
    </div>
  `;
}

function renderRiskCardsForFilter(filteredRisks, filter, allRisks, contract) {
  if (filter === "passed") {
    return renderPassedRuleCards(contract, allRisks);
  }
  if (filter === "incomplete") {
    return renderIncompleteRuleCards(contract);
  }
  if (!filteredRisks.length) {
    const labelMap = {
      high: "暂无重大风险",
      general: "暂无一般风险",
      all: "暂无风险",
    };
    return renderRiskFilterEmpty(labelMap[filter] || "暂无匹配风险");
  }
  return renderRiskCards(filteredRisks);
}

function getPassedRuleEvents(contract) {
  return ((contract.report || {}).rule_events || []).filter((event) => event.evaluated !== false && event.passed);
}

function getIncompleteRuleEvents(contract) {
  const report = contract.report || {};
  const events = report.incomplete_rules?.length ? report.incomplete_rules : (report.rule_events || []);
  return events.filter((event) => event.evaluated === false || event.execution_status === "incomplete");
}

function getExecutedRuleCount(contract, risks) {
  const report = contract.report || {};
  if (Number.isFinite(Number(report.executed_rules))) return Number(report.executed_rules);
  const ruleEvents = report.rule_events || [];
  if (ruleEvents.length) return ruleEvents.length;
  const strategyRules = contract.review_strategy?.rules || [];
  if (strategyRules.length) return strategyRules.length;
  const strategyRuleIds = contract.review_strategy?.rule_ids || [];
  if (strategyRuleIds.length) return strategyRuleIds.length;
  const totalConfiguredRules = state.ruleStats?.total_rules || 0;
  return Math.max(totalConfiguredRules, risks.length);
}

function renderPassedRuleCards(contract, allRisks) {
  const passedEvents = getPassedRuleEvents(contract);
  const executedRuleCount = getExecutedRuleCount(contract, allRisks);
  const incompleteCount = getIncompleteRuleEvents(contract).length;
  const passedCount = Math.max(0, Number(contract.report?.passed_rules ?? passedEvents.length) || (executedRuleCount - allRisks.length - incompleteCount));
  if (!passedCount) return renderRiskFilterEmpty("暂无通过规则");
  if (!passedEvents.length) {
    return `
      <article class="review-pass-card">
        <b>已有 ${passedCount} 条规则通过</b>
        <p>当前记录未保存通过规则明细；重新审核后可在这里查看具体通过的规则。</p>
      </article>
    `;
  }
  return passedEvents.map((event) => `
    <article class="review-pass-card passed-rule-card">
      <b>规则(${escapeHtml(event.rule_id || "-")})：${escapeHtml(event.rule_name || "未命名规则")}</b>
      <p>${escapeHtml(event.mode || "规则")} · ${escapeHtml(event.risk_level || "-")} · ${escapeHtml(event.priority || "-")}</p>
    </article>
  `).join("");
}

function renderIncompleteRuleCards(contract) {
  const events = getIncompleteRuleEvents(contract);
  if (!events.length) return renderRiskFilterEmpty("暂无未完成规则");
  return events.map((event) => `
    <article class="review-pass-card incomplete-rule-card">
      <b>规则(${escapeHtml(event.rule_id || "-")})：${escapeHtml(event.rule_name || "未命名规则")}</b>
      <p>${escapeHtml(event.issue || "该规则因系统或大模型调用问题未完成判断。")}</p>
      <small>${escapeHtml(event.suggestion || "请稍后重试，或由人工复核该规则。")}</small>
    </article>
  `).join("");
}

function renderRiskFilterEmpty(message) {
  return `
    <article class="review-pass-card">
      <b>${escapeHtml(message)}</b>
      <p>可切换上方分类查看其他审核结果。</p>
    </article>
  `;
}

function bindResultFilterActions(contract) {
  document.querySelectorAll("[data-result-filter]").forEach((button) => {
    button.addEventListener("click", () => {
      state.resultFilter = button.dataset.resultFilter || "all";
      renderResult(contract);
    });
  });
}

function renderRiskCards(risks) {
  if (!risks.length) {
    return `
      <article class="review-pass-card">
        <b>未发现需处理的规则风险</b>
        <p>当前合同可进入后续流转，仍建议按业务流程完成必要的人工确认。</p>
      </article>
    `;
  }
  return risks.map((risk) => `
    <article class="review-risk-card risk-card-${risk.priority}">
      <div class="risk-head">
        <div>
          <span class="risk-level-label">${escapeHtml(priorityLabel(risk.priority))}</span>
          <b>规则(${escapeHtml(risk.rule_id || "-")})：${escapeHtml(risk.rule_name)}</b>
        </div>
        <span class="risk-close">×</span>
      </div>
      <div class="risk-source-excerpt">${escapeHtml(getRiskSourceExcerpt(risk))}</div>
      ${renderRiskMatchedClauses(risk)}
      <section class="risk-detail-block">
        <div class="risk-block-title">
          <span class="risk-block-icon">!</span>
          <b>风险提示</b>
        </div>
        <p>${escapeHtml(risk.issue || "-")}</p>
      </section>
      <section class="risk-detail-block">
        <div class="risk-block-title">
          <span class="risk-block-icon edit">修</span>
          <b>修改建议</b>
        </div>
        <p>${escapeHtml(risk.suggestion || "-")}</p>
      </section>
      <div class="risk-rule-meta">${escapeHtml(risk.mode)} · ${escapeHtml(risk.risk_level)} · ${escapeHtml(risk.priority)}</div>
    </article>
  `).join("");
}

function renderRiskMatchedClauses(risk) {
  const clauses = risk.matched_clauses || [];
  if (!clauses.length) return "";
  return `
    <section class="risk-clause-block">
      <div class="risk-clause-head">
        <b>条款判定</b>
        <span>${clauses.length} 条</span>
      </div>
      <div class="risk-clause-list">
        ${clauses.map((clause) => {
          const judgement = getClauseJudgement(risk, clause);
          return `
          <article class="risk-clause-item risk-clause-${judgement.status}">
            <div>
              <div class="risk-clause-title-row">
                <b>${escapeHtml(clause.number || clause.id || "-")} ${escapeHtml(clause.title || "未命名条款")}</b>
                <em class="clause-judgement-pill">${escapeHtml(judgement.label)}</em>
              </div>
              <span>${escapeHtml(formatClauseType(clause.type))} · ${escapeHtml(clause.location || "-")}</span>
            </div>
            <p>${escapeHtml(clause.text || "")}</p>
            <small>${escapeHtml(judgement.reason)}</small>
          </article>
        `;}).join("")}
      </div>
    </section>
  `;
}

function getClauseJudgement(risk, clause) {
  if (clause.status || clause.status_label || clause.status_reason) {
    return {
      status: normalizeClauseStatus(clause.status),
      label: clause.status_label || clauseStatusLabel(clause.status),
      reason: clause.status_reason || clauseStatusReason(clause.status, risk),
    };
  }
  if (risk.evaluated === false || risk.execution_status === "incomplete") {
    return {
      status: "unknown",
      label: "未完成",
      reason: "该规则未完成判断，暂不能判定该条款是否通过。",
    };
  }
  if (risk.passed) {
    return {
      status: "passed",
      label: "通过",
      reason: "该条款与当前规则相关，未触发该规则风险。",
    };
  }
  if (clauseMatchesRiskEvidence(risk, clause)) {
    return {
      status: "failed",
      label: "触发风险",
      reason: "该条款包含当前规则命中的直接证据。",
    };
  }
  return {
    status: "review",
    label: "需复核",
    reason: "该条款被规则召回为相关依据，需要结合规则结论复核。",
  };
}

function normalizeClauseStatus(status) {
  if (["passed", "failed", "review", "unknown"].includes(status)) return status;
  if (status === "triggered" || status === "risk") return "failed";
  if (status === "incomplete") return "unknown";
  return "review";
}

function clauseStatusLabel(status) {
  return {
    passed: "通过",
    failed: "触发风险",
    review: "需复核",
    unknown: "未完成",
  }[normalizeClauseStatus(status)] || "需复核";
}

function clauseStatusReason(status, risk) {
  const normalized = normalizeClauseStatus(status);
  if (normalized === "passed") return "该条款与当前规则相关，未触发该规则风险。";
  if (normalized === "failed") return "该条款包含当前规则命中的直接证据。";
  if (normalized === "unknown") return "该规则未完成判断，暂不能判定该条款是否通过。";
  return risk?.passed === false ? "该条款与当前未通过规则相关，需要人工复核。" : "该条款被规则召回为相关依据。";
}

function clauseMatchesRiskEvidence(risk, clause) {
  const text = compactText(clause.text || "");
  const clauseId = String(clause.id || "");
  if (!text && !clauseId) return false;
  return (risk.evidence || []).some((item) => {
    if (!item || typeof item !== "object") return false;
    if (clauseId && String(item.clause_id || "") === clauseId) return true;
    const snippet = compactText(item.snippet || "");
    if (snippet && (text.includes(snippet) || snippet.includes(text.slice(0, 80)))) return true;
    if (typeof item.value === "string" && item.value.trim().length >= 2) {
      return text.includes(compactText(item.value));
    }
    if (Array.isArray(item.value)) {
      return item.value.some((value) => String(value || "").trim().length >= 2 && text.includes(compactText(value)));
    }
    return false;
  });
}

function compactText(value) {
  return String(value || "").replace(/\s+/g, "");
}

function getRiskSourceExcerpt(risk) {
  const sourceEvidence = (risk.evidence || []).find((item) => item.type === "source_excerpt" && item.snippet);
  if (sourceEvidence) return sourceEvidence.snippet;
  const snippetEvidence = (risk.evidence || []).find((item) => item.snippet);
  if (snippetEvidence) return snippetEvidence.snippet;
  const valueEvidence = (risk.evidence || []).find((item) => item.value);
  if (valueEvidence) return formatValue(valueEvidence.value);
  return "未定位到合同原文片段。";
}

function renderPartyLabel(parties) {
  if (parties.length >= 2) return "合同甲乙方";
  if (parties.length === 1) return parties[0];
  return "合同主体";
}

function getReviewMeta(contract, risks) {
  const strategyName = contract.review_strategy?.name || contract.review_strategy || "未匹配审核策略";
  const executedRuleCount = getExecutedRuleCount(contract, risks);
  const incompleteCount = getIncompleteRuleEvents(contract).length;
  const passedRuleCount = Math.max(0, Number(contract.report?.passed_rules || 0) || (executedRuleCount - risks.length - incompleteCount));
  return `${strategyName} · 已审 ${executedRuleCount} 条规则，通过 ${passedRuleCount} 条，风险 ${risks.length} 条${incompleteCount ? `，未完成 ${incompleteCount} 条` : ""}`;
}

function priorityLabel(priority) {
  if (priority === "P0") return "重大";
  if (priority === "P1") return "重大";
  if (priority === "P2") return "一般";
  return "提示";
}

function renderHumanReviewPanel(contract) {
  if (contract.human_review) {
    return `
      <div class="human-review-panel human-reviewed">
        <div class="human-review-head">
          <b>人工审核</b>
          <span>${escapeHtml(contract.human_review.decision || "-")}</span>
        </div>
        <p>${escapeHtml(contract.human_review.opinion || "未填写补充意见。")}</p>
        <small>${escapeHtml(contract.human_review.reviewer || "人工审核人")} · ${escapeHtml(contract.human_review.time || "")}</small>
      </div>
    `;
  }
  const reviewableStatuses = new Set(["NeedHumanConfirm", "NeedRevision", "Blocked"]);
  if (!reviewableStatuses.has(contract.status)) {
    return "";
  }
  const statusCopy = getHumanReviewStatusCopy(contract);
  const defaultOpinion = contract.report?.default_human_review_opinion || buildDefaultHumanReviewOpinion(contract);
  const humanOpinionSource = contract.report?.default_human_review_opinion_source;
  const opinionSource = humanOpinionSource && humanOpinionSource !== "template"
    ? "大模型已根据最终审查报告生成默认意见，可人工修改。"
    : "已根据最终审查报告生成默认意见，可人工修改。";
  return `
    <div class="human-review-panel">
      <div class="human-review-head">
        <b>${escapeHtml(statusCopy.title)}</b>
        <span>${escapeHtml(statusCopy.status)}</span>
      </div>
      <p class="human-review-tip">${escapeHtml(opinionSource)}</p>
      <textarea id="humanReviewOpinion" placeholder="填写人工审核意见，如：请补充付款节点、发票税率及双方签章生效条款后再流转。">${escapeHtml(defaultOpinion)}</textarea>
      <div class="human-review-actions">
        <button class="danger-btn" id="ignoreRiskBtn">忽略风险，审核通过</button>
        <button class="primary-btn" id="approveBtn">${escapeHtml(statusCopy.submitLabel)}</button>
      </div>
    </div>
  `;
}

function getHumanReviewStatusCopy(contract) {
  if (contract.status === "NeedRevision") {
    return { title: "人工修改意见", status: "等待退回意见", submitLabel: "提交退回意见" };
  }
  if (contract.status === "Blocked") {
    return { title: "人工处理意见", status: "等待风险解除意见", submitLabel: "提交处理意见" };
  }
  return { title: "人工审核", status: "等待确认", submitLabel: "提交意见" };
}

function buildDefaultHumanReviewOpinion(contract) {
  const risks = contract.risks || [];
  if (!risks.length) {
    return "经系统智能审核，当前合同未发现明显规则风险。建议经办部门复核合同正文、附件和签章信息后，按公司流程继续办理审批、用印和归档。";
  }
  const highCount = risks.filter((risk) => ["P0", "P1"].includes(risk.priority)).length;
  const riskNames = risks
    .slice(0, 3)
    .map((risk) => risk.rule_name || risk.rule_id || "规则风险")
    .join("、");
  const action = highCount
    ? "建议暂缓流转，先由经办部门会同法务、财务或用印相关人员补充修订后再提交复核。"
    : "建议经办部门根据风险提示补充完善后，再按流程继续审批。";
  return `经系统智能审核，本合同共发现 ${risks.length} 项风险，其中高风险 ${highCount} 项，主要涉及${riskNames}。${action}`;
}

function bindHumanReviewActions(contract) {
  const approveBtn = $("#approveBtn");
  const ignoreRiskBtn = $("#ignoreRiskBtn");
  if (!approveBtn || !ignoreRiskBtn) return;
  approveBtn.addEventListener("click", () => submitHumanReview(contract.id, "reject"));
  ignoreRiskBtn.addEventListener("click", () => submitHumanReview(contract.id, "approve", "ignoreRisk"));
}

async function submitHumanReview(contractId, action, submitMode = "opinion") {
  const rawOpinion = $("#humanReviewOpinion")?.value || "";
  const opinion = submitMode === "ignoreRisk"
    ? `【忽略风险，审核通过】${rawOpinion}`
    : rawOpinion;
  await api(`/api/contracts/${contractId}/human-review`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      action,
      opinion,
      reviewer: els.initiator.value || "人工审核人",
    }),
  });
  toast(submitMode === "ignoreRisk" ? "已忽略风险并审核通过。" : "已提交人工审核意见。");
  state.contractListTab = "done";
  await loadContractDetail(contractId);
}

async function uploadFile(file) {
  if (!file) return;
  const form = new FormData();
  form.append("file", file);
  form.append("source", "upload");
  form.append("business_dept", els.businessDept.value || "");
  form.append("initiator", els.initiator.value || "");
  setUploadStatus("uploading", `正在上传：${file.name}`);
  els.uploadBtn.disabled = true;
  try {
    const data = await api("/api/contracts", { method: "POST", body: form });
    setUploadStatus("success", "上传成功，已进入审核链路。");
    toast("合同已入库，Agent 审核链路已启动。");
    state.contractListTab = "todo";
    await loadContracts();
    await selectContract(data.item.id);
  } catch (error) {
    const apiError = parseApiError(error);
    setUploadStatus("error", apiError.message);
    toast(apiError.message);
    if (apiError.code === "duplicate_contract" && apiError.existing_id) {
      state.contractListTab = "todo";
      await loadContracts();
      await selectContract(apiError.existing_id);
    }
  } finally {
    els.uploadBtn.disabled = false;
    els.fileInput.value = "";
  }
}

function setUploadStatus(type, message) {
  if (!els.uploadStatus) return;
  els.uploadStatus.textContent = message || "";
  els.uploadStatus.className = `upload-status ${type ? `upload-status-${type}` : ""}`;
}

function startPolling() {
  if (state.pollTimer) clearInterval(state.pollTimer);
  state.pollStableTicks = 0;
  pollSelectedContract().catch((error) => console.warn(error));
  state.pollTimer = setInterval(async () => {
    pollSelectedContract().catch((error) => console.warn(error));
  }, 1500);
}

async function pollSelectedContract() {
  if (!state.selectedId) return;
  const contract = await loadContractDetail(state.selectedId);
  const terminal = ["Completed", "NeedHumanConfirm", "NeedRevision", "Blocked", "Failed"].includes(contract.status);
  const resultReady = contract.status === "Failed" || !!contract.report || !!contract.error;
  if (terminal && resultReady) {
    state.pollStableTicks += 1;
  } else {
    state.pollStableTicks = 0;
  }
  if (state.pollStableTicks >= 2 && state.pollTimer) {
    clearInterval(state.pollTimer);
    state.pollTimer = null;
  }
}

function renderObjectTable(object) {
  const entries = Object.entries(object || {});
  if (!entries.length) return `<div class="empty-state"><strong>暂无数据</strong><span>等待 Skill 输出。</span></div>`;
  return `
    <table class="kv-table">
      <tbody>
        ${entries.map(([key, value]) => `
          <tr>
            <th>${escapeHtml(key)}</th>
            <td>${escapeHtml(formatValue(value))}</td>
          </tr>
        `).join("")}
      </tbody>
    </table>
  `;
}

function formatValue(value) {
  if (Array.isArray(value)) return value.length ? value.map((v) => typeof v === "object" ? JSON.stringify(v) : String(v)).join("；") : "-";
  if (typeof value === "object" && value !== null) return JSON.stringify(value, null, 2);
  if (value === null || value === undefined || value === "") return "-";
  return String(value);
}

function formatAmount(value) {
  if (!value) return "-";
  return new Intl.NumberFormat("zh-CN", { style: "currency", currency: "CNY", maximumFractionDigits: 2 }).format(value);
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function toast(message, type = "") {
  const node = document.createElement("div");
  node.className = `toast ${type ? `toast-${type}` : ""}`;
  node.textContent = message;
  document.body.appendChild(node);
  setTimeout(() => node.remove(), 2600);
}

els.uploadBtn.addEventListener("click", () => {
  els.fileInput.value = "";
  setUploadStatus("", "");
  els.fileInput.click();
});
els.fileInput.addEventListener("change", () => uploadFile(els.fileInput.files[0]).catch((error) => toast(error.message)));
els.refreshBtn.addEventListener("click", () => loadContracts().catch((error) => toast(error.message)));
els.evidenceTabBtns.forEach((button) => {
  button.addEventListener("click", () => setEvidenceTab(button.dataset.evidenceTab));
});
els.knowledgeBtn.addEventListener("click", () => openKnowledgeModal().catch((error) => toast(error.message)));
els.closeKnowledgeBtn.addEventListener("click", () => els.knowledgeModal.classList.add("hidden"));
els.refreshKnowledgeBtn.addEventListener("click", () => loadKnowledge(true).then(() => toast("知识库索引已刷新。")).catch((error) => toast(error.message)));
els.knowledgeFileInput.addEventListener("change", () => uploadKnowledgeFile(els.knowledgeFileInput.files[0]).catch((error) => toast(error.message)));
els.knowledgeSearchBtn.addEventListener("click", () => searchKnowledge().catch((error) => toast(error.message)));
els.knowledgeClearSearchBtn.addEventListener("click", () => {
  state.knowledgeQuery = "";
  state.knowledgeSearchResults = [];
  els.knowledgeSearchInput.value = "";
  renderKnowledge();
});
els.knowledgeSearchInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    event.preventDefault();
    searchKnowledge().catch((error) => toast(error.message));
  }
});
els.feedbackBtn.addEventListener("click", () => openFeedbackModal().catch((error) => toast(error.message)));
els.closeFeedbackBtn.addEventListener("click", () => els.feedbackModal.classList.add("hidden"));
els.refreshFeedbackBtn.addEventListener("click", () => loadHumanFeedback().then(() => toast("人工反馈已刷新。")).catch((error) => toast(error.message)));
els.agentsBtn.addEventListener("click", () => openAgentsModal().catch((error) => toast(error.message)));
els.flowStrategiesBtn.addEventListener("click", () => openFlowStrategiesModal().catch((error) => toast(error.message)));
els.closeFlowStrategiesBtn.addEventListener("click", () => els.flowStrategiesModal.classList.add("hidden"));
els.newFlowStrategyBtn.addEventListener("click", startNewFlowStrategy);
els.resetFlowStrategiesBtn.addEventListener("click", () => resetFlowStrategies().catch((error) => toast(error.message)));
els.flowStrategyForm.addEventListener("submit", (event) => saveCurrentFlowStrategy(event).catch((error) => toast(error.message)));
els.deleteFlowStrategyBtn.addEventListener("click", () => deleteCurrentFlowStrategy().catch((error) => toast(error.message)));
els.closeAgentsBtn.addEventListener("click", () => els.agentsModal.classList.add("hidden"));
els.newAgentBtn.addEventListener("click", startNewAgent);
els.resetAgentsBtn.addEventListener("click", () => resetAgents().catch((error) => toast(error.message)));
els.agentForm.addEventListener("submit", (event) => saveCurrentAgent(event).catch((error) => toast(error.message)));
els.agentModelTestBtn.addEventListener("click", () => testAgentModelConnection());
els.deleteAgentBtn.addEventListener("click", () => deleteCurrentAgent().catch((error) => toast(error.message)));
els.agentSkillSearch.addEventListener("input", () => {
  state.agentSkillSearch = els.agentSkillSearch.value;
  renderAgentSkills();
});
els.agentToolSearch.addEventListener("input", () => {
  state.agentToolSearch = els.agentToolSearch.value;
  renderAgentTools();
});
els.strategiesBtn.addEventListener("click", () => openStrategiesModal().catch((error) => toast(error.message)));
els.closeStrategiesBtn.addEventListener("click", () => els.strategiesModal.classList.add("hidden"));
els.newStrategyBtn.addEventListener("click", startNewStrategy);
els.resetStrategiesBtn.addEventListener("click", () => resetStrategies().catch((error) => toast(error.message)));
els.strategyForm.addEventListener("submit", (event) => saveCurrentStrategy(event).catch((error) => toast(error.message)));
els.deleteStrategyBtn.addEventListener("click", () => deleteCurrentStrategy().catch((error) => toast(error.message)));
els.createRuleFromStrategyBtn.addEventListener("click", createRuleFromStrategy);
els.rulesBtn.addEventListener("click", () => openRulesModal().catch((error) => toast(error.message)));
els.closeRulesBtn.addEventListener("click", () => els.rulesModal.classList.add("hidden"));
els.newRuleBtn.addEventListener("click", startNewRule);
els.resetRulesBtn.addEventListener("click", () => resetRules().catch((error) => toast(error.message)));
els.ruleForm.addEventListener("submit", (event) => saveCurrentRule(event).catch((error) => toast(error.message)));
els.deleteRuleBtn.addEventListener("click", () => deleteCurrentRule().catch((error) => toast(error.message)));
els.ruleScript.addEventListener("input", updateScriptLineNumbers);
els.ruleScript.addEventListener("scroll", syncScriptLineScroll);
els.addInputParamBtn.addEventListener("click", () => {
  syncParamStateFromDom();
  addParam("input");
});
els.addOutputParamBtn.addEventListener("click", () => {
  syncParamStateFromDom();
  addParam("output");
});
els.ruleForm.addEventListener("click", (event) => {
  const button = event.target.closest(".param-remove-btn");
  if (!button) return;
  const row = button.closest(".param-row");
  syncParamStateFromDom();
  removeParam(row.dataset.paramKind, Number(row.dataset.paramIndex));
});
els.chooseDebugFileBtn.addEventListener("click", () => els.debugFileInput.click());
els.debugFileInput.addEventListener("change", () => {
  state.debugFile = els.debugFileInput.files[0] || null;
  els.debugFileName.textContent = state.debugFile ? state.debugFile.name : "未选择文件";
  els.runRuleDebugBtn.disabled = !state.debugFile;
  els.debugResult.classList.add("hidden");
  els.debugResult.innerHTML = "";
});
els.runRuleDebugBtn.addEventListener("click", () => runRuleDebug().catch((error) => toast(error.message)));
document.querySelectorAll(".mode-tab").forEach((btn) => {
  btn.addEventListener("click", () => {
    state.currentRuleMode = btn.dataset.ruleMode;
    renderRuleMode();
  });
});
document.querySelectorAll(".contract-list-tab").forEach((btn) => {
  btn.addEventListener("click", () => {
    state.contractListTab = btn.dataset.contractTab;
    const visibleContracts = getVisibleContracts();
    if (visibleContracts.length && !visibleContracts.some((item) => item.id === state.selectedId)) {
      selectContract(visibleContracts[0].id);
      return;
    }
    renderContractList();
  });
});
els.rerunBtn.addEventListener("click", async () => {
  if (!state.selectedId) return;
  await api(`/api/contracts/${state.selectedId}/review`, { method: "POST" });
  toast("已重新发起审核。");
  state.contractListTab = "todo";
  await loadContractDetail(state.selectedId);
  startPolling();
});

els.dropZone.addEventListener("dragover", (event) => {
  event.preventDefault();
  els.dropZone.classList.add("dragging");
});
els.dropZone.addEventListener("dragleave", () => els.dropZone.classList.remove("dragging"));
els.dropZone.addEventListener("drop", (event) => {
  event.preventDefault();
  els.dropZone.classList.remove("dragging");
  uploadFile(event.dataTransfer.files[0]).catch((error) => toast(error.message));
});

loadContracts().catch((error) => toast(error.message));
