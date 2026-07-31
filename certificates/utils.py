import hashlib
import PyPDF2
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone


def generate_certificate_hash(student_name, course_name, issue_date):
    data = f"{student_name}-{course_name}-{issue_date}"
    return hashlib.sha256(data.encode()).hexdigest()


def generate_pdf_hash(pdf_file):
    sha256 = hashlib.sha256()
    pdf_file.seek(0)
    for chunk in iter(lambda: pdf_file.read(8192), b''):
        sha256.update(chunk)
    pdf_file.seek(0)
    return sha256.hexdigest()


def verify_certificate_hash(student_name, course_name, issue_date, stored_hash):
    computed_hash = generate_certificate_hash(student_name, course_name, str(issue_date))
    return computed_hash == stored_hash


def send_certificate_email(certificate, tx_hash):
    if not certificate.student_email:
        return False

    verification_url = f"http://13.204.65.237/verify/{certificate.certificate_id}/"
    verification_timestamp = timezone.now().strftime('%d %b %Y, %H:%M %Z')

    subject = (
        f"CertChain Blockchain Verification Receipt - {certificate.course_name}"
    )

    tx_hash_display = tx_hash if tx_hash and tx_hash != 'Blockchain unavailable' else 'Not available'

    body = f"""
Dear {certificate.student_name},

Your academic credential has been authenticated by the issuing institution.

CertChain has generated a SHA-256 fingerprint for the referenced credential and permanently stored it on the Ethereum blockchain.

Attached to this email is your official Blockchain Verification Receipt. This receipt confirms the credential authenticity status and blockchain verification record.

--------------------------------------------------
VERIFICATION SUMMARY
--------------------------------------------------
Verification Status : AUTHENTIC ✓
Certificate ID      : {certificate.certificate_id}
Verification System : CertChain
Blockchain Network  : Ethereum
Verification Timestamp : {verification_timestamp}
Transaction Hash    : {tx_hash_display}

Verification URL:
{verification_url}

Please retain this Blockchain Verification Receipt for your records. It may be shared with employers, universities, or other organizations that need independent proof of credential authenticity.

Note:
This receipt confirms the authenticity of the referenced academic credential. It does not replace the original certificate issued by the institution.

Thank you for using CertChain.

--------------------------------------------------
CertChain
Blockchain-Based Academic Credential Verification System
--------------------------------------------------
"""

    try:
        from django.core.mail import EmailMessage
        from django.conf import settings
        from .pdf_generator import generate_certificate_pdf

        # Generate Blockchain Verification Receipt
        pdf_buffer = generate_certificate_pdf(certificate, tx_hash)

        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=settings.EMAIL_HOST_USER,
            to=[certificate.student_email],
        )

        # Attach Verification Receipt
        email.attach(
            f"certchain_blockchain_verification_receipt_{certificate.certificate_id}.pdf",
            pdf_buffer.read(),
            "application/pdf",
        )

        email.send(fail_silently=False)
        return True

    except Exception as e:
        print(f"EMAIL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False