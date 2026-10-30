# SGNIA staff portal foundation

This Flask application serves the public End User archive at `/` and the separate staff workspace at `/login`. Public visitors only see notifications whose staff workflow status is `Published`; staff routes remain protected by the server-enforced RBAC rules.

## Requirements

- Python 3.10+
- For local development: SQLite (included with Python)
- For deployment: MySQL, a private `FLASK_SECRET_KEY`, and persistent document/key storage

## Run locally

From this directory in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Set `FLASK_SECRET_KEY` in `.env` to a long random value. The local default database is `instance/sdgnm-dev.db`.

For a fresh database, apply the versioned schema and create staff accounts using interactive prompts (passwords are not placed in source code):

```powershell
python -m flask --app run.py db upgrade
python -m flask --app run.py seed-departments
python -m flask --app run.py create-user
```

For an existing database created before versioned migrations were introduced, back it up first (database, PDFs, and signing-key directory), then run the compatibility update and stamp the current baseline:

```powershell
python -m flask --app run.py migrate-db
python -m flask --app run.py db stamp head
```

Use the versioned migration commands for future changes. Review generated migrations before applying them:

```powershell
python -m flask --app run.py db migrate -m "Describe schema change"
python -m flask --app run.py db upgrade
```

The user command asks for name, email, department, one role (`super_admin`, `approver`, `creator`, or `auditor`), and an initial password of at least 12 characters. Create one account per staff member; do not share passwords.

Start the app:

```powershell
python -m flask --app run.py run
```

Open `http://127.0.0.1:5000` for the public archive or `http://127.0.0.1:5000/login` for the staff workspace. There are no built-in demo accounts or passwords.

To use MySQL, create a database and restricted database user, then set this in `.env`:

```text
DATABASE_URL=mysql+pymysql://sdgnm_user:your-password@127.0.0.1:3306/sdgnm
```

Do not commit `.env` or use development credentials on a deployed server. Set `APP_ENV=production`, `FLASK_SECRET_KEY`, `DATABASE_URL`, `NOTIFICATION_UPLOAD_DIR`, and `SIGNING_KEY_DIR` before deployment. The two storage paths must be persistent, access-controlled locations outside the source checkout; the private-key directory must be readable only by the application identity. Production mode refuses to start without these settings and enables secure session cookies (which require HTTPS). `GET /health` checks database readiness and returns only `ok` or `unavailable`.

## First increment

- Password-hashed staff accounts and session-based login/logout.
- Server-enforced role permissions from the supplied RBAC matrix.
- Role-specific navigation and dashboard.
- Super Admin can provision staff accounts, assign/update roles, and activate/deactivate accounts from the protected user-management page; initial password values are hashed and not displayed again.
- Super Admin can assign staff to departments. Creators can draft only for their assigned department, and Approvers see only workflow items for that same department.
- Draft creation, submission, review decisions, and publish status transitions.
- Required PDF upload (PDF signature checked; maximum request size 16 MB), document date, and optional official reference on each new notification draft.
- Published notifications and their PDFs are exposed to the public archive only after approval and publication; draft, pending, rejected, and returned records remain private.
- Every published SGNIA notification has a downloadable QR code that opens its public archive lookup. QR codes are project-generated and do not provide cryptographic proof of authenticity.
- Uploaded notification PDFs receive a SHA-256 fingerprint. The public lookup can compare a user-selected PDF locally in the browser; it reports byte equality with the stored file, not Government authenticity.
- Super Admin can generate and rotate project Ed25519 keys. Publication is blocked until an active private key is available and the PDF matches its stored fingerprint. Public signature verification checks the signature, archive reference, version, PDF fingerprint, and archived file bytes. Historical public keys remain available for verification; private keys are never displayed or stored in the database.
- Amendments create a numbered version with a new PDF and change summary. Each amendment follows approval and publication again; the public archive keeps the previous published version until the replacement is approved, and staff can inspect the historical PDFs.
- Department scoping for approvers and author scoping for creators.
- Audit events use a SHA-256 hash chain, including staff login/logout events. Run `python -m flask --app run.py verify-audit-chain` to check the full chain; this detects edits, interior deletions, and reordering, but cannot stop a privileged database administrator from rewriting the complete chain. Keep independent, access-controlled backups for stronger evidence.
- Local PDF text extraction and OCR are separated from draft creation. Staff must review and confirm the extracted text before a draft is saved. Scanned PDFs require the Tesseract executable to be installed on the same server; no third-party OCR service is used. On Windows, the app recognizes the standard `C:\Program Files\Tesseract-OCR\tesseract.exe` install path; set `TESSERACT_CMD` if it is installed elsewhere.
- Admin pages for staff directory, signing key rotation, and the read-only permission matrix.
- Protected scaffolds for departments and workflow settings.

## Supplied RBAC matrix

| Permission | Super Admin | Approver | Creator | Auditor |
|---|---:|---:|---:|---:|
| Create / draft notification | Yes | Yes | Yes | No |
| Approve / reject | Yes | Yes | No | No |
| Publish to public portal | Yes | Yes | No | No |
| OCR digitization | Yes | Yes | Yes | No |
| Manage users / roles | Yes | No | No | No |
| Manage signing keys | Yes | No | No | No |
| View audit trail | Yes | Yes | No | Yes |

Dashboard and navigation visibility are not the security boundary: the same permissions are checked on server routes and write actions. Public End User pages do not grant staff permissions.

## Public API

- `GET /api/public/notifications` returns published SGNIA records only, including archive reference, document URL, SHA-256 fingerprint, QR URL, and project-signature verification page URL.
- `GET /api/public/notifications/<id>/pdf` serves only the current published PDF.
- `GET /api/public/notifications/<id>/qr` generates a project lookup QR code.
- `GET /api/public/notifications/<id>/signature` verifies the published version signature and archived PDF bytes, returning a status such as `verified`, `unsigned`, `unknown_key`, `invalid_signature`, or `document_mismatch`.
- `GET /signature/<reference>` presents the same signature result with an explicit project-not-Government disclaimer.
- `GET /health` checks database readiness and returns no database details.

The archive API is read-only and does not expose drafts, pending approvals, staff accounts, or audit details. A successful signature verification confirms the project key signed the archive reference, version, and PDF fingerprint; it does not confirm Government issuance.

## Current limitations

This remains a university-project prototype, not an official Government system. Project-generated Ed25519 signatures are not Government PKI signatures and do not establish Government authority. SHA-256 comparison checks file integrity only. The audit hash chain is tamper-evident, not tamper-proof; an administrator able to rewrite the database can replace the full chain. Do not treat project records, signatures, or audit logs as official Government records. For scanned PDFs, install Tesseract locally; the app reports when it is unavailable.

The `migrate-db` command is retained only as a one-time compatibility update for pre-migration installations; it adds document, version-history, signature, SHA-256, and audit-chain columns, records existing notifications as their original version, hashes available local PDFs, and initializes the legacy audit chain. New schema changes use Flask-Migrate/Alembic. Before any real deployment, select and harden a hosting platform, configure HTTPS and monitoring, test encrypted database/file/key backups and restore procedures, and complete a security review. No hosting provider or deployment credentials have been supplied, so this project has not been deployed.
