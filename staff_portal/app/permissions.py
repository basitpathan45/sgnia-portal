from functools import wraps

from flask import abort
from flask_login import current_user, login_required

SUPER_ADMIN = "super_admin"
APPROVER = "approver"
CREATOR = "creator"
AUDITOR = "auditor"

ROLES = {SUPER_ADMIN, APPROVER, CREATOR, AUDITOR}

# These permissions follow the role matrix supplied with the project proposal.
ROLE_PERMISSIONS = {
    SUPER_ADMIN: {
        "view_dashboard", "view_notifications", "create_notification",
        "approve_notification", "publish_notification", "use_ocr",
        "manage_departments", "manage_users", "manage_roles",
        "manage_signing_keys", "view_audit", "view_archive",
        "view_versions", "view_approval_history", "configure_workflow",
    },
    APPROVER: {
        "view_dashboard", "view_notifications", "create_notification",
        "approve_notification", "publish_notification", "use_ocr",
        "view_audit", "view_archive", "view_versions",
        "view_approval_history",
    },
    CREATOR: {
        "view_dashboard", "view_notifications", "create_notification",
        "use_ocr", "view_archive", "view_versions",
    },
    AUDITOR: {
        "view_dashboard", "view_notifications", "view_audit",
        "view_archive", "view_versions",
    },
}


def can(permission, user=None):
    user = user or current_user
    return bool(
        user
        and user.is_authenticated
        and user.active
        and permission in ROLE_PERMISSIONS.get(user.role, set())
    )


def permission_required(permission):
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapped(*args, **kwargs):
            if not can(permission):
                abort(403)
            return view(*args, **kwargs)

        return wrapped

    return decorator
