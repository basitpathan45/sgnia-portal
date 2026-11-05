import os
import tempfile
import unittest
from unittest.mock import patch

from app import create_app
from app.extensions import db
from app.models import User
from app.cnic import cnic_fingerprint, normalize_cnic


class CnicAccountTests(unittest.TestCase):
    def setUp(self):
        self.upload_directory = tempfile.TemporaryDirectory()
        self.app = create_app({
            "TESTING": True,
            "SECRET_KEY": "test-key",
            "CNIC_LOOKUP_KEY": "test-cnic-lookup-key",
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
            "WTF_CSRF_ENABLED": False,
            "SUPER_ADMIN_EMAIL": "owaispathan@sgnia.gos.pk",
            "NOTIFICATION_UPLOAD_DIR": self.upload_directory.name,
            "SIGNING_KEY_DIR": os.path.join(self.upload_directory.name, "signing-keys"),
        })
        self.context = self.app.app_context()
        self.context.push()
        db.create_all()
        self.client = self.app.test_client()
        self.admin = User(
            name="Portal Admin",
            email="admin@example.com",
            role="admin",
            department="Finance Department",
        )
        self.admin.set_password("a-long-test-password")
        db.session.add(self.admin)
        db.session.commit()
        self.client.post("/login", data={
            "email": self.admin.email,
            "password": "a-long-test-password",
        })

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()
        self.upload_directory.cleanup()

    def account_data(self, **overrides):
        data = {
            "name": "New Staff",
            "email": "new-staff@example.com",
            "cnic": "42101-1234567-8",
            "department": "Finance Department",
            "role": "creator",
            "password": "another-long-password",
            "submit": "Create staff account",
        }
        data.update(overrides)
        return data

    def test_cnic_normalization_and_validation(self):
        self.assertEqual("4210112345678", normalize_cnic(" 42101-1234567-8 "))
        for invalid in ("421011234567", "42101123456789", "42101/1234567/8", "１２３４５６７８９０１２３"):
            with self.subTest(invalid=invalid):
                self.assertIsNone(normalize_cnic(invalid))

    def test_new_account_requires_valid_cnic_and_does_not_echo_it(self):
        missing = self.client.post("/users", data=self.account_data(cnic=""))
        self.assertEqual(200, missing.status_code)
        self.assertIn(b"This field is required.", missing.data)
        self.assertIsNone(User.query.filter_by(email="new-staff@example.com").first())

        invalid_cnic = "42101/1234567/8"
        invalid = self.client.post("/users", data=self.account_data(cnic=invalid_cnic))
        self.assertEqual(200, invalid.status_code)
        self.assertNotIn(invalid_cnic.encode(), invalid.data)

    def test_new_account_stores_only_keyed_hash_and_masked_suffix(self):
        response = self.client.post("/users", data=self.account_data(), follow_redirects=True)
        self.assertEqual(200, response.status_code)
        user = User.query.filter_by(email="new-staff@example.com").one()
        self.assertEqual(cnic_fingerprint("4210112345678"), user.cnic_hash)
        self.assertNotEqual("4210112345678", user.cnic_hash)
        self.assertEqual("5678", user.cnic_last4)
        self.assertEqual("*****-****567-8", user.masked_cnic)
        self.assertNotIn(b"42101-1234567-8", response.data)
        self.assertIn(b"*****-****567-8", response.data)

    def test_duplicate_cnic_is_rejected_after_normalization(self):
        self.client.post("/users", data=self.account_data())
        response = self.client.post("/users", data=self.account_data(
            name="Duplicate Staff",
            email="duplicate@example.com",
            cnic="4210112345678",
        ))
        self.assertEqual(200, response.status_code)
        self.assertIn(b"A staff account with that CNIC already exists.", response.data)
        self.assertIsNone(User.query.filter_by(email="duplicate@example.com").first())
        self.assertNotIn(b"4210112345678", response.data)

    def test_full_cnic_search_finds_account_without_exposing_number(self):
        self.client.post("/users", data=self.account_data())
        response = self.client.post("/users", data={
            "cnic": "4210112345678",
            "search_cnic": "1",
        })
        self.assertEqual(200, response.status_code)
        self.assertIn(b"new-staff@example.com", response.data)
        self.assertIn(b"*****-****567-8", response.data)
        self.assertNotIn(b"4210112345678", response.data)

    def test_create_user_command_requires_and_stores_cnic(self):
        runner = self.app.test_cli_runner()
        invalid_answers = iter([
            "CLI Staff",
            "cli@example.com",
            "Finance Department",
            "invalid",
            "creator",
        ])
        with patch("builtins.input", side_effect=lambda _prompt="": next(invalid_answers)):
            invalid_result = runner.invoke(args=["create-user"])
        self.assertNotEqual(0, invalid_result.exit_code)
        self.assertIn("valid 13-digit CNIC", invalid_result.output)
        self.assertIsNone(User.query.filter_by(email="cli@example.com").first())

        answers = iter([
            "CLI Staff",
            "cli@example.com",
            "Finance Department",
            "42101-1234567-8",
            "creator",
        ])
        with patch("builtins.input", side_effect=lambda _prompt="": next(answers)), patch(
            "getpass.getpass", return_value="another-long-password"
        ):
            result = runner.invoke(args=["create-user"])
        self.assertEqual(0, result.exit_code, result.output)
        user = User.query.filter_by(email="cli@example.com").one()
        self.assertEqual("5678", user.cnic_last4)
