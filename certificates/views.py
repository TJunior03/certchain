from django.shortcuts import render, redirect
from .forms import CertificateForm
from .models import Certificate
from .utils import generate_certificate_hash
from .forms import VerifyCertificateForm
from .utils import verify_certificate_hash

def home(request):

    return render(request, 'certificates/home.html')

def issue_certificate(request):

    if request.method == 'POST':

        form = CertificateForm(request.POST)

        if form.is_valid():

            certificate = form.save(commit=False)

            # Generate SHA-256 hash
            cert_hash = generate_certificate_hash(
                certificate.student_name,
                certificate.course_name,
                certificate.issue_date
            )

            certificate.certificate_hash = cert_hash

            # Save issuer (logged-in admin)
            if request.user.is_authenticated:
                certificate.issuer = request.user

            # Save to database
            certificate.save()

            return redirect('issue_certificate')

    else:
        form = CertificateForm()

    return render(request, 'certificates/issue_certificate.html', {
        'form': form
    })

def verify_certificate(request):

    result = None

    if request.method == 'POST':

        form = VerifyCertificateForm(request.POST)

        if form.is_valid():

            student_name = form.cleaned_data['student_name']
            course_name = form.cleaned_data['course_name']
            issue_date = form.cleaned_data['issue_date']

            try:

                # Find certificate in database
                certificate = Certificate.objects.filter(
                    student_name=student_name,
                    course_name=course_name,
                    issue_date=issue_date
                ).latest('created_at')

                # Verify hash
                is_valid = verify_certificate_hash(
                    student_name,
                    course_name,
                    issue_date,
                    certificate.certificate_hash
                )

                if is_valid:
                    result = "VALID CERTIFICATE ✅"
                else:
                    result = "INVALID CERTIFICATE ❌"

            except Certificate.DoesNotExist:

                result = "CERTIFICATE NOT FOUND ❌"

    else:
        form = VerifyCertificateForm()

    return render(request, 'certificates/verify_certificate.html', {
        'form': form,
        'result': result
    })