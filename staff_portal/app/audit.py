import hashlib
import json
from datetime import timezone

from .extensions import db
from .models import AuditLog

GENESIS_HASH = "0" * 64


def _entry_payload(entry):
    created_at = entry.created_at
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    return {
        "action": entry.action,
        "actor_id": entry.actor_id,
        "created_at": created_at.isoformat(),
        "details": entry.details,
        "id": entry.id,
        "previous_hash": entry.previous_hash,
        "target_id": entry.target_id,
        "target_type": entry.target_type,
    }


def calculate_entry_hash(entry):
    canonical_entry = json.dumps(
        _entry_payload(entry),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical_entry).hexdigest()


def append_audit_log(actor, action, target_type, target_id=None, details=""):
    previous = AuditLog.query.order_by(AuditLog.id.desc()).with_for_update().first()
    entry = AuditLog(
        actor=actor,
        action=action,
        target_type=target_type,
        target_id=str(target_id) if target_id is not None else None,
        details=details[:500],
        previous_hash=previous.entry_hash if previous else GENESIS_HASH,
    )
    db.session.add(entry)
    db.session.flush()
    entry.entry_hash = calculate_entry_hash(entry)
    return entry


def verify_audit_chain():
    expected_previous_hash = GENESIS_HASH
    for entry in AuditLog.query.order_by(AuditLog.id.asc()).yield_per(500):
        if entry.previous_hash != expected_previous_hash:
            return False, entry.id
        if not entry.entry_hash or calculate_entry_hash(entry) != entry.entry_hash:
            return False, entry.id
        expected_previous_hash = entry.entry_hash
    return True, None


def backfill_audit_chain():
    entries = AuditLog.query.order_by(AuditLog.id.asc()).all()
    if not entries:
        return
    unhashed = [entry for entry in entries if not entry.previous_hash and not entry.entry_hash]
    if len(unhashed) not in {0, len(entries)}:
        raise RuntimeError("Audit chain has partially missing hashes; investigate before migration.")
    if not unhashed:
        return

    previous_hash = GENESIS_HASH
    for entry in entries:
        entry.previous_hash = previous_hash
        db.session.flush()
        entry.entry_hash = calculate_entry_hash(entry)
        previous_hash = entry.entry_hash
    db.session.commit()
