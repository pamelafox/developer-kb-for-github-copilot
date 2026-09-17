const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
let documents = [];
const mcpEndpoints = {};

function toast(message) {
  const element = $("#toast");
  element.textContent = message;
  element.classList.add("show");
  window.setTimeout(() => element.classList.remove("show"), 3200);
}

async function api(url, options = {}) {
  const response = await fetch(url, options);
  if (!response.ok) {
    let message = `${response.status} ${response.statusText}`;
    try { message = (await response.json()).detail || message; } catch {}
    throw new Error(message);
  }
  return response.status === 204 ? null : response.json();
}

function showJson(selector, value) {
  const element = $(selector);
  element.classList.remove("empty");
  element.textContent = JSON.stringify(value, null, 2);
}

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function formatBytes(size) {
  if (!Number.isFinite(size)) return "Unknown size";
  if (size < 1024) return `${size} B`;
  return `${(size / 1024).toFixed(1)} KB`;
}

function setLoading(container, message) {
  container.replaceChildren(element("div", "empty-state loading", message));
}

const panelPaths = {
  documents: "/documents",
  chunks: "/document-chunks",
  search: "/document-search",
  "documents-kb": "/documents-kb",
  "combined-kb": "/combined-kb",
};

function activatePanel(target, updateHistory = false) {
  const button = $(`.nav-item[data-target="${target}"]`);
  const panel = $(`#${target}`);
  if (!button || !panel) return;
  $$(".nav-item, .panel").forEach((item) => item.classList.remove("active"));
  button.classList.add("active");
  panel.classList.add("active");
  if (updateHistory) window.history.pushState({ target }, "", panelPaths[target]);
}

function activatePanelFromLocation() {
  const target = Object.entries(panelPaths).find(([, path]) => path === window.location.pathname)?.[0] || "documents";
  activatePanel(target);
}

$$('.nav-item').forEach((button) => button.addEventListener("click", () => activatePanel(button.dataset.target, true)));
window.addEventListener("popstate", activatePanelFromLocation);
activatePanelFromLocation();

async function loadDocuments() {
  const list = $("#document-list");
  try {
    const result = await api("/api/documents");
    documents = result.documents || [];
    list.replaceChildren();
    for (const document of documents) {
      const link = element("a", "document-row");
      link.href = document.url;
      link.target = "_blank";
      link.rel = "noopener";
      const identity = element("div", "document-identity");
      identity.append(element("span", "file-type", "PDF"), element("strong", "", document.name));
      const metadata = element("span", "document-meta", formatBytes(document.size));
      if (document.lastModified) metadata.textContent += ` · ${new Date(document.lastModified).toLocaleDateString()}`;
      link.append(identity, metadata, element("span", "open-mark", "↗"));
      list.append(link);
    }
    if (!documents.length) list.append(element("div", "empty-state", "No PDF documents found."));

    const select = $("#document-select");
    select.replaceChildren(new Option("Select a document", ""));
    for (const document of documents) select.add(new Option(document.name, document.name));
  } catch (error) {
    list.replaceChildren(element("div", "empty-state error", error.message));
    toast(error.message);
  }
}

$("#document-select").addEventListener("change", async (event) => {
  const documentName = event.target.value;
  const list = $("#chunk-list");
  if (!documentName) {
    list.replaceChildren(element("div", "empty-state", "Select a document to inspect its chunks."));
    return;
  }
  setLoading(list, "Loading ordered chunks...");
  try {
    const result = await api(`/api/documents/chunks?document=${encodeURIComponent(documentName)}&limit=500`);
    $("#chunk-summary").textContent = `${result.chunks.length} chunks · ${result.index}`;
    list.replaceChildren(...result.chunks.map((chunk, index) => renderChunk(chunk, index + 1)));
  } catch (error) {
    list.replaceChildren(element("div", "empty-state error", error.message));
    toast(error.message);
  }
});

function renderChunk(chunk, position, includeScore = false) {
  const article = element("article", "chunk-card");
  const heading = element("div", "chunk-heading");
  heading.append(element("span", "chunk-number", String(position).padStart(2, "0")));
  const title = element("div");
  title.append(element("h3", "", chunk.title || "Untitled chunk"));
  const pages = [chunk.page_number_from, chunk.page_number_to].filter((value) => value !== null && value !== undefined);
  title.append(element("span", "chunk-pages", pages.length ? `Pages ${pages.join("–")}` : "Page unavailable"));
  heading.append(title);
  if (includeScore) {
    const scores = element("div", "score-list");
    const rerankerScore = chunk["@search.reranker_score"];
    const searchScore = chunk["@search.score"];
    if (rerankerScore !== undefined) scores.append(element("span", "score", `Reranker ${Number(rerankerScore).toFixed(3)}`));
    if (searchScore !== undefined) scores.append(element("span", "score score-secondary", `Search ${Number(searchScore).toFixed(3)}`));
    if (rerankerScore === undefined && searchScore === undefined) scores.append(element("span", "score", "Match"));
    heading.append(scores);
  }
  article.append(heading, element("div", "chunk-content", chunk.chunk || "No chunk text."));
  const metadata = element("dl", "chunk-metadata");
  for (const [label, value] of [
    ["chunk_id", chunk.chunk_id],
    ["page_number_from", chunk.page_number_from],
    ["page_number_to", chunk.page_number_to],
    ["image_path", chunk.image_path],
  ]) {
    metadata.append(element("dt", "", label), element("dd", "", value ?? "—"));
  }
  article.append(metadata);
  return article;
}

$("#search-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const query = $("#search-query").value.trim();
  const results = $("#search-results");
  if (!query) return;
  setLoading(results, "Running hybrid search...");
  try {
    const result = await api("/api/documents/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, limit: 10 }),
    });
    $("#search-summary").textContent = `${result.matches.length} matches · hybrid semantic + vector`;
    results.replaceChildren(...result.matches.map((chunk, index) => renderChunk(chunk, index + 1, true)));
    if (!result.matches.length) results.append(element("div", "empty-state", "No matching chunks."));
  } catch (error) {
    results.replaceChildren(element("div", "empty-state error", error.message));
    toast(error.message);
  }
});

function configDetails(title, value) {
  const details = element("details", "config-details");
  details.append(element("summary", "", title));
  const pre = element("pre");
  pre.textContent = JSON.stringify(value, null, 2);
  details.append(pre);
  return details;
}

function sourceFacts(source) {
  const facts = element("dl", "config-facts source-facts");
  const parameters = source.searchIndexParameters || source.search_index_parameters
    || source.mcpServerParameters || source.mcp_server_parameters || {};
  const kind = source.kind || source["@odata.type"] || "source";
  const entries = source.kind === "mcpServer"
    ? [
        ["Kind", kind],
        ["Description", source.description],
        ["Server URL", parameters.serverURL || parameters.server_url],
        ["Tools", parameters.tools?.map((tool) => tool.name).join(", ")],
      ]
    : [
        ["Kind", kind],
        ["Description", source.description],
        ["Search index", parameters.searchIndexName || parameters.search_index_name],
        ["Semantic configuration", parameters.semanticConfigurationName || parameters.semantic_configuration_name],
        ["Search fields", parameters.searchFields?.map((field) => field.name).join(", ")],
        ["Source data fields", parameters.sourceDataFields?.map((field) => field.name).join(", ")],
      ];
  for (const [label, value] of entries) {
    if (!value) continue;
    facts.append(element("dt", "", label), element("dd", "", value));
  }
  return facts;
}

async function loadConfiguration() {
  const containers = {
    documents: $("#documents-kb-configuration"),
    combined: $("#combined-kb-configuration"),
  };
  Object.values(containers).forEach((container) => setLoading(container, "Loading live resource definition..."));
  try {
    const result = await api("/api/knowledge-bases");
    const sources = new Map(result.knowledgeSources.map((source) => [source.name, source]));
    Object.values(containers).forEach((container) => container.replaceChildren());
    for (const kb of result.knowledgeBases) {
      const section = element("section", "configuration-item");
      section.append(element("h3", "", kb.name));
      const facts = element("dl", "config-facts");
      const model = kb.models?.[0]?.azureOpenAIParameters || kb.models?.[0]?.azure_open_ai_parameters || {};
      for (const [label, value] of [
        ["Description", kb.description],
        ["Output mode", kb.outputMode || kb.output_mode || "default"],
        ["Reasoning", kb.retrievalReasoningEffort?.kind || kb.retrieval_reasoning_effort?.kind || "default"],
        ["Retrieval instructions", kb.retrievalInstructions || kb.retrieval_instructions],
        ["Model deployment", model.deploymentId || model.deployment_id || model.modelName || model.model_name],
      ]) {
        if (!value) continue;
        facts.append(element("dt", "", label), element("dd", "", value));
      }
      const endpointKind = kb.name === "cocoarynth-kb-all" ? "combined" : "documents";
      const endpointStrip = $(`.mcp-strip[data-kb="${endpointKind}"]`);
      const endpointValue = element("dd", "mcp-value mcp-strip");
      endpointValue.dataset.kb = endpointKind;
      endpointValue.append($("code", endpointStrip), $("button", endpointStrip));
      endpointStrip.remove();
      facts.append(element("dt", "", "MCP URL"), endpointValue);
      section.append(facts);
      const sourceList = element("div", "source-list");
      sourceList.append(element("h3", "", "Knowledge sources:"));
      for (const reference of kb.knowledgeSources || kb.knowledge_sources || []) {
        const source = sources.get(reference.name) || reference;
        const row = element("div", "source-row");
        row.append(element("h4", "", source.name));
        row.append(sourceFacts(source));
        sourceList.append(row);
      }
      section.append(sourceList);
      containers[endpointKind].append(section);
    }
  } catch (error) {
    Object.values(containers).forEach((container) => container.replaceChildren(element("div", "empty-state error", error.message)));
    toast(error.message);
  }
}

function parseExtractedRecords(result) {
  const text = result.response?.flatMap((message) => message.content || []).find((item) => item.type === "text")?.text;
  if (!text) return [];
  try {
    const records = JSON.parse(text);
    return Array.isArray(records) ? records : [records];
  } catch {
    return [{ content: text }];
  }
}

function activityLabel(activity) {
  return ({
    modelQueryPlanning: "Query planning",
    searchIndex: "Index search",
    mcpServer: "MCP tool call",
    mcpTool: "MCP tool call",
    agenticReasoning: "Agentic reasoning",
    modelAnswerSynthesis: "Answer synthesis",
  })[activity.type] || activity.type || "Activity";
}

function appendActivityFact(container, label, value) {
  if (value === undefined || value === null || value === "") return;
  const row = element("div", "activity-fact");
  row.append(element("strong", "", `${label}:`), element("span", "", String(value)));
  container.append(row);
}

function createTokenMeter(activity) {
  const input = Math.max(Number(activity.inputTokens) || 0, 0);
  const output = Math.max(Number(activity.outputTokens) || 0, 0);
  const reasoning = Math.max(Number(activity.reasoningTokens) || 0, 0);
  const total = input + output + reasoning;
  if (!total) return null;

  const meter = element("div", "token-meter");
  const heading = element("div", "token-meter-heading");
  heading.append(element("span", "", "Token usage"), element("strong", "", total.toLocaleString()));
  meter.append(heading);

  const track = element("div", "token-track");
  for (const [kind, value] of [["input", input], ["output", output], ["reasoning", reasoning]]) {
    if (!value) continue;
    const segment = element("span", `token-segment token-${kind}`);
    segment.style.width = `${(value / total) * 100}%`;
    segment.title = `${kind[0].toUpperCase()}${kind.slice(1)}: ${value.toLocaleString()} tokens`;
    track.append(segment);
  }
  meter.append(track);

  const legend = element("div", "token-legend");
  for (const [kind, value] of [["Input", input], ["Output", output], ["Reasoning", reasoning]]) {
    if (!value) continue;
    const item = element("span", `token-key token-${kind.toLowerCase()}`);
    item.append(element("i"), document.createTextNode(`${kind} ${value.toLocaleString()}`));
    legend.append(item);
  }
  meter.append(legend);
  return meter;
}

function createActivityDetails(activity) {
  const details = element("div", "activity-details");
  const tokenMeter = createTokenMeter(activity);
  if (tokenMeter) details.append(tokenMeter);

  if (activity.type === "searchIndex") {
    appendActivityFact(details, "Source", activity.knowledgeSourceName || "Search index");
    appendActivityFact(details, "Search", activity.searchIndexArguments?.search || "—");
    appendActivityFact(details, "Results", activity.count);
  } else if (activity.type === "mcpServer" || activity.type === "mcpTool") {
    appendActivityFact(details, "Source", activity.knowledgeSourceName || "MCP server");
    appendActivityFact(details, "Tool", activity.mcpServerArguments?.toolName || activity.toolName || "—");
    const toolArguments = activity.mcpServerArguments?.toolArguments || activity.toolArguments;
    if (toolArguments && Object.keys(toolArguments).length) {
      appendActivityFact(details, "Arguments", JSON.stringify(toolArguments));
    }
    appendActivityFact(details, "Results", activity.count);
  } else if (activity.type === "modelQueryPlanning" || activity.type === "modelAnswerSynthesis") {
    appendActivityFact(details, "Model", activity.modelName);
  } else if (activity.type === "agenticReasoning") {
    appendActivityFact(details, "Reasoning effort", activity.retrievalReasoningEffort?.kind || "default");
    details.append(element("p", "activity-note", "Reasoning tokens are consumed by Azure AI Search models, not the deployed chat model."));
  }

  if (activity.error?.message) details.append(element("div", "activity-error", activity.error.message));
  details.append(configDetails("View step data", activity));
  return details;
}

function renderActivityLog(activities) {
  const table = element("div", "activity-table");
  table.setAttribute("role", "table");
  const header = element("div", "activity-table-header");
  header.setAttribute("role", "row");
  for (const label of ["Step", "Details", "Elapsed"]) {
    const cell = element("span", "", label);
    cell.setAttribute("role", "columnheader");
    header.append(cell);
  }
  table.append(header);

  activities.forEach((activity, index) => {
    const row = element("div", "activity-row");
    row.setAttribute("role", "row");
    const step = element("div", "activity-step-name");
    step.append(element("span", "activity-step-number", `Step ${index + 1}`));
    step.append(element("strong", "", activityLabel(activity)));
    const elapsed = element("div", "activity-elapsed", activity.elapsedMs === undefined ? "—" : `${activity.elapsedMs.toLocaleString()} ms`);
    row.append(step, createActivityDetails(activity), elapsed);
    table.append(row);
  });
  return table;
}

function formatReferenceContent(sourceData) {
  const content = sourceData?.chunk ?? sourceData?.content;
  if (content === undefined || content === null) return "";
  if (typeof content !== "string") return JSON.stringify(content, null, 2);
  try {
    return JSON.stringify(JSON.parse(content), null, 2);
  } catch {
    return content;
  }
}

function renderKnowledgeBaseResult(container, result) {
  container.replaceChildren();
  const records = parseExtractedRecords(result);
  const evidence = element("section", "kb-section");
  evidence.append(element("h3", "", `Extracted evidence · ${records.length}`));
  const evidenceList = element("div", "evidence-list");
  records.forEach((record, index) => {
    const item = element("article", "evidence-item");
    item.append(element("span", "evidence-index", String(index + 1).padStart(2, "0")));
    const body = element("div");
    body.append(element("h4", "", record.title || `Evidence ${index + 1}`));
    body.append(element("div", "evidence-content", record.content || JSON.stringify(record, null, 2)));
    item.append(body);
    evidenceList.append(item);
  });
  evidence.append(evidenceList);

  const activitySection = element("section", "kb-section");
  activitySection.append(element("h3", "", `Activity log · ${(result.activity || []).length} steps`));
  activitySection.append(renderActivityLog(result.activity || []));

  const references = element("section", "kb-section");
  references.append(element("h3", "", `References · ${(result.references || []).length}`));
  const referenceList = element("div", "reference-list");
  for (const reference of result.references || []) {
    const item = element("article", "reference-item");
    item.append(element("strong", "", reference.title || reference.type || "Reference"));
    item.append(element("span", "", `Source step ${reference.activitySource ?? "—"}`));
    if (reference.rerankerScore !== undefined) item.append(element("span", "score", `Score ${reference.rerankerScore.toFixed(3)}`));
    const content = formatReferenceContent(reference.sourceData);
    if (content) item.append(element("p", "reference-excerpt", content));
    referenceList.append(item);
  }
  references.append(referenceList);
  container.append(evidence, activitySection, references);
}

$$('.kb-search').forEach((form) => form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const output = form.nextElementSibling;
  const question = $("textarea", form).value.trim();
  const combined = form.dataset.combined === "true";
  if (!question) return;
  setLoading(output, combined ? "Searching documents and GitHub..." : "Searching documents knowledge base...");
  try {
    const result = await api("/api/retrieve", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, combined }),
    });
    renderKnowledgeBaseResult(output, result);
  } catch (error) {
    output.replaceChildren(element("div", "empty-state error", error.message));
    toast(error.message);
  }
}));

async function loadMcpEndpoints() {
  const [documentsConfig, combinedConfig] = await Promise.all([
    api("/api/mcp?combined=false"),
    api("/api/mcp?combined=true"),
  ]);
  mcpEndpoints.documents = documentsConfig.url;
  mcpEndpoints.combined = combinedConfig.url;
  $$(".mcp-strip").forEach((strip) => $("code", strip).textContent = mcpEndpoints[strip.dataset.kb]);
}

document.addEventListener("click", async (event) => {
  const button = event.target.closest(".copy-endpoint");
  if (!button) return;
  const endpoint = mcpEndpoints[button.closest(".mcp-strip").dataset.kb];
  await navigator.clipboard.writeText(endpoint);
  toast("MCP endpoint copied.");
});

Promise.all([loadDocuments(), loadMcpEndpoints(), loadConfiguration()]).catch((error) => toast(error.message));
