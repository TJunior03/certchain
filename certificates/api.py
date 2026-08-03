from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from .models import Certificate, TransactionLog
from .serializers import (
    CertificateSerializer,
    CertificateIssueSerializer,
    VerifyResponseSerializer
)
from .blockchain import verify_hash_on_blockchain


class CertificateIssueAPIView(APIView):
    """
    POST /api/issue/
    Issue a new certificate, generate SHA-256 hash,
    and anchor it to the blockchain.
    Requires authentication.
    """
    permission_classes = [IsAuthenticated]
    parser_classes     = [MultiPartParser, FormParser, JSONParser]

    def post(self, request):
        serializer = CertificateIssueSerializer(data=request.data)

        if serializer.is_valid():
            certificate = serializer.save(
                issuer=request.user,
                status=Certificate.STATUS_PENDING
            )

            response_data = CertificateSerializer(certificate).data
            response_data['message'] = (
                'Verification request submitted. Certificate is pending institutional approval.'
            )

            return Response(response_data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CertificateVerifyAPIView(APIView):
    """
    POST /api/verify/
    Verify a certificate by UUID or verification ID.
    Also returns blockchain record if available.
    Open to anyone.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        certificate_id = request.data.get('certificate_id', '').strip()

        if not certificate_id:
            return Response(
                {'error': 'certificate_id is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        certificate = Certificate.resolve_lookup(certificate_id)

        if certificate is None:
            return Response({
                'valid'  : False,
                'message': 'Certificate not found — invalid or tampered.',
            }, status=status.HTTP_404_NOT_FOUND)

        if certificate.status != Certificate.STATUS_VERIFIED:
            status_message = (
                'Certificate exists but is pending institutional approval.'
                if certificate.status == Certificate.STATUS_PENDING
                else 'Certificate has been approved and is awaiting blockchain anchoring.'
                if certificate.status == Certificate.STATUS_STAFF
                else 'Certificate request has been rejected by the institution.'
            )
            return Response({
                'valid': False,
                'message': status_message,
                'certificate_id': str(certificate.certificate_id),
                'verification_id': certificate.verification_id,
                'status': certificate.status,
                'status_label': certificate.status_label,
                'blockchain_anchored': certificate.blockchain_anchored,
            }, status=status.HTTP_200_OK)

        tx_log = certificate.transaction_log

        blockchain_data = None
        if tx_log:
            blockchain_data = {
                'tx_hash'   : tx_log.tx_hash,
                'blockchain': tx_log.blockchain,
                'timestamp' : str(tx_log.timestamp)
            }

        return Response({
            'valid'             : True,
            'message'           : 'Certificate is valid.',
            'certificate_id'    : str(certificate.certificate_id),
            'verification_id'   : certificate.verification_id,
            'student_name'      : certificate.student_name,
            'course_name'       : certificate.course_name,
            'issue_date'        : str(certificate.issue_date),
            'status'            : certificate.status,
            'status_label'      : certificate.status_label,
            'certificate_hash'  : certificate.certificate_hash,
            'blockchain_anchored': certificate.blockchain_anchored,
            'blockchain_record' : blockchain_data,
        }, status=status.HTTP_200_OK)


class CertificateListAPIView(APIView):
    """
    GET /api/certificates/
    List all certificates with blockchain status.
    Requires authentication.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        certificates = Certificate.objects.all().order_by('-created_at')
        data = []

        for cert in certificates:
            cert_data = CertificateSerializer(cert).data

            data.append(cert_data)

        return Response(data, status=status.HTTP_200_OK)


class BlockchainVerifyAPIView(APIView):
    """
    GET /api/blockchain/verify/<str:certificate_hash>/
    Verify a certificate hash directly on the blockchain.
    Open to anyone.
    """
    permission_classes = [AllowAny]

    def get(self, request, certificate_hash):
        result = verify_hash_on_blockchain(certificate_hash)

        if result['exists']:
            return Response({
                'exists'   : True,
                'message'  : 'Hash found on blockchain.',
                'timestamp': result['timestamp'],
                'issuer'   : result['issuer']
            }, status=status.HTTP_200_OK)

        return Response({
            'exists' : False,
            'message': 'Hash not found on blockchain.'
        }, status=status.HTTP_404_NOT_FOUND)