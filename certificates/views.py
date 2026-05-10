from django.shortcuts import render
from .forms import CertificateForm
from .models import Certificate
from .utils import generate_certificate_hash, generate_pdf_hash, verify_certificate_hash


def home(request):
    return render(request, 'certificates/home.html')


def issue_certificate(request):
    if request.method == 'POST':
        form = CertificateForm(request.POST, request.FILES)

        if form.is_valid():
            certificate = form.save(commit=False)

            # Generate hash — from PDF if uploaded, otherwise from text fields
            if request.FILES.get('pdf_file'):
                cert_hash = generate_pdf_hash(request.FILES['pdf_file'])
            else:
                cert_hash = generate_certificate_hash(
                    certificate.student_name,
                    certificate.course_name,
                    certificate.issue_date
                )

            # Check for duplicate
            if Certificate.objects.filter(certificate_hash=cert_hash).exists():
                return render(request, 'certificates/issue_certificate.html', {
                    'form': form,
                    'error': 'This certificate already exists in the system.'
                })

            certificate.certificate_hash = cert_hash

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


def verify_certificate(request):
    result = None
    certificate = None

    if request.method == 'POST':
        certificate_id = request.POST.get('certificate_id', '').strip()

        try:
            certificate = Certificate.objects.get(certificate_id=certificate_id)
            result = True
        except Certificate.DoesNotExist:
            result = False

    return render(request, 'certificates/verify_certificate.html', {
        'result': result,
        'certificate': certificate
    })