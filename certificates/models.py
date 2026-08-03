import uuid
import re
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


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

    @classmethod
    def resolve_lookup(cls, lookup_value):
        if not lookup_value:
            return None

        normalized = str(lookup_value).strip()
        if not normalized:
            return None

        try:
            uuid.UUID(normalized)
            certificate = cls.objects.filter(certificate_id=normalized).first()
            if certificate:
                return certificate
        except (ValueError, TypeError):
            pass

        return cls.objects.filter(verification_id=normalized).first()

    @property
    def status_label(self):
        return {
            self.STATUS_PENDING: 'Pending',
            self.STATUS_STAFF: 'Approved',
            self.STATUS_VERIFIED: 'Verified',
            self.STATUS_REJECTED: 'Rejected',
        }.get(self.status, 'Pending')

    @property
    def status_badge_class(self):
        return {
            self.STATUS_PENDING: 'badge-pending',
            self.STATUS_STAFF: 'badge-approved',
            self.STATUS_VERIFIED: 'badge-approved',
            self.STATUS_REJECTED: 'badge-rejected',
        }.get(self.status, 'badge-pending')

    @property
    def blockchain_anchored(self):
        return self.status == self.STATUS_VERIFIED

    @property
    def blockchain_label(self):
        return 'Anchored' if self.blockchain_anchored else 'Not Anchored'

    @property
    def blockchain_badge_class(self):
        return 'badge-blockchain' if self.blockchain_anchored else 'badge-warning'

    @property
    def transaction_log(self):
        return TransactionLog.objects.filter(
            certificate_hash=self.certificate_hash
        ).first()

    def timeline_steps(self):
        tx_log = self.transaction_log

        if self.status == self.STATUS_REJECTED:
            return [
                {
                    'label': 'Credential Registered',
                    'state': 'completed',
                    'timestamp': self.created_at,
                },
                {
                    'label': 'Institution Review',
                    'state': 'blocked',
                    'timestamp': self.staff_approved_at,
                },
                {
                    'label': 'Rejected',
                    'state': 'completed',
                    'timestamp': self.verified_at or self.staff_approved_at or self.created_at,
                },
                {
                    'label': 'SHA-256 Generated',
                    'state': 'blocked',
                    'timestamp': None,
                },
                {
                    'label': 'Recorded on Ethereum',
                    'state': 'blocked',
                    'timestamp': None,
                },
                {
                    'label': 'Verification Receipt Generated',
                    'state': 'blocked',
                    'timestamp': None,
                },
            ]

        approved = self.status in {self.STATUS_STAFF, self.STATUS_VERIFIED}
        verified = self.status == self.STATUS_VERIFIED

        return [
            {
                'label': 'Credential Registered',
                'state': 'completed' if self.created_at else 'upcoming',
                'timestamp': self.created_at,
            },
            {
                'label': 'Institution Approved',
                'state': 'completed' if approved else 'current' if self.status == self.STATUS_PENDING else 'blocked',
                'timestamp': self.staff_approved_at,
            },
            {
                'label': 'SHA-256 Generated',
                'state': 'completed' if verified else 'upcoming',
                'timestamp': self.verified_at if verified else None,
            },
            {
                'label': 'Recorded on Ethereum',
                'state': 'completed' if verified else 'upcoming',
                'timestamp': tx_log.timestamp if tx_log else None,
            },
            {
                'label': 'Verification Receipt Generated',
                'state': 'completed' if verified else 'upcoming',
                'timestamp': self.verified_at if verified else None,
            },
        ]

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


class TransactionLog(models.Model):
    certificate_hash = models.CharField(max_length=64)
    tx_hash          = models.CharField(max_length=255)
    blockchain       = models.CharField(max_length=100)
    timestamp        = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.blockchain} — {self.tx_hash}"