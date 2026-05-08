from django.urls import path
from .views import issue_certificate, verify_certificate

urlpatterns = [
    path('issue/', issue_certificate, name='issue_certificate'),

    path('verify/', verify_certificate, name='verify_certificate'),
]