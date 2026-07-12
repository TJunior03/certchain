import uuid
from django.db import models
from django.contrib.auth.models import User


class Certificate(models.Model):
    certificate_id   = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    student_name     = models.CharField(max_length=255)
    student_email    = models.EmailField(null=True, blank=True)
    course_name      = models.CharField(max_length=255)
    issue_date       = models.DateField()
    certificate_hash = models.CharField(max_length=64, unique=True)
    pdf_file         = models.FileField(upload_to='certificates/', null=True, blank=True)
    issuer           = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at       = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student_name} — {self.course_name}"


class TransactionLog(models.Model):
    certificate_hash = models.CharField(max_length=64)
    tx_hash          = models.CharField(max_length=255)
    blockchain       = models.CharField(max_length=100)
    timestamp        = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.blockchain} — {self.tx_hash}"