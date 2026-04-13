from django.db import models
from django.contrib.auth.models import User

class Resume(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # Basic info
    full_name = models.CharField(max_length=200)
    designation = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    location = models.CharField(max_length=200, blank=True, null=True)
    linkedin = models.URLField(blank=True, null=True)
    github = models.URLField(blank=True, null=True)

    # Summary
    summary = models.TextField(blank=True, null=True)

    # Skills
    programming_languages = models.TextField(blank=True, null=True)
    web_technologies = models.TextField(blank=True, null=True)
    frameworks_tools = models.TextField(blank=True, null=True)
    database = models.TextField(blank=True, null=True)

    # Education
    college = models.CharField(max_length=200, blank=True, null=True)
    course = models.CharField(max_length=200, blank=True, null=True)
    cgpa = models.FloatField(blank=True, null=True)
    year = models.CharField(max_length=10, blank=True, null=True)

    # Experience
    experience = models.TextField(blank=True, null=True)

    # Projects
    projects = models.TextField(blank=True, null=True)

    # Certifications
    certifications = models.TextField(blank=True, null=True)

    # Achievements
    achievements = models.TextField(blank=True, null=True)

    # ATS Score
    score = models.FloatField(default=0)

    # Auto fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.full_name} ({self.user.username})"


class Score(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    resume_name = models.CharField(max_length=200)
    ats_score = models.FloatField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.resume_name} - {self.ats_score}"


class Performance(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    test_name = models.CharField(max_length=200)
    score = models.FloatField()
    date_taken = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.test_name} - {self.score}"