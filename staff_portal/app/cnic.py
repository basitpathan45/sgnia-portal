import hashlib
import hmac
import re

from flask import current_app


def normalize_cnic(value):
    normalized = re.sub(r"[\s-]", "", value.strip()) if isinstance(value, str) else ""
    return normalized if re.fullmatch(r"[0-9]{13}", normalized) else None


def cnic_fingerprint(normalized_cnic):
    key = current_app.config.get("CNIC_LOOKUP_KEY") or current_app.config["SECRET_KEY"]
    if isinstance(key, str):
        key = key.encode("utf-8")
    return hmac.new(
        key,
        b"sgnia:user-cnic:v1:" + normalized_cnic.encode("ascii"),
        hashlib.sha256,
    ).hexdigest()
