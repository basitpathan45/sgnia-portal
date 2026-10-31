import logging
from datetime import datetime, timezone
from pathlib import Path
import shutil
from uuid import uuid4

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, send_from_directory, url_for
from flask_login import current_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import BooleanField, DateField, EmailField, HiddenField, PasswordField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, InputRequired, Length, Optional

from .extensions import db
from .audit import append_audit_log, verify_audit_chain
from .documents import sha256_file
from .models import AuditLog, Department, Notification, NotificationVersion, SigningKey, User
from .ocr import OcrError, extract_pdf_text, ocr_engine_available
from .permissions import (
    APPROVER,
    AUDITOR,
    CREATOR,
    ROLE_PERMISSIONS,
    ROLES,
    permission_required,
)
from .signatures import SigningConfigurationError, generate_signing_key, sign_published_version
from .pdf_generator import generate_official_sindh_pdf

staff_bp = Blueprint("staff", __name__)
log = logging.getLogger(__name__)

STATUS_FLOW = {
    "Draft": {"submit": "Pending Approval"},
    "Returned": {"submit": "Pending Approval"},
    "Pending Approval": {"approve": "Published", "return": "Returned", "reject": "Rejected"},
    "Approved": {"publish": "Published"},
}


class NotificationForm(FlaskForm):
    title = StringField("Notification title", validators=[DataRequired(), Length(max=240)])
    category = SelectField(
        "Document type",
        choices=[("Notification", "Notification"), ("Order", "Order"), ("Circular", "Circular"), ("Letter", "Letter"), ("Advisory", "Advisory")],
        validators=[DataRequired()],
    )
    department = SelectField("Department", validators=[DataRequired()])
    subject = StringField("Subject", validators=[DataRequired(), Length(max=500)])
    body = TextAreaField("Draft text", validators=[DataRequired()])
    document_date = DateField("Document date", validators=[DataRequired()])
    official_reference = StringField("Official reference (optional)", validators=[Optional(), Length(max=120)])
    document = FileField("PDF document (optional)", validators=[Optional(), FileAllowed(["pdf"], "Upload a PDF document.")])
    submit = SubmitField("Save draft")


class AmendmentForm(NotificationForm):
    change_summary = TextAreaField(
        "Amendment summary",
        validators=[DataRequired(), Length(max=500)],
    )
    submit = SubmitField("Save amendment draft")


class OcrUploadForm(FlaskForm):
    document = FileField("Scanned or text PDF", validators=[
        FileRequired(),
        FileAllowed(["pdf"], "Upload a PDF document."),
    ])
    submit = SubmitField("Extract text for review")


class OcrDraftForm(FlaskForm):
    token = HiddenField(validators=[DataRequired()])
    title = StringField("Notification title", validators=[DataRequired(), Length(max=240)])
    category = SelectField(
        "Document type",
        choices=[("Notification", "Notification"), ("Order", "Order"), ("Circular", "Circular"), ("Letter", "Letter"), ("Advisory", "Advisory")],
        validators=[DataRequired()],
    )
    department = SelectField("Department", validators=[DataRequired()])
    subject = StringField("Subject", validators=[DataRequired(), Length(max=500)])
    document_date = DateField("Document date", validators=[DataRequired()])
    official_reference = StringField("Official reference (optional)", validators=[Optional(), Length(max=120)])
    body = TextAreaField("Extracted text — review and correct before saving", validators=[DataRequired()])
    reviewed = BooleanField("I reviewed and corrected the extracted text", validators=[InputRequired()])
    submit = SubmitField("Save reviewed text as draft")


class StaffUserForm(FlaskForm):
    name = StringField("Full name", validators=[DataRequired(), Length(max=120)])
    email = EmailField("Staff email", validators=[DataRequired(), Email(), Length(max=254)])
    department = SelectField("Department", validators=[DataRequired()])
    role = SelectField(
        "Role",
        choices=[
            ("super_admin", "Super Admin"),
            ("approver", "Approver"),
            ("creator", "Creator"),
            ("auditor", "Auditor"),
        ],
        validators=[DataRequired()],
    )
    password = PasswordField("Initial password (at least 12 characters)", validators=[DataRequired(), Length(min=12, max=128)])
    submit = SubmitField("Create staff account")


def record_audit(action, target_type, target_id=None, details=""):
    append_audit_log(current_user, action, target_type, target_id, details)


def get_notification_or_404(notification_id):
    notification = db.session.get(Notification, notification_id)
    if notification is None:
        abort(404)
    return notification


def latest_version(notification):
    return NotificationVersion.query.filter_by(notification_id=notification.id).order_by(
        NotificationVersion.version_number.desc()
    ).first()


def published_version(notification):
    return NotificationVersion.query.filter_by(
        notification_id=notification.id,
        status="Published",
    ).order_by(NotificationVersion.version_number.desc()).first()


def can_view_notification_document(notification):
    return (
        current_user.role == "super_admin"
        or current_user.role == AUDITOR
        or (current_user.role == CREATOR and notification.created_by_id == current_user.id)
        or (current_user.role == APPROVER and notification.department == current_user.department)
    )


def snapshot_notification_version(notification, version_number, status, change_summary=""):
    version = NotificationVersion(
        notification=notification,
        version_number=version_number,
        title=notification.title,
        category=notification.category,
        department=notification.department,
        subject=notification.subject,
        body=notification.body,
        document_date=notification.document_date,
        official_reference=notification.official_reference,
        pdf_path=notification.pdf_path,
        pdf_sha256=notification.pdf_sha256,
        change_summary=change_summary,
        status=status,
        created_by_id=notification.created_by_id,
        reviewed_by_id=notification.reviewed_by_id,
    )
    db.session.add(version)
    return version


def visible_notifications_query():
    query = Notification.query
    if current_user.role == CREATOR:
        return query.filter_by(created_by_id=current_user.id)
    if current_user.role == APPROVER:
        return query.filter_by(department=current_user.department)
    return query


@staff_bp.get("/dashboard")
@permission_required("view_dashboard")
def dashboard():
    if current_user.role == AUDITOR:
        recent_logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(8).all()
    else:
        recent_logs = []
    visible_query = visible_notifications_query()
    notifications = visible_query.order_by(Notification.updated_at.desc()).limit(6).all()
    return render_template(
        "dashboard.html",
        pending_count=visible_query.filter_by(status="Pending Approval").count(),
        published_count=visible_query.filter_by(status="Published").count(),
        draft_count=visible_query.filter_by(status="Draft").count(),
        recent_notifications=notifications,
        recent_logs=recent_logs,
    )


@staff_bp.get("/notifications")
@permission_required("view_notifications")
def notifications():
    query = Notification.query
    status = request.args.get("status", "").strip()
    if status:
        query = query.filter_by(status=status)
    if current_user.role == CREATOR:
        query = query.filter_by(created_by_id=current_user.id)
    elif current_user.role != "super_admin":
        query = query.filter_by(department=current_user.department)
    items = query.order_by(Notification.updated_at.desc()).limit(100).all()
    return render_template("notifications.html", notifications=items, selected_status=status)


@staff_bp.route("/notifications/new", methods=["GET", "POST"])
@permission_required("create_notification")
def notification_new():
    form = NotificationForm()
    departments = Department.query.filter_by(active=True).order_by(Department.name).all()
    if current_user.role == "super_admin":
        department_names = [department.name for department in departments]
    else:
        department_names = [current_user.department]
    if current_user.department not in department_names:
        department_names.append(current_user.department)
    form.department.choices = [(name, name) for name in department_names]

    if form.validate_on_submit():
        # Department-scoped staff may only create drafts for their own department.
        department = form.department.data
        if current_user.role != "super_admin" and department != current_user.department:
            abort(403)
        reference = f"SGNIA-{datetime.now(timezone.utc):%Y}-{uuid4().hex[:8].upper()}"
        upload_dir = Path(current_app.config["NOTIFICATION_UPLOAD_DIR"])
        upload_dir.mkdir(parents=True, exist_ok=True)
        stored_pdf_name = f"{uuid4().hex}.pdf"

        uploaded_pdf = form.document.data
        if uploaded_pdf and uploaded_pdf.filename:
            # --- Manually uploaded PDF ---
            pdf_size = uploaded_pdf.stream.seek(0, 2)
            uploaded_pdf.stream.seek(0)
            if pdf_size > current_app.config["MAX_NOTIFICATION_PDF_BYTES"]:
                form.document.errors.append("The PDF must be no larger than 16 MB.")
                return render_template("notification_new.html", form=form)
            if uploaded_pdf.stream.read(5) != b"%PDF-":
                form.document.errors.append("The uploaded file does not appear to be a valid PDF.")
                return render_template("notification_new.html", form=form)
            uploaded_pdf.stream.seek(0)
            uploaded_pdf.save(upload_dir / stored_pdf_name)
            document_sha256 = sha256_file(upload_dir / stored_pdf_name)
        else:
            # --- Auto-generate official Sindh Government PDF ---
            try:
                document_sha256 = generate_official_sindh_pdf(
                    reference=reference,
                    title=form.title.data.strip(),
                    category=form.category.data,
                    department=department,
                    subject=form.subject.data.strip(),
                    body=form.body.data.strip(),
                    document_date=form.document_date.data,
                    official_reference=(form.official_reference.data or "").strip() or None,
                    destination_path=upload_dir / stored_pdf_name,
                    host_url=request.host_url,
                )
            except Exception as exc:
                log.exception("PDF auto-generation failed for draft %s: %s", reference, exc)
                flash("Failed to auto-generate the official PDF. Please try uploading a PDF manually.", "danger")
                return render_template("notification_new.html", form=form)

        notification = Notification(
            reference=reference,
            title=form.title.data.strip(),
            category=form.category.data,
            department=department,
            subject=form.subject.data.strip(),
            body=form.body.data.strip(),
            document_date=form.document_date.data,
            official_reference=(form.official_reference.data or "").strip() or None,
            pdf_path=stored_pdf_name,
            pdf_sha256=document_sha256,
            status="Draft",
            created_by=current_user,
        )
        db.session.add(notification)
        db.session.flush()
        snapshot_notification_version(notification, 1, "Draft", "Initial version.")
        record_audit("draft_created", "notification", notification.id, f"Created draft {reference}.")
        db.session.commit()
        flash("Draft saved. Submit it to the approval queue when it is ready.", "success")
        return redirect(url_for("staff.notifications"))

    return render_template("notification_new.html", form=form)


@staff_bp.get("/notifications/<int:notification_id>/pdf")
@permission_required("view_notifications")
def staff_notification_pdf(notification_id):
    notification = get_notification_or_404(notification_id)
    if not can_view_notification_document(notification):
        abort(403)
    version = latest_version(notification)
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


@staff_bp.post("/notifications/<int:notification_id>/submit")
@permission_required("create_notification")
def submit_notification(notification_id):
    notification = get_notification_or_404(notification_id)
    if current_user.role != "super_admin" and notification.created_by_id != current_user.id:
        abort(403)
    next_status = STATUS_FLOW.get(notification.status, {}).get("submit")
    if not next_status:
        abort(400, description="Only draft or returned notifications can be submitted.")
    # PDF is guaranteed to exist (auto-generated or uploaded on draft creation)
    notification.status = next_status
    version = latest_version(notification)
    if version and version.status in {"Draft", "Returned"}:
        version.status = next_status
    record_audit("submitted_for_approval", "notification", notification.id, f"Submitted {notification.reference}.")
    db.session.commit()
    flash("Notification sent to the approval queue.", "success")
    return redirect(url_for("staff.notifications"))


@staff_bp.get("/approvals")
@permission_required("view_approval_history")
def approvals():
    query = Notification.query
    version_query = NotificationVersion.query.join(Notification).filter(NotificationVersion.version_number > 1)
    if current_user.role != "super_admin":
        query = query.filter_by(department=current_user.department)
        version_query = version_query.filter(Notification.department == current_user.department)
    pending = query.filter_by(status="Pending Approval").order_by(Notification.created_at.asc()).all()
    history = query.filter(Notification.status.in_(["Approved", "Published", "Returned", "Rejected"])).order_by(
        Notification.updated_at.desc()
    ).limit(30).all()
    pending_versions = version_query.filter(NotificationVersion.status == "Pending Approval").order_by(
        NotificationVersion.created_at.asc()
    ).all()
    approved_versions = version_query.filter(NotificationVersion.status == "Approved").order_by(
        NotificationVersion.updated_at.asc()
    ).all()
    return render_template(
        "approvals.html",
        pending=pending,
        history=history,
        pending_versions=pending_versions,
        approved_versions=approved_versions,
    )


@staff_bp.post("/approvals/<int:notification_id>/<action>")
@permission_required("approve_notification")
def process_approval(notification_id, action):
    if action not in {"approve", "return", "reject", "publish"}:
        abort(400)
    notification = get_notification_or_404(notification_id)
    if current_user.role != "super_admin" and notification.department != current_user.department:
        abort(403)

    current_status = notification.status
    next_status = STATUS_FLOW.get(current_status, {}).get(action)
    if not next_status:
        abort(400, description=f"Action '{action}' is not allowed for status '{current_status}'.")
    if action == "publish" and not notification.pdf_path:
        abort(400, description="A notification PDF is required before publication.")
    version = latest_version(notification)
    if next_status == "Published":
        if version is not None and notification.pdf_path:
            try:
                sign_published_version(version, notification.reference)
            except SigningConfigurationError as error:
                current_app.logger.warning("Signing skipped or key missing: %s", error)
    notification.status = next_status
    notification.reviewed_by = current_user
    if version and (version.status == current_status or next_status == "Published"):
        version.status = next_status
        version.reviewed_by = current_user
    record_audit(
        f"notification_{action}",
        "notification",
        notification.id,
        f"{notification.reference}: {current_status} -> {next_status}.",
    )
    db.session.commit()
    flash(f"{notification.reference} status changed to {next_status}.", "success")
    return redirect(url_for("staff.approvals"))


@staff_bp.route("/ocr", methods=["GET", "POST"])
@permission_required("use_ocr")
def ocr():
    form = OcrUploadForm()
    if form.validate_on_submit():
        uploaded_pdf = form.document.data
        pdf_size = uploaded_pdf.stream.seek(0, 2)
        uploaded_pdf.stream.seek(0)
        if pdf_size > current_app.config["MAX_NOTIFICATION_PDF_BYTES"]:
            flash("The PDF must be no larger than 16 MB.", "danger")
            return render_template("ocr.html", engine_available=ocr_engine_available(), form=form)
        pdf_bytes = uploaded_pdf.stream.read()
        if not pdf_bytes.startswith(b"%PDF-"):
            flash("The uploaded file does not appear to be a valid PDF.", "danger")
            return render_template("ocr.html", engine_available=ocr_engine_available(), form=form)
        try:
            extracted_text, extraction_method = extract_pdf_text(pdf_bytes)
        except OcrError as error:
            flash(str(error), "danger")
            return render_template("ocr.html", engine_available=ocr_engine_available(), form=form)
        token = uuid4().hex
        pending_directory = Path(current_app.instance_path) / "pending-ocr"
        pending_directory.mkdir(parents=True, exist_ok=True)
        current_timestamp = datetime.now(timezone.utc).timestamp()
        for stale_pdf in pending_directory.glob("*.pdf"):
            if current_timestamp - stale_pdf.stat().st_mtime > 86_400:
                stale_pdf.unlink()
                stale_pdf.with_suffix(".txt").unlink(missing_ok=True)
                stale_pdf.with_suffix(".method").unlink(missing_ok=True)
        (pending_directory / f"{token}.pdf").write_bytes(pdf_bytes)
        (pending_directory / f"{token}.txt").write_text(extracted_text, encoding="utf-8")
        (pending_directory / f"{token}.method").write_text(extraction_method, encoding="utf-8")
        return redirect(url_for("staff.ocr_review", token=token))
    return render_template("ocr.html", engine_available=ocr_engine_available(), form=form)


@staff_bp.route("/ocr/<string:token>/review", methods=["GET", "POST"])
@permission_required("use_ocr")
def ocr_review(token):
    if len(token) != 32 or any(character not in "0123456789abcdef" for character in token):
        abort(404)
    pending_pdf = Path(current_app.instance_path) / "pending-ocr" / f"{token}.pdf"
    pending_text = pending_pdf.with_suffix(".txt")
    pending_method = pending_pdf.with_suffix(".method")
    if not pending_pdf.is_file():
        abort(404)
    form = OcrDraftForm()
    departments = Department.query.filter_by(active=True).order_by(Department.name).all()
    department_names = [department.name for department in departments] if current_user.role == "super_admin" else [
        current_user.department,
    ]
    if current_user.department not in department_names:
        department_names.append(current_user.department)
    form.department.choices = [(name, name) for name in department_names]

    if request.method == "GET":
        form.token.data = token
        form.body.data = pending_text.read_text(encoding="utf-8") if pending_text.is_file() else ""
        return render_template(
            "ocr_review.html",
            form=form,
            extraction_method=pending_method.read_text(encoding="utf-8") if pending_method.is_file() else "local text extraction",
        )
    if form.validate_on_submit():
        if form.token.data != token:
            abort(400, description="The review token did not match the uploaded document.")
        if current_user.role != "super_admin" and form.department.data != current_user.department:
            abort(403)
        pdf_bytes = pending_pdf.read_bytes()
        if len(pdf_bytes) > current_app.config["MAX_NOTIFICATION_PDF_BYTES"] or not pdf_bytes.startswith(b"%PDF-"):
            abort(400, description="The pending document is invalid or exceeds the upload limit.")
        stored_pdf_name = f"{uuid4().hex}.pdf"
        upload_directory = Path(current_app.config["NOTIFICATION_UPLOAD_DIR"])
        upload_directory.mkdir(parents=True, exist_ok=True)
        stored_pdf_path = upload_directory / stored_pdf_name
        shutil.copyfile(pending_pdf, stored_pdf_path)
        reference = f"SGNIA-{datetime.now(timezone.utc):%Y}-{uuid4().hex[:8].upper()}"
        notification = Notification(
            reference=reference,
            title=form.title.data.strip(),
            category=form.category.data,
            department=form.department.data,
            subject=form.subject.data.strip(),
            body=form.body.data.strip(),
            document_date=form.document_date.data,
            official_reference=(form.official_reference.data or "").strip() or None,
            pdf_path=stored_pdf_name,
            pdf_sha256=sha256_file(stored_pdf_path),
            status="Draft",
            created_by=current_user,
        )
        db.session.add(notification)
        db.session.flush()
        snapshot_notification_version(notification, 1, "Draft", "Initial version created from reviewed local text extraction.")
        record_audit(
            "ocr_draft_created",
            "notification",
            notification.id,
            f"Created reviewed draft {reference} using OCR/text extraction.",
        )
        db.session.commit()
        pending_pdf.unlink(missing_ok=True)
        pending_text.unlink(missing_ok=True)
        pending_method.unlink(missing_ok=True)
        flash("Reviewed text saved as a draft. It still requires the normal approval workflow.", "success")
        return redirect(url_for("staff.notifications"))
    extraction_method = pending_method.read_text(encoding="utf-8") if pending_method.is_file() else "local text extraction"
    return render_template("ocr_review.html", form=form, extraction_method=extraction_method)


@staff_bp.get("/archive")
@permission_required("view_archive")
def archive():
    items = Notification.query.filter(Notification.status.in_(["Published", "Withdrawn"])).order_by(
        Notification.updated_at.desc()
    ).limit(100).all()
    return render_template("archive.html", notifications=items)


@staff_bp.get("/versions")
@permission_required("view_versions")
def versions():
    query = NotificationVersion.query.join(Notification)
    notification_id = request.args.get("notification_id", type=int)
    if notification_id:
        query = query.filter(Notification.id == notification_id)
    if current_user.role == CREATOR:
        query = query.filter(Notification.created_by_id == current_user.id)
    elif current_user.role == APPROVER:
        query = query.filter(Notification.department == current_user.department)
    items = query.order_by(
        NotificationVersion.notification_id.desc(),
        NotificationVersion.version_number.desc(),
    ).limit(300).all()
    return render_template("versions.html", versions=items)


@staff_bp.route("/notifications/<int:notification_id>/amend", methods=["GET", "POST"])
@permission_required("create_notification")
def notification_amend(notification_id):
    notification = get_notification_or_404(notification_id)
    if not can_view_notification_document(notification):
        abort(403)
    if notification.status != "Published":
        abort(400, description="Only published notifications can be amended.")
    active_version = NotificationVersion.query.filter(
        NotificationVersion.notification_id == notification.id,
        NotificationVersion.status.in_(["Draft", "Pending Approval", "Approved"]),
    ).first()
    if active_version:
        flash("This notification already has an amendment in progress. Complete or reject that version first.", "warning")
        return redirect(url_for("staff.versions", notification_id=notification.id))

    source = published_version(notification) or notification
    form = AmendmentForm(obj=source)
    form.department.choices = [(notification.department, notification.department)]
    if form.validate_on_submit():
        upload_dir = Path(current_app.config["NOTIFICATION_UPLOAD_DIR"])
        upload_dir.mkdir(parents=True, exist_ok=True)
        stored_pdf_name = f"{uuid4().hex}.pdf"
        version_number = max((item.version_number for item in notification.versions), default=0) + 1

        uploaded_pdf = form.document.data
        if uploaded_pdf and uploaded_pdf.filename:
            # --- Manually uploaded amendment PDF ---
            pdf_size = uploaded_pdf.stream.seek(0, 2)
            uploaded_pdf.stream.seek(0)
            if pdf_size > current_app.config["MAX_NOTIFICATION_PDF_BYTES"]:
                form.document.errors.append("The PDF must be no larger than 16 MB.")
                return render_template("notification_amend.html", form=form, notification=notification)
            if uploaded_pdf.stream.read(5) != b"%PDF-":
                form.document.errors.append("The uploaded file does not appear to be a valid PDF.")
                return render_template("notification_amend.html", form=form, notification=notification)
            uploaded_pdf.stream.seek(0)
            uploaded_pdf.save(upload_dir / stored_pdf_name)
            document_sha256 = sha256_file(upload_dir / stored_pdf_name)
        else:
            # --- Auto-generate official Sindh Government PDF for amendment ---
            amendment_ref = f"{notification.reference}-v{version_number}"
            try:
                document_sha256 = generate_official_sindh_pdf(
                    reference=amendment_ref,
                    title=form.title.data.strip(),
                    category=form.category.data,
                    department=notification.department,
                    subject=form.subject.data.strip(),
                    body=form.body.data.strip(),
                    document_date=form.document_date.data,
                    official_reference=(form.official_reference.data or "").strip() or None,
                    destination_path=upload_dir / stored_pdf_name,
                    host_url=request.host_url,
                )
            except Exception as exc:
                log.exception("PDF auto-generation failed for amendment %s v%s: %s", notification.reference, version_number, exc)
                flash("Failed to auto-generate the official PDF. Please try uploading a PDF manually.", "danger")
                return render_template("notification_amend.html", form=form, notification=notification)

        version = NotificationVersion(
            notification=notification,
            version_number=version_number,
            title=form.title.data.strip(),
            category=form.category.data,
            department=notification.department,
            subject=form.subject.data.strip(),
            body=form.body.data.strip(),
            document_date=form.document_date.data,
            official_reference=(form.official_reference.data or "").strip() or None,
            pdf_path=stored_pdf_name,
            pdf_sha256=document_sha256,
            change_summary=form.change_summary.data.strip(),
            status="Draft",
            created_by=current_user,
        )
        db.session.add(version)
        db.session.flush()
        record_audit(
            "notification_amendment_created",
            "notification",
            notification.id,
            f"Created version {version_number} of {notification.reference}.",
        )
        db.session.commit()
        flash(f"Amendment version {version_number} saved as a draft. The currently published version remains public.", "success")
        return redirect(url_for("staff.versions", notification_id=notification.id))
    return render_template("notification_amend.html", form=form, notification=notification)


@staff_bp.get("/notifications/<int:notification_id>/versions/<int:version_id>/pdf")
@permission_required("view_notifications")
def staff_version_pdf(notification_id, version_id):
    notification = get_notification_or_404(notification_id)
    version = db.session.get(NotificationVersion, version_id)
    if version is None or version.notification_id != notification.id:
        abort(404)
    if not can_view_notification_document(notification):
        abort(403)
    if not version.pdf_path:
        abort(404)
    response = send_from_directory(
        current_app.config["NOTIFICATION_UPLOAD_DIR"],
        version.pdf_path,
        mimetype="application/pdf",
        as_attachment=False,
        download_name=f"{notification.reference}-v{version.version_number}.pdf",
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@staff_bp.post("/notifications/<int:notification_id>/versions/<int:version_id>/submit")
@permission_required("create_notification")
def submit_amendment(notification_id, version_id):
    notification = get_notification_or_404(notification_id)
    version = db.session.get(NotificationVersion, version_id)
    if version is None or version.notification_id != notification.id:
        abort(404)
    if not can_view_notification_document(notification):
        abort(403)
    if current_user.role != "super_admin" and version.created_by_id != current_user.id:
        abort(403)
    if version.status != "Draft":
        abort(400, description="Only draft amendment versions can be submitted. Create a new amendment after a return or rejection.")
    # PDF is guaranteed to exist (auto-generated or uploaded on draft creation)
    version.status = "Pending Approval"
    record_audit(
        "notification_amendment_submitted",
        "notification",
        notification.id,
        f"Submitted version {version.version_number} of {notification.reference}.",
    )
    db.session.commit()
    flash(f"Amendment version {version.version_number} sent for approval.", "success")
    return redirect(url_for("staff.versions", notification_id=notification.id))


@staff_bp.post("/approvals/versions/<int:version_id>/<action>")
@permission_required("approve_notification")
def process_amendment_approval(version_id, action):
    if action not in {"approve", "return", "reject", "publish"}:
        abort(400)
    version = db.session.get(NotificationVersion, version_id)
    if version is None or version.version_number == 1:
        abort(404)
    notification = version.notification
    if current_user.role != "super_admin" and notification.department != current_user.department:
        abort(403)
    current_status = version.status
    next_status = STATUS_FLOW.get(current_status, {}).get(action)
    if not next_status:
        abort(400, description=f"Action '{action}' is not allowed for amendment status '{current_status}'.")
    if next_status == "Published":
        if version.pdf_path:
            try:
                sign_published_version(version, notification.reference)
            except SigningConfigurationError as error:
                current_app.logger.warning("Signing skipped or key missing: %s", error)
        notification.title = version.title
        notification.category = version.category
        notification.department = version.department
        notification.subject = version.subject
        notification.body = version.body
        notification.document_date = version.document_date
        notification.official_reference = version.official_reference
        notification.pdf_path = version.pdf_path
        notification.pdf_sha256 = version.pdf_sha256
        notification.status = "Published"
    version.status = next_status
    version.reviewed_by = current_user
    notification.reviewed_by = current_user
    record_audit(
        f"notification_amendment_{action}",
        "notification",
        notification.id,
        f"{notification.reference} version {version.version_number}: {current_status} -> {next_status}.",
    )
    db.session.commit()
    flash(f"{notification.reference} version {version.version_number} status changed to {next_status}.", "success")
    return redirect(url_for("staff.approvals"))


@staff_bp.get("/departments")
@permission_required("manage_departments")
def departments():
    return render_template("departments.html", departments=Department.query.order_by(Department.name).all())


@staff_bp.route("/users", methods=["GET", "POST"])
@permission_required("manage_users")
def users():
    form = StaffUserForm()
    users_list = User.query.order_by(User.name).all()
    department_names = sorted(
        {department.name for department in Department.query.filter_by(active=True).all()}
        | {user.department for user in users_list if user.department}
    )
    form.department.choices = [(name, name) for name in department_names]

    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        if User.query.filter_by(email=email).first():
            flash("A staff account with that email already exists.", "danger")
        else:
            user = User(
                name=form.name.data.strip(),
                email=email,
                department=form.department.data.strip(),
                role=form.role.data,
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.flush()
            record_audit("staff_account_created", "user", user.id, f"Created {user.role} account for {user.email}.")
            db.session.commit()
            flash("Staff account created. Share its initial password securely with the staff member.", "success")
            return redirect(url_for("staff.users"))

    return render_template(
        "users.html",
        users=users_list,
        roles=ROLE_PERMISSIONS,
        form=form,
        departments=department_names,
    )






@staff_bp.post("/users/<int:user_id>/reset-password")
@permission_required("manage_users")
def reset_user_password(user_id):
    """Super Admin resets another staff member's password.

    Guards:
    - Cannot reset your own password here (use profile/login flow).
    - New password must be at least 12 characters.
    """
    user = db.session.get(User, user_id)
    if user is None:
        abort(404)
    if user.id == current_user.id:
        flash("Use your account settings to change your own password.", "danger")
        return redirect(url_for("staff.users"))
    new_password = request.form.get("new_password", "").strip()
    if len(new_password) < 12:
        flash("Password must be at least 12 characters.", "danger")
        return redirect(url_for("staff.users"))
    user.set_password(new_password)
    record_audit(
        "staff_password_reset",
        "user",
        user.id,
        f"Password reset for {user.email} by {current_user.email}.",
    )
    db.session.commit()
    flash(f"Password successfully reset for {user.name}.", "success")
    return redirect(url_for("staff.users"))


@staff_bp.post("/users/<int:user_id>/edit-name")
@permission_required("manage_users")
def edit_user_name(user_id):
    """Super Admin updates the display name of a staff account."""
    user = db.session.get(User, user_id)
    if user is None:
        abort(404)
    new_name = request.form.get("name", "").strip()
    if not new_name or len(new_name) > 120:
        flash("Please provide a valid name (max 120 characters).", "danger")
        return redirect(url_for("staff.users"))
    old_name = user.name
    if new_name != old_name:
        user.name = new_name
        record_audit(
            "staff_name_changed",
            "user",
            user.id,
            f"Name changed: '{old_name}' -> '{new_name}' by {current_user.email}.",
        )
        db.session.commit()
        flash(f"Name updated to '{new_name}'.", "success")
    return redirect(url_for("staff.users"))


@staff_bp.post("/users/<int:user_id>/delete")
@permission_required("manage_users")
def delete_user(user_id):
    """Permanently delete a staff account.

    Guards:
    - Cannot delete yourself.
    - Nullifies created_by_id / reviewed_by_id on linked Notifications and
      NotificationVersions so FK constraints are not violated.
    - Sets actor_id = NULL on AuditLog rows so the audit chain is preserved.
    """
    user = db.session.get(User, user_id)
    if user is None:
        abort(404)
    if user.id == current_user.id:
        flash("You cannot delete your own account.", "danger")
        return redirect(url_for("staff.users"))

    # Nullify FK references so the delete succeeds and data integrity is kept.
    Notification.query.filter_by(created_by_id=user.id).update({"created_by_id": None})
    Notification.query.filter_by(reviewed_by_id=user.id).update({"reviewed_by_id": None})
    NotificationVersion.query.filter_by(created_by_id=user.id).update({"created_by_id": None})
    NotificationVersion.query.filter_by(reviewed_by_id=user.id).update({"reviewed_by_id": None})
    AuditLog.query.filter_by(actor_id=user.id).update({"actor_id": None})

    deleted_email = user.email
    deleted_name = user.name
    record_audit(
        "staff_account_deleted",
        "user",
        user.id,
        f"Staff account permanently deleted: {deleted_name} ({deleted_email}).",
    )
    db.session.delete(user)
    db.session.commit()
    flash(f"Staff account for {deleted_name} has been permanently deleted.", "success")
    return redirect(url_for("staff.users"))


@staff_bp.post("/users/<int:user_id>/toggle-active")
@permission_required("manage_users")
def toggle_user_active(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        abort(404)
    if user.id == current_user.id:
        flash("You cannot deactivate your own account.", "danger")
        return redirect(url_for("staff.users"))
    user.active = not user.active
    status = "activated" if user.active else "deactivated"
    record_audit(f"staff_account_{status}", "user", user.id, f"{user.email} was {status}.")
    db.session.commit()
    flash(f"Staff account {status}.", "success")
    return redirect(url_for("staff.users"))


@staff_bp.post("/users/<int:user_id>/department")
@permission_required("manage_users")
def update_user_department(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        abort(404)
    department = request.form.get("department", "").strip()
    allowed_departments = {
        item.name for item in Department.query.filter_by(active=True).all()
    } | {item.department for item in User.query.all()}
    if not department or len(department) > 160 or department not in allowed_departments:
        abort(400, description="Select an active department from the list.")
    if department != user.department:
        previous_department = user.department
        user.department = department
        record_audit(
            "staff_department_changed",
            "user",
            user.id,
            f"{user.email}: {previous_department} -> {department}.",
        )
        db.session.commit()
        flash(f"Department updated for {user.email}.", "success")
    return redirect(url_for("staff.users"))


@staff_bp.post("/users/<int:user_id>/role")
@permission_required("manage_roles")
def update_user_role(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        abort(404)
    role = request.form.get("role", "").strip()
    if user.id == current_user.id:
        flash("You cannot change your own role.", "danger")
    elif role not in ROLES:
        abort(400, description="Select one of the defined staff roles.")
    else:
        previous_role = user.role
        user.role = role
        record_audit("staff_role_changed", "user", user.id, f"{user.email}: {previous_role} -> {role}.")
        db.session.commit()
        flash(f"Role updated for {user.email}.", "success")
    return redirect(url_for("staff.users"))


@staff_bp.get("/roles")
@permission_required("manage_roles")
def roles():
    return render_template("roles.html", role_permissions=ROLE_PERMISSIONS)


@staff_bp.get("/keys")
@permission_required("manage_signing_keys")
def keys():
    keys = SigningKey.query.order_by(SigningKey.created_at.desc()).all()
    return render_template("keys.html", signing_keys=keys)


@staff_bp.post("/keys/generate")
@permission_required("manage_signing_keys")
def generate_key():
    try:
        key_id = generate_signing_key()
    except SigningConfigurationError as error:
        flash(str(error), "danger")
        return redirect(url_for("staff.keys"))
    record_audit("signing_key_generated", "signing_key", key_id, "Generated project signing key; private key stored outside the database.")
    db.session.commit()
    flash(f"Project signing key {key_id[:12]} generated and activated.", "success")
    return redirect(url_for("staff.keys"))


@staff_bp.get("/workflow")
@permission_required("configure_workflow")
def workflow():
    return render_template("placeholder.html", title="Workflow settings", description="Workflow configuration is restricted to Super Admin. Approval rules will be configurable in a later increment.")


@staff_bp.get("/audit")
@permission_required("view_audit")
def audit():
    logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(200).all()
    chain_valid, invalid_entry_id = verify_audit_chain()
    return render_template(
        "audit.html",
        logs=logs,
        chain_valid=chain_valid,
        invalid_entry_id=invalid_entry_id,
    )


@staff_bp.app_errorhandler(403)
def forbidden(error):
    return render_template("error.html", code=403, title="Access restricted", message="Your staff role does not have permission to access this page or perform this action."), 403
