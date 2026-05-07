from django.shortcuts import render, redirect
from .forms import CertificateForm
from .models import Certificate
from .utils import generate_certificate_hash


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