import uuid
import re
from django.db import models
from django.contrib.auth.models import User


VERIFICATION_ID_PATTERN = re.compile(r'^VR-(\d{4})-(\d{6})$')


def generate_verification_id():
    """Generate human-readable verification ID like VR-2026-000041"""
    from django.utils import timezone
    year = timezone.now().year
    prefix = f"VR-{year}-"

    highest_sequence = 0
    for verification_id in Certificate.objects.filter(
        verification_id__startswith=prefix
    ).values_list('verification_id', flat=True):
        if not verification_id:
            continue

        match = VERIFICATION_ID_PATTERN.match(verification_id)
        if match and int(match.group(1)) == year:
            highest_sequence = max(highest_sequence, int(match.group(2)))

    return f"VR-{year}-{highest_sequence + 1:06d}"


class Certificate(models.Model):
    STATUS_PENDING  = 'pending'
    STATUS_STAFF    = 'staff_approved'
    STATUS_VERIFIED = 'verified'
    STATUS_REJECTED = 'rejected'

    STATUS_CHOICES = [
        (STATUS_PENDING,  'Pending Review'),
        (STATUS_STAFF,    'Staff Approved'),
        (STATUS_VERIFIED, 'Verified'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    # Core identification
    certificate_id      = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    verification_id     = models.CharField(max_length=20, unique=True, null=True, blank=True)

    # Student info
    student_name        = models.CharField(max_length=255)
    student_email       = models.EmailField(null=True, blank=True)

    # Credential details
    course_name         = models.CharField(max_length=255)
    certificate_type    = models.CharField(max_length=100, default='Academic Certificate')
    original_issuer     = models.CharField(max_length=255, default='Institution')
    issue_date          = models.DateField()

    # Verification
    certificate_hash    = models.CharField(max_length=64, unique=True, null=True, blank=True)
    status              = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    rejection_reason    = models.TextField(null=True, blank=True)

    # Files
    pdf_file            = models.FileField(upload_to='certificates/', null=True, blank=True)

    # Workflow tracking
    issuer              = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                            related_name='issued_certificates')
    staff_approver      = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                            related_name='staff_approved_certificates')
    admin_approver      = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                            related_name='admin_approved_certificates')

    # Timestamps
    created_at          = models.DateTimeField(auto_now_add=True)
    staff_approved_at   = models.DateTimeField(null=True, blank=True)
    verified_at         = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        update_fields = kwargs.get('update_fields')
        if not self.verification_id:
            self.verification_id = generate_verification_id()
            if update_fields is not None:
                kwargs['update_fields'] = set(update_fields) | {'verification_id'}
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.verification_id} — {self.student_name}"

    @property
    def is_pending(self):
        return self.status == self.STATUS_PENDING

    @property
    def is_staff_approved(self):
        return self.status == self.STATUS_STAFF

    @property
    def is_verified(self):
        return self.status == self.STATUS_VERIFIED

    @property
    def is_rejected(self):
        return self.status == self.STATUS_REJECTED

    @property
    def blockchain_anchored(self):
        return TransactionLog.objects.filter(
            certificate_hash=self.certificate_hash
        ).exists()


class TransactionLog(models.Model):
    certificate_hash = models.CharField(max_length=64)
    tx_hash          = models.CharField(max_length=255)
    blockchain       = models.CharField(max_length=100)
    timestamp        = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.blockchain} — {self.tx_hash}"