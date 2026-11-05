import tempfile
import unittest
from datetime import date
from pathlib import Path

import pymupdf

from app.pdf_generator import generate_official_sindh_pdf


LONG_DRAFT = """GOVERNMENT OF SINDH
ENERGY DEPARTMENT

Karachi, dated the 5th November, 2026

NOTIFICATION

No. SO(G)/ENERGY/SOLAR/2026-001: In partial modification of this department's earlier notification of even number and in order to ensure seamless execution, transparency, and timely delivery of renewable energy initiatives across the province, the Competent Authority is pleased to reconstitute the Review Committee comprising the following members with immediate effect:

1. Secretary, Energy Department, Government of Sindh - Convener
2. Additional Secretary (Development), Energy Department - Member
3. Chief Engineer (Alternative Energy), Energy Department - Member
4. Representative of Planning & Development Department (BS-19/Above) - Member
5. Director (Alternate Energy / Alternative & Renewable), Energy - Member
6. Deputy Secretary (Technical), Energy Department - Secretary

2. The Terms of Reference (ToRs) and responsibilities of the reconstituted Committee shall be as under:
(i) To comprehensively review the physical and financial progress of all ongoing solar energy projects across various districts of Sindh;
(ii) To identify bottlenecks, administrative delays, or technical constraints hindering project execution and recommend immediate corrective measures;
(iii) To closely monitor the procurement, installation, and grid-integration milestones of solar electrification schemes;
(iv) To coordinate with relevant federal, provincial, and private stakeholders to streamline funding and operational approvals;
(v) To propose a revised, realistic timeline and milestone chart for the timely completion of all pending and ongoing works.

3. The Committee shall conduct fortnightly review meetings and submit a comprehensive progress report along with actionable recommendations to the Competent Authority within forty-five (45) days of the issuance of this Notification.

4. This Notification shall supersede all previous notifications issued in this regard and shall come into force with immediate effect.

SECRETARY
Energy Department
Government of Sindh"""


class PdfGeneratorTests(unittest.TestCase):
    def generate_pdf(self, body):
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        destination = Path(temporary_directory.name) / "notification.pdf"
        generate_official_sindh_pdf(
            reference="SGNIA-2026-TEST1234",
            title="Solar energy review committee",
            category="Notification",
            department="Energy Department",
            subject="Constitution of a Committee to Review Solar Energy Projects",
            body=body,
            document_date=date(2026, 11, 5),
            official_reference=None,
            destination_path=destination,
        )
        return pymupdf.open(destination)

    def test_long_draft_is_paginated_without_losing_body_text(self):
        document = self.generate_pdf(LONG_DRAFT)
        self.addCleanup(document.close)

        self.assertGreater(document.page_count, 1)
        text = " ".join(page.get_text() for page in document)
        normalized_text = " ".join(text.split())
        for expected in (
            "Karachi, dated the 5th November, 2026",
            "SO(G)/ENERGY/SOLAR/2026-001",
            "reconstitute the Review Committee",
            "fortnightly review meetings",
            "forty-five (45) days",
            "shall come into force with immediate effect",
            "SECRETARY",
            "Government of Sindh",
            "(continued)",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, normalized_text)

    def test_short_draft_stays_on_one_page(self):
        document = self.generate_pdf("The committee shall meet monthly.")
        self.addCleanup(document.close)

        self.assertEqual(document.page_count, 1)
        self.assertIn("The committee shall meet monthly.", document[0].get_text())

    def test_saved_draft_pdf_can_be_regenerated_without_changing_published_pdf(self):
        from app import create_app
        from app.extensions import db
        from app.models import Notification, NotificationVersion, User

        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        app = create_app({
            "TESTING": True,
            "SECRET_KEY": "test-key",
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
            "WTF_CSRF_ENABLED": False,
            "NOTIFICATION_UPLOAD_DIR": temporary_directory.name,
            "SIGNING_KEY_DIR": str(Path(temporary_directory.name) / "signing-keys"),
        })
        context = app.app_context()
        context.push()
        self.addCleanup(context.pop)
        db.create_all()
        self.addCleanup(db.drop_all)
        self.addCleanup(db.session.remove)

        creator = User(
            name="Draft Creator",
            email="creator@example.com",
            role="creator",
            department="Energy Department",
        )
        creator.set_password("a-long-test-password")
        notification = Notification(
            reference="SGNIA-2026-REGEN001",
            title="Published solar notice",
            category="Notification",
            department=creator.department,
            subject="Published solar subject",
            body="Published body",
            document_date=date(2026, 11, 5),
            pdf_path="published.pdf",
            pdf_sha256="published-hash",
            status="Published",
            created_by=creator,
        )
        db.session.add_all([creator, notification])
        db.session.flush()
        published_version = NotificationVersion(
            notification=notification,
            version_number=1,
            title=notification.title,
            category=notification.category,
            department=notification.department,
            subject=notification.subject,
            body=notification.body,
            document_date=notification.document_date,
            pdf_path=notification.pdf_path,
            pdf_sha256=notification.pdf_sha256,
            status="Published",
            created_by_id=creator.id,
        )
        draft = NotificationVersion(
            notification=notification,
            version_number=2,
            title="Solar review amendment",
            category="Notification",
            department=creator.department,
            subject="Review ongoing solar projects",
            body="The committee shall review solar projects and submit actionable recommendations. " * 60,
            document_date=date(2026, 11, 5),
            pdf_path="old-draft.pdf",
            status="Draft",
            created_by_id=creator.id,
        )
        db.session.add_all([published_version, draft])
        db.session.commit()

        old_pdf = Path(temporary_directory.name) / draft.pdf_path
        old_pdf.write_bytes(b"Old generated draft PDF")
        client = app.test_client()
        client.post("/login", data={
            "email": creator.email,
            "password": "a-long-test-password",
        })
        rejected_response = client.post(
            f"/notifications/{notification.id}/versions/{published_version.id}/regenerate-pdf",
        )
        self.assertEqual(400, rejected_response.status_code)
        self.assertEqual("published.pdf", notification.pdf_path)

        response = client.post(
            f"/notifications/{notification.id}/versions/{draft.id}/regenerate-pdf",
            follow_redirects=True,
        )

        self.assertEqual(200, response.status_code)
        db.session.refresh(notification)
        db.session.refresh(draft)
        self.assertEqual("published.pdf", notification.pdf_path)
        self.assertEqual("published-hash", notification.pdf_sha256)
        self.assertNotEqual("old-draft.pdf", draft.pdf_path)
        self.assertFalse(old_pdf.exists())
        regenerated_pdf = Path(temporary_directory.name) / draft.pdf_path
        self.assertTrue(regenerated_pdf.is_file())
        with pymupdf.open(regenerated_pdf) as document:
            self.assertGreater(document.page_count, 1)
            text = " ".join(page.get_text() for page in document)
            self.assertIn("actionable recommendations", text)


if __name__ == "__main__":
    unittest.main()
