// lit-drop Studio Client Logic
const API_BASE = window.location.origin;

let state = {
  documents: [],
  selectedDoc: null,
  canonicalDoc: null,
  currentPage: 1,
  totalPages: 1,
  showOverlays: true,
  activeElement: null,
  activeTab: "studio",
  compareSelectedIds: [],
  activeCitationId: null,
};

// DOM Elements
const navTabs = document.querySelectorAll(".nav-tab");
const tabPanes = document.querySelectorAll(".tab-pane");
const docListEl = document.getElementById("document-list");
const docCountBadge = document.getElementById("doc-count-badge");
const librarySearch = document.getElementById("library-search");
const currentDocTitle = document.getElementById("current-doc-title");
const currentPageIndicator = document.getElementById("current-page-indicator");
const pageImageEl = document.getElementById("page-image");
const bboxOverlayEl = document.getElementById("bbox-overlay");
const emptyViewerState = document.getElementById("empty-viewer-state");
const inspectorElemType = document.getElementById("inspector-elem-type");
const inspectorElemContent = document.getElementById("inspector-elem-content");
const btnCropZoom = document.getElementById("btn-crop-zoom");
const prevPageBtn = document.getElementById("prev-page-btn");
const nextPageBtn = document.getElementById("next-page-btn");
const toggleBBoxesBtn = document.getElementById("toggle-bboxes-btn");
const queryForm = document.getElementById("query-form");
const queryInput = document.getElementById("query-input");
const qaResultsContainer = document.getElementById("qa-results");
const uploadBtnTrigger = document.getElementById("upload-btn-trigger");
const pdfFileInput = document.getElementById("pdf-file-input");

// Compare Elements
const compareDocSelector = document.getElementById("compare-doc-selector");
const compareSelectedCount = document.getElementById("compare-selected-count");
const compareQueryInput = document.getElementById("compare-query-input");
const btnRunCompare = document.getElementById("btn-run-compare");
const compareResultsArea = document.getElementById("compare-results-area");

// Search Elements
const globalSearchInput = document.getElementById("global-search-input");
const btnRunGlobalSearch = document.getElementById("btn-run-global-search");
const globalSearchResults = document.getElementById("global-search-results");

// Graph Elements
const graphDocTitle = document.getElementById("graph-doc-title");
const graphStatsBadge = document.getElementById("graph-stats-badge");
const graphSvg = document.getElementById("graph-svg");

// Modal Elements
const cropModal = document.getElementById("crop-modal");
const modalCropImg = document.getElementById("modal-crop-img");
const modalCropTitle = document.getElementById("modal-crop-title");
const btnCloseModal = document.getElementById("btn-close-modal");

// Init
window.addEventListener("DOMContentLoaded", () => {
  setupNavigation();
  setupEventListeners();
  fetchDocuments();
});

// Tab Navigation
function setupNavigation() {
  navTabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      const targetTab = tab.getAttribute("data-tab");
      state.activeTab = targetTab;

      navTabs.forEach((t) => t.classList.remove("active"));
      tabPanes.forEach((p) => p.classList.remove("active"));

      tab.classList.add("active");
      const activePane = document.getElementById(`tab-${targetTab}`);
      if (activePane) activePane.classList.add("active");

      if (targetTab === "graph" && state.selectedDoc) {
        renderDocumentGraph(state.selectedDoc.document_id);
      }
    });
  });
}

// Fetch Corpus Documents
async function fetchDocuments() {
  try {
    const res = await fetch(`${API_BASE}/api/v1/documents`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const docs = await res.json();
    state.documents = docs;
    docCountBadge.innerText = `${docs.length} papers`;
    renderDocumentList(docs);
    renderCompareSelector(docs);

    if (docs.length > 0 && !state.selectedDoc) {
      selectDocument(docs[0]);
    }
  } catch (err) {
    console.error("Failed to load corpus documents:", err);
    docListEl.innerHTML = `<div class="p-3 text-xs text-muted">Error connecting to lit-drop API. Verify backend server is active.</div>`;
  }
}

// Render Document Cards in Left Column
function renderDocumentList(docs) {
  if (!docs.length) {
    docListEl.innerHTML = `<div class="p-3 text-xs text-muted">No documents found. Upload a PDF to start.</div>`;
    return;
  }

  docListEl.innerHTML = docs
    .map((doc) => {
      const isSelected = state.selectedDoc && state.selectedDoc.document_id === doc.document_id;
      const cleanTitle = doc.title || doc.filename || "Untitled Paper";
      const cleanId = doc.filename ? doc.filename.replace(".pdf", "") : doc.document_id.slice(0, 16);
      const pages = doc.page_count ? `${doc.page_count} pgs` : "Ready";

      return `
        <div class="doc-card ${isSelected ? "selected" : ""}" data-doc-id="${doc.document_id}">
          <div class="doc-card-title">${escapeHtml(cleanTitle)}</div>
          <div class="doc-card-meta">
            <span>arXiv: ${escapeHtml(cleanId)}</span>
            <span class="badge badge-accent">${pages}</span>
          </div>
        </div>
      `;
    })
    .join("");

  docListEl.querySelectorAll(".doc-card").forEach((card) => {
    card.addEventListener("click", () => {
      const docId = card.getAttribute("data-doc-id");
      const found = state.documents.find((d) => d.document_id === docId);
      if (found) selectDocument(found);
    });
  });
}

// Select Active Paper
async function selectDocument(doc) {
  state.selectedDoc = doc;
  state.currentPage = 1;
  state.totalPages = doc.page_count || 1;

  document.querySelectorAll(".doc-card").forEach((c) => {
    c.classList.toggle("selected", c.getAttribute("data-doc-id") === doc.document_id);
  });

  const cleanTitle = doc.title || doc.filename;
  currentDocTitle.innerText = cleanTitle;
  currentDocTitle.title = cleanTitle;
  graphDocTitle.innerText = cleanTitle;

  try {
    const res = await fetch(`${API_BASE}/api/v1/documents/${doc.document_id}`);
    if (res.ok) {
      state.canonicalDoc = await res.json();
      state.totalPages = state.canonicalDoc.metadata.page_count || 1;
    }
  } catch (err) {
    console.warn("Could not fetch canonical JSON:", err);
  }

  renderActivePage();

  if (state.activeTab === "graph") {
    renderDocumentGraph(doc.document_id);
  }
}

// Render Page Image & SVG Bounding Boxes
function renderActivePage() {
  if (!state.selectedDoc) return;

  const docId = state.selectedDoc.document_id;
  currentPageIndicator.innerText = `Page ${state.currentPage} / ${state.totalPages}`;

  emptyViewerState.style.display = "none";
  pageImageEl.style.display = "block";

  const imgUrl = `${API_BASE}/api/v1/documents/${docId}/pages/${state.currentPage}`;
  pageImageEl.src = imgUrl;

  pageImageEl.onload = () => {
    renderBoundingBoxes();
  };
}

// Render SVG Bounding Box Layer
function renderBoundingBoxes() {
  bboxOverlayEl.innerHTML = "";
  if (!state.showOverlays || !state.canonicalDoc) return;

  const elements = state.canonicalDoc.elements || [];
  const pageElements = elements.filter((el) => el.page_number === state.currentPage);

  const imgW = pageImageEl.clientWidth;
  const imgH = pageImageEl.clientHeight;

  if (!imgW || !imgH) return;

  bboxOverlayEl.setAttribute("viewBox", `0 0 ${imgW} ${imgH}`);

  pageElements.forEach((el) => {
    const bbox = el.bounding_box;
    if (!bbox || !bbox.coordinates || bbox.coordinates.length < 4) return;

    // Normalized coordinates [x0, y0, x1, y1] (0 to 1)
    const [x0, y0, x1, y1] = bbox.coordinates;
    const rectX = x0 * imgW;
    const rectY = y0 * imgH;
    const rectW = (x1 - x0) * imgW;
    const rectH = (y1 - y0) * imgH;

    const typeColor = getElementTypeColor(el.element_type);

    const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    rect.setAttribute("x", rectX);
    rect.setAttribute("y", rectY);
    rect.setAttribute("width", rectW);
    rect.setAttribute("height", rectH);
    rect.setAttribute("fill", typeColor.fill);
    rect.setAttribute("stroke", typeColor.stroke);
    rect.setAttribute("stroke-width", "1");
    rect.setAttribute("class", "bbox-rect");
    rect.setAttribute("data-element-id", el.element_id);

    rect.addEventListener("mouseenter", () => inspectElement(el));
    rect.addEventListener("click", () => {
      inspectElement(el);
      if (el.element_type === "TABLE" || el.element_type === "FIGURE" || el.element_type === "CHART") {
        openCropModal(el.element_id, el.element_type);
      }
    });

    bboxOverlayEl.appendChild(rect);
  });
}

function getElementTypeColor(type) {
  switch (type) {
    case "TABLE":
      return { fill: "rgba(16, 185, 129, 0.25)", stroke: "#10b981" };
    case "FIGURE":
    case "CHART":
      return { fill: "rgba(168, 85, 247, 0.25)", stroke: "#a855f7" };
    case "EQUATION":
      return { fill: "rgba(245, 158, 11, 0.25)", stroke: "#f59e0b" };
    default:
      return { fill: "rgba(59, 130, 246, 0.15)", stroke: "#3b82f6" };
  }
}

// Inspect Element in Bottom Drawer
function inspectElement(el) {
  state.activeElement = el;
  inspectorElemType.innerText = el.element_type || "TEXT";
  inspectorElemContent.innerText = el.text || el.latex_representation || "[Visual Element]";

  if (el.element_type === "TABLE" || el.element_type === "FIGURE" || el.element_type === "CHART") {
    btnCropZoom.style.display = "inline-block";
    btnCropZoom.onclick = () => openCropModal(el.element_id, el.element_type);
  } else {
    btnCropZoom.style.display = "none";
  }
}

// Open Visual Crop Modal
function openCropModal(elementId, type) {
  const cropUrl = `${API_BASE}/api/v1/elements/${elementId}/crop`;
  modalCropImg.src = cropUrl;
  modalCropTitle.innerText = `${type} Crop — ${elementId}`;
  cropModal.style.display = "flex";
}

// Single-Doc Grounded QA Submission
async function handleQuerySubmit(e) {
  e.preventDefault();
  const query = queryInput.value.trim();
  if (!query) return;
  if (!state.selectedDoc) {
    alert("Please select a paper from the left library first.");
    return;
  }

  qaResultsContainer.innerHTML = `
    <div class="p-4 text-center text-muted">
      <div class="loading-spinner"></div>
      <p style="margin-top:10px; font-size:12px;">Synthesizing grounded answer with verified citations...</p>
    </div>
  `;

  try {
    const res = await fetch(`${API_BASE}/api/v1/documents/${state.selectedDoc.document_id}/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, top_k: 6 }),
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    renderQueryAnswer(data);
  } catch (err) {
    qaResultsContainer.innerHTML = `
      <div class="p-3 bg-red-900/30 border border-red-500/40 rounded text-xs text-red-300">
        Query failed: ${escapeHtml(err.message)}
      </div>
    `;
  }
}

// Render Answer with Interactive Citations
function renderQueryAnswer(data) {
  const statusBadge =
    data.status === "FOUND"
      ? '<span class="badge badge-found">FOUND (Verified)</span>'
      : data.status === "INFERRED"
      ? '<span class="badge badge-inferred">INFERRED</span>'
      : '<span class="badge badge-notfound">NOT_FOUND</span>';

  // Replace [SRC_XX] with clickable tags
  let formattedAnswer = escapeHtml(data.answer).replace(
    /\[(SRC_\d+)\]/g,
    `<button class="cite-tag-btn" data-tag="$1">[$1]</button>`
  );

  const evidenceCardsHtml = (data.citations || [])
    .map((cite) => {
      const pageNum = cite.page_number || 1;
      return `
        <div class="evidence-card" data-tag="${cite.source_id}">
          <div class="evidence-meta">
            <span class="badge badge-accent">${cite.source_id}</span>
            <span>Page ${pageNum}</span>
            <button class="btn-jump" data-page="${pageNum}" data-elem-ids="${(cite.element_ids || []).join(",")}">Jump to Page ➔</button>
          </div>
          <div class="evidence-snippet">${escapeHtml(cite.text_snippet || cite.snippet || "")}</div>
        </div>
      `;
    })
    .join("");

  qaResultsContainer.innerHTML = `
    <div class="qa-answer-card">
      <div class="answer-header">
        <span style="font-size:11px; font-weight:700; color:var(--text-muted)">MODEL ANSWER</span>
        ${statusBadge}
      </div>
      <div class="answer-text">${formattedAnswer}</div>
    </div>
    <div class="evidence-header">VERIFIED SOURCE RECEIPTS (${data.citations ? data.citations.length : 0})</div>
    <div class="evidence-list">${evidenceCardsHtml || '<p class="text-xs text-muted">No explicit evidence cited.</p>'}</div>
  `;

  // Attach citation button click jump
  qaResultsContainer.querySelectorAll(".cite-tag-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const tag = btn.getAttribute("data-tag");
      jumpToCitationTag(tag, data.citations);
    });
  });

  qaResultsContainer.querySelectorAll(".btn-jump").forEach((btn) => {
    btn.addEventListener("click", () => {
      const page = parseInt(btn.getAttribute("data-page"), 10);
      const elemIds = btn.getAttribute("data-elem-ids").split(",");
      jumpToPageAndHighlight(page, elemIds);
    });
  });
}

function jumpToCitationTag(tag, citations) {
  const match = citations.find((c) => c.source_id === tag);
  if (match) {
    jumpToPageAndHighlight(match.page_number || 1, match.element_ids || []);
  }
}

function jumpToPageAndHighlight(pageNum, elementIds) {
  state.currentPage = pageNum;
  renderActivePage();

  setTimeout(() => {
    elementIds.forEach((eid) => {
      const rect = bboxOverlayEl.querySelector(`rect[data-element-id="${eid}"]`);
      if (rect) {
        rect.classList.add("highlight-pulse");
        setTimeout(() => rect.classList.remove("highlight-pulse"), 4000);
      }
    });
  }, 300);
}

// Compare View Selector
function renderCompareSelector(docs) {
  compareDocSelector.innerHTML = docs
    .map((doc) => {
      const cleanTitle = doc.title || doc.filename;
      const cleanId = doc.filename ? doc.filename.replace(".pdf", "") : doc.document_id.slice(0, 10);
      return `
        <label class="compare-item">
          <input type="checkbox" value="${doc.document_id}" class="compare-checkbox" />
          <div style="overflow:hidden">
            <div style="font-size:11px; font-weight:600; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${escapeHtml(cleanTitle)}</div>
            <div style="font-size:10px; color:var(--text-muted)">arXiv: ${cleanId}</div>
          </div>
        </label>
      `;
    })
    .join("");

  compareDocSelector.querySelectorAll(".compare-checkbox").forEach((cb) => {
    cb.addEventListener("change", () => {
      const checked = Array.from(compareDocSelector.querySelectorAll(".compare-checkbox:checked")).map((c) => c.value);
      state.compareSelectedIds = checked;
      compareSelectedCount.innerText = `${checked.length} selected`;
    });
  });
}

// Run Compare
async function handleRunCompare() {
  const query = compareQueryInput.value.trim();
  if (!query) {
    alert("Please enter a comparative question.");
    return;
  }
  if (state.compareSelectedIds.length < 2) {
    alert("Please select at least 2 papers from the left list to compare.");
    return;
  }

  compareResultsArea.innerHTML = `
    <div class="p-8 text-center text-muted">
      <div class="loading-spinner"></div>
      <p style="margin-top:10px; font-size:13px;">Performing cross-paper retrieval, reranking, and comparative synthesis...</p>
    </div>
  `;

  try {
    const res = await fetch(`${API_BASE}/api/v1/compare`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ document_ids: state.compareSelectedIds, query, top_k: 10 }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    const formattedAns = escapeHtml(data.answer).replace(
      /\[(SRC_\d+)\]/g,
      `<span class="badge badge-accent" style="margin:0 2px;">$1</span>`
    );

    const evidenceHtml = (data.citations || [])
      .map(
        (c) => `
        <div class="evidence-card" style="margin-bottom:8px;">
          <div class="evidence-meta">
            <span class="badge badge-accent">${c.source_id}</span>
            <span>Doc: ${c.document_id.slice(0, 16)}... | Page ${c.page_number}</span>
          </div>
          <div class="evidence-snippet">${escapeHtml(c.text_snippet || c.snippet || "")}</div>
        </div>
      `
      )
      .join("");

    compareResultsArea.innerHTML = `
      <div class="qa-answer-card" style="padding:16px;">
        <div class="answer-header">
          <span style="font-size:12px; font-weight:700;">CROSS-PAPER SYNTHESIS</span>
          <span class="badge badge-found">${data.status}</span>
        </div>
        <div class="answer-text" style="font-size:13px;">${formattedAns}</div>
      </div>
      <div class="evidence-header">RETRIEVED MULTI-PAPER RECEIPTS</div>
      <div>${evidenceHtml}</div>
    `;
  } catch (err) {
    compareResultsArea.innerHTML = `<div class="p-4 text-xs text-red-400">Comparison failed: ${escapeHtml(err.message)}</div>`;
  }
}

// Global Hybrid Search
async function handleGlobalSearch() {
  const q = globalSearchInput.value.trim();
  if (!q) return;

  globalSearchResults.innerHTML = `
    <div class="p-8 text-center text-muted">
      <div class="loading-spinner"></div>
      <p style="margin-top:10px; font-size:13px;">Executing Qdrant SQ8 + BM25 Hybrid Reciprocal Rank Fusion search...</p>
    </div>
  `;

  try {
    const res = await fetch(`${API_BASE}/api/v1/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: q, top_k: 8 }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const results = await res.json();

    if (!results.length) {
      globalSearchResults.innerHTML = `<div class="p-8 text-center text-muted">No matching chunks found.</div>`;
      return;
    }

    globalSearchResults.innerHTML = results
      .map((hit, idx) => {
        const score = hit.fusion_score ? `RRF Score: ${hit.fusion_score.toFixed(4)}` : `Score: ${hit.score?.toFixed(2) || ""}`;
        return `
        <div class="search-result-card">
          <div class="search-result-meta">
            <span class="badge badge-accent">#${idx + 1} Result</span>
            <span>Doc: ${hit.document_id.slice(0, 18)}... | Page ${hit.page_numbers ? hit.page_numbers.join(",") : "?"}</span>
            <span style="font-family:var(--font-mono); color:#60a5fa">${score}</span>
          </div>
          <div style="font-size:12px; color:var(--text-main); line-height:1.5;">${escapeHtml(hit.text || "")}</div>
        </div>
      `;
      })
      .join("");
  } catch (err) {
    globalSearchResults.innerHTML = `<div class="p-4 text-xs text-red-400">Search error: ${escapeHtml(err.message)}</div>`;
  }
}

// Render Citation Graph Visualizer
async function renderDocumentGraph(docId) {
  graphSvg.innerHTML = "";
  try {
    const res = await fetch(`${API_BASE}/api/v1/documents/${docId}/graph`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const graph = await res.json();

    const nodes = graph.nodes || [];
    const edges = graph.edges || [];
    graphStatsBadge.innerText = `${nodes.length} nodes, ${edges.length} edges`;

    const w = graphSvg.clientWidth || 900;
    const h = graphSvg.clientHeight || 500;
    graphSvg.setAttribute("viewBox", `0 0 ${w} ${h}`);

    // Circular layout
    const cx = w / 2;
    const cy = h / 2;
    const radius = Math.min(w, h) * 0.38;

    const nodePositions = {};
    nodes.slice(0, 32).forEach((node, idx, arr) => {
      const angle = (idx / arr.length) * 2 * Math.PI;
      nodePositions[node.id] = {
        x: cx + radius * Math.cos(angle),
        y: cy + radius * Math.sin(angle),
        type: node.type,
      };
    });

    // Render edges
    edges.forEach((edge) => {
      const p1 = nodePositions[edge.source];
      const p2 = nodePositions[edge.target];
      if (p1 && p2) {
        const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
        line.setAttribute("x1", p1.x);
        line.setAttribute("y1", p1.y);
        line.setAttribute("x2", p2.x);
        line.setAttribute("y2", p2.y);
        line.setAttribute("stroke", "#334155");
        line.setAttribute("stroke-width", "1");
        graphSvg.appendChild(line);
      }
    });

    // Render nodes
    Object.keys(nodePositions).forEach((nodeId) => {
      const pos = nodePositions[nodeId];
      const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      circle.setAttribute("cx", pos.x);
      circle.setAttribute("cy", pos.y);
      circle.setAttribute("r", "6");
      circle.setAttribute("fill", pos.type === "DOCUMENT" ? "#3b82f6" : "#10b981");
      circle.setAttribute("stroke", "#0f172a");
      circle.setAttribute("stroke-width", "2");

      const title = document.createElementNS("http://www.w3.org/2000/svg", "title");
      title.textContent = `${pos.type}: ${nodeId}`;
      circle.appendChild(title);

      graphSvg.appendChild(circle);
    });
  } catch (err) {
    console.warn("Could not load graph:", err);
  }
}

// Event Listeners
function setupEventListeners() {
  prevPageBtn.addEventListener("click", () => {
    if (state.currentPage > 1) {
      state.currentPage--;
      renderActivePage();
    }
  });

  nextPageBtn.addEventListener("click", () => {
    if (state.currentPage < state.totalPages) {
      state.currentPage++;
      renderActivePage();
    }
  });

  toggleBBoxesBtn.addEventListener("click", () => {
    state.showOverlays = !state.showOverlays;
    toggleBBoxesBtn.classList.toggle("active", state.showOverlays);
    renderBoundingBoxes();
  });

  queryForm.addEventListener("submit", handleQuerySubmit);

  document.querySelectorAll(".suggestion-pill").forEach((pill) => {
    pill.addEventListener("click", () => {
      const q = pill.getAttribute("data-query");
      const c = pill.getAttribute("data-compare");
      if (q) {
        queryInput.value = q;
        handleQuerySubmit(new Event("submit"));
      } else if (c) {
        compareQueryInput.value = c;
      }
    });
  });

  btnRunCompare.addEventListener("click", handleRunCompare);
  btnRunGlobalSearch.addEventListener("click", handleGlobalSearch);
  globalSearchInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") handleGlobalSearch();
  });

  librarySearch.addEventListener("input", (e) => {
    const term = e.target.value.toLowerCase();
    const filtered = state.documents.filter(
      (d) =>
        (d.title && d.title.toLowerCase().includes(term)) ||
        (d.filename && d.filename.toLowerCase().includes(term)) ||
        d.document_id.toLowerCase().includes(term)
    );
    renderDocumentList(filtered);
  });

  uploadBtnTrigger.addEventListener("click", () => pdfFileInput.click());
  pdfFileInput.addEventListener("change", async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    uploadBtnTrigger.innerText = "Uploading...";
    try {
      const res = await fetch(`${API_BASE}/api/v1/documents`, {
        method: "POST",
        body: formData,
      });
      if (res.ok) {
        alert(`Paper "${file.name}" accepted for asynchronous parsing and indexing!`);
        setTimeout(fetchDocuments, 3000);
      }
    } catch (err) {
      alert("Upload failed: " + err.message);
    } finally {
      uploadBtnTrigger.innerHTML = `
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg>
        Upload PDF
      `;
    }
  });

  btnCloseModal.addEventListener("click", () => {
    cropModal.style.display = "none";
  });
  cropModal.addEventListener("click", (e) => {
    if (e.target === cropModal) cropModal.style.display = "none";
  });
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
