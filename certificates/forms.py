from django import forms
from .models import Certificate


class CertificateForm(forms.ModelForm):
    class Meta:
        model  = Certificate
        fields = ['student_name', 'student_email', 'course_name', 'issue_date', 'pdf_file']
        widgets = {
            'pdf_file': forms.FileInput(attrs={'accept': '.pdf'})
        }


class VerifyCertificateForm(forms.Form):
    student_name = forms.CharField(max_length=255)
    course_name  = forms.CharField(max_length=255)
    issue_date   = forms.DateField()