from django.shortcuts import get_object_or_404, render
from .forms import CertificateForm
from .models import Certificate, TransactionLog
from .utils import approve_certificate_workflow
from django.contrib.auth.decorators import login_required
from django.utils import timezone

def home(request):
    return render(request, 'certificates/home.html')


def issue_certificate(request):
    if request.method == 'POST':
        form = CertificateForm(request.POST, request.FILES)

        if form.is_valid():
            certificate = form.save(commit=False)
            certificate.status = Certificate.STATUS_PENDING

            if request.user.is_authenticated:
                certificate.issuer = request.user

            certificate.save()

            return render(request, 'certificates/issue_certificate.html', {
                'form': CertificateForm(),
                'success': True,
                'certificate': certificate
            })

        else:
            return render(request, 'certificates/issue_certificate.html', {
                'form': form,
                'error': 'Please fix the errors below.'
            })

    else:
        form = CertificateForm()

    return render(request, 'certificates/issue_certificate.html', {'form': form})


def verify_certificate(request, certificate_id=None):
    result = None
    certificate = None
    blockchain_info = None
    message = None

    lookup_certificate_id = None
    if certificate_id:
        lookup_certificate_id = str(certificate_id)
    elif request.method == 'POST':
        lookup_certificate_id = request.POST.get('certificate_id', '').strip()

    if lookup_certificate_id:
        try:
            certificate = Certificate.objects.get(certificate_id=lookup_certificate_id)
            if certificate.status == Certificate.STATUS_VERIFIED:
                result = True

                tx_log = TransactionLog.objects.filter(
                    certificate_hash=certificate.certificate_hash
                ).first()

                if tx_log:
                    blockchain_info = {
                        'tx_hash'  : tx_log.tx_hash,
                        'blockchain': tx_log.blockchain,
                        'timestamp': tx_log.timestamp
                    }
            else:
                result = False
                message = (
                    'Certificate record found, but verification is not approved yet.'
                    if certificate.status == Certificate.STATUS_PENDING
                    else 'This certificate request was rejected by the institution.'
                )

        except Certificate.DoesNotExist:
            result = False
            message = 'Certificate ID not found in the system.'

    return render(request, 'certificates/verify_certificate.html', {
        'result'         : result,
        'certificate'    : certificate,
        'blockchain_info': blockchain_info,
        'message'        : message,
    })

@login_required
def dashboard_home(request):
    total_certificates = Certificate.objects.count()
    issued_by_me = Certificate.objects.filter(issuer=request.user).count()
    pending_count = Certificate.objects.filter(status=Certificate.STATUS_PENDING).count()
    staff_count = Certificate.objects.filter(status=Certificate.STATUS_STAFF).count()
    verified_count = Certificate.objects.filter(status=Certificate.STATUS_VERIFIED).count()
    rejected_count = Certificate.objects.filter(status=Certificate.STATUS_REJECTED).count()

    anchored_hashes = TransactionLog.objects.values_list('certificate_hash', flat=True)
    blockchain_anchored = Certificate.objects.filter(
        certificate_hash__in=anchored_hashes,
        status=Certificate.STATUS_VERIFIED,
    ).count()
    not_anchored = total_certificates - blockchain_anchored
    recent_certificates = list(Certificate.objects.all().order_by('-created_at')[:5])

    return render(request, 'certificates/dashboard_home.html', {
        'total_certificates': total_certificates,
        'issued_by_me': issued_by_me,
        'pending_count': pending_count,
        'staff_count': staff_count,
        'verified_count': verified_count,
        'rejected_count': rejected_count,
        'blockchain_anchored': blockchain_anchored,
        'not_anchored': not_anchored,
        'recent_certificates': recent_certificates,
    })


@login_required
def dashboard_certificates(request):
    certificates = Certificate.objects.all().order_by('-created_at')
    return render(request, 'certificates/dashboard_certificates.html', {
        'certificates': certificates,
    })
@login_required
def dashboard_blockchain(request):
    logs = TransactionLog.objects.all().order_by('-timestamp')
    return render(request, 'certificates/dashboard_blockchain.html', {
        'logs': logs
    })

@login_required
def dashboard_issue(request):
    if request.method == 'POST':
        form = CertificateForm(request.POST, request.FILES)

        if form.is_valid():
            certificate = form.save(commit=False)
            certificate.status = Certificate.STATUS_PENDING
            certificate.issuer = request.user
            certificate.save()

            return render(request, 'certificates/dashboard_issue.html', {
                'form'       : CertificateForm(),
                'success'    : True,
                'certificate': certificate,
            })
        return render(request, 'certificates/dashboard_issue.html', {
            'form': form,
            'error': 'Please fix the errors below.'
        })
        
    else:
        form = CertificateForm()

    return render(request, 'certificates/dashboard_issue.html', {'form': form})

@login_required
def dashboard_requests(request):
    """
    Shows all pending verification requests for staff review.
    """
    pending    = Certificate.objects.filter(status=Certificate.STATUS_PENDING).order_by('-created_at')
    staff_done = Certificate.objects.filter(status=Certificate.STATUS_STAFF).order_by('-created_at')
    verified   = Certificate.objects.filter(status=Certificate.STATUS_VERIFIED).order_by('-created_at')
    rejected   = Certificate.objects.filter(status=Certificate.STATUS_REJECTED).order_by('-created_at')

    return render(request, 'certificates/dashboard_requests.html', {
        'pending'   : pending,
        'staff_done': staff_done,
        'verified'  : verified,
        'rejected'  : rejected,
        'pending_count'   : pending.count(),
        'staff_done_count': staff_done.count(),
        'verified_count'  : verified.count(),
        'rejected_count'  : rejected.count(),
    })


@login_required
def dashboard_request_detail(request, certificate_id):
    """
    Single request detail page — staff can approve or reject here.
    """
    cert = get_object_or_404(Certificate, certificate_id=certificate_id)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'staff_approve' and cert.status == Certificate.STATUS_PENDING:
            cert.status           = Certificate.STATUS_STAFF
            cert.staff_approver   = request.user
            cert.staff_approved_at = timezone.now()
            cert.save(update_fields=['status', 'staff_approver', 'staff_approved_at'])
            return render(request, 'certificates/dashboard_request_detail.html', {
                'cert'   : cert,
                'success': 'Request approved by staff. Awaiting admin final approval.'
            })

        elif action == 'admin_approve' and cert.status == Certificate.STATUS_STAFF:
            cert.admin_approver = request.user
            cert.verified_at = timezone.now()
            cert.save(update_fields=['admin_approver', 'verified_at'])
            outcome = approve_certificate_workflow(cert, acting_user=request.user)
            if outcome['success']:
                return render(request, 'certificates/dashboard_request_detail.html', {
                    'cert'   : cert,
                    'success': f"Certificate verified and anchored on blockchain. "
                               f"{'Email sent.' if outcome['email_sent'] else 'Email not sent.'}"
                })
            else:
                return render(request, 'certificates/dashboard_request_detail.html', {
                    'cert' : cert,
                    'error': outcome.get('error', 'Verification failed.')
                })

        elif action == 'reject':
            reason = request.POST.get('rejection_reason', 'No reason provided.')
            cert.status           = Certificate.STATUS_REJECTED
            cert.rejection_reason = reason
            cert.save()
            return render(request, 'certificates/dashboard_request_detail.html', {
                'cert'   : cert,
                'success': 'Request rejected.'
            })

    tx_log = TransactionLog.objects.filter(
        certificate_hash=cert.certificate_hash
    ).first()

    return render(request, 'certificates/dashboard_request_detail.html', {
        'cert'  : cert,
        'tx_log': tx_log,
    })