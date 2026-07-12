import hashlib
import PyPDF2
from django.core.mail import send_mail
from django.conf import settings


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
    """
    Send certificate credentials to the student via email.
    """
    if not certificate.student_email:
        return False

    subject = f"Your Certificate — {certificate.course_name}"

    message = f"""
Dear {certificate.student_name},

Congratulations! Your certificate has been officially issued
and permanently recorded on the Ethereum blockchain.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CERTIFICATE DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Student  : {certificate.student_name}
Course   : {certificate.course_name}
Date     : {certificate.issue_date}
Issued by: {certificate.issuer}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
YOUR VERIFICATION CREDENTIALS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Certificate ID:
{certificate.certificate_id}

SHA-256 Hash:
{certificate.certificate_hash}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BLOCKCHAIN RECORD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Transaction Hash:
{tx_hash}
Network: Ethereum (Ganache Local)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

To verify your certificate, visit:
http://localhost/verify/

Enter your Certificate ID to instantly verify authenticity.

Keep this email safe — it contains your permanent
blockchain proof of certification.

— CertChain Certification System
    """

    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [certificate.student_email],
            fail_silently=False
        )
        return True
    except Exception as e:
        return False