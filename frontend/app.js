const state = {
  contracts: [],
  ruleStats: null,
  selectedId: null,
  contractListTab: "todo",
  pollTimer: null,
};

const $ = (selector) => document.querySelector(selector);

const els = {
  uploadBtn: $("#uploadBtn"),
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
  templateScore: $("#templateScore"),
  textTab: $("#textTab"),
  fieldsTab: $("#fieldsTab"),
  templateTab: $("#templateTab"),
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
};

async function api(path, options = {}) {
  const response = await fetch(path, options);
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `HTTP ${response.status}`);
  }
  return response.json();
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

function renderStats() {
  const total = state.contracts.length;
  const passed = state.contracts.filter((item) => item.status === "Completed").length;
  const needConfirm = state.contracts.filter((item) => item.status === "NeedHumanConfirm").length;
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
      <b>${escapeHtml(item.name)}</b>
      <div class="contract-meta">
        <span class="status-pill status-${item.status}">${escapeHtml(item.status_text || item.status)}</span>
        <span>${escapeHtml(item.contract_type || "待识别")}</span>
        <span class="risk-pill">风险 ${item.risk_count || 0}</span>
        ${item.p0_count ? `<span class="risk-pill">P0 ${item.p0_count}</span>` : ""}
        ${item.p1_count ? `<span class="risk-pill">P1 ${item.p1_count}</span>` : ""}
      </div>
    </article>
  `).join("");
  document.querySelectorAll(".contract-item").forEach((node) => {
    node.addEventListener("click", () => selectContract(node.dataset.id));
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
  if (item.status === "Completed" || item.status === "NeedRevision") return "done";
  if ((item.status_text || "").includes("人工已确认")) return "done";
  return "todo";
}

async function selectContract(id) {
  state.selectedId = id;
  renderContractList();
  els.rerunBtn.disabled = false;
  await loadContractDetail(id);
  startPolling();
}

async function loadContractDetail(id) {
  const data = await api(`/api/contracts/${id}`);
  renderContract(data.item);
  await loadContracts();
}

function renderContract(contract) {
  els.emptyPreview.classList.add("hidden");
  els.previewContent.classList.remove("hidden");
  els.previewTitle.textContent = contract.name;
  els.previewSub.textContent = `来源：${contract.source || "-"} · 创建时间：${contract.created_at || "-"}`;
  els.contractType.textContent = contract.contract_type || "识别中";
  els.reviewStatus.textContent = contract.status_text || contract.status || "-";
  els.maxAmount.textContent = formatAmount(contract.fields?.max_amount);
  els.templateScore.textContent = contract.template_match?.similarity != null
    ? `${Math.round(contract.template_match.similarity * 100)}%`
    : "-";
  els.textTab.textContent = contract.parsed_text || "正在等待文档解析结果...";
  els.fieldsTab.innerHTML = renderObjectTable(contract.fields || {});
  els.templateTab.innerHTML = renderObjectTable(contract.template_match || {});
  els.agentPromptVersion.textContent = contract.agent_prompt_version || "-";
  renderTimeline(contract.review?.events || []);
  renderResult(contract);
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
    const passed = risks.length ? 0 : 1;
    const partyLabel = renderPartyLabel(contract.fields?.parties || []);
    els.resultSummary.innerHTML = `
      <div class="review-board ${risks.length ? "review-board-rejected" : "review-board-passed"}">
        <div class="review-board-head">
          <div class="review-title-block">
            <div class="review-title-line">
              <h3>审查结果</h3>
              <span class="review-status-badge ${risks.length ? "status-fail" : "status-pass"}">${risks.length ? "不通过" : "通过"}</span>
            </div>
            <b>审核结论：</b>
          </div>
        </div>
        <p class="review-summary">${escapeHtml(contract.report.summary)}</p>
        <div class="review-tabs">
          <button class="review-tab">全部 <b>${risks.length}</b></button>
          <button class="review-tab active">重大风险 <b>${high}</b></button>
          <button class="review-tab">一般风险 <b>${general}</b></button>
          <button class="review-tab">通过 <b>${passed}</b></button>
        </div>
        <div class="review-contract-row">
          <span class="contract-icon">合</span>
          <b>${escapeHtml(partyLabel)}</b>
          <span class="review-page-nav">‹ 1 / 1 ›</span>
        </div>
      </div>
    `;
    els.riskList.innerHTML = renderRiskCards(risks) + renderHumanReviewPanel(contract);
    bindHumanReviewActions(contract);
  }
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
      <div class="risk-source-excerpt">${escapeHtml(risk.evidence?.[0]?.snippet || risk.issue || "系统根据合同文本、字段抽取结果和规则配置形成该风险提示。")}</div>
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

function renderPartyLabel(parties) {
  if (parties.length >= 2) return "合同甲乙方";
  if (parties.length === 1) return parties[0];
  return "合同主体";
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
  if (contract.status !== "NeedHumanConfirm") {
    return "";
  }
  const defaultOpinion = contract.report?.default_human_review_opinion || buildDefaultHumanReviewOpinion(contract);
  const opinionSource = contract.report?.default_human_review_opinion_source === "glm" ? "GLM 已根据最终审查报告生成默认意见，可人工修改。" : "已根据最终审查报告生成默认意见，可人工修改。";
  return `
    <div class="human-review-panel">
      <div class="human-review-head">
        <b>人工审核</b>
        <span>等待确认</span>
      </div>
      <p class="human-review-tip">${escapeHtml(opinionSource)}</p>
      <textarea id="humanReviewOpinion" placeholder="填写人工审核意见，如：请补充付款节点、发票税率及双方签章生效条款后再流转。">${escapeHtml(defaultOpinion)}</textarea>
      <div class="human-review-actions">
        <button class="danger-btn" id="ignoreRiskBtn">忽略风险，审核通过</button>
        <button class="primary-btn" id="approveBtn">提交意见</button>
      </div>
    </div>
  `;
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
  const data = await api("/api/contracts", { method: "POST", body: form });
  toast("合同已入库，Agent 审核链路已启动。");
  state.contractListTab = "todo";
  await loadContracts();
  await selectContract(data.item.id);
}

function startPolling() {
  if (state.pollTimer) clearInterval(state.pollTimer);
  state.pollTimer = setInterval(async () => {
    if (!state.selectedId) return;
    const current = state.contracts.find((item) => item.id === state.selectedId);
    if (current && ["Completed", "NeedHumanConfirm", "NeedRevision", "Failed"].includes(current.status)) return;
    try {
      await loadContractDetail(state.selectedId);
    } catch (error) {
      console.warn(error);
    }
  }, 1500);
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

function toast(message) {
  const node = document.createElement("div");
  node.className = "toast";
  node.textContent = message;
  document.body.appendChild(node);
  setTimeout(() => node.remove(), 2600);
}

els.uploadBtn.addEventListener("click", () => els.fileInput.click());
els.fileInput.addEventListener("change", () => uploadFile(els.fileInput.files[0]).catch((error) => toast(error.message)));
els.refreshBtn.addEventListener("click", () => loadContracts().catch((error) => toast(error.message)));
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

document.querySelectorAll(".tab-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab-btn").forEach((item) => item.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach((item) => item.classList.add("hidden"));
    btn.classList.add("active");
    $(`#${btn.dataset.tab}Tab`).classList.remove("hidden");
  });
});

loadContracts().catch((error) => toast(error.message));
