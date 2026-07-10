from django.urls import path
from . import views
from . import api

urlpatterns = [
    # UI routes
    path('',        views.home,               name='home'),
    path('issue/',  views.issue_certificate,  name='issue_certificate'),
    path('verify/', views.verify_certificate, name='verify_certificate'),

    # API routes
    path('api/certificates/', api.CertificateListAPIView.as_view(),   name='api_list'),
    path('api/issue/',        api.CertificateIssueAPIView.as_view(),   name='api_issue'),
    path('api/verify/',       api.CertificateVerifyAPIView.as_view(),  name='api_verify'),

    # Blockchain API
    path('api/blockchain/verify/<str:certificate_hash>/',
         api.BlockchainVerifyAPIView.as_view(), name='api_blockchain_verify'),
]