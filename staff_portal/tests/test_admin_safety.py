import os
import tempfile
import unittest

from sqlalchemy import text

from app import create_app
from app.extensions import db
from app.models import Department, Notification, User
from app.permissions import ADMIN, ROLE_PERMISSIONS, SUPER_ADMIN


SUPER_ADMIN_EMAIL = "owaispathan@sgnia.gos.pk"


class AdminSafetyTests(unittest.TestCase):
    def setUp(self):
        self.upload_directory = tempfile.TemporaryDirectory()
        self.app = create_app({
            "TESTING": True,
            "SECRET_KEY": "test-key",
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
            "WTF_CSRF_ENABLED": False,
            "SUPER_ADMIN_EMAIL": SUPER_ADMIN_EMAIL,
            "NOTIFICATION_UPLOAD_DIR": self.upload_directory.name,
            "SIGNING_KEY_DIR": os.path.join(self.upload_directory.name, "signing-keys"),
        })
        self.context = self.app.app_context()
        self.context.push()
        db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()
        self.upload_directory.cleanup()

    def create_user(self, name, email, role):
        user = User(
            name=name,
            email=email,
            role=role,
            department="Finance Department",
        )
        user.set_password("a-long-test-password")
        db.session.add(user)
        db.session.commit()
        return user

    def sign_in(self, user):
        return self.client.post("/login", data={
            "email": user.email,
            "password": "a-long-test-password",
        })

    def test_admin_has_full_operational_permissions(self):
        admin = self.create_user("Portal Admin", "admin@example.com", ADMIN)
        db.session.add(Department(name="Other Department"))
        db.session.add(Notification(
            reference="SGNIA-2026-OTHER001",
            title="Another department draft",
            category="Notification",
            department="Other Department",
            subject="Cross-department access",
            body="Draft content",
            status="Draft",
        ))
        db.session.commit()
        self.sign_in(admin)

        for path in ("/users", "/roles", "/departments", "/keys", "/workflow", "/approvals"):
            with self.subTest(path=path):
                self.assertEqual(200, self.client.get(path).status_code)

        notifications_page = self.client.get("/notifications")
        self.assertIn(b"Another department draft", notifications_page.data)
        draft_form = self.client.get("/notifications/new")
        self.assertIn(b'value="Other Department"', draft_form.data)
        self.assertEqual(ROLE_PERMISSIONS[SUPER_ADMIN], ROLE_PERMISSIONS[ADMIN])

    def test_admin_cannot_create_or_assign_a_super_admin(self):
        admin = self.create_user("Portal Admin", "admin@example.com", ADMIN)
        self.sign_in(admin)

        self.client.post("/users", data={
            "name": "Unauthorized Admin",
            "email": "unauthorized@example.com",
            "department": "Finance Department",
            "role": SUPER_ADMIN,
            "password": "another-long-password",
            "submit": "Create staff account",
        })
        self.client.post("/users", data={
            "name": "Replacement Owais",
            "email": SUPER_ADMIN_EMAIL,
            "department": "Finance Department",
            "role": ADMIN,
            "password": "another-long-password",
            "submit": "Create staff account",
        })

        self.assertIsNone(User.query.filter_by(email="unauthorized@example.com").first())
        self.assertIsNone(User.query.filter_by(email=SUPER_ADMIN_EMAIL).first())

    def test_admin_cannot_change_designated_super_admin_account(self):
        admin = self.create_user("Portal Admin", "admin@example.com", ADMIN)
        super_admin = self.create_user("Owais Pathan", SUPER_ADMIN_EMAIL, SUPER_ADMIN)
        self.sign_in(admin)
        response = self.client.get("/users")
        self.assertEqual(200, response.status_code)
        self.assertIn(b"Protected Super Admin", response.data)
        self.assertNotIn(f"/users/{super_admin.id}/reset-password".encode(), response.data)

        protected_actions = (
            (f"/users/{super_admin.id}/edit-name", {"name": "Changed Name"}),
            (f"/users/{super_admin.id}/reset-password", {"new_password": "changed-password"}),
            (f"/users/{super_admin.id}/toggle-active", {}),
            (f"/users/{super_admin.id}/delete", {}),
            (f"/users/{super_admin.id}/department", {"department": "Other Department"}),
            (f"/users/{super_admin.id}/role", {"role": ADMIN}),
        )
        for path, data in protected_actions:
            with self.subTest(path=path):
                self.assertEqual(403, self.client.post(path, data=data).status_code)

        db.session.refresh(super_admin)
        self.assertEqual("Owais Pathan", super_admin.name)
        self.assertEqual(SUPER_ADMIN, super_admin.role)
        self.assertTrue(super_admin.active)
        self.assertEqual("Finance Department", super_admin.department)
        self.assertIsNotNone(db.session.get(User, super_admin.id))

class AdminRoleMigrationTests(unittest.TestCase):
    def create_migration_app(self, database_path, temporary_directory):
        return create_app({
            "TESTING": True,
            "SECRET_KEY": "migration-test",
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{database_path}",
            "SUPER_ADMIN_EMAIL": SUPER_ADMIN_EMAIL,
            "NOTIFICATION_UPLOAD_DIR": temporary_directory,
            "SIGNING_KEY_DIR": os.path.join(temporary_directory, "migration-keys"),
        })

    def insert_legacy_user(self, name, email, role, active=True):
        user = User(
            name=name,
            email=email,
            role=role,
            department="Finance Department",
            active=active,
        )
        user.set_password("a-long-test-password")
        db.session.execute(
            text(
                "INSERT INTO user "
                "(name, email, password_hash, role, department, active, created_at) "
                "VALUES (:name, :email, :password_hash, :role, :department, :active, CURRENT_TIMESTAMP)"
            ),
            {
                "name": user.name,
                "email": user.email,
                "password_hash": user.password_hash,
                "role": user.role,
                "department": user.department,
                "active": user.active,
            },
        )
        db.session.commit()

    def test_migration_promotes_designated_account_and_demotes_other_super_admins(self):
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        database_path = os.path.join(temporary_directory.name, "migration.sqlite")
        migration_app = self.create_migration_app(database_path, temporary_directory.name)

        def dispose_migration_database():
            with migration_app.app_context():
                db.session.remove()
                db.engine.dispose()

        self.addCleanup(dispose_migration_database)
        runner = migration_app.test_cli_runner()

        baseline = runner.invoke(args=["db", "upgrade", "08a5be3079bc"])
        self.assertEqual(0, baseline.exit_code, f"{baseline.output}\n{baseline.exception!r}")
        with migration_app.app_context():
            self.insert_legacy_user(
                "Owais Pathan", SUPER_ADMIN_EMAIL, SUPER_ADMIN, active=False
            )
            self.insert_legacy_user(
                "Previous Super Admin", "previous@example.com", SUPER_ADMIN
            )

        upgraded = runner.invoke(args=["db", "upgrade", "head"])
        self.assertEqual(0, upgraded.exit_code, f"{upgraded.output}\n{upgraded.exception!r}")
        with migration_app.app_context():
            db.session.expire_all()
            designated = User.query.filter_by(email=SUPER_ADMIN_EMAIL).one()
            previous_admin = User.query.filter_by(email="previous@example.com").one()
            self.assertEqual(SUPER_ADMIN, designated.role)
            self.assertTrue(designated.active)
            self.assertEqual(ADMIN, previous_admin.role)

    def test_fresh_database_can_migrate_before_creating_designated_admin(self):
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        database_path = os.path.join(temporary_directory.name, "fresh.sqlite")
        migration_app = self.create_migration_app(database_path, temporary_directory.name)

        def dispose_migration_database():
            with migration_app.app_context():
                db.session.remove()
                db.engine.dispose()

        self.addCleanup(dispose_migration_database)
        runner = migration_app.test_cli_runner()

        upgraded = runner.invoke(args=["db", "upgrade", "head"])
        self.assertEqual(0, upgraded.exit_code, f"{upgraded.output}\n{upgraded.exception!r}")

        with migration_app.app_context():
            designated = User(
                name="Owais Pathan",
                email=SUPER_ADMIN_EMAIL,
                role=SUPER_ADMIN,
                department="Finance Department",
            )
            designated.set_password("a-long-test-password")
            db.session.add(designated)
            db.session.commit()
            self.assertEqual(SUPER_ADMIN, User.query.filter_by(email=SUPER_ADMIN_EMAIL).one().role)

    def test_prepare_db_migrates_an_existing_unstamped_database(self):
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        database_path = os.path.join(temporary_directory.name, "legacy.sqlite")
        migration_app = self.create_migration_app(database_path, temporary_directory.name)

        def dispose_migration_database():
            with migration_app.app_context():
                db.session.remove()
                db.engine.dispose()

        self.addCleanup(dispose_migration_database)
        with migration_app.app_context():
            db.create_all()
            designated = User(
                name="Owais Pathan",
                email=SUPER_ADMIN_EMAIL,
                role=SUPER_ADMIN,
                department="Finance Department",
            )
            designated.set_password("a-long-test-password")
            previous_admin = User(
                name="Previous Super Admin",
                email="previous@example.com",
                role=SUPER_ADMIN,
                department="Finance Department",
            )
            previous_admin.set_password("a-long-test-password")
            db.session.add_all([designated, previous_admin])
            db.session.commit()

        result = migration_app.test_cli_runner().invoke(args=["prepare-db"])
        self.assertEqual(0, result.exit_code, f"{result.output}\n{result.exception!r}")
        with migration_app.app_context():
            db.session.expire_all()
            self.assertEqual(
                SUPER_ADMIN,
                User.query.filter_by(email=SUPER_ADMIN_EMAIL).one().role,
            )
            self.assertEqual(
                ADMIN,
                User.query.filter_by(email="previous@example.com").one().role,
            )


if __name__ == "__main__":
    unittest.main()
