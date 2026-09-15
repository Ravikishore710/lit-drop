/**
 * lit-drop — Scientific Document Intelligence & Grounded Reasoning UI
 * Precision ES6+ Client Architecture
 */

const API_BASE = "";

// Global State
const state = {
  theme: localStorage.getItem("litdrop_theme") || "light",
  activeTab: "studio",
  documents: [],
  selectedDoc: null,
  canonicalDoc: null,
  currentPage: 1,
  totalPages: 1,
  showBBoxes: true,
  zoomLevel: 1.0,
  activeProofCitation: null,
  compareSelectedIds: [],
};

// DOM References
const appEl = document.getElementById("app");
const themeToggleBtn = document.getElementById("theme-toggle-btn");
const themeIcon = document.getElementById("theme-icon");
const themeLabel = document.getElementById("theme-label");

const navTabs = document.querySelectorAll(".nav-tab");
const tabPanes = document.querySelectorAll(".tab-pane");

const docCountBadge = document.getElementById("doc-count-badge");
const librarySearchInput = document.getElementById("library-search");
const documentListEl = document.getElementById("document-list");

const currentDocTitle = document.getElementById("current-doc-title");
const currentPageIndicator = document.getElementById("current-page-indicator");
const prevPageBtn = document.getElementById("prev-page-btn");
const nextPageBtn = document.getElementById("next-page-btn");
const zoomInBtn = document.getElementById("zoom-in-btn");
const zoomOutBtn = document.getElementById("zoom-out-btn");
const zoomResetBtn = document.getElementById("zoom-reset-btn");
const zoomDisplay = document.getElementById("zoom-display");
const toggleBBoxesBtn = document.getElementById("toggle-bboxes-btn");

const viewerViewport = document.getElementById("viewer-viewport");
const emptyViewerState = document.getElementById("empty-viewer-state");
const pageCanvasWrapper = document.getElementById("page-canvas-wrapper");
const pageImageEl = document.getElementById("page-image");
const bboxOverlayEl = document.getElementById("bbox-overlay");

const activeProofBanner = document.getElementById("active-proof-banner");
const proofBadgeLabel = document.getElementById("proof-badge-label");
const proofBannerText = document.getElementById("proof-banner-text");
const inspectActiveProofBtn = document.getElementById("inspect-active-proof-btn");
const dismissProofBannerBtn = document.getElementById("dismiss-proof-banner-btn");

const qaFeed = document.getElementById("qa-feed");
const qaForm = document.getElementById("qa-form");
const qaQueryInput = document.getElementById("qa-query-input");
const suggestionPills = document.querySelectorAll(".suggestion-pill");

// Compare & Search DOM
const compareDocPicker = document.getElementById("compare-doc-picker");
const compareQueryInput = document.getElementById("compare-query-input");
const btnRunCompare = document.getElementById("btn-run-compare");
const compareResultsArea = document.getElementById("compare-results-area");

const globalSearchInput = document.getElementById("global-search-input");
const btnRunSearch = document.getElementById("btn-run-search");
const globalSearchResults = document.getElementById("global-search-results");

const graphDocTitle = document.getElementById("graph-doc-title");
const graphStatsBadge = document.getElementById("graph-stats-badge");
const graphSvg = document.getElementById("graph-svg");

// Modals
const uploadBtnTrigger = document.getElementById("upload-btn-trigger");
const uploadModal = document.getElementById("upload-modal");
const closeUploadModal = document.getElementById("close-upload-modal");
const pdfDropZone = document.getElementById("pdf-drop-zone");
const modalFileInput = document.getElementById("modal-file-input");
const uploadProgressBox = document.getElementById("upload-progress-box");
const uploadStatusText = document.getElementById("upload-status-text");

const elementInspectorModal = document.getElementById("element-inspector-modal");
const closeInspectorModal = document.getElementById("close-inspector-modal");
const modalElementTypeBadge = document.getElementById("modal-element-type-badge");
const modalElementId = document.getElementById("modal-element-id");
const modalMetaPage = document.getElementById("modal-meta-page");
const modalMetaBbox = document.getElementById("modal-meta-bbox");
const modalMetaReading = document.getElementById("modal-meta-reading");
const modalElementContent = document.getElementById("modal-element-content");
const btnCopyElementContent = document.getElementById("btn-copy-element-content");

// ==========================================================================
// Initialization & Theme Handling
// ==========================================================================
document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  setupEventListeners();
  fetchDocuments();
});

function initTheme() {
  document.documentElement.setAttribute("data-theme", state.theme);
  updateThemeUI();
}

function toggleTheme() {
  state.theme = state.theme === "light" ? "dark" : "light";
  localStorage.setItem("litdrop_theme", state.theme);
  document.documentElement.setAttribute("data-theme", state.theme);
  updateThemeUI();
}

function updateThemeUI() {
  if (state.theme === "dark") {
    themeIcon.innerText = "☀️";
    themeLabel.innerText = "Light Mode";
  } else {
    themeIcon.innerText = "🌙";
    themeLabel.innerText = "Dark Mode";
  }
}

// ==========================================================================
// Event Listeners Setup
// ==========================================================================
function setupEventListeners() {
  // Theme Toggle
  themeToggleBtn.addEventListener("click", toggleTheme);

  // Tab Navigation
  navTabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      const targetTab = tab.getAttribute("data-tab");
      switchTab(targetTab);
    });
  });

  // Library Filter Search
  librarySearchInput.addEventListener("input", (e) => {
    renderDocumentList(e.target.value.trim().toLowerCase());
  });

  // Page Viewer Pagination
  prevPageBtn.addEventListener("click", () => {
    if (state.currentPage > 1) {
      state.currentPage--;
      renderCurrentPage();
    }
  });

  nextPageBtn.addEventListener("click", () => {
    if (state.currentPage < state.totalPages) {
      state.currentPage++;
      renderCurrentPage();
    }
  });

  // Zoom Controls
  zoomInBtn.addEventListener("click", () => setZoom(state.zoomLevel + 0.15));
  zoomOutBtn.addEventListener("click", () => setZoom(state.zoomLevel - 0.15));
  zoomResetBtn.addEventListener("click", () => setZoom(1.0));

  // Bounding Boxes Toggle
  toggleBBoxesBtn.addEventListener("click", () => {
    state.showBBoxes = !state.showBBoxes;
    toggleBBoxesBtn.classList.toggle("active", state.showBBoxes);
    bboxOverlayEl.style.display = state.showBBoxes ? "block" : "none";
  });

  // Proof Banner Actions
  dismissProofBannerBtn.addEventListener("click", () => {
    activeProofBanner.style.display = "none";
    document.querySelectorAll(".proof-highlight-active").forEach((r) => {
      r.classList.remove("proof-highlight-active");
    });
  });

  inspectActiveProofBtn.addEventListener("click", () => {
    if (state.activeProofCitation) {
      inspectProofCitation(state.activeProofCitation);
    }
  });

  // Q&A Submit Form & Enter Key Handler
  qaForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const query = qaQueryInput.value.trim();
    if (query) {
      executeUserQuery(query);
      qaQueryInput.value = "";
    }
  });

  qaQueryInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      const query = qaQueryInput.value.trim();
      if (query) {
        executeUserQuery(query);
        qaQueryInput.value = "";
      }
    }
  });

  // Suggestion Pills (Strictly 3 live queries)
  suggestionPills.forEach((pill) => {
    pill.addEventListener("click", () => {
      const q = pill.getAttribute("data-query");
      qaQueryInput.value = q;
      executeUserQuery(q);
    });
  });

  // Compare & Search
  btnRunCompare.addEventListener("click", runCrossPaperCompare);
  btnRunSearch.addEventListener("click", runGlobalHybridSearch);
  globalSearchInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") runGlobalHybridSearch();
  });

  // Upload Modal Handlers
  uploadBtnTrigger.addEventListener("click", () => {
    uploadModal.style.display = "flex";
  });
  closeUploadModal.addEventListener("click", () => {
    uploadModal.style.display = "none";
  });
  pdfDropZone.addEventListener("click", () => {
    modalFileInput.click();
  });
  modalFileInput.addEventListener("change", (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFileUpload(e.target.files[0]);
    }
  });

  // Drag & Drop
  pdfDropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    pdfDropZone.style.borderColor = "var(--accent-primary)";
  });
  pdfDropZone.addEventListener("dragleave", () => {
    pdfDropZone.style.borderColor = "var(--border-medium)";
  });
  pdfDropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    pdfDropZone.style.borderColor = "var(--border-medium)";
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  });

  // Element Inspector Close Handlers (X button, footer button, backdrop click, Escape key)
  closeInspectorModal.addEventListener("click", () => {
    elementInspectorModal.style.display = "none";
  });
  const btnModalCloseFooter = document.getElementById("btn-modal-close-footer");
  if (btnModalCloseFooter) {
    btnModalCloseFooter.addEventListener("click", () => {
      elementInspectorModal.style.display = "none";
    });
  }

  elementInspectorModal.addEventListener("click", (e) => {
    if (e.target === elementInspectorModal || e.target.classList.contains("modal-close-btn")) {
      elementInspectorModal.style.display = "none";
    }
  });

  uploadModal.addEventListener("click", (e) => {
    if (e.target === uploadModal || e.target.classList.contains("modal-close-btn")) {
      uploadModal.style.display = "none";
    }
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      elementInspectorModal.style.display = "none";
      uploadModal.style.display = "none";
    }
  });

  btnCopyElementContent.addEventListener("click", () => {
    navigator.clipboard.writeText(modalElementContent.innerText);
    btnCopyElementContent.innerText = "Copied!";
    setTimeout(() => {
      btnCopyElementContent.innerText = "Copy Text";
    }, 1500);
  });
}

function switchTab(tabId) {
  state.activeTab = tabId;
  navTabs.forEach((t) => t.classList.toggle("active", t.getAttribute("data-tab") === tabId));
  tabPanes.forEach((p) => p.classList.toggle("active", p.id === `tab-${tabId}`));

  if (tabId === "graph" && state.selectedDoc) {
    fetchAndRenderGraph(state.selectedDoc.document_id);
  }
}

// ==========================================================================
// Documents Catalog & Library Management
// ==========================================================================
async function fetchDocuments() {
  try {
    const res = await fetch(`${API_BASE}/api/v1/documents`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    state.documents = await res.json();
    docCountBadge.innerText = `${state.documents.length} Papers`;

    renderDocumentList();
    renderComparePicker();

    // Auto-select first paper if none active
    if (state.documents.length > 0 && !state.selectedDoc) {
      selectDocument(state.documents[0]);
    }
  } catch (err) {
    documentListEl.innerHTML = `<div class="loading-state">Failed to load papers: ${err.message}</div>`;
  }
}

function renderDocumentList(filterQuery = "") {
  if (!state.documents || state.documents.length === 0) {
    documentListEl.innerHTML = `<div class="loading-state">No documents available in catalog.</div>`;
    return;
  }

  const filtered = state.documents.filter((doc) => {
    if (!filterQuery) return true;
    const titleMatch = (doc.title || "").toLowerCase().includes(filterQuery);
    const idMatch = (doc.arxiv_id || doc.document_id || "").toLowerCase().includes(filterQuery);
    const authorMatch = (doc.authors || []).join(" ").toLowerCase().includes(filterQuery);
    return titleMatch || idMatch || authorMatch;
  });

  if (filtered.length === 0) {
    documentListEl.innerHTML = `<div class="loading-state">No papers matching "${filterQuery}"</div>`;
    return;
  }

  documentListEl.innerHTML = filtered
    .map((doc) => {
      const isSelected = state.selectedDoc && state.selectedDoc.document_id === doc.document_id;
      const authorsDisplay = doc.authors && doc.authors.length > 0
        ? doc.authors.slice(0, 2).join(", ") + (doc.authors.length > 2 ? " et al." : "")
        : doc.category || "Research Paper";

      return `
        <div class="doc-card ${isSelected ? "selected" : ""}" data-doc-id="${doc.document_id}">
          <div class="doc-card-title">${escapeHtml(doc.title || doc.filename)}</div>
          <div class="doc-card-meta">
            <span class="doc-card-authors">${escapeHtml(authorsDisplay)}</span>
            <span class="doc-card-pages">${doc.page_count || 1} pgs • ${doc.element_count || 0} elems</span>
          </div>
        </div>
      `;
    })
    .join("");

  documentListEl.querySelectorAll(".doc-card").forEach((card) => {
    card.addEventListener("click", () => {
      const docId = card.getAttribute("data-doc-id");
      const found = state.documents.find((d) => d.document_id === docId);
      if (found) selectDocument(found);
    });
  });
}

// Select Paper
async function selectDocument(doc) {
  state.selectedDoc = doc;
  state.currentPage = 1;
  state.totalPages = doc.page_count || 1;
  state.activeProofCitation = null;
  activeProofBanner.style.display = "none";

  currentDocTitle.innerText = doc.title || doc.filename;
  graphDocTitle.innerText = doc.title || doc.filename;

  // Update selection UI in library
  document.querySelectorAll(".doc-card").forEach((c) => {
    c.classList.toggle("selected", c.getAttribute("data-doc-id") === doc.document_id);
  });

  // Fetch full canonical document (elements, pages, relations)
  try {
    const res = await fetch(`${API_BASE}/api/v1/documents/${doc.document_id}`);
    if (res.ok) {
      state.canonicalDoc = await res.json();
      state.totalPages = state.canonicalDoc.metadata.page_count || state.totalPages;
    }
  } catch (err) {
    console.warn("Canonical doc fetch warning:", err);
  }

  renderCurrentPage();

  if (state.activeTab === "graph") {
    fetchAndRenderGraph(doc.document_id);
  }
}

// ==========================================================================
// 150 DPI Page Render & SVG Bounding Box Engine
// ==========================================================================
function renderCurrentPage() {
  if (!state.selectedDoc) return;

  const docId = state.selectedDoc.document_id;
  currentPageIndicator.innerText = `Page ${state.currentPage} of ${state.totalPages}`;

  emptyViewerState.style.display = "none";
  pageCanvasWrapper.style.display = "inline-block";

  const imgUrl = `${API_BASE}/api/v1/documents/${docId}/pages/${state.currentPage}`;
  pageImageEl.src = imgUrl;

  pageImageEl.onload = () => {
    renderBoundingBoxes();
    checkActiveProofHighlight();
  };
}

function setZoom(val) {
  state.zoomLevel = Math.max(0.5, Math.min(2.5, val));
  zoomDisplay.innerText = `${Math.round(state.zoomLevel * 100)}%`;
  pageCanvasWrapper.style.transform = `scale(${state.zoomLevel})`;
}

function renderBoundingBoxes() {
  bboxOverlayEl.innerHTML = "";
  if (!state.showBBoxes || !state.canonicalDoc) return;

  // Find page dimensions in PDF points
  const pageMeta = (state.canonicalDoc.pages || []).find((p) => p.page_number === state.currentPage);
  const pWidth = pageMeta ? pageMeta.width : 612;
  const pHeight = pageMeta ? pageMeta.height : 792;

  // Configure SVG viewBox matching PDF point space exactly
  bboxOverlayEl.setAttribute("viewBox", `0 0 ${pWidth} ${pHeight}`);
  bboxOverlayEl.setAttribute("preserveAspectRatio", "none");

  const pageElements = (state.canonicalDoc.elements || []).filter(
    (el) => el.page_number === state.currentPage
  );

  pageElements.forEach((el) => {
    const bbox = el.bounding_box;
    if (!bbox || bbox.length < 4) return;

    const [x0, y0, x1, y1] = bbox;
    const w = Math.max(2, x1 - x0);
    const h = Math.max(2, y1 - y0);

    const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    rect.setAttribute("x", x0);
    rect.setAttribute("y", y0);
    rect.setAttribute("width", w);
    rect.setAttribute("height", h);
    rect.setAttribute("stroke-width", "1.2");
    rect.setAttribute("data-element-id", el.element_id);

    // Color-code class
    const typeClass = getElementTypeClass(el);
    rect.setAttribute("class", `bbox-rect ${typeClass}`);

    // Click to Inspect Modal
    rect.addEventListener("click", (e) => {
      e.stopPropagation();
      openElementInspector(el);
    });

    bboxOverlayEl.appendChild(rect);
  });
}

function getPaperTitle(docId) {
  if (!docId && state.selectedDoc) return state.selectedDoc.title || state.selectedDoc.filename;
  if (state.selectedDoc && (state.selectedDoc.document_id === docId || (state.selectedDoc.arxiv_id && (docId + "").includes(state.selectedDoc.arxiv_id)))) {
    return state.selectedDoc.title || state.selectedDoc.filename;
  }
  const match = state.documents.find(
    (d) => d.document_id === docId || (d.arxiv_id && (docId + "").includes(d.arxiv_id)) || (d.title && (docId + "").includes(d.title))
  );
  return match ? match.title : (state.selectedDoc?.title || "Scientific Paper");
}

function getElementTypeClass(el) {
  const t = typeof el === "string" ? el.toLowerCase() : ((el.element_type || "") + "").toLowerCase();
  const text = typeof el === "object" ? (el.normalized_content || "") : "";

  // 1. Tables (headers, columns, pipes, numbers grids)
  if (
    t.includes("table") ||
    /\bTable\s+\d+/i.test(text) ||
    (text.includes("|") && text.split("|").length > 2) ||
    /\b(projected dimensions|time saved|memory saved|length n|dimension k)\b/i.test(text)
  ) {
    return "type-table";
  }

  // 2. Equations & Formulas
  if (
    t.includes("equation") ||
    t.includes("formula") ||
    /[=∑∫√×±]|\b(softmax|Attention|head_i|d_k|d_v|W_i|d_model)\b|\\frac|\\sum|\(\d+\)\s*$/i.test(text) ||
    /\b(dim|matrix|vector|parameter)\b.*[=<>]/i.test(text)
  ) {
    return "type-equation";
  }

  // 3. Figures & Charts
  if (t.includes("figure") || t.includes("chart") || t.includes("caption") || /\b(Figure|Fig\.)\s+\d+/i.test(text)) {
    return "type-figure";
  }

  return "type-text";
}

// ==========================================================================
// Interactive Citation Jump & Proof Focus Engine
// ==========================================================================
function jumpToCitationProof(citation) {
  if (!citation) return;
  state.activeProofCitation = citation;

  // 1. Switch to cited page
  state.currentPage = citation.page_number;
  currentPageIndicator.innerText = `Page ${state.currentPage} of ${state.totalPages}`;

  // 2. Display Proof Banner with human paper title
  const paperName = getPaperTitle(citation.document_id);
  proofBadgeLabel.innerText = citation.source_id;
  proofBannerText.innerText = `Proof focused: ${paperName} • Page ${citation.page_number} • "${(citation.text_snippet || "").slice(0, 75)}..."`;
  activeProofBanner.style.display = "flex";

  // 3. Render page and trigger bounding box highlight
  const docId = state.selectedDoc.document_id;
  pageImageEl.src = `${API_BASE}/api/v1/documents/${docId}/pages/${state.currentPage}`;

  pageImageEl.onload = () => {
    renderBoundingBoxes();
    checkActiveProofHighlight();
  };
}

function checkActiveProofHighlight() {
  if (!state.activeProofCitation) return;
  const targetIds = state.activeProofCitation.element_ids || [];

  // Remove previous pulse highlights
  document.querySelectorAll(".proof-highlight-active").forEach((r) => {
    r.classList.remove("proof-highlight-active");
  });

  let matchedRect = null;
  for (const eid of targetIds) {
    const rect = bboxOverlayEl.querySelector(`[data-element-id="${eid}"]`);
    if (rect) {
      matchedRect = rect;
      break;
    }
  }

  // If exact element ID not mapped, highlight first element on that page
  if (!matchedRect) {
    matchedRect = bboxOverlayEl.querySelector(".bbox-rect");
  }

  if (matchedRect) {
    matchedRect.classList.add("proof-highlight-active");
    // Center proof bounding box smoothly in the viewport
    matchedRect.scrollIntoView({ behavior: "smooth", block: "center", inline: "center" });
  }
}

function inspectProofCitation(citation) {
  const targetId = citation.element_ids && citation.element_ids[0];
  let el = null;
  if (state.canonicalDoc && targetId) {
    el = (state.canonicalDoc.elements || []).find((e) => e.element_id === targetId);
  }

  if (el) {
    openElementInspector(el);
  } else {
    const paperTitle = getPaperTitle(citation.document_id);
    modalElementTypeBadge.className = "badge type-table";
    modalElementTypeBadge.innerText = citation.source_id;
    modalElementId.innerText = `${paperTitle} • Page ${citation.page_number} Proof`;
    modalMetaPage.innerText = `Page ${citation.page_number}`;
    modalMetaBbox.innerText = "Evidence Candidate";
    modalMetaReading.innerText = citation.parent_section_id || "Section";
    modalElementContent.innerText = citation.text_snippet || "No text available";
    elementInspectorModal.style.display = "flex";
  }
}

function openElementInspector(el) {
  const paperTitle = getPaperTitle(state.selectedDoc?.document_id);
  const typeClass = getElementTypeClass(el);
  const typeLabel = typeClass.replace("type-", "").toUpperCase();

  modalElementTypeBadge.className = `badge ${typeClass}`;
  modalElementTypeBadge.innerText = typeLabel;
  modalElementId.innerText = `${paperTitle} • Page ${el.page_number} (Item #${el.reading_order ?? 1})`;
  modalMetaPage.innerText = `Page ${el.page_number}`;
  modalMetaBbox.innerText = Array.isArray(el.bounding_box)
    ? el.bounding_box.map((n) => Math.round(n)).join(", ")
    : "N/A";
  modalMetaReading.innerText = `#${el.reading_order ?? 1}`;
  modalElementContent.innerText = el.normalized_content || "(No text content)";
  elementInspectorModal.style.display = "flex";
}

// ==========================================================================
// Grounded Q&A Assistant Execution
// ==========================================================================
async function executeUserQuery(query) {
  if (!state.selectedDoc) {
    alert("Please select a paper from the library first.");
    return;
  }

  // Append user bubble
  appendChatBubble("user", query);

  // Append loading assistant bubble
  const loadingBubble = appendChatBubble("assistant", `
    <div style="display:flex; align-items:center; gap:8px; color:var(--text-secondary);">
      <div class="spinner"></div>
      <span>Reasoning across multimodal evidence & generating grounded citations...</span>
    </div>
  `);

  try {
    const res = await fetch(`${API_BASE}/api/v1/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        document_id: state.selectedDoc.document_id,
        query: query,
        top_k: 6,
      }),
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    // Clean internal doc/sha256 prefixes from answer text
    const rawAnswer = data.answer || "No response received.";
    const cleanAnswer = rawAnswer
      .replace(/\(Doc:\s*[^)]+\):?/gi, "")
      .replace(/\bDoc:\s*sha256:[a-f0-9]+/gi, "")
      .replace(/\bsha256:[a-f0-9]{12,}\b/gi, "")
      .replace(/\s{2,}/g, " ")
      .trim();

    const formattedAnswer = escapeHtml(cleanAnswer).replace(
      /\[(SRC_\d{2})\]/g,
      `<button class="citation-badge" data-source-id="$1">[$1]</button>`
    );

    // Build evidence cards HTML with clean paper titles
    const citations = data.citations || [];
    const evidenceHtml = citations.length > 0
      ? `
        <div class="evidence-section">
          <div class="evidence-header">Verified Evidence Citations (Click to jump to proof):</div>
          ${citations
            .map((c) => {
              const paperName = getPaperTitle(c.document_id);
              return `
                <div class="evidence-card" data-source-id="${c.source_id}">
                  <div class="evidence-card-meta">
                    <span class="proof-badge">${c.source_id}</span>
                    <span style="font-weight:600; color:var(--text-primary); font-size:11.5px;">${escapeHtml(paperName)}</span>
                    <span style="font-family:var(--font-mono); color:var(--accent-primary);">Page ${c.page_number}</span>
                  </div>
                  <div class="evidence-card-text">${escapeHtml(c.text_snippet || "")}</div>
                </div>
              `;
            })
            .join("")}
        </div>
      `
      : "";

    // Replace loading bubble content
    loadingBubble.querySelector(".bubble-body").innerHTML = `
      <div class="answer-meta-row">
        <span style="font-weight:600; font-size:12px; color:var(--text-secondary);">Grounded Synthesis</span>
        <span class="confidence-chip">Confidence: ${(data.confidence * 100).toFixed(0)}%</span>
      </div>
      <div class="answer-text">${formattedAnswer}</div>
      ${evidenceHtml}
    `;

    // Attach click handlers to citation badges & evidence cards
    loadingBubble.querySelectorAll("[data-source-id]").forEach((el) => {
      el.addEventListener("click", () => {
        const srcId = el.getAttribute("data-source-id");
        const foundCitation = citations.find((c) => c.source_id === srcId);
        if (foundCitation) {
          jumpToCitationProof(foundCitation);
        }
      });
    });

    qaFeed.scrollTop = qaFeed.scrollHeight;
  } catch (err) {
    loadingBubble.querySelector(".bubble-body").innerHTML = `
      <div style="color:#ef4444; font-size:12.5px;">Query processing error: ${escapeHtml(err.message)}</div>
    `;
  }
}

function appendChatBubble(role, contentHtml) {
  const bubble = document.createElement("div");
  bubble.className = `chat-bubble ${role}`;
  bubble.innerHTML = `<div class="bubble-body">${contentHtml}</div>`;
  qaFeed.appendChild(bubble);
  qaFeed.scrollTop = qaFeed.scrollHeight;
  return bubble;
}

// ==========================================================================
// Cross-Paper Compare Tab
// ==========================================================================
function renderComparePicker() {
  if (!state.documents || state.documents.length === 0) return;
  compareDocPicker.innerHTML = state.documents
    .map(
      (doc) => `
      <label class="compare-doc-item">
        <input type="checkbox" value="${doc.document_id}" />
        <span class="compare-doc-label">${escapeHtml(doc.title || doc.filename)}</span>
      </label>
    `
    )
    .join("");

  compareDocPicker.querySelectorAll("input").forEach((box) => {
    box.addEventListener("change", () => {
      state.compareSelectedIds = Array.from(
        compareDocPicker.querySelectorAll("input:checked")
      ).map((b) => b.value);
    });
  });
}

async function runCrossPaperCompare() {
  const query = compareQueryInput.value.trim();
  if (state.compareSelectedIds.length < 2) {
    alert("Please select at least 2 papers from the list to compare.");
    return;
  }
  if (!query) {
    alert("Please enter a comparative research question.");
    return;
  }

  compareResultsArea.innerHTML = `
    <div class="loading-state">
      <div class="spinner"></div>
      <p style="margin-top:10px;">Synthesizing comparative evidence across ${state.compareSelectedIds.length} papers...</p>
    </div>
  `;

  try {
    const res = await fetch(`${API_BASE}/api/v1/compare`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        document_ids: state.compareSelectedIds,
        query: query,
        top_k: 10,
      }),
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    const formattedAns = escapeHtml(data.answer).replace(
      /\[(SRC_\d{2})\]/g,
      `<span class="proof-badge" style="margin:0 2px;">$1</span>`
    );

    const evidenceList = (data.citations || [])
      .map(
        (c) => `
        <div class="evidence-card">
          <div class="evidence-card-meta">
            <span class="proof-badge">${c.source_id}</span>
            <span style="font-family:var(--font-mono); color:var(--accent-primary);">Page ${c.page_number}</span>
          </div>
          <div class="evidence-card-text">${escapeHtml(c.text_snippet || "")}</div>
        </div>
      `
      )
      .join("");

    compareResultsArea.innerHTML = `
      <div class="chat-bubble assistant" style="width:100%;">
        <div class="bubble-body" style="padding:18px;">
          <div class="answer-meta-row">
            <span style="font-weight:600; font-size:13px; color:var(--accent-primary);">Cross-Paper Comparative Analysis</span>
            <span class="confidence-chip">Confidence: ${(data.confidence * 100).toFixed(0)}%</span>
          </div>
          <div style="font-size:13.5px; line-height:1.6; margin-bottom:14px;">${formattedAns}</div>
          <div class="evidence-section">
            <div class="evidence-header">Supporting Cross-Paper Evidence:</div>
            ${evidenceList}
          </div>
        </div>
      </div>
    `;
  } catch (err) {
    compareResultsArea.innerHTML = `<div class="loading-state" style="color:#ef4444;">Comparison error: ${escapeHtml(err.message)}</div>`;
  }
}

// ==========================================================================
// Global Hybrid Search Tab
// ==========================================================================
async function runGlobalHybridSearch() {
  const q = globalSearchInput.value.trim();
  if (!q) return;

  globalSearchResults.innerHTML = `
    <div class="loading-state">
      <div class="spinner"></div>
      <p style="margin-top:10px;">Searching Qdrant dense vectors and BM25 inverted index with RRF fusion...</p>
    </div>
  `;

  try {
    const res = await fetch(`${API_BASE}/api/v1/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: q, top_k: 10 }),
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const results = await res.json();

    if (!results || results.length === 0) {
      globalSearchResults.innerHTML = `<div class="empty-viewer-state"><p class="text-muted">No matching chunks found for "${escapeHtml(q)}".</p></div>`;
      return;
    }

    globalSearchResults.innerHTML = results
      .map((hit, idx) => {
        const score = hit.fusion_score
          ? `RRF Score: ${hit.fusion_score.toFixed(4)}`
          : `Score: ${hit.score?.toFixed(2) || ""}`;

        // Find paper title if possible
        const docMatch = state.documents.find((d) => hit.document_id.includes(d.arxiv_id || ""));
        const paperName = docMatch ? docMatch.title : `Document ${hit.document_id.slice(0, 16)}...`;

        return `
        <div class="search-result-card">
          <div class="search-result-meta">
            <span class="proof-badge">Rank #${idx + 1}</span>
            <span style="font-weight:600; color:var(--text-primary);">${escapeHtml(paperName)}</span>
            <span style="font-family:var(--font-mono); color:var(--accent-primary);">${score}</span>
          </div>
          <div style="font-size:12.5px; color:var(--text-secondary); line-height:1.5;">${escapeHtml(hit.text || "")}</div>
        </div>
      `;
      })
      .join("");
  } catch (err) {
    globalSearchResults.innerHTML = `<div class="loading-state" style="color:#ef4444;">Search error: ${escapeHtml(err.message)}</div>`;
  }
}

// ==========================================================================
// Citation Knowledge Graph Visualizer
// ==========================================================================
async function fetchAndRenderGraph(docId) {
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

    if (nodes.length === 0) {
      const txt = document.createElementNS("http://www.w3.org/2000/svg", "text");
      txt.setAttribute("x", w / 2);
      txt.setAttribute("y", h / 2);
      txt.setAttribute("text-anchor", "middle");
      txt.setAttribute("fill", "var(--text-muted)");
      txt.textContent = "No graph relations available for this document.";
      graphSvg.appendChild(txt);
      return;
    }

    // Circular layout
    const centerX = w / 2;
    const centerY = h / 2;
    const radius = Math.min(w, h) * 0.38;

    const displayNodes = nodes.slice(0, 36);
    const nodeCoords = new Map();

    displayNodes.forEach((node, i) => {
      const angle = (2 * Math.PI * i) / displayNodes.length;
      const x = centerX + radius * Math.cos(angle);
      const y = centerY + radius * Math.sin(angle);
      nodeCoords.set(node.id, { x, y, ...node });
    });

    // Edges
    edges.forEach((edge) => {
      const source = nodeCoords.get(edge.source);
      const target = nodeCoords.get(edge.target);
      if (source && target) {
        const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
        line.setAttribute("x1", source.x);
        line.setAttribute("y1", source.y);
        line.setAttribute("x2", target.x);
        line.setAttribute("y2", target.y);
        line.setAttribute("stroke", "var(--border-medium)");
        line.setAttribute("stroke-width", "1");
        line.setAttribute("stroke-opacity", "0.4");
        graphSvg.appendChild(line);
      }
    });

    // Nodes
    nodeCoords.forEach((node) => {
      const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      circle.setAttribute("cx", node.x);
      circle.setAttribute("cy", node.y);
      circle.setAttribute("r", node.type === "Document" ? 10 : 6);

      let col = "#f59e0b";
      if (node.type === "Document") col = "#2563eb";
      else if (node.type === "Page") col = "#10b981";

      circle.setAttribute("fill", col);
      circle.setAttribute("stroke", "#fff");
      circle.setAttribute("stroke-width", "1.5");
      circle.style.cursor = "pointer";

      circle.addEventListener("click", () => {
        alert(`Node: ${node.id}\nType: ${node.type}\nLabel: ${node.title || node.content_preview || ""}`);
      });

      graphSvg.appendChild(circle);
    });
  } catch (err) {
    console.warn("Graph rendering exception:", err);
  }
}

// ==========================================================================
// Custom PDF File Upload
// ==========================================================================
async function handleFileUpload(file) {
  if (!file.name.toLowerCase().endsWith(".pdf")) {
    alert("Only PDF files are supported.");
    return;
  }

  uploadProgressBox.style.display = "flex";
  uploadStatusText.innerText = `Uploading and ingesting ${file.name}...`;

  const formData = new FormData();
  formData.append("file", file);

  try {
    const res = await fetch(`${API_BASE}/api/v1/documents`, {
      method: "POST",
      body: formData,
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    uploadStatusText.innerText = "Ingestion complete! Refreshing catalog...";
    setTimeout(async () => {
      uploadModal.style.display = "none";
      uploadProgressBox.style.display = "none";
      await fetchDocuments();
    }, 1500);
  } catch (err) {
    uploadStatusText.innerText = `Upload failed: ${err.message}`;
  }
}

// Utility
function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
