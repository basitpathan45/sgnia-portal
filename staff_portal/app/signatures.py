import base64
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from flask import current_app
from sqlalchemy import select

from .extensions import db
from .models import SigningKey


class SigningConfigurationError(Exception):
    pass


def signing_key_directory():
    return Path(current_app.config.get(
        "SIGNING_KEY_DIR",
        Path(current_app.instance_path) / "signing-keys",
    ))


def private_key_path(key_id):
    return signing_key_directory() / f"{key_id}.pem"


def signature_message(reference, version_number, pdf_sha256, key_id):
    payload = {
        "key_id": key_id,
        "pdf_sha256": pdf_sha256,
        "reference": reference,
        "version_number": version_number,
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def generate_signing_key():
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    private_key = Ed25519PrivateKey.generate()
    public_bytes = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    key_id = hashlib.sha256(public_bytes).hexdigest()
    directory = signing_key_directory()
    directory.mkdir(parents=True, exist_ok=True)
    key_path = private_key_path(key_id)
    encoded_private_key = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    try:
        with key_path.open("xb") as private_file:
            private_file.write(encoded_private_key)
        try:
            os.chmod(key_path, 0o600)
        except OSError:
            current_app.logger.warning("Could not restrict signing-key permissions on %s.", key_path)
    except FileExistsError as error:
        raise SigningConfigurationError(f"Signing-key file already exists: {key_path}") from error

    for existing_key in SigningKey.query.filter_by(active=True).all():
        existing_key.active = False
    db.session.add(SigningKey(
        key_id=key_id,
        public_key=base64.b64encode(public_bytes).decode("ascii"),
        active=True,
    ))
    db.session.commit()
    return key_id


def sign_published_version(version, reference):
    from cryptography.hazmat.primitives import serialization

    active_key = db.session.execute(
        select(SigningKey).where(SigningKey.active.is_(True)).order_by(SigningKey.created_at.desc())
    ).scalars().first()
    if active_key is None:
        raise SigningConfigurationError("No active signing key. Generate one before publishing.")
    key_path = private_key_path(active_key.key_id)
    if not key_path.is_file():
        raise SigningConfigurationError(
            f"Private signing key {active_key.key_id} is unavailable; publication was not signed."
        )
    if not version.pdf_sha256 or not version.pdf_path:
        raise SigningConfigurationError("The PDF and its SHA-256 fingerprint are required for signing.")
    from .documents import sha256_file

    pdf_path = Path(current_app.config["NOTIFICATION_UPLOAD_DIR"]) / Path(version.pdf_path).name
    if not pdf_path.is_file() or sha256_file(pdf_path) != version.pdf_sha256:
        raise SigningConfigurationError("The stored PDF does not match its recorded SHA-256 fingerprint.")
    private_key = serialization.load_pem_private_key(key_path.read_bytes(), password=None)
    signed_at = datetime.now(timezone.utc)
    signature = private_key.sign(signature_message(
        reference,
        version.version_number,
        version.pdf_sha256,
        active_key.key_id,
    ))
    version.signature = base64.b64encode(signature).decode("ascii")
    version.signature_key_id = active_key.key_id
    version.signature_signed_at = signed_at
    return active_key.key_id


def verify_version_signature(version, reference, verify_pdf_file=False):
    if not version.signature or not version.signature_key_id or not version.pdf_sha256:
        return {"status": "unsigned", "valid": False}
    key = db.session.get(SigningKey, version.signature_key_id)
    if key is None:
        return {"status": "unknown_key", "valid": False}
    try:
        from cryptography.exceptions import InvalidSignature
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

        public_bytes = base64.b64decode(key.public_key, validate=True)
        if hashlib.sha256(public_bytes).hexdigest() != key.key_id:
            return {"status": "invalid_key", "valid": False}
        public_key = Ed25519PublicKey.from_public_bytes(public_bytes)
        signature = base64.b64decode(version.signature, validate=True)
        public_key.verify(
            signature,
            signature_message(reference, version.version_number, version.pdf_sha256, key.key_id),
        )
    except (InvalidSignature, ValueError, TypeError):
        return {"status": "invalid_signature", "valid": False}

    result = {
        "status": "verified",
        "valid": True,
        "keyId": key.key_id,
        "publicKey": key.public_key,
        "signature": version.signature,
        "signedAt": version.signature_signed_at.isoformat() if version.signature_signed_at else None,
        "pdfSha256": version.pdf_sha256,
    }
    if verify_pdf_file:
        from .documents import sha256_file

        pdf_path = Path(current_app.config["NOTIFICATION_UPLOAD_DIR"]) / Path(version.pdf_path or "").name
        file_matches = pdf_path.is_file() and sha256_file(pdf_path) == version.pdf_sha256
        result["fileMatchesSignature"] = file_matches
        if not file_matches:
            result.update(status="document_mismatch", valid=False)
    return result
