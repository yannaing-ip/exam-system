from django.contrib import admin
from .models import Course, Exam, Question, Choice, ExamAttempt

# -------------------------
# Choice Inline (for Question)
# -------------------------
class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 4  # show 4 empty choice fields by default
    max_num = 10  # optional: max choices allowed
    min_num = 2   # optional: at least 2 choices per question

# -------------------------
# Question Admin
# -------------------------
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'exam')
    inlines = [ChoiceInline]  # add/edit choices in the same page

# -------------------------
# Exam Admin
# -------------------------
@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'duration', 'is_active', 'max_attempts')
    list_filter = ('course', 'is_active')
    search_fields = ('title',)

# -------------------------
# Course Admin
# -------------------------
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active')
    search_fields = ('title',)

# -------------------------
# ExamAttempt Admin
# -------------------------
@admin.register(ExamAttempt)
class ExamAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'exam', 'attempt_number', 'start_time', 'is_submitted')
    list_filter = ('exam', 'is_submitted')
    search_fields = ('user__username', 'exam__title')
