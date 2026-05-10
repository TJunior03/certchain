from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from .models import Certificate
from .serializers import (
    CertificateSerializer,
    CertificateIssueSerializer,
    VerifyResponseSerializer
)
from .utils import generate_certificate_hash, generate_pdf_hash


class CertificateIssueAPIView(APIView):
    """
    POST /api/certificates/
    Issue a new certificate and generate its SHA-256 hash.
    Requires authentication.
    """
    permission_classes = [IsAuthenticated]
    parser_classes     = [MultiPartParser, FormParser, JSONParser]

    def post(self, request):
        serializer = CertificateIssueSerializer(data=request.data)

        if serializer.is_valid():
            student_name = serializer.validated_data['student_name']
            course_name  = serializer.validated_data['course_name']
            issue_date   = serializer.validated_data['issue_date']
            pdf_file     = serializer.validated_data.get('pdf_file', None)

            # Generate hash from PDF or text fields
            if pdf_file:
                cert_hash = generate_pdf_hash(pdf_file)
            else:
                cert_hash = generate_certificate_hash(
                    student_name, course_name, str(issue_date)
                )

            # Check for duplicate
            if Certificate.objects.filter(certificate_hash=cert_hash).exists():
                return Response(
                    {'error': 'This certificate already exists in the system.'},
                    status=status.HTTP_409_CONFLICT
                )

            # Save to database
            certificate = Certificate.objects.create(
                student_name=student_name,
                course_name=course_name,
                issue_date=issue_date,
                certificate_hash=cert_hash,
                pdf_file=pdf_file,
                issuer=request.user
            )

            return Response(
                CertificateSerializer(certificate).data,
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CertificateVerifyAPIView(APIView):
    """
    POST /api/verify/
    Verify a certificate by its UUID.
    Open to anyone — no authentication required.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        certificate_id = request.data.get('certificate_id', '').strip()

        if not certificate_id:
            return Response(
                {'error': 'certificate_id is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            certificate = Certificate.objects.get(certificate_id=certificate_id)
            return Response({
                'valid'           : True,
                'message'         : 'Certificate is valid.',
                'certificate_id'  : str(certificate.certificate_id),
                'student_name'    : certificate.student_name,
                'course_name'     : certificate.course_name,
                'issue_date'      : str(certificate.issue_date),
                'certificate_hash': certificate.certificate_hash,
            }, status=status.HTTP_200_OK)

        except Certificate.DoesNotExist:
            return Response({
                'valid'  : False,
                'message': 'Certificate not found — invalid or tampered.',
            }, status=status.HTTP_404_NOT_FOUND)


class CertificateListAPIView(APIView):
    """
    GET /api/certificates/
    List all certificates.
    Requires authentication.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        certificates = Certificate.objects.all().order_by('-created_at')
        serializer   = CertificateSerializer(certificates, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)