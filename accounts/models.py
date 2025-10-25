# accounts/models.py
from django.db import models
from django.contrib.auth.models import User

class CandidateProfile(models.Model):
    STAGE_CHOICES = [
        ("resume", "Resume Uploaded"),
        ("aptitude", "Aptitude"),
        ("coding", "Coding"),
        ("tech", "Tech Interview"),
        ("hr", "HR Interview"),
        ("done", "Completed"),
    ]
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("rejected", "Rejected"),
        ("shortlisted", "Shortlisted"),
        ("offered", "Offered"),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    resume = models.FileField(upload_to="resumes/", null=True, blank=True)
    current_stage = models.CharField(max_length=32, choices=STAGE_CHOICES, default="resume")
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default="pending")

    # existing fields
    skills = models.JSONField(default=list, blank=True)
    resume_text = models.TextField(blank=True, null=True)
    embedding = models.JSONField(default=list, blank=True)
    violations = models.PositiveIntegerField(default=0)

    # NEW field: list of project names / short descriptors
    projects = models.JSONField(default=list, blank=True)

    def __str__(self):
        return f"{self.user.username} profile"
