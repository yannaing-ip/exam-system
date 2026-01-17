from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL

# -------------------------
# Course
# -------------------------
class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

# -------------------------
# Exam
# -------------------------
class Exam(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="exams")
    title = models.CharField(max_length=200)
    duration = models.PositiveIntegerField(help_text="Duration in minutes")
    total_marks = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    max_attempts = models.PositiveIntegerField(
        default=1,
        help_text="Maximum attempts per student (0 = unlimited)"
    )

    def __str__(self):
        return f"{self.course.title} - {self.title}"

# -------------------------
# Question
# -------------------------
class Question(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField()

    def __str__(self):
        return self.text[:50]

# -------------------------
# Choice
# -------------------------
class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="choices")
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)
    image_url = models.URLField(blank=True, null=True)
    code_snippet = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.text

# -------------------------
# Exam Attempt
# -------------------------
class ExamAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="exam_attempts")
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="attempts")
    attempt_number = models.PositiveIntegerField(default=1)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    is_submitted = models.BooleanField(default=False)

    class Meta:
        ordering = ['-start_time']

    def __str__(self):
        return f"{self.user} - {self.exam.title} (Attempt {self.attempt_number})"
