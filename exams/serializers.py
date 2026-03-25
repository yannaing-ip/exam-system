from rest_framework import serializers
from .models import Course, Exam, Question, Choice, ExamAttempt, Answer


class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ['id', 'text']


class QuestionSerializer(serializers.ModelSerializer):
    choices = ChoiceSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ['id', 'text', 'choices']


class ExamSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source='course.title', read_only=True)
    question_count = serializers.IntegerField(source='questions.count', read_only=True)

    class Meta:
        model = Exam
        fields = ['id', 'title', 'course_title', 'duration', 'total_marks', 'max_attempts', 'question_count']


class ExamDetailSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source='course.title', read_only=True)
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Exam
        fields = ['id', 'title', 'course_title', 'duration', 'total_marks', 'max_attempts', 'questions']


class SaveAnswerSerializer(serializers.Serializer):
    attempt_id = serializers.IntegerField()
    question_id = serializers.IntegerField()
    choice_id = serializers.IntegerField()


class AttemptResultSerializer(serializers.ModelSerializer):
    exam_title = serializers.CharField(source='exam.title', read_only=True)
    total_questions = serializers.IntegerField(source='exam.questions.count', read_only=True)

    class Meta:
        model = ExamAttempt
        fields = ['id', 'exam_title', 'score', 'total_questions', 'started_at', 'ends_at', 'is_submitted']
