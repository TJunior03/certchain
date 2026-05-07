import hashlib


def generate_certificate_hash(student_name, course_name, issue_date):
    """
    Generate a SHA-256 hash from certificate data.
    This hash is the tamper-proof fingerprint of the certificate.
    Any change in the data will produce a completely different hash.
    """
    data = f"{student_name}-{course_name}-{issue_date}"
    return hashlib.sha256(data.encode()).hexdigest()


def verify_certificate_hash(student_name, course_name, issue_date, stored_hash):
    """
    Recompute the hash from submitted data and compare
    it against the stored hash in the database.
    Returns True if valid, False if tampered or invalid.
    """
    computed_hash = generate_certificate_hash(student_name, course_name, issue_date)
    return computed_hash == stored_hash