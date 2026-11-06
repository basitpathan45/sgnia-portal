// Homepage search and source lookup.

// Connect the homepage controls to their HTML elements.
const searchForm = document.querySelector("#search-form");
const keywordInput = document.querySelector("#keyword");
const departmentSelect = document.querySelector("#department");
const dateFromInput = document.querySelector("#date-from");
const dateToInput = document.querySelector("#date-to");
const referenceInput = document.querySelector("#reference");
const sortSelect = document.querySelector("#sort-order");
const recordList = document.querySelector("#record-list");
const resultsSummary = document.querySelector("#results-summary");
const emptyState = document.querySelector("#empty-state");
const verifyForm = document.querySelector("#verify-form");
const verifyReferenceInput = document.querySelector("#verify-reference");
const verifyResult = document.querySelector("#verify-result");
const qrStartButton = document.querySelector("#qr-start");
const qrStopButton = document.querySelector("#qr-stop");
const qrImageInput = document.querySelector("#qr-image");
const qrCamera = document.querySelector("#qr-camera");
const qrVideo = document.querySelector("#qr-video");
const qrStatus = document.querySelector("#qr-status");
const qrCanvas = document.createElement("canvas");
const qrCanvasContext = qrCanvas.getContext("2d", { willReadFrequently: true });

// Escape values from records before placing them in HTML templates.
const escapeHtml = (value) => String(value).replace(/[&<>"']/g, (character) => ({
  "&": "&amp;",
  "<": "&lt;",
  ">": "&gt;",
  '"': "&quot;",
  "'": "&#39;",
}[character]));

const formatDate = (dateString, options) => new Intl.DateTimeFormat("en-GB", options)
  .format(new Date(`${dateString}T00:00:00`));

// Fill the department dropdown using the shared department list.
function populateDepartments() {
  for (const department of departments) {
    if (Array.from(departmentSelect.options).some((option) => option.value === department.name)) continue;
    const option = document.createElement("option");
    option.value = department.name;
    option.textContent = department.name;
    departmentSelect.append(option);
  }

  const unspecified = records.find((record) => record.departmentCode === null);
  if (unspecified && !Array.from(departmentSelect.options).some((option) => option.value === unspecified.department)) {
    const option = document.createElement("option");
    option.value = unspecified.department;
    option.textContent = unspecified.department;
    departmentSelect.append(option);
  }

  for (const record of records) {
    if (!record.isSgniaRecord || Array.from(departmentSelect.options).some((option) => option.value === record.department)) continue;
    const option = document.createElement("option");
    option.value = record.department;
    option.textContent = record.department;
    departmentSelect.append(option);
  }
}

// Apply the homepage keyword, department, date, reference, and sort filters.
function getFilteredRecords() {
  const keyword = keywordInput.value.trim().toLocaleLowerCase();
  const department = departmentSelect.value;
  const from = dateFromInput.value;
  const to = dateToInput.value;
  const reference = referenceInput.value.trim().toLocaleLowerCase();

  return records
    .filter((record) => {
      const searchText = `${record.title} ${record.department} ${record.shortDepartment} ${record.id} ${record.archiveReference} ${record.officialReference || ""} ${record.portalListingNumber} ${record.pdfUrl} ${record.type}`.toLocaleLowerCase();
      return (!keyword || searchText.includes(keyword))
        && (!department || record.department === department)
        && (!from || record.date >= from)
        && (!to || record.date <= to)
        && (!reference || record.archiveReference.toLocaleLowerCase().includes(reference)
          || Boolean(record.officialReference && record.officialReference.toLocaleLowerCase().includes(reference))
          || String(record.portalListingNumber) === reference
          || record.title.toLocaleLowerCase().includes(reference)
          || record.pdfUrl.toLocaleLowerCase().includes(reference));
    })
    .sort((left, right) => sortSelect.value === "oldest"
      ? left.date.localeCompare(right.date)
      : right.date.localeCompare(left.date));
}

// Show up to nine matching records; the archive page shows the complete result set.
function renderRecords() {
  const filteredRecords = getFilteredRecords();
  const visibleRecords = filteredRecords.slice(0, 9);
  const hasRecords = filteredRecords.length > 0;

  resultsSummary.innerHTML = hasRecords
    ? filteredRecords.length > visibleRecords.length
      ? `Showing first <strong>${visibleRecords.length}</strong> of <strong>${filteredRecords.length}</strong> archive records · <a href="archive.html">View all matches →</a>`
      : `Showing <strong>${visibleRecords.length}</strong> of <strong>${filteredRecords.length}</strong> archive records`
    : "No records match your search";
  recordList.hidden = !hasRecords;
  emptyState.hidden = hasRecords;
  recordList.innerHTML = visibleRecords.map((record) => {
    const day = formatDate(record.date, { day: "2-digit" });
    const month = formatDate(record.date, { month: "short" });
    const fullDate = formatDate(record.date, { day: "numeric", month: "short", year: "numeric" });

    return `
      <article class="record-card">
        <div class="record-date" aria-label="${escapeHtml(fullDate)}">
          <span class="day">${day}</span>
          <span class="month">${month}</span>
        </div>
        <div class="record-main">
          <div class="record-type"><span class="type-dot"></span>${escapeHtml(record.type)}</div>
          <h3 class="record-title">${escapeHtml(record.title)}</h3>
          <div class="record-meta">
            <span><strong>Department:</strong> ${escapeHtml(record.shortDepartment)}</span>
            <span><strong>${record.isSgniaRecord ? "SGNIA record" : "Portal listing"}:</strong> ${record.isSgniaRecord ? "" : "#"}${escapeHtml(record.portalListingNumber)}</span>
            <span class="reference-meta"><strong>Archive ref:</strong> ${escapeHtml(record.archiveReference)}</span>
            ${record.officialReference ? `<span class="reference-meta"><strong>Official ref:</strong> ${escapeHtml(record.officialReference)}</span>` : ""}
          </div>
        </div>
        <div class="record-actions">
          <span class="status-badge">${record.isSgniaRecord ? "Published in SGNIA archive" : "Official source"}</span>
          ${record.isSgniaRecord && record.signatureVerificationUrl ? `<a class="record-qr-download" href="${escapeHtml(record.signatureVerificationUrl)}">Verify project signature</a>` : ""}
          <a class="record-qr-download" href="${escapeHtml(record.isSgniaRecord ? record.qrUrl : `assets/qr-codes/${record.archiveReference}.png`)}" download="${escapeHtml(record.archiveReference)}.png" aria-label="Download project QR code for ${escapeHtml(record.title)}">Download QR</a>
          <a class="record-open" href="${escapeHtml(record.pdfUrl)}" target="_blank" rel="noopener noreferrer">${record.isSgniaRecord ? "Open archived PDF" : "Open official PDF"} <span aria-hidden="true">↗</span></a>
        </div>
      </article>`;
  }).join("");
}

// Match only known archive records. QR-provided links are never opened automatically.
function findRecordFromQr(payload) {
  const value = String(payload).trim();
  const candidates = [value];

  try {
    const parsedPayload = JSON.parse(value);
    if (typeof parsedPayload === "string") candidates.push(parsedPayload);
    if (parsedPayload && typeof parsedPayload === "object") {
      candidates.push(...Object.values(parsedPayload).filter((item) => typeof item === "string"));
    }
  } catch {
    // Plain text and URLs are expected QR payloads; they do not need JSON parsing.
  }

  for (const candidate of [...candidates]) {
    try {
      const qrUrl = new URL(candidate);
      if (qrUrl.origin === window.location.origin) {
        const verificationMatch = qrUrl.pathname.match(/^\/verify\/([^/]+)$/);
        if (verificationMatch) candidates.push(decodeURIComponent(verificationMatch[1]));
        const queryReference = qrUrl.searchParams.get("verify");
        if (queryReference) candidates.push(queryReference);
      }
      const trustedHost = qrUrl.hostname === "sindh.gov.pk" || qrUrl.hostname === "www.sindh.gov.pk";
      if (qrUrl.protocol === "https:" && trustedHost && !qrUrl.port && !qrUrl.username && !qrUrl.password) {
        const path = qrUrl.pathname.toLocaleLowerCase();
        const record = records.find((item) => new URL(item.pdfUrl).pathname.toLocaleLowerCase() === path);
        if (record) return record;

        for (const key of ["ref", "reference", "id", "record", "number", "token", "listing"]) {
          const queryValue = qrUrl.searchParams.get(key);
          if (queryValue) candidates.push(queryValue);
        }
      }
    } catch {
      // The QR may contain a reference or plain text rather than a URL.
    }
  }

  return records.find((record) => candidates.some((candidate) => {
    const normalizedCandidate = candidate.trim().toLocaleLowerCase();
    return normalizedCandidate === record.archiveReference.toLocaleLowerCase()
      || normalizedCandidate === String(record.portalListingNumber)
      || normalizedCandidate === record.title.toLocaleLowerCase()
      || Boolean(record.officialReference
        && normalizedCandidate === record.officialReference.toLocaleLowerCase());
  })) || null;
}

// Allow a user-initiated link only when the QR points to the Government of Sindh domain.
function getOfficialQrUrl(payload) {
  const values = [String(payload).trim()];

  try {
    const parsedPayload = JSON.parse(values[0]);
    if (typeof parsedPayload === "string") values.push(parsedPayload);
    if (parsedPayload && typeof parsedPayload === "object") {
      values.push(...Object.values(parsedPayload).filter((item) => typeof item === "string"));
    }
  } catch {
    // QR payloads are often plain URLs rather than JSON.
  }

  for (const value of values) {
    try {
      const url = new URL(value);
      const trustedHost = url.hostname === "sindh.gov.pk" || url.hostname === "www.sindh.gov.pk";
      if (url.protocol === "https:" && trustedHost && !url.port && !url.username && !url.password) {
        return url.href;
      }
    } catch {
      // Ignore values that are not absolute URLs.
    }
  }

  return null;
}

// Show a matched record in the same result panel used by manual lookup.
let selectedVerificationRecord = null;

function showVerifiedRecord(record) {
  selectedVerificationRecord = record;
  if (!verifyReferenceInput.value) { verifyReferenceInput.value = record.archiveReference; }
  verifyResult.hidden = false;
  verifyResult.classList.remove("not-found");

  const recordSource = record.isSgniaRecord ? "SGNIA project record" : "Govt of Sindh Portal Listing";
  const documentLink = record.isSgniaRecord ? "Open Archived PDF Document" : "Open PDF on Official Sindh Govt Portal";
  const formattedDate = formatDate(record.date, { day: "numeric", month: "short", year: "numeric" });

  const integrityCheck = record.isSgniaRecord && record.pdfSha256
    ? `<div class="pdf-integrity">
        <div class="integrity-waiting" id="pdf-integrity-result" aria-live="polite">
          <div class="integrity-waiting-icon">🔍</div>
          <div class="integrity-waiting-text">
            <strong>Compare a PDF with the archived copy</strong>
            <span>Choose a local PDF to check whether its bytes match the file stored for this project record.</span>
          </div>
        </div>
        <details class="sha-technical-details" id="sha-details-accordion">
          <summary>Technical Details & SHA-256 Fingerprint</summary>
          <div class="sha-detail-block">
            <span class="sha-detail-label">Stored file fingerprint:</span>
            <code class="sha-hash-code">${escapeHtml(record.pdfSha256)}</code>
            <p class="sha-note">Verified locally in your browser using WebCrypto SHA-256. Zero data uploaded to servers.</p>
          </div>
        </details>
      </div>`
    : record.isSgniaRecord
      ? `<div class="pdf-integrity"><p class="sha-note">Fingerprint verification is pending for this record.</p></div>`
      : "";

  verifyResult.innerHTML = `
    <div class="verify-record-header">
      <span class="verify-record-badge"><span class="badge-dot"></span> ${escapeHtml(recordSource)}</span>
      <span class="verify-record-date">${escapeHtml(formattedDate)}</span>
    </div>
    <h4 class="verify-record-title">${escapeHtml(record.title)}</h4>
    <div class="verify-record-grid">
      <div class="verify-meta-cell">
        <span class="verify-meta-label">Department</span>
        <span class="verify-meta-val">${escapeHtml(record.shortDepartment)}</span>
      </div>
      <div class="verify-meta-cell">
        <span class="verify-meta-label">Archive Reference</span>
        <span class="verify-meta-val font-mono">${escapeHtml(record.archiveReference)}</span>
      </div>
      ${record.officialReference ? `
      <div class="verify-meta-cell full-width">
        <span class="verify-meta-label">Official Document Ref</span>
        <span class="verify-meta-val font-mono">${escapeHtml(record.officialReference)}</span>
      </div>` : ""}
    </div>
    <div class="verify-record-action">
      <a class="verify-pdf-btn" href="${escapeHtml(record.pdfUrl)}" target="_blank" rel="noopener noreferrer">
        <span aria-hidden="true">📄</span> ${escapeHtml(documentLink)} ↗
      </a>
    </div>
    ${integrityCheck}
  `;
}

// Request camera permission only after the visitor presses the start button.
let qrDetector;
let qrStream;
let qrAnimationFrame;
let isScanningQr = false;
let lastQrScanTime = 0;

function getQrDetector() {
  if ("BarcodeDetector" in window && !qrDetector) {
    try {
      qrDetector = new window.BarcodeDetector({ formats: ["qr_code"] });
    } catch (error) {
      if (typeof window.jsQR !== "function") throw error;
    }
  }

  return qrDetector || null;
}

// Decode a QR from a canvas-compatible source using the local browser library fallback.
function decodeQrWithLibrary(source) {
  if (typeof window.jsQR !== "function") {
    throw new Error("The QR decoder did not load. Check your internet connection and reload the page.");
  }
  if (!qrCanvasContext) {
    throw new Error("This browser cannot prepare an image for QR scanning.");
  }

  const sourceWidth = source.videoWidth || source.naturalWidth || source.width;
  const sourceHeight = source.videoHeight || source.naturalHeight || source.height;
  if (!sourceWidth || !sourceHeight) return null;

  const scale = Math.min(1, 1000 / Math.max(sourceWidth, sourceHeight));
  qrCanvas.width = Math.max(1, Math.round(sourceWidth * scale));
  qrCanvas.height = Math.max(1, Math.round(sourceHeight * scale));
  qrCanvasContext.drawImage(source, 0, 0, qrCanvas.width, qrCanvas.height);
  const pixels = qrCanvasContext.getImageData(0, 0, qrCanvas.width, qrCanvas.height);
  return window.jsQR(pixels.data, pixels.width, pixels.height, {
    inversionAttempts: "attemptBoth",
  })?.data || null;
}

// Prefer the native decoder; fall back to jsQR for browsers without it.
async function detectQrPayload(source) {
  const detector = getQrDetector();
  if (detector) {
    try {
      const [result] = await detector.detect(source);
      return result?.rawValue || null;
    } catch (error) {
      if (typeof window.jsQR !== "function") throw error;
    }
  }

  return decodeQrWithLibrary(source);
}

// Load image files in browsers that do not implement createImageBitmap.
async function loadQrImage(file) {
  if ("createImageBitmap" in window) {
    const image = await window.createImageBitmap(file);
    return { source: image, cleanup: () => image.close() };
  }

  const image = new Image();
  const objectUrl = URL.createObjectURL(file);
  try {
    await new Promise((resolve, reject) => {
      image.onload = resolve;
      image.onerror = () => reject(new Error("The selected image could not be opened."));
      image.src = objectUrl;
    });
  } catch (error) {
    URL.revokeObjectURL(objectUrl);
    throw error;
  }

  return { source: image, cleanup: () => URL.revokeObjectURL(objectUrl) };
}

function stopQrCamera(statusMessage = "Camera stopped.") {
  isScanningQr = false;
  window.cancelAnimationFrame(qrAnimationFrame);
  qrStream?.getTracks().forEach((track) => track.stop());
  qrStream = null;
  qrVideo.srcObject = null;
  qrCamera.hidden = true;
  qrStartButton.disabled = false;
  qrStopButton.disabled = true;
  qrStatus.textContent = statusMessage;
}

function handleQrPayload(payload) {
  const record = findRecordFromQr(payload);
  if (record) {
    showVerifiedRecord(record);
    return true;
  }

  const officialUrl = getOfficialQrUrl(payload);
  verifyResult.hidden = false;
  verifyResult.classList.toggle("not-found", !officialUrl);
  verifyResult.innerHTML = officialUrl
    ? `<strong>Government of Sindh link found</strong>This QR points to the official Government of Sindh website, but is not in this prototype's archive. Review the destination, then open it if expected: <a href="${escapeHtml(officialUrl)}" target="_blank" rel="noopener noreferrer">Open official website link ↗</a>. The link itself has not been authenticated.`
    : "<strong>No matching archive record</strong>This QR code does not match an archive record or an HTTPS link on the Government of Sindh website. No QR-provided link was opened. You can search the archive by title or reference.";
  return false;
}

async function scanCameraFrame() {
  if (!isScanningQr) return;

  try {
    const detector = getQrDetector();
    const now = performance.now();
    if (!detector && now - lastQrScanTime < 220) {
      qrAnimationFrame = window.requestAnimationFrame(scanCameraFrame);
      return;
    }

    if (qrVideo.readyState >= HTMLMediaElement.HAVE_CURRENT_DATA) {
      lastQrScanTime = now;
      const payload = await detectQrPayload(qrVideo);
      if (payload) {
        stopQrCamera("QR code scanned.");
        handleQrPayload(payload);
        return;
      }
    }
    qrAnimationFrame = window.requestAnimationFrame(scanCameraFrame);
  } catch (error) {
    stopQrCamera(`Could not scan this camera frame: ${error.message}`);
  }
}

if (qrStartButton) qrStartButton.addEventListener("click", async () => {
  try {
    if (!window.isSecureContext) {
      throw new Error("Camera access requires localhost or an HTTPS website.");
    }
    if (!navigator.mediaDevices?.getUserMedia) {
      throw new Error("Camera access is unavailable in this browser.");
    }
    getQrDetector();

    qrStatus.textContent = "Requesting camera permission…";
    qrStream = await navigator.mediaDevices.getUserMedia({
      audio: false,
      video: { facingMode: { ideal: "environment" } },
    });
    qrVideo.srcObject = qrStream;
    await qrVideo.play();
    qrCamera.hidden = false;
    qrStartButton.disabled = true;
    qrStopButton.disabled = false;
    isScanningQr = true;
    qrStatus.textContent = "Point the camera at a document QR code.";
    scanCameraFrame();
  } catch (error) {
    stopQrCamera(error.name === "NotAllowedError"
      ? "Camera permission was denied. Allow camera access in your browser settings, then try again."
      : error.message);
  }
});

if (qrStopButton) qrStopButton.addEventListener("click", () => stopQrCamera());

// Decode a selected QR image using the same browser QR detector as the camera.
if (qrImageInput) qrImageInput.addEventListener("change", async () => {
  const [imageFile] = qrImageInput.files;
  if (!imageFile) return;

  try {
    const image = await loadQrImage(imageFile);
    let payload;
    try {
      payload = await detectQrPayload(image.source);
    } finally {
      image.cleanup();
    }

    if (!payload) {
      qrStatus.textContent = "No QR code was found in that image. Try a clearer, well-lit image.";
      return;
    }

    qrStatus.textContent = "QR code scanned from image.";
    handleQrPayload(payload);
    verifyResult.scrollIntoView({ behavior: "smooth", block: "nearest" });
  } catch (error) {
    qrStatus.textContent = error.message;
  } finally {
    qrImageInput.value = "";
  }
});

// Stop the camera when the visitor leaves the page.
window.addEventListener("pagehide", () => stopQrCamera("Camera stopped."));

// Refresh results when the visitor searches, changes a filter, sorts, or clears the form.
searchForm.addEventListener("submit", (event) => {
  event.preventDefault();
  renderRecords();
});

searchForm.addEventListener("reset", () => {
  window.setTimeout(renderRecords, 0);
});

for (const input of [keywordInput, departmentSelect, dateFromInput, dateToInput, referenceInput]) {
  input.addEventListener("input", renderRecords);
  input.addEventListener("change", renderRecords);
}

sortSelect.addEventListener("change", renderRecords);
document.querySelector("#clear-filters").addEventListener("click", () => {
  window.setTimeout(renderRecords, 0);
});
document.querySelector("#empty-clear").addEventListener("click", () => {
  searchForm.reset();
  renderRecords();
});

function findArchiveRecord(query) {
  const trimmed = String(query || "").trim();
  const q = trimmed.toLocaleLowerCase();

  // 1. Minimum query length check
  if (!q || q.length < 3) {
    return null;
  }

  // 2. Reject pure numbers (e.g. "1", "2", "3", "8", "23", "24", "25", "31")
  // In document verification, a naked number is NOT a valid archive or official reference.
  if (/^\d+$/.test(q)) {
    return null;
  }

  // Also reject strings that are just hash/number prefixes and digits like "#23", "no. 23", "listing 23"
  if (/^(#|no\.?\s*|listing\s*)?\d+$/i.test(q)) {
    return null;
  }

  // 3. Exact match on Archive Reference (e.g., "SGNIA-2026-DFEE90F8", "SGNIA-ARCH-031")
  let found = records.find((item) => 
    item.archiveReference && item.archiveReference.toLocaleLowerCase() === q
  );
  if (found) return found;

  // 4. Exact match on Project ID (e.g., "SGNIA-56", "GOS-PORTAL-031")
  found = records.find((item) => 
    item.id && item.id.toLocaleLowerCase() === q
  );
  if (found) return found;

  // 5. Official Reference match (e.g. "SOVI(SGA&CD)4(24)/2026", "SO(T)/HD/9-2/2026", "DG-II/CERT/4/124/2023/P-I")
  // First try exact match
  found = records.find((item) => 
    item.officialReference && item.officialReference.toLocaleLowerCase() === q
  );
  if (found) return found;

  // Next try substring on officialReference ONLY if query has at least 5 chars AND contains letters
  if (q.length >= 5 && /[a-z]/i.test(q)) {
    found = records.find((item) => 
      item.officialReference && item.officialReference.toLocaleLowerCase().includes(q)
    );
    if (found) return found;
  }

  // 6. Title match
  // Exact match on Title
  found = records.find((item) => 
    item.title && item.title.toLocaleLowerCase() === q
  );
  if (found) return found;

  // Substring match on Title ONLY if query is at least 6 characters long and has real words (at least 3 letters in a row)
  if (q.length >= 6 && /[a-z]{3,}/i.test(q)) {
    found = records.find((item) => 
      item.title && item.title.toLocaleLowerCase().includes(q)
    );
    if (found) return found;
  }

  // Note: We deliberately do NOT match against item.pdfUrl or naked portalListingNumber
  return null;
}

function lookupArchiveRecord(reference) {
  selectedVerificationRecord = null;
  const rawInput = String(reference || "").trim();
  const record = findArchiveRecord(rawInput);
  verifyResult.hidden = false;
  verifyResult.classList.toggle("not-found", !record);

  if (!record) {
    const isPureNumber = /^\d+$/.test(rawInput) || /^(#|no\.?\s*|listing\s*)?\d+$/i.test(rawInput);
    const isTooShort = rawInput.length < 3;

    verifyResult.innerHTML = `
      <div class="verify-not-found-banner">
        <div class="not-found-badge" aria-hidden="true">✕</div>
        <div class="not-found-body">
          <strong class="not-found-title">Document Record Not Found</strong>
          <p class="not-found-message">
            ${isPureNumber ? `
              Aap ne sirf number <code>${escapeHtml(rawInput)}</code> darj kiya hai. Plain numbers se document verify <strong>nahi ho sakta</strong>.
            ` : isTooShort ? `
              Search query bohot choti hai (${escapeHtml(rawInput)}). Barah-e-karam kam az kam 3 characters darj karein.
            ` : `
              <code>${escapeHtml(rawInput)}</code> se koi official notification record match nahi hua.
            `}
          </p>
          <div class="not-found-guide">
            <span>Barah-e-karam notification par darj in mein se koi ek maloomat darj karein:</span>
            <ul>
              <li><strong>Archive Reference:</strong> Maslan <code>SGNIA-2026-0FD1FA7E</code> ya <code>SGNIA-ARCH-031</code></li>
              <li><strong>Official Reference:</strong> Maslan <code>SO(T)/HD/9-2/2026</code> ya <code>SOVI(SGA&CD)</code></li>
              <li><strong>Document Title:</strong> Maslan <em>Imposition of Section 144</em></li>
            </ul>
          </div>
        </div>
      </div>
    `;
    return;
  }

  showVerifiedRecord(record);
}

// Look up a source listing by its portal number, project reference, official reference, or title.
verifyForm.addEventListener("submit", (event) => {
  event.preventDefault();
  lookupArchiveRecord(verifyReferenceInput.value);
});

const verificationPdfInput = document.querySelector("#verify-pdf");
const verificationDropzone = document.querySelector("#verify-upload-dropzone");
const verificationFileName = document.querySelector("#verify-file-name");
const updateVerificationFileName = () => {
  verificationFileName.textContent = verificationPdfInput.files[0]?.name || "PDF only · Up to 16 MB";
};

verificationPdfInput.addEventListener("change", updateVerificationFileName);
verificationDropzone.addEventListener("dragover", (event) => {
  event.preventDefault();
  verificationDropzone.classList.add("is-dragging");
});
verificationDropzone.addEventListener("dragleave", () => {
  verificationDropzone.classList.remove("is-dragging");
});
verificationDropzone.addEventListener("drop", (event) => {
  event.preventDefault();
  verificationDropzone.classList.remove("is-dragging");
  if (!event.dataTransfer.files.length) return;
  verificationPdfInput.files = event.dataTransfer.files;
  verificationPdfInput.dispatchEvent(new Event("change", { bubbles: true }));
});

verificationPdfInput.addEventListener("change", async () => {
  const file = verificationPdfInput.files[0];
  if (!file) return;
  const result = document.querySelector("#pdf-integrity-result");
  if (!selectedVerificationRecord?.isSgniaRecord || !selectedVerificationRecord.pdfSha256) {
    verifyResult.hidden = false;
    const guidance = document.createElement("p");
    guidance.textContent = "Search for a published SGNIA record with a stored fingerprint first. Government source listings cannot be checked against an SGNIA file fingerprint.";
    verifyResult.append(guidance);
    return;
  }
  if (!result) {
    return;
  }
  if (file.size > 16 * 1024 * 1024) {
    result.textContent = "This PDF exceeds the 16 MB verification limit.";
    return;
  }

  result.className = "integrity-waiting integrity-calculating";
  result.innerHTML = `
    <div class="integrity-spinner"></div>
    <div class="integrity-waiting-text">
      <strong>Comparing PDF fingerprints...</strong>
      <span>Calculating the SHA-256 fingerprint locally in your browser.</span>
    </div>`;

  try {
    const header = new Uint8Array(await file.slice(0, 5).arrayBuffer());
    if (new TextDecoder().decode(header) !== "%PDF-") {
      result.className = "integrity-banner integrity-fake";
      result.innerHTML = `
        <div class="integrity-banner-icon">✕</div>
        <div class="integrity-banner-body">
          <strong>INVALID FILE FORMAT</strong>
          <span>The selected file is not a valid PDF document.</span>
        </div>`;
      return;
    }
    if (!window.crypto?.subtle) {
      throw new Error("Secure SHA-256 is unavailable. Open the archive through localhost or HTTPS.");
    }
    const bytes = await file.arrayBuffer();
    const digest = await window.crypto.subtle.digest("SHA-256", bytes);
    const actualHash = Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, "0")).join("");
    const isMatch = actualHash === selectedVerificationRecord.pdfSha256;

    if (isMatch) {
      result.className = "integrity-banner integrity-verified";
      result.innerHTML = `
        <div class="integrity-badge-indicator green-pulse">
          <span class="indicator-icon">✓</span>
        </div>
        <div class="integrity-banner-body">
          <div class="status-headline status-headline-green">
            <span class="status-tag status-tag-green">BYTE-FOR-BYTE MATCH</span>
            <strong>FILE MATCHES THE STORED COPY</strong>
          </div>
          <p class="status-description">
            The selected file matches the PDF stored for this SGNIA project record. This comparison checks file integrity only; it does not prove Government issuance or authenticity.
          </p>
        </div>`;
    } else {
      result.className = "integrity-banner integrity-fake";
      result.innerHTML = `
        <div class="integrity-badge-indicator red-pulse">
          <span class="indicator-icon">✕</span>
        </div>
        <div class="integrity-banner-body">
          <div class="status-headline status-headline-red">
            <span class="status-tag status-tag-red">NO FILE MATCH</span>
            <strong>FINGERPRINTS DO NOT MATCH</strong>
          </div>
          <p class="status-description">
            The selected file differs from the PDF currently stored for this project record. It may be another version or a changed file; this result alone does not establish forgery or tampering.
          </p>
        </div>`;
    }

    // Update details accordion if present
    const detailsAccordion = document.querySelector("#sha-details-accordion");
    if (detailsAccordion) {
      detailsAccordion.innerHTML = `
        <summary>Technical Verification Details (SHA-256)</summary>
        <div class="sha-detail-block">
          <div class="sha-row">
            <span class="sha-row-label">Stored PDF hash:</span>
            <code class="sha-hash-code font-mono">${escapeHtml(selectedVerificationRecord.pdfSha256)}</code>
          </div>
          <div class="sha-row">
            <span class="sha-row-label">Uploaded File Hash:</span>
            <code class="sha-hash-code font-mono ${isMatch ? "hash-match-green" : "hash-mismatch-red"}">${escapeHtml(actualHash)}</code>
          </div>
          <div class="sha-row-status">
            <span>Result:</span> <strong>${isMatch ? "✓ Byte-for-byte match confirmed" : "✕ Hash mismatch detected"}</strong>
          </div>
        </div>`;
      detailsAccordion.open = true;
    }
  } catch (error) {
    result.className = "integrity-banner integrity-fake";
    result.innerHTML = `
      <div class="integrity-banner-icon">!</div>
      <div class="integrity-banner-body">
        <strong>Verification Error</strong>
        <span>Could not complete check: ${escapeHtml(error.message)}</span>
      </div>`;
  }
});

// Set the total in the page and show the initial search results.
const featuredTotal = document.querySelector("#total-records");
const heroTotal = document.querySelector("#hero-total-records");
const initialTotal = records.length > 0 || window.location.protocol === "file:"
  ? String(records.length)
  : "Loading…";
if (featuredTotal) featuredTotal.textContent = initialTotal;
if (heroTotal) heroTotal.textContent = initialTotal;
populateDepartments();
renderRecords();
document.addEventListener("sgnia:public-records-loaded", () => {
  if (featuredTotal) featuredTotal.textContent = records.length;
  if (heroTotal) heroTotal.textContent = records.length;
  populateDepartments();
  renderRecords();
  const initialReference = new URLSearchParams(window.location.search).get("verify");
  if (initialReference) {
    verifyReferenceInput.value = initialReference;
    lookupArchiveRecord(initialReference);
  }
});
document.addEventListener("sgnia:public-records-unavailable", () => {
  if (records.length > 0) return;
  if (featuredTotal) featuredTotal.textContent = "—";
  if (heroTotal) heroTotal.textContent = "—";
});
const initialReference = new URLSearchParams(window.location.search).get("verify");
if (initialReference) {
  verifyReferenceInput.value = initialReference;
  lookupArchiveRecord(initialReference);
}
