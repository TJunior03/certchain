from django.urls import path
from .views import issue_certificate

urlpatterns = [
    path('issue/', issue_certificate, name='issue_certificate'),
]