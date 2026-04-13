from django import forms
from .models import Resume

class ResumeForm(forms.ModelForm):
    class Meta:
        model = Resume
        exclude = ['user', 'score', 'created_at']  # No ATS score here
        widgets = {
            # ===== BASIC INFO =====
            'full_name': forms.TextInput(attrs={'class':'form-control','placeholder':'Full Name'}),
            'designation': forms.TextInput(attrs={
    'class': 'form-control',
    'placeholder': 'Enter your role (optional)'
}),
            'email': forms.EmailInput(attrs={'class':'form-control','placeholder':'Email Address'}),
            'phone': forms.TextInput(attrs={'class':'form-control','placeholder':'Phone Number'}),
            'location': forms.TextInput(attrs={'class':'form-control','placeholder':'City, State'}),
            # ===== LINKS =====
            'linkedin': forms.TextInput(attrs={'class':'form-control','placeholder':'LinkedIn Profile (optional)'}),
            'github': forms.TextInput(attrs={'class':'form-control','placeholder':'GitHub / Portfolio (optional)'}),
            # ===== SUMMARY =====
            'summary': forms.Textarea(attrs={'class':'form-control','rows':3,'placeholder':'Short professional summary...'}),
            # ===== SKILLS =====
            'programming_languages': forms.Textarea(attrs={'class':'form-control','rows':2,'placeholder':'Python, Java, C'}),
            'web_technologies': forms.Textarea(attrs={'class':'form-control','rows':2,'placeholder':'HTML, CSS, JavaScript'}),
            'frameworks_tools': forms.Textarea(attrs={'class':'form-control','rows':2,'placeholder':'Django, Git, VS Code'}),
            'database': forms.Textarea(attrs={'class':'form-control','rows':2,'placeholder':'MySQL, MongoDB'}),
            # ===== EDUCATION =====
            'college': forms.TextInput(attrs={'class':'form-control','placeholder':'College Name'}),
            'course': forms.TextInput(attrs={'class':'form-control','placeholder':'Course (B.Tech, Diploma, etc.)'}),
            'cgpa': forms.TextInput(attrs={'class':'form-control','placeholder':'CGPA / Percentage'}),
            'year': forms.TextInput(attrs={'class':'form-control','placeholder':'Year of Passing'}),
            # ===== PROJECTS =====
            'projects': forms.Textarea(attrs={'class':'form-control','rows':4,'placeholder':'Project Name + Description + Technologies'}),
            # ===== EXPERIENCE =====
            'experience': forms.Textarea(attrs={'class':'form-control','rows':3,'placeholder':'Internship / Experience details'}),
            # ===== CERTIFICATIONS =====
            'certifications': forms.Textarea(attrs={'class':'form-control','rows':2,'placeholder':'Python Course - Coursera'}),
            # ===== ACHIEVEMENTS =====
            'achievements': forms.Textarea(attrs={'class':'form-control','rows':2,'placeholder':'Hackathons, Awards, Activities'}),
        }


# core/forms.py
from django import forms
from django.contrib.auth.forms import PasswordChangeForm

class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap form-control class to all fields
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})