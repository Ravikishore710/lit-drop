// Scientific Multimodal Document Intelligence Studio Client Logic

const API_BASE = "http://localhost:8000";

let state = {
  documents: [],
  selectedDoc: null,
  canonicalData: null,
  currentPage: 1,
  totalPages: 1,
  showOverlays: true,
  activeCitationId: null,
};

// DOM Elements
const docListEl = document.getElementById("document-list");
const docCountBadge = document.getElementById("doc-count-badge");
const searchInput = document.getElementById("library-search");
const currentDocTitle = document.getElementById("current-doc-title");
const currentPageIndicator = document.getElementById("current-page-indicator");
const pageImageEl = document.getElementById("page-image");
const bboxOverlayEl = document.getElementById("bbox-overlay");
const emptyViewerState = document.getElementById("empty-viewer-state");
const inspectorElemType = document.getElementById("inspector-elem-type");
const inspectorElemContent = document.getElementById("inspector-elem-content");
const prevPageBtn = document.getElementById("prev-page-btn");
const nextPageBtn = document.getElementById("next-page-btn");
const toggleBBoxesBtn = document.getElementById("toggle-bboxes-btn");
const queryForm = document.getElementById("query-form");
const queryInput = document.getElementById("query-input");
const qaResultsContainer = document.getElementById("qa-results");
const uploadBtnTrigger = document.getElementById("upload-btn-trigger");
const pdfFileInput = document.getElementById("pdf-file-input");

// Initialization
async function init() {
  await fetchDocuments();
  setupEventListeners();
}

// Fetch Document Collection
async function fetchDocuments() {
  try {
    const res = await fetch(`${API_BASE}/api/v1/documents`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const docs = await res.json();
    state.documents = docs;
    docCountBadge.innerText = `${docs.length} papers`;
    renderDocumentList(docs);

    if (docs.length > 0 && !state.selectedDoc) {
      selectDocument(docs[0]);
    }
  } catch (err) {
    console.warn("Could not reach backend API:", err);
    docListEl.innerHTML = `<div class="p-4 text-xs text-muted">Backend not connected on ${API_BASE}. Start FastAPI backend or check network.</div>`;
  }
}

// Render Document Cards
function renderDocumentList(docs) {
  if (!docs.length) {
    docListEl.innerHTML = `<div class="p-4 text-xs text-muted">No documents found. Use 'Upload PDF' to ingest.</div>`;
    return;
  }

  docListEl.innerHTML = docs
    .map((doc) => {
      const isSelected = state.selectedDoc && state.selectedDoc.document_id === doc.document_id;
      const cleanTitle = doc.title || doc.filename || "Untitled Paper";
      const authors = doc.authors && doc.authors.length ? doc.authors.join(", ") : "Unknown authors";
      const pages = doc.page_count ? `${doc.page_count} pages` : "Processing...";
      const statusClass = doc.status === "READY" ? "badge-found" : "badge-inferred";

      return `
        <div class="doc-card ${isSelected ? "selected" : ""}" data-doc-id="${doc.document_id}">
          <div class="doc-card-title">${escapeHtml(cleanTitle)}</div>
          <div class="doc-card-meta">
            <span>${escapeHtml(authors.slice(0, 30))}...</span>
            <span class="badge ${statusClass}">${pages}</span>
          </div>
        </div>
      `;
    })
    .join("");

  // Attach click events
  document.querySelectorAll(".doc-card").forEach((card) => {
    card.addEventListener("click", () => {
      const docId = card.getAttribute("data-doc-id");
      const found = state.documents.find((d) => d.document_id === docId);
      if (found) selectDocument(found);
    });
  });
}

// Select Active Document
async function selectDocument(doc) {
  state.selectedDoc = doc;
  state.currentPage = 1;
  currentDocTitle.innerText = doc.title || doc.filename;

  // Highlight card in list
  document.querySelectorAll(".doc-card").forEach((c) => {
    c.classList.toggle("selected", c.getAttribute("data-doc-id") === doc.document_id);
  });

  // Fetch Full Canonical Record
  try {
    const res = await fetch(`${API_BASE}/api/v1/documents/${encodeURIComponent(doc.document_id)}`);
    if (res.ok) {
      state.canonicalData = await res.json();
      state.totalPages = state.canonicalData.pages ? state.canonicalData.pages.length : (doc.page_count || 1);
    } else {
      state.canonicalData = null;
      state.totalPages = doc.page_count || 1;
    }
  } catch (e) {
    state.canonicalData = null;
    state.totalPages = doc.page_count || 1;
  }

  renderActivePage();
}

// Render Page and Bounding Box Overlays
function renderActivePage() {
  if (!state.selectedDoc) return;

  emptyViewerState.style.display = "none";
  pageImageEl.style.display = "block";
  currentPageIndicator.innerText = `Page ${state.currentPage} / ${state.totalPages}`;

  const cleanId = state.selectedDoc.document_id;
  const pageUrl = `${API_BASE}/api/v1/documents/${encodeURIComponent(cleanId)}/pages/${state.currentPage}`;

  pageImageEl.src = pageUrl;
  pageImageEl.onload = () => {
    drawBoundingBoxes();
  };
}

// Draw Interactive SVG Bounding Boxes
function drawBoundingBoxes() {
  bboxOverlayEl.innerHTML = "";
  if (!state.showOverlays || !state.canonicalData) return;

  const width = pageImageEl.clientWidth;
  const height = pageImageEl.clientHeight;
  const naturalWidth = pageImageEl.naturalWidth || width;
  const naturalHeight = pageImageEl.naturalHeight || height;

  const scaleX = width / naturalWidth;
  const scaleY = height / naturalHeight;

  // Filter elements on current page
  const pageElements = (state.canonicalData.elements || []).filter(
    (e) => e.page_number === state.currentPage
  );

  pageElements.forEach((elem) => {
    const [x0, y0, x1, y1] = elem.bounding_box;
    const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");

    // Standard fitz 72-dpi PDF coordinates to rendered pixels (150-dpi)
    const renderScale = 150 / 72;
    const rx = x0 * renderScale * scaleX;
    const ry = y0 * renderScale * scaleY;
    const rw = (x1 - x0) * renderScale * scaleX;
    const rh = (y1 - y0) * renderScale * scaleY;

    rect.setAttribute("x", rx);
    rect.setAttribute("y", ry);
    rect.setAttribute("width", rw);
    rect.setAttribute("height", rh);
    rect.setAttribute("class", `bbox-rect type-${elem.element_type}`);
    rect.setAttribute("data-element-id", elem.element_id);

    // Hover Inspection
    rect.addEventListener("mouseenter", () => {
      inspectorElemType.innerText = elem.element_type.toUpperCase();
      let content = elem.normalized_content;
      if (elem.structured_data && elem.structured_data.columns) {
        content = `TABLE COLUMNS: ${elem.structured_data.columns.join(" | ")}\n` +
          elem.structured_data.rows.slice(0, 3).map((r) => r.join(" | ")).join("\n");
      }
      inspectorElemContent.innerText = `[${elem.element_id}] bbox=${JSON.stringify(elem.bounding_box)}\n\n${content}`;
    });

    bboxOverlayEl.appendChild(rect);
  });
}

// Grounded Query Submission
async function handleQuery(e) {
  e.preventDefault();
  const query = queryInput.value.trim();
  if (!query) return;

  if (!state.selectedDoc) {
    alert("Please select a paper from the library first.");
    return;
  }

  const docId = state.selectedDoc.document_id;
  qaResultsContainer.innerHTML = `
    <div class="p-6 text-center text-xs text-muted">
      <div style="margin-bottom:8px;font-weight:600;">Executing Multi-Channel Hybrid Retrieval & Verification...</div>
      Dense (Qdrant) + Lexical (BM25) → RRF Fusion → Cross-Encoder → Evidence Grounding
    </div>
  `;

  try {
    const res = await fetch(`${API_BASE}/api/v1/documents/${encodeURIComponent(docId)}/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: query, top_k: 8 }),
    });

    if (!res.ok) throw new Error(`Query failed with HTTP ${res.status}`);
    const answerData = await res.json();
    renderAnswer(query, answerData);
  } catch (err) {
    qaResultsContainer.innerHTML = `
      <div class="answer-card">
        <div class="answer-header">
          <span class="badge badge-notfound">ERROR</span>
        </div>
        <div class="answer-text">Failed to execute grounded query: ${err.message}</div>
      </div>
    `;
  }
}

// Render Structured Answer with Clickable Citations
function renderAnswer(query, data) {
  const statusClass =
    data.status === "FOUND" ? "badge-found" : data.status === "INFERRED" ? "badge-inferred" : "badge-notfound";

  // Replace [SRC_XX] tags with clickable chips
  let formattedAnswer = escapeHtml(data.answer);
  formattedAnswer = formattedAnswer.replace(/\[(SRC_\d{2})\]/g, (match, tag) => {
    return `<span class="citation-chip" data-src-tag="${tag}">${tag}</span>`;
  });

  const evidenceHtml = (data.citations || [])
    .map(
      (c) => `
      <div class="evidence-item" data-src-tag="${c.source_id}">
        <strong>[${c.source_id}]</strong> Page ${c.page_number} (Doc: ${escapeHtml(c.document_id.slice(0, 16))}...)
        <div style="color:var(--text-muted);margin-top:2px;">${escapeHtml(c.text_snippet)}</div>
      </div>
    `
    )
    .join("");

  qaResultsContainer.innerHTML = `
    <div class="answer-card">
      <div class="answer-header">
        <span class="badge ${statusClass}">${data.status}</span>
        <span class="text-xs text-muted" style="font-family:var(--font-mono)">Confidence: ${(data.confidence * 100).toFixed(0)}%</span>
      </div>
      <div class="answer-text">${formattedAnswer}</div>

      <div class="evidence-drawer">
        <div class="evidence-title">Verified Supporting Evidence (${data.citations ? data.citations.length : 0})</div>
        ${evidenceHtml || '<div class="text-xs text-muted">No explicit citation evidence items linked.</div>'}
      </div>
    </div>
  `;

  // Attach Citation Jump Listeners
  document.querySelectorAll(".citation-chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      const tag = chip.getAttribute("data-src-tag");
      const citation = (data.citations || []).find((c) => c.source_id === tag);
      if (citation && citation.page_number) {
        state.currentPage = citation.page_number;
        renderActivePage();
      }
    });
  });
}

// Event Listeners Setup
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
    drawBoundingBoxes();
  });

  queryForm.addEventListener("submit", handleQuery);

  uploadBtnTrigger.addEventListener("click", () => pdfFileInput.click());

  pdfFileInput.addEventListener("change", async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${API_BASE}/api/v1/documents`, {
        method: "POST",
        body: formData,
      });
      if (res.ok) {
        alert(`Document "${file.name}" uploaded successfully! Asynchronous parsing running.`);
        await fetchDocuments();
      }
    } catch (err) {
      alert(`Upload failed: ${err.message}`);
    }
  });

  searchInput.addEventListener("input", (e) => {
    const term = e.target.value.toLowerCase();
    const filtered = state.documents.filter(
      (d) =>
        (d.title && d.title.toLowerCase().includes(term)) ||
        (d.filename && d.filename.toLowerCase().includes(term)) ||
        (d.document_id && d.document_id.toLowerCase().includes(term))
    );
    renderDocumentList(filtered);
  });
}

function escapeHtml(str) {
  if (!str) return "";
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

window.addEventListener("DOMContentLoaded", init);
