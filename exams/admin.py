from django.contrib import admin
from .models import Course, Exam, Question, Choice, ExamAttempt, Answer

admin.site.register(Course)
admin.site.register(Exam)
admin.site.register(Question)
admin.site.register(Choice)
admin.site.register(ExamAttempt)
admin.site.register(Answer)
