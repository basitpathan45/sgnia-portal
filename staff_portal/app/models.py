from datetime import datetime, timezone

from flask_login import UserMixin
from sqlalchemy import UniqueConstraint
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db, login_manager


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(254), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(32), nullable=False, index=True)
    department = db.Column(db.String(160), nullable=False)
    active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def role_label(self):
        return self.role.replace("_", " ").title()


class Department(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), unique=True, nullable=False)
    short_name = db.Column(db.String(100), nullable=True)
    code = db.Column(db.String(32), nullable=True)
    parent_id = db.Column(db.Integer, db.ForeignKey("department.id"), nullable=True)
    overview = db.Column(db.Text, nullable=True)
    key_functions = db.Column(db.Text, nullable=True)
    governance_hierarchy = db.Column(db.Text, nullable=True)
    active = db.Column(db.Boolean, nullable=False, default=True)
    parent = db.relationship("Department", remote_side=[id], backref="subdepartments")


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(32), unique=True, nullable=False, index=True)
    title = db.Column(db.String(240), nullable=False)
    category = db.Column(db.String(80), nullable=False)
    department = db.Column(db.String(160), nullable=False)
    subject = db.Column(db.String(500), nullable=False)
    body = db.Column(db.Text, nullable=False)
    document_date = db.Column(db.Date, nullable=True)
    official_reference = db.Column(db.String(120), nullable=True)
    pdf_path = db.Column(db.String(500), nullable=True)
    pdf_sha256 = db.Column(db.String(64), nullable=True)
    status = db.Column(db.String(32), nullable=False, default="Draft", index=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    reviewed_by_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    created_by = db.relationship("User", foreign_keys=[created_by_id])
    reviewed_by = db.relationship("User", foreign_keys=[reviewed_by_id])
    versions = db.relationship(
        "NotificationVersion",
        back_populates="notification",
        order_by="NotificationVersion.version_number",
        cascade="all, delete-orphan",
    )


class NotificationVersion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    notification_id = db.Column(db.Integer, db.ForeignKey("notification.id"), nullable=False, index=True)
    version_number = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(240), nullable=False)
    category = db.Column(db.String(80), nullable=False)
    department = db.Column(db.String(160), nullable=False)
    subject = db.Column(db.String(500), nullable=False)
    body = db.Column(db.Text, nullable=False)
    document_date = db.Column(db.Date, nullable=True)
    official_reference = db.Column(db.String(120), nullable=True)
    pdf_path = db.Column(db.String(500), nullable=True)
    pdf_sha256 = db.Column(db.String(64), nullable=True)
    signature = db.Column(db.String(128), nullable=True)
    signature_key_id = db.Column(db.String(64), nullable=True)
    signature_signed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    change_summary = db.Column(db.String(500), nullable=False, default="")
    status = db.Column(db.String(32), nullable=False, default="Draft", index=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    reviewed_by_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    notification = db.relationship("Notification", back_populates="versions")
    created_by = db.relationship("User", foreign_keys=[created_by_id])
    reviewed_by = db.relationship("User", foreign_keys=[reviewed_by_id])
    __table_args__ = (
        UniqueConstraint("notification_id", "version_number", name="uq_notification_version_number"),
    )


class SigningKey(db.Model):
    key_id = db.Column(db.String(64), primary_key=True)
    public_key = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    active = db.Column(db.Boolean, nullable=False, default=True, index=True)


class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    actor_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    action = db.Column(db.String(80), nullable=False)
    target_type = db.Column(db.String(80), nullable=False)
    target_id = db.Column(db.String(80), nullable=True)
    details = db.Column(db.String(500), nullable=False, default="")
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    previous_hash = db.Column(db.String(64), nullable=True)
    entry_hash = db.Column(db.String(64), nullable=True, unique=True)
    actor = db.relationship("User")


@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(User, int(user_id))
    except (TypeError, ValueError):
        return None
