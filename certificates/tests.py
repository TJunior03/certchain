from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase

from .models import Certificate, generate_verification_id


class CertificateVerificationIdTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(
			username='issuer',
			email='issuer@example.com',
			password='password123',
		)

	def test_generate_verification_id_uses_highest_existing_sequence(self):
		Certificate.objects.create(
			student_name='Existing One',
			course_name='Course A',
			issue_date=date(2026, 1, 1),
			issuer=self.user,
			verification_id='VR-2026-000010',
		)
		Certificate.objects.create(
			student_name='Existing Two',
			course_name='Course B',
			issue_date=date(2026, 1, 2),
			issuer=self.user,
			verification_id='VR-2026-000011',
		)

		self.assertEqual(generate_verification_id(), 'VR-2026-000012')

	def test_save_assigns_unique_verification_id_when_missing(self):
		Certificate.objects.create(
			student_name='Existing One',
			course_name='Course A',
			issue_date=date(2026, 1, 1),
			issuer=self.user,
			verification_id='VR-2026-000010',
		)
		Certificate.objects.create(
			student_name='Existing Two',
			course_name='Course B',
			issue_date=date(2026, 1, 2),
			issuer=self.user,
			verification_id='VR-2026-000011',
		)

		cert = Certificate.objects.create(
			student_name='Needs ID',
			course_name='Course C',
			issue_date=date(2026, 1, 3),
			issuer=self.user,
		)

		self.assertEqual(cert.verification_id, 'VR-2026-000012')

	def test_save_with_update_fields_persists_generated_verification_id(self):
		Certificate.objects.create(
			student_name='Existing One',
			course_name='Course A',
			issue_date=date(2026, 1, 1),
			issuer=self.user,
			verification_id='VR-2026-000010',
		)

		cert = Certificate.objects.create(
			student_name='Legacy Blank',
			course_name='Course D',
			issue_date=date(2026, 1, 4),
			issuer=self.user,
			verification_id='VR-2026-000011',
		)

		Certificate.objects.filter(pk=cert.pk).update(verification_id=None)
		cert.refresh_from_db()

		cert.status = Certificate.STATUS_REJECTED
		cert.save(update_fields=['status'])

		cert.refresh_from_db()
		self.assertEqual(cert.verification_id, 'VR-2026-000011')
