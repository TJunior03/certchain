from django.contrib import admin
from .models import Certificate, TransactionLog


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ['certificate_id', 'student_name', 'course_name', 'issue_date', 'issuer', 'created_at']
    search_fields = ['student_name', 'course_name', 'certificate_hash']
    readonly_fields = ['certificate_id', 'certificate_hash', 'created_at']


@admin.register(TransactionLog)
class TransactionLogAdmin(admin.ModelAdmin):
    list_display = ['certificate_hash', 'tx_hash', 'blockchain', 'timestamp']
    readonly_fields = ['timestamp']