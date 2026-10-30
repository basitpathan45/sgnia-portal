from io import BytesIO
from pathlib import Path

import qrcode
from flask import Blueprint, abort, current_app, jsonify, redirect, render_template, send_file, send_from_directory, url_for

from .models import Notification, NotificationVersion
from .signatures import verify_version_signature

public_bp = Blueprint("public", __name__)
PUBLIC_ROOT = Path(__file__).resolve().parents[2]
PUBLIC_FILES = {"archive.html", "app.js", "archive.js", "public-records.js", "records.js", "theme.js", "styles.css", "supabase-config.js"}


@public_bp.get("/")
@public_bp.get("/index.html")
def homepage():
    return send_from_directory(PUBLIC_ROOT, "index.html")


@public_bp.get("/archive.html")
def public_archive():
    return send_from_directory(PUBLIC_ROOT, "archive.html")


@public_bp.get("/<path:filename>")
def public_file(filename):
    if filename not in PUBLIC_FILES:
        abort(404)
    return send_from_directory(PUBLIC_ROOT, filename)


@public_bp.get("/assets/<path:filename>")
def public_asset(filename):
    return send_from_directory(PUBLIC_ROOT / "assets", filename)


@public_bp.get("/verify/<string:reference>")
def verify_notification(reference):
    notification = Notification.query.filter_by(reference=reference, status="Published").first()
    if notification is None:
        abort(404)
    return redirect(url_for("public.homepage", verify=notification.reference) + "#verify")


@public_bp.get("/signature/<string:reference>")
def signature_page(reference):
    notification = Notification.query.filter_by(reference=reference, status="Published").first()
    if notification is None:
        abort(404)
    version = NotificationVersion.query.filter_by(
        notification_id=notification.id,
        status="Published",
    ).order_by(NotificationVersion.version_number.desc()).first()
    verification = verify_version_signature(version, notification.reference, verify_pdf_file=True) if version else {
        "status": "unsigned",
        "valid": False,
    }
    return render_template(
        "signature_verification.html",
        notification=notification,
        version=version,
        verification=verification,
    )


@public_bp.get("/api/public/notifications")
def published_notifications():
    notifications = Notification.query.filter_by(status="Published").order_by(
        Notification.document_date.desc(), Notification.id.desc()
    ).all()
    records = []
    for item in notifications:
        version = NotificationVersion.query.filter_by(
            notification_id=item.id,
            status="Published",
        ).order_by(NotificationVersion.version_number.desc()).first()
        source = version or item
        records.append({
            "id": f"SGNIA-{item.id}",
            "portalListingNumber": item.reference,
            "archiveReference": item.reference,
            "officialReference": source.official_reference,
            "versionNumber": version.version_number if version else 1,
            "title": source.title,
            "type": source.category,
            "department": source.department,
            "shortDepartment": source.department,
            "departmentCode": None,
            "date": (source.document_date or item.created_at.date()).isoformat(),
            "pdfUrl": url_for("public.notification_pdf", notification_id=item.id),
            "pdfSha256": source.pdf_sha256,
            "signatureVerificationUrl": url_for(
                "public.signature_page",
                reference=item.reference,
            ),
            "qrUrl": url_for("public.notification_qr", notification_id=item.id),
            "isSgniaRecord": True,
        })
    return jsonify(records)


@public_bp.get("/api/public/notifications/<int:notification_id>/signature")
def verify_notification_signature(notification_id):
    notification = Notification.query.filter_by(id=notification_id, status="Published").first()
    if notification is None:
        abort(404)
    version = NotificationVersion.query.filter_by(
        notification_id=notification.id,
        status="Published",
    ).order_by(NotificationVersion.version_number.desc()).first()
    if version is None:
        return jsonify({"status": "unsigned", "valid": False}), 200
    result = verify_version_signature(version, notification.reference, verify_pdf_file=True)
    result.update({
        "reference": notification.reference,
        "versionNumber": version.version_number,
        "authorityNotice": (
            "Project-generated Ed25519 signature. It is not a Government PKI signature "
            "and does not establish official Government authority."
        ),
    })
    return jsonify(result)


@public_bp.get("/api/public/notifications/<int:notification_id>/qr")
def notification_qr(notification_id):
    notification = Notification.query.filter_by(id=notification_id, status="Published").first()
    if notification is None:
        abort(404)
    verification_url = url_for(
        "public.verify_notification",
        reference=notification.reference,
        _external=True,
    )
    image = qrcode.make(verification_url)
    output = BytesIO()
    image.save(output, format="PNG")
    output.seek(0)
    return send_file(
        output,
        mimetype="image/png",
        as_attachment=True,
        download_name=f"{notification.reference}.png",
        max_age=3600,
    )


@public_bp.get("/api/public/notifications/<int:notification_id>/pdf")
def notification_pdf(notification_id):
    notification = Notification.query.filter_by(id=notification_id, status="Published").first()
    if notification is None:
        abort(404)
    version = NotificationVersion.query.filter_by(
        notification_id=notification.id,
        status="Published",
    ).order_by(NotificationVersion.version_number.desc()).first()
    pdf_path = version.pdf_path if version else notification.pdf_path
    if not pdf_path:
        abort(404)
    response = send_from_directory(
        current_app.config["NOTIFICATION_UPLOAD_DIR"],
        pdf_path,
        mimetype="application/pdf",
        as_attachment=False,
        download_name=f"{notification.reference}.pdf",
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response
