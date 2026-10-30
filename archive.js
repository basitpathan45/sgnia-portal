// Full archive search, result rendering, and pagination.

// Number of source listings shown on each archive page.
const pageSize = 10;

// Connect the archive controls to their HTML elements.
const searchForm = document.querySelector("#archive-search-form");
const keywordInput = document.querySelector("#archive-keyword");
const departmentSelect = document.querySelector("#archive-department");
const dateFromInput = document.querySelector("#archive-date-from");
const dateToInput = document.querySelector("#archive-date-to");
const referenceInput = document.querySelector("#archive-reference");
const sortSelect = document.querySelector("#archive-sort-order");
const recordList = document.querySelector("#archive-record-list");
const resultsSummary = document.querySelector("#archive-results-summary");
const emptyState = document.querySelector("#archive-empty-state");
const pagination = document.querySelector("#archive-pagination");
let currentPage = 1;

// Escape record values before placing them in HTML templates.
const escapeHtml = (value) => String(value).replace(/[&<>"']/g, (character) => ({
  "&": "&amp;",
  "<": "&lt;",
  ">": "&gt;",
  '"': "&quot;",
  "'": "&#39;",
}[character]));

const formatDate = (dateString, options) => new Intl.DateTimeFormat("en-GB", options)
  .format(new Date(`${dateString}T00:00:00`));

// Fill the selector with all departments and include an unspecified group only if data needs it.
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

// Apply keyword, department, posted-date, reference, and sort filters.
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

// Draw the page-number buttons and previous/next controls.
function renderPagination(totalPages) {
  pagination.hidden = totalPages <= 1;
  if (totalPages <= 1) {
    pagination.innerHTML = "";
    return;
  }

  const pageButtons = Array.from({ length: totalPages }, (_, index) => {
    const page = index + 1;
    return `<button class="page-button${page === currentPage ? " current" : ""}" type="button" data-page="${page}"${page === currentPage ? ' aria-current="page"' : ""}>${page}</button>`;
  }).join("");

  pagination.innerHTML = `
    <button class="page-button page-direction" type="button" data-step="-1"${currentPage === 1 ? " disabled" : ""}>← <span>Previous</span></button>
    <div class="page-numbers">${pageButtons}</div>
    <button class="page-button page-direction" type="button" data-step="1"${currentPage === totalPages ? " disabled" : ""}><span>Next</span> →</button>`;
}

// Draw the current page of matching records and update the result count.
function renderRecords() {
  const filteredRecords = getFilteredRecords();
  const totalPages = Math.ceil(filteredRecords.length / pageSize);
  currentPage = Math.min(currentPage, Math.max(totalPages, 1));
  const startIndex = (currentPage - 1) * pageSize;
  const visibleRecords = filteredRecords.slice(startIndex, startIndex + pageSize);
  const hasRecords = filteredRecords.length > 0;

  resultsSummary.innerHTML = hasRecords
    ? `Showing <strong>${startIndex + 1}–${startIndex + visibleRecords.length}</strong> of <strong>${filteredRecords.length}</strong> archive records`
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
          <a class="record-qr-download" href="${escapeHtml(record.isSgniaRecord ? record.qrUrl : `assets/qr-codes/${record.archiveReference}.png`)}" download="${escapeHtml(record.archiveReference)}.png" aria-label="Download project QR code for ${escapeHtml(record.title)}">Download QR</a>
          <a class="record-open" href="${escapeHtml(record.pdfUrl)}" target="_blank" rel="noopener noreferrer">${record.isSgniaRecord ? "Open archived PDF" : "Open official PDF"} <span aria-hidden="true">↗</span></a>
        </div>
      </article>`;
  }).join("");

  renderPagination(totalPages);
}

// Reset to the first page when a search or filter changes.
searchForm.addEventListener("submit", (event) => {
  event.preventDefault();
  currentPage = 1;
  renderRecords();
});

searchForm.addEventListener("reset", () => {
  currentPage = 1;
  window.setTimeout(renderRecords, 0);
});

for (const input of [keywordInput, departmentSelect, dateFromInput, dateToInput, referenceInput]) {
  input.addEventListener("input", () => {
    currentPage = 1;
    renderRecords();
  });
  input.addEventListener("change", () => {
    currentPage = 1;
    renderRecords();
  });
}

sortSelect.addEventListener("change", () => {
  currentPage = 1;
  renderRecords();
});

document.querySelector("#archive-empty-clear").addEventListener("click", () => {
  searchForm.reset();
  renderRecords();
});

pagination.addEventListener("click", (event) => {
  const pageButton = event.target.closest("[data-page]");
  const directionButton = event.target.closest("[data-step]");
  const button = pageButton || directionButton;
  if (!button || button.disabled) return;
  currentPage = pageButton
    ? Number(pageButton.dataset.page)
    : currentPage + Number(directionButton.dataset.step);
  renderRecords();
  document.querySelector("#main-content").scrollIntoView({ behavior: "smooth" });
});

// Populate controls and display the first page of results.
const archiveTotal = document.querySelector("#archive-total");
if (archiveTotal) archiveTotal.textContent = records.length;
populateDepartments();
renderRecords();
document.addEventListener("sgnia:public-records-loaded", () => {
  if (archiveTotal) archiveTotal.textContent = records.length;
  populateDepartments();
  currentPage = 1;
  renderRecords();
});
