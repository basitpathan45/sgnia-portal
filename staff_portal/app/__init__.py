import os
import warnings
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_login import current_user
from flask_migrate import Migrate
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from .extensions import csrf, db, login_manager


def create_app(test_config=None):
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    app = Flask(__name__, instance_relative_config=True)
    instance_dir = Path(app.instance_path)
    instance_dir.mkdir(parents=True, exist_ok=True)
    is_production = os.environ.get("APP_ENV", "development").lower() == "production"
    secret_key = os.environ.get("FLASK_SECRET_KEY")
    database_url = os.environ.get("DATABASE_URL")
    if is_production and (not secret_key or not database_url):
        raise RuntimeError("Production requires FLASK_SECRET_KEY and DATABASE_URL.")
    if is_production and (
        not os.environ.get("NOTIFICATION_UPLOAD_DIR")
        or not os.environ.get("SIGNING_KEY_DIR")
    ):
        raise RuntimeError("Production requires persistent NOTIFICATION_UPLOAD_DIR and SIGNING_KEY_DIR paths.")
    if is_production:
        source_root = Path(__file__).resolve().parents[2]
        for storage_setting in ("NOTIFICATION_UPLOAD_DIR", "SIGNING_KEY_DIR"):
            storage_path = Path(os.environ[storage_setting]).resolve()
            if storage_path == source_root or source_root in storage_path.parents:
                raise RuntimeError(f"Production {storage_setting} must be outside the source checkout.")
    if not secret_key and not (test_config and test_config.get("TESTING")):
        warnings.warn("Using a development-only secret key; configure FLASK_SECRET_KEY before deployment.", stacklevel=2)

    app.config.from_mapping(
        SECRET_KEY=secret_key or "local-development-key-change-before-deploy",
        SQLALCHEMY_DATABASE_URI=database_url or f"sqlite:///{instance_dir / 'sdgnm-dev.db'}",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_ENGINE_OPTIONS={"pool_pre_ping": True},
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=is_production,
        WTF_CSRF_TIME_LIMIT=3600,
        MAX_CONTENT_LENGTH=17 * 1024 * 1024,
        MAX_NOTIFICATION_PDF_BYTES=16 * 1024 * 1024,
        NOTIFICATION_UPLOAD_DIR=os.environ.get(
            "NOTIFICATION_UPLOAD_DIR",
            str(instance_dir / "notification-files"),
        ),
        SIGNING_KEY_DIR=os.environ.get(
            "SIGNING_KEY_DIR",
            str(instance_dir / "signing-keys"),
        ),
        TESSERACT_CMD=os.environ.get("TESSERACT_CMD"),
    )
    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    Migrate(app, db, compare_type=True)
    login_manager.init_app(app)
    csrf.init_app(app)

    from . import models  # noqa: F401
    from .auth import auth_bp
    from .public import public_bp
    from .staff import staff_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(public_bp)
    app.register_blueprint(staff_bp)

    @app.get("/health")
    def health():
        try:
            db.session.execute(text("SELECT 1"))
        except SQLAlchemyError:
            db.session.rollback()
            return jsonify({"status": "unavailable"}), 503
        return jsonify({"status": "ok"}), 200

    @app.context_processor
    def provide_template_helpers():
        from .permissions import can

        return {"can": can}

    @app.cli.command("init-db")
    def init_db_command():
        """Create tables for a fresh local or MySQL database."""
        db.create_all()
        add_notification_columns()
        add_audit_columns()
        backfill_notification_versions()
        backfill_document_hashes()
        backfill_audit_hash_chain()
        print("Database tables are ready.")

    def add_notification_columns():
        from sqlalchemy import inspect, text

        columns = {column["name"] for column in inspect(db.engine).get_columns("notification")}
        additions = {
            "document_date": "DATE",
            "official_reference": "VARCHAR(120)",
            "pdf_path": "VARCHAR(500)",
            "pdf_sha256": "VARCHAR(64)",
        }
        with db.engine.begin() as connection:
            for name, column_type in additions.items():
                if name not in columns:
                    connection.execute(text(f"ALTER TABLE notification ADD COLUMN {name} {column_type}"))

        version_columns = {
            column["name"] for column in inspect(db.engine).get_columns("notification_version")
        }
        version_additions = {
            "pdf_sha256": "VARCHAR(64)",
            "signature": "VARCHAR(128)",
            "signature_key_id": "VARCHAR(64)",
            "signature_signed_at": "DATETIME",
        }
        with db.engine.begin() as connection:
            for name, column_type in version_additions.items():
                if name not in version_columns:
                    connection.execute(text(
                        f"ALTER TABLE notification_version ADD COLUMN {name} {column_type}"
                    ))

    def add_audit_columns():
        from sqlalchemy import inspect, text

        inspector = inspect(db.engine)
        columns = {column["name"] for column in inspector.get_columns("audit_log")}
        unique_constraints = inspector.get_unique_constraints("audit_log")
        unique_indexes = inspector.get_indexes("audit_log")
        with db.engine.begin() as connection:
            if "previous_hash" not in columns:
                connection.execute(text("ALTER TABLE audit_log ADD COLUMN previous_hash VARCHAR(64)"))
            if "entry_hash" not in columns:
                connection.execute(text("ALTER TABLE audit_log ADD COLUMN entry_hash VARCHAR(64)"))
            has_unique_hash = any(
                constraint.get("column_names") == ["entry_hash"]
                for constraint in unique_constraints
            ) or any(
                index.get("unique") and index.get("column_names") == ["entry_hash"]
                for index in unique_indexes
            )
            if not has_unique_hash:
                connection.execute(text(
                    "CREATE UNIQUE INDEX uq_audit_log_entry_hash ON audit_log (entry_hash)"
                ))

    def backfill_notification_versions():
        from .models import Notification, NotificationVersion

        for notification in Notification.query.all():
            if notification.versions:
                continue
            db.session.add(NotificationVersion(
                notification=notification,
                version_number=1,
                title=notification.title,
                category=notification.category,
                department=notification.department,
                subject=notification.subject,
                body=notification.body,
                document_date=notification.document_date,
                official_reference=notification.official_reference,
                pdf_path=notification.pdf_path,
                pdf_sha256=notification.pdf_sha256,
                change_summary="Original notification record.",
                status=notification.status,
                created_by_id=notification.created_by_id,
                reviewed_by_id=notification.reviewed_by_id,
                created_at=notification.created_at,
                updated_at=notification.updated_at,
            ))
        db.session.commit()

    def backfill_document_hashes():
        from .documents import sha256_file
        from .models import Notification, NotificationVersion

        upload_dir = Path(app.config["NOTIFICATION_UPLOAD_DIR"])
        for notification in Notification.query.all():
            if notification.pdf_path and not notification.pdf_sha256:
                path = upload_dir / Path(notification.pdf_path).name
                if path.is_file():
                    notification.pdf_sha256 = sha256_file(path)
            for version in notification.versions:
                if version.pdf_path and not version.pdf_sha256:
                    path = upload_dir / Path(version.pdf_path).name
                    if path.is_file():
                        version.pdf_sha256 = sha256_file(path)
                if version.version_number == 1 and not version.pdf_sha256:
                    version.pdf_sha256 = notification.pdf_sha256
        db.session.commit()

    def backfill_audit_hash_chain():
        from .audit import backfill_audit_chain

        backfill_audit_chain()

    @app.cli.command("migrate-db")
    def migrate_db_command():
        """Add document, version-history, and audit-chain fields to the existing database."""
        db.create_all()
        add_notification_columns()
        add_audit_columns()
        backfill_notification_versions()
        backfill_document_hashes()
        backfill_audit_hash_chain()
        print("Database schema is up to date.")

    @app.cli.command("verify-audit-chain")
    def verify_audit_chain_command():
        """Check all audit events against their SHA-256 hash chain."""
        from .audit import verify_audit_chain

        is_valid, invalid_entry_id = verify_audit_chain()
        if not is_valid:
            raise SystemExit(f"Audit chain verification FAILED at entry {invalid_entry_id}.")
        print("Audit chain verification passed.")

    @app.cli.command("create-user")
    def create_user_command():
        """Interactively provision a staff account without storing demo passwords."""
        import getpass

        from .models import User
        from .permissions import ROLES

        name = input("Full name: ").strip()
        email = input("Email: ").strip().lower()
        department = input("Department: ").strip()
        print(f"Roles: {', '.join(sorted(ROLES))}")
        role = input("Role: ").strip().lower()
        if not name or not email or not department or role not in ROLES:
            raise SystemExit("Name, email, department, and a valid role are required.")
        if User.query.filter_by(email=email).first():
            raise SystemExit("A staff account with that email already exists.")

        password = getpass.getpass("Initial password (at least 12 characters): ")
        if len(password) < 12:
            raise SystemExit("Password must contain at least 12 characters.")

        user = User(name=name, email=email, department=department, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        print(f"Created {role} account for {email}.")

    @app.cli.command("seed-departments")
    def seed_departments_command():
        """Add or update the 43 official Sindh departments with codes and profiles."""
        from .models import Department

        depts_data = [
            {
                "name": "Agriculture, Supply & Prices Department",
                "short_name": "Agriculture & Supply",
                "code": "ASP",
                "overview": "The Agriculture, Supply & Prices Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.",
            },
            {
                "name": "Auqaf Religious Affairs Zakat & Ushr Department",
                "short_name": "Auqaf, Religious Affairs & Zakat",
                "code": "ARAZU",
                "overview": "The Auqaf Religious Affairs Zakat & Ushr Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.",
            },
            {
                "name": "Board of Revenue (BOR)",
                "short_name": "Board of Revenue",
                "code": "BOR",
                "overview": "The Board of Revenue (BOR) operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.",
            },
            {
                "name": "Chief Minister's Secretariat & Inspection Team",
                "short_name": "CM Secretariat",
                "code": "CMSIT",
                "overview": "The Chief Minister's Secretariat & Inspection Team operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.",
            },
            {
                "name": "College Education Department",
                "short_name": "College Education",
                "code": "CED",
                "overview": "The College Education Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.",
            },
            {
                "name": "Cooperative Department",
                "short_name": "Cooperative",
                "code": "COOP",
                "overview": "The Cooperative Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.",
            },
            {
                "name": "Culture, Tourism & Antiquities Department",
                "short_name": "Culture & Tourism",
                "code": "CTA",
                "overview": "The Culture, Tourism & Antiquities Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.",
            },
            {
                "name": "Department of Empowerment of Persons with Disabilities",
                "short_name": "Empowerment of Persons with Disabilities",
                "code": "DEPD",
                "overview": "The Department of Empowerment of Persons with Disabilities operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.",
            },
            {
                "name": "Energy Department",
                "short_name": "Energy",
                "code": "ENERGY",
                "overview": "The Energy Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.",
            },
            {
                "name": "Enquiries & Anti-Corruption Establishment",
                "short_name": "Anti-Corruption Establishment",
                "code": "EACE",
                "overview": "The Enquiries & Anti-Corruption Establishment operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.",
            },
            {
                "name": "Environment, Climate Change & Coastal Development Department",
                "short_name": "Environment & Climate Change",
                "code": "ECCD",
                "overview": "The Environment, Climate Change & Coastal Development Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.",
            },
            {
                "name": "Excise, Taxation & Narcotics Control Department",
                "short_name": "Excise & Taxation",
                "code": "ETNC",
                "overview": "The Excise, Taxation & Narcotics Control Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.",
            },
            {
                "name": "Finance Department",
                "short_name": "Finance",
                "code": "FIN",
                "overview": "The Finance Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.",
            },
            {
                "name": "Food Department & Sindh Food Authority",
                "short_name": "Food & Food Authority",
                "code": "FD-SFA",
                "overview": "The Food Department & Sindh Food Authority operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.",
            },
            {
                "name": "Forest & Wildlife Department",
                "short_name": "Forest & Wildlife",
                "code": "FW",
                "overview": "The Forest & Wildlife Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.",
            },
            {
                "name": "Health Department",
                "short_name": "Health",
                "code": "HEALTH",
                "overview": "The Health Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.",
            },
            {
                "name": "Home Department & Sindh Police",
                "short_name": "Home & Police",
                "code": "HOME-POL",
                "overview": "The Home Department & Sindh Police operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.",
            },
            {
                "name": "Human Rights Department",
                "short_name": "Human Rights",
                "code": "HRD",
                "overview": "The Human Rights Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.",
            },
            {
                "name": "Industries & Commerce Department",
                "short_name": "Industries & Commerce",
                "code": "IC",
                "overview": "The Industries & Commerce Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.",
            },
            {
                "name": "Information Department",
                "short_name": "Information",
                "code": "INFO",
                "overview": "The Information Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.",
            },
            {
                "name": "Inter Provincial Coordination Department",
                "short_name": "Inter Provincial Coordination",
                "code": "IPCD",
                "overview": "The Inter Provincial Coordination Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.",
            },
            {
                "name": "Investment Department",
                "short_name": "Investment",
                "code": "INVEST",
                "overview": "The Investment Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.",
            },
            {
                "name": "Irrigation Department",
                "short_name": "Irrigation",
                "code": "IRR",
                "overview": "The Irrigation Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.",
            },
            {
                "name": "Labour & Human Resources Department",
                "short_name": "Labour & Human Resources",
                "code": "LHR",
                "overview": "The Labour & Human Resources Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.",
            },
            {
                "name": "Law Department & Prosecutor General",
                "short_name": "Law & Prosecution",
                "code": "LDPG",
                "overview": "The Law Department & Prosecutor General operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.",
            },
            {
                "name": "Livestock & Fisheries Department",
                "short_name": "Livestock & Fisheries",
                "code": "LF",
                "overview": "The Livestock & Fisheries Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.",
            },
            {
                "name": "Local Government & Housing Town Planning Department",
                "short_name": "Local Government & Housing",
                "code": "LGHTP",
                "overview": "The Local Government & Housing Town Planning Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.",
            },
            {
                "name": "Mines & Mineral Development Department",
                "short_name": "Mines & Minerals",
                "code": "MMD",
                "overview": "The Mines & Mineral Development Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.",
            },
            {
                "name": "Minorities Affairs Department",
                "short_name": "Minorities Affairs",
                "code": "MA",
                "overview": "The Minorities Affairs Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.",
            },
            {
                "name": "Planning & Development Department",
                "short_name": "Planning & Development",
                "code": "P&D",
                "overview": "The Planning & Development Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.",
            },
            {
                "name": "Population Welfare Department",
                "short_name": "Population Welfare",
                "code": "PWD",
                "overview": "The Population Welfare Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.",
            },
            {
                "name": "Public Health Engineering & Rural Development Department",
                "short_name": "Public Health Engineering",
                "code": "PHERDD",
                "overview": "The Public Health Engineering & Rural Development Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.",
            },
            {
                "name": "Rehabilitation Department",
                "short_name": "Rehabilitation",
                "code": "REHAB",
                "overview": "The Rehabilitation Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.",
            },
            {
                "name": "School Education & Literacy Department",
                "short_name": "School Education & Literacy",
                "code": "SELD",
                "overview": "The School Education & Literacy Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.",
            },
            {
                "name": "Science & Information Technology Department",
                "short_name": "Science & Information Technology",
                "code": "SIT",
                "overview": "The Science & Information Technology Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.",
            },
            {
                "name": "Services, General Administration & Coordination Department (SGA&CD)",
                "short_name": "Services & General Administration",
                "code": "SGA-CD",
                "overview": "The Services, General Administration & Coordination Department (SGA&CD) operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.",
            },
            {
                "name": "Sindh Higher Education Commission (Sindh HEC)",
                "short_name": "Sindh HEC",
                "code": "SHEC",
                "overview": "The Sindh Higher Education Commission (Sindh HEC) operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.",
            },
            {
                "name": "Social Welfare Department",
                "short_name": "Social Welfare",
                "code": "SWD",
                "overview": "The Social Welfare Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.",
            },
            {
                "name": "Sports & Youth Affairs Department",
                "short_name": "Sports & Youth Affairs",
                "code": "SYA",
                "overview": "The Sports & Youth Affairs Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.",
            },
            {
                "name": "Transport & Mass Transit Department",
                "short_name": "Transport & Mass Transit",
                "code": "TMT",
                "overview": "The Transport & Mass Transit Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.",
            },
            {
                "name": "Universities & Boards Department",
                "short_name": "Universities & Boards",
                "code": "UBD",
                "overview": "The Universities & Boards Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.",
            },
            {
                "name": "Women Development Department",
                "short_name": "Women Development",
                "code": "WDD",
                "overview": "The Women Development Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.",
            },
            {
                "name": "Works & Services Department",
                "short_name": "Works & Services",
                "code": "W&S",
                "overview": "The Works & Services Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.",
            },
        ]
        count = 0
        for data in depts_data:
            dept = Department.query.filter_by(name=data["name"]).first()
            if not dept:
                dept = Department(name=data["name"])
                db.session.add(dept)
                count += 1
            dept.short_name = data["short_name"]
            dept.code = data["code"]
            dept.overview = data["overview"]
        db.session.commit()
        print(f"Processed {len(depts_data)} departments ({count} newly added).")

    return app
