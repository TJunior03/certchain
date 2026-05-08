from django.urls import path
from .views import home, issue_certificate, verify_certificate

urlpatterns = [
    path('', home, name='home'),

    path('issue/', issue_certificate, name='issue_certificate'),

    path('verify/', verify_certificate, name='verify_certificate'),
]