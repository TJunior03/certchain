from django.contrib import admin
from django.contrib import messages
from .models import Certificate, TransactionLog
from .utils import approve_certificate_workflow


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ['certificate_id', 'student_name', 'course_name', 'status', 'issue_date', 'issuer', 'created_at']
    search_fields = ['student_name', 'course_name', 'certificate_hash']
    readonly_fields = ['certificate_id', 'certificate_hash', 'created_at']
    list_filter = ['status', 'issue_date', 'created_at']
    actions = ['approve_selected', 'reject_selected']

    @admin.action(description='Approve selected certificates')
    def approve_selected(self, request, queryset):
        approved = 0
        failed = 0

        for certificate in queryset:
            result = approve_certificate_workflow(certificate, acting_user=request.user)
            if result['success']:
                approved += 1
            else:
                failed += 1

        if approved:
            self.message_user(request, f'{approved} certificate(s) approved successfully.')
        if failed:
            self.message_user(request, f'{failed} certificate(s) could not be approved.', level=messages.WARNING)

    @admin.action(description='Reject selected certificates')
    def reject_selected(self, request, queryset):
        updated = queryset.update(status=Certificate.STATUS_REJECTED)
        self.message_user(request, f'{updated} certificate(s) marked as rejected.')


@admin.register(TransactionLog)
class TransactionLogAdmin(admin.ModelAdmin):
    list_display = ['certificate_hash', 'tx_hash', 'blockchain', 'timestamp']
    readonly_fields = ['timestamp']