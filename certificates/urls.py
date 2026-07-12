from django.urls import path, re_path
from django.contrib.auth import views as auth_views
from . import views
from . import api
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    # Public routes
    path('',        views.home,               name='home'),
    path('verify/', views.verify_certificate, name='verify_certificate'),

    # Staff Dashboard
    path('dashboard/login/',        auth_views.LoginView.as_view(
                                        template_name='certificates/dashboard_login.html',
                                        next_page='/dashboard/'
                                    ), name='dashboard_login'),
    path('dashboard/logout/',       auth_views.LogoutView.as_view(
                                        next_page='/'
                                    ), name='dashboard_logout'),
    path('dashboard/',              views.dashboard_home,         name='dashboard_home'),
    path('dashboard/certificates/', views.dashboard_certificates, name='dashboard_certificates'),
    path('dashboard/issue/',        views.dashboard_issue,        name='dashboard_issue'),
    path('dashboard/blockchain/',   views.dashboard_blockchain,   name='dashboard_blockchain'),

    # API routes
    path('api/certificates/', api.CertificateListAPIView.as_view(),  name='api_list'),
    path('api/issue/',        api.CertificateIssueAPIView.as_view(),  name='api_issue'),
    path('api/verify/',       api.CertificateVerifyAPIView.as_view(), name='api_verify'),
    path('api/token/',         TokenObtainPairView.as_view(),         name='token_obtain'),
    path('api/token/refresh/', TokenRefreshView.as_view(),            name='token_refresh'),

    # Blockchain API
    re_path(r'^api/blockchain/verify/(?P<certificate_hash>[a-f0-9]{64})/$',
            api.BlockchainVerifyAPIView.as_view(), name='api_blockchain_verify'),
]