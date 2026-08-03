from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Certificate, TransactionLog, generate_verification_id


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


class VerifyCertificateViewTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(
			username='issuer',
			email='issuer@example.com',
			password='password123',
		)

	def test_verify_view_accepts_verification_id_lookup(self):
		cert = Certificate.objects.create(
			student_name='Verified Student',
			course_name='Blockchain Security',
			issue_date=date(2026, 8, 1),
			issuer=self.user,
			status=Certificate.STATUS_VERIFIED,
			verification_id='VR-2026-000013',
			certificate_hash='a' * 64,
		)

		response = self.client.post(reverse('verify_certificate'), {
			'certificate_id': cert.verification_id,
		})

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'CREDENTIAL VERIFIED')
		self.assertContains(response, cert.verification_id)

	def test_pending_certificate_remains_unanchored_and_pending(self):
		cert = Certificate.objects.create(
			student_name='Pending Student',
			course_name='Blockchain Security',
			issue_date=date(2026, 8, 1),
			issuer=self.user,
			status=Certificate.STATUS_PENDING,
			verification_id='VR-2026-000014',
		)

		response = self.client.post(reverse('verify_certificate'), {
			'certificate_id': cert.verification_id,
		})

		self.assertEqual(response.status_code, 200)
		self.assertFalse(response.context['result'])
		self.assertFalse(response.context['certificate'].blockchain_anchored)
		self.assertContains(response, 'CREDENTIAL PENDING')
		self.assertContains(response, 'pending institutional approval')

	def test_verified_certificate_downloads_receipt_and_reports_anchored(self):
		cert = Certificate.objects.create(
			student_name='Verified Student',
			course_name='Blockchain Security',
			issue_date=date(2026, 8, 1),
			issuer=self.user,
			status=Certificate.STATUS_VERIFIED,
			verification_id='VR-2026-000015',
			certificate_hash='b' * 64,
		)
		TransactionLog.objects.create(
			certificate_hash=cert.certificate_hash,
			tx_hash='c' * 64,
			blockchain='Ethereum',
		)

		view_url = reverse('verify_certificate_detail', args=[cert.certificate_id])
		response = self.client.get(view_url, {'download': 'true'})

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response['Content-Type'], 'application/pdf')
		self.assertTrue(cert.blockchain_anchored)

	def test_rejected_certificate_reports_rejected_and_unanchored(self):
		cert = Certificate.objects.create(
			student_name='Rejected Student',
			course_name='Blockchain Security',
			issue_date=date(2026, 8, 1),
			issuer=self.user,
			status=Certificate.STATUS_REJECTED,
			verification_id='VR-2026-000016',
			rejection_reason='Document mismatch',
		)

		response = self.client.post(reverse('verify_certificate'), {
			'certificate_id': cert.verification_id,
		})

		self.assertEqual(response.status_code, 200)
		self.assertFalse(response.context['result'])
		self.assertFalse(response.context['certificate'].blockchain_anchored)
		self.assertContains(response, 'CREDENTIAL REJECTED')
		self.assertContains(response, 'rejected by the institution')
