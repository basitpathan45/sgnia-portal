# SGNIA — Sindh Government Notification Issuing Authority

Responsive public archive frontend prototype for the Sindh Government Notification Issuing Authority (SGNIA) final-year project.

## Run it

Open `index.html` in a modern browser to browse the source-linked portal listings without running the backend.
To include notifications published by staff, run the Flask portal in [`staff_portal/README.md`](staff_portal/README.md) and open `http://127.0.0.1:5000`. The same server hosts the public archive, staff login, and published-notification API.

## Included

- Home page with a searchable preview of official source listings.
- Separate public archive page with 55 records from the official Government of Sindh notification listing and direct links to the source-hosted PDFs.
- Department names are assigned from the issuing department visible in each source document or the official portal listing title. Each department filter uses the supplied 29-department list.
- Shared source data and department list in `records.js`.
- Each record has a searchable `SGNIA-ARCH-###` archive reference created for this prototype. This is not a Government reference number.
- Official document references are shown only when legible in the linked source PDF. Portal listing numbers identify rows in the public portal and are not official notification references.
- Newest/oldest sorting and clear-filter controls.
- Shared night/day theme toggle on the homepage and archive; the selected theme is saved in the browser, and the first visit follows the device theme.
- Every listing has a direct PDF link to the official source; linked documents open in a new tab.
- Public lookup and filtering by archive reference, transcribed official reference, portal listing number, or title search the same source-backed records.
- When hosted through the Flask app, the public homepage and archive also show staff-workflow notifications only after they have been approved and published. Each such record links to its uploaded PDF and is labeled as an SGNIA archive record, not an official Government source.
- QR scanning from a camera or uploaded image uses the browser's `BarcodeDetector` when available, with a pinned jsQR fallback for other browsers. Scanned portal references, archive references, and exact official PDF links are matched against the archive.
- The 55 bundled Government portal listings have project QR images that open their source PDFs. Staff-published SGNIA records get individual QR codes that open the record lookup in the running Flask archive; those codes are generated when requested and are available from the public archive or staff digital archive.
- Responsive layout and keyboard-accessible form controls.

## Where to make changes

- **Notification records and department names:** `records.js`
- **Published staff-workflow records loaded from the Flask API:** `public-records.js`
- **Homepage search, preview, and source lookup behavior:** `app.js`
- **Full archive search and pagination behavior:** `archive.js`
- **Shared theme selection and saved preference:** `theme.js`
- **Homepage content and layout:** `index.html`
- **Archive page content and layout:** `archive.html`
- **Colors, spacing, typography, and responsive design:** `styles.css`
- **Generated QR images and mapping index:** `assets/qr-codes/` and `assets/sgnia-notification-qr-codes.zip`

## Adding or updating a record

1. Add a record to the `records` list in `records.js`.
2. Set its portal listing number, posted date (`YYYY-MM-DD`), title, type, department code, official PDF URL, and official listing-page URL.
3. Use the department codes in the `departments` list. If the source PDF identifies a department more clearly than the portal title, add its portal number to `departmentOverrides`.
4. Add an `officialReferences` entry only when the number can be read from the original PDF. Do not put a made-up document number there.
5. The app creates a project-only `SGNIA-ARCH-###` search reference from the portal listing number. It is not an official Government reference.

## Important

The bundled listing metadata and PDF links are sourced from the [official Government of Sindh notifications page](https://www.sindh.gov.pk/notifications?show=notification). SGNIA is still a university project prototype, not a Government of Sindh service. Generated QR images are project-made links, never Government-issued; scanning finds an archive entry but does not cryptographically authenticate a document. Unknown QR links are never opened automatically; only same-origin SGNIA verification links and HTTPS links on the Government of Sindh domain are recognized. Camera use requires permission and a secure browser context such as localhost or HTTPS. QR decoding is performed in the browser; the pinned jsQR script is loaded from jsDelivr.

When opened directly as static files, the frontend shows only the bundled portal listings and has no database connection. When served by the Flask app, the public pages load published staff-workflow records from the backend and can compare a supplied PDF's SHA-256 fingerprint with a published SGNIA file. This is a byte-integrity check, not a digital signature or proof of official authenticity.

The project proposal identifies Flask, Jinja2, Bootstrap 5, and MySQL as the intended stack. These files keep the public prototype dependency-free so the screens can be reviewed before backend integration.

## Internal staff workspace

The separate [Flask staff portal](staff_portal/README.md) provides the internal workflow with the supplied four-role RBAC matrix, authenticated staff sessions, notification drafting/review/publication, a hash-chained audit trail, project digital signatures, and human-reviewed local PDF text extraction/OCR. Its default local database is SQLite; it supports MySQL through `DATABASE_URL`.

The public End User frontend is served by the Flask app at `/`; the homepage and archive both link to protected staff sign-in at `/login`, and the sign-in page links back to the public archive. Public and staff features share one website/server while keeping separate routes and permissions. Versioned amendments are reviewed before public replacement. Project signatures are not Government PKI signatures, OCR requires a local Tesseract installation for scanned PDFs, and the audit chain detects tampering but is not tamper-proof. This is still a university prototype, not an official Government service.

The Government of Sindh emblem in the header and footer is a local copy of the logo served by the [official Government of Sindh website](https://www.sindh.gov.pk/images/government-of-sindh-pakistan-logo.png).
