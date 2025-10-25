from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class TestSubmission(models.Model):
    candidate = models.ForeignKey(User, on_delete=models.CASCADE)
    test_type = models.CharField(max_length=50)
    answers = models.JSONField(default=dict)
    score = models.FloatField(default=0.0)
    submitted_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.candidate.username} - {self.test_type} ({self.score})"

class ResultReport(models.Model):
    DECISIONS = [("rejected", "Rejected"), ("offered", "Offered")]
    candidate = models.ForeignKey(User, on_delete=models.CASCADE)
    report_text = models.TextField()
    decision = models.CharField(max_length=32, choices=DECISIONS)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.candidate.username} - {self.decision}"
    
class Question(models.Model):
    text = models.TextField()
    options = models.JSONField()  # list of 4 options
    correct_index = models.IntegerField()  # 0–3
    difficulty = models.CharField(max_length=16, default="medium")
    tags = models.JSONField(default=list, blank=True)  # ['math','logic','python']
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.text[:80]


class CodingQuestion(models.Model):
    title = models.CharField(max_length=128)
    description = models.TextField()
    starter_code = models.TextField(blank=True)
    test_cases = models.JSONField(default=list)
    skill_tags = models.JSONField(default=list)  # e.g. ["C", "Java", "DSA"]
    difficulty = models.CharField(max_length=16, default="medium")

    def __str__(self):
        return self.title

    @classmethod
    def get_by_skill(cls, skill):
        return cls.objects.filter(skill_tags__icontains=skill).order_by('?').first()

class TestSubmission(models.Model):
    candidate = models.ForeignKey(User, on_delete=models.CASCADE)
    test_type = models.CharField(max_length=32)
    answers = models.JSONField(default=dict)
    score = models.FloatField(default=0.0)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("candidate", "test_type")
