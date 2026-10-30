/**
 * SGNIA Public Records Integration
 * Loads live published records from Supabase PostgreSQL database,
 * with graceful fallback to Flask API and offline bundled records.
 */

function resolveShortDepartment(name, code) {
  if (typeof departments !== "undefined" && Array.isArray(departments)) {
    const match = departments.find((d) => (code && d.code === code) || d.name === name);
    if (match && match.short) return match.short;
  }
  return name;
}

function mergeRecords(newRecords) {
  if (!Array.isArray(newRecords) || newRecords.length === 0) return;

  const existingMap = new Map();
  records.forEach((r, index) => {
    const key = r.archiveReference || r.portalListingNumber;
    if (key) existingMap.set(String(key).toLowerCase(), index);
  });

  for (const item of newRecords) {
    const key = item.archiveReference || item.portalListingNumber;
    const lowerKey = key ? String(key).toLowerCase() : null;

    if (lowerKey && existingMap.has(lowerKey)) {
      // Update existing record with fresh Supabase data
      records[existingMap.get(lowerKey)] = {
        ...records[existingMap.get(lowerKey)],
        ...item,
      };
    } else {
      // Add new record from database
      records.push(item);
      if (lowerKey) existingMap.set(lowerKey, records.length - 1);
    }
  }

  document.dispatchEvent(new CustomEvent("sgnia:public-records-loaded"));
}

async function loadLiveRecordsFromSupabase() {
  if (!window.SGNIA_SUPABASE) return false;

  try {
    // 1. Optionally sync latest active departments
    try {
      const activeDepts = await window.SGNIA_SUPABASE.getDepartments();
      if (Array.isArray(activeDepts) && activeDepts.length > 0 && typeof departments !== "undefined") {
        for (const dept of activeDepts) {
          if (!departments.some((d) => d.name === dept.name)) {
            departments.push({
              name: dept.name,
              short: dept.short_name || dept.name,
              code: dept.code,
            });
          }
        }
      }
    } catch (deptErr) {
      console.warn("Could not sync departments from Supabase; using existing department list.", deptErr);
    }

    // 2. Fetch published notifications
    const supabaseData = await window.SGNIA_SUPABASE.getPublishedNotifications();
    if (!Array.isArray(supabaseData)) return false;

    const mappedRecords = supabaseData.map((item) => {
      const archiveRef = item.reference || (item.portal_listing_number ? `SGNIA-ARCH-${String(item.portal_listing_number).padStart(3, "0")}` : `SGNIA-${item.id}`);
      return {
        id: `SGNIA-${item.id}`,
        portalListingNumber: item.portal_listing_number || item.reference,
        archiveReference: archiveRef,
        officialReference: item.official_reference || null,
        versionNumber: 1,
        title: item.title,
        type: item.category || "Notification",
        department: item.department,
        shortDepartment: resolveShortDepartment(item.department, item.department_code),
        departmentCode: item.department_code || null,
        date: item.document_date || (item.created_at ? item.created_at.slice(0, 10) : ""),
        pdfUrl: item.pdf_url || (item.pdf_path ? `/api/public/notifications/${item.id}/pdf` : null),
        pdfSha256: item.pdf_sha256 || null,
        sourceUrl: item.source_url || null,
        signatureVerificationUrl: `/signature/${archiveRef}`,
        qrUrl: `/api/public/notifications/${item.id}/qr`,
        isSgniaRecord: Boolean(item.pdf_path || !item.source_url),
      };
    });

    mergeRecords(mappedRecords);
    console.info(`Successfully synchronized ${mappedRecords.length} records from Supabase database.`);
    return true;
  } catch (error) {
    console.warn("Direct Supabase sync unavailable; falling back to local/backend source.", error);
    return false;
  }
}

async function loadPublishedFlaskRecords() {
  if (window.location.protocol === "file:") return;

  try {
    const response = await fetch("/api/public/notifications", {
      headers: { Accept: "application/json" },
    });
    if (!response.ok) return;

    const publishedRecords = await response.json();
    mergeRecords(publishedRecords);
  } catch (error) {
    console.debug("Flask backend endpoint not reachable; keeping current records.");
  }
}

async function initializePublicRecords() {
  const supabaseSuccess = await loadLiveRecordsFromSupabase();
  if (!supabaseSuccess) {
    await loadPublishedFlaskRecords();
  }
}

initializePublicRecords();
