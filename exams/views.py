from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta
from drf_yasg.utils import swagger_auto_schema

from .models import Exam, ExamAttempt, Question, Answer, Choice
from .serializers import (
    ExamSerializer, ExamDetailSerializer,
    SaveAnswerSerializer, AttemptResultSerializer
)


def auto_submit_if_expired(attempt):
    if not attempt.is_submitted and timezone.now() > attempt.ends_at:
        score = sum(
            1 for answer in attempt.answers.select_related('choice')
            if answer.choice.is_correct
        )
        attempt.score = score
        attempt.is_submitted = True
        attempt.save()
        return True
    return False


def get_saved_answers(attempt):
    return {
        str(answer.question_id): answer.choice_id
        for answer in attempt.answers.all()
    }


class ExamListView(APIView):
    def get(self, request):
        exams = Exam.objects.filter(is_active=True).select_related('course')
        serializer = ExamSerializer(exams, many=True)
        return Response(serializer.data)


class ExamDetailView(APIView):
    def get(self, request, exam_id):
        exam = get_object_or_404(Exam, id=exam_id, is_active=True)
        serializer = ExamDetailSerializer(exam)
        return Response(serializer.data)


class StartExamView(APIView):
    @swagger_auto_schema(operation_description="Start an exam attempt. No request body needed.")
    def post(self, request, exam_id):
        exam = get_object_or_404(Exam, id=exam_id, is_active=True)

        existing = ExamAttempt.objects.filter(
            user=request.user, exam=exam, is_submitted=False
        ).first()

        if existing:
            if auto_submit_if_expired(existing):
                return Response(
                    {'error': 'Your previous attempt expired and was auto-submitted.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            return Response({
                'attempt_id': existing.id,
                'ends_at': existing.ends_at,
                'saved_answers': get_saved_answers(existing),
                'message': 'Resuming existing attempt.'
            }, status=status.HTTP_200_OK)

        attempts_done = ExamAttempt.objects.filter(user=request.user, exam=exam).count()
        if exam.max_attempts > 0 and attempts_done >= exam.max_attempts:
            return Response(
                {'error': 'Maximum attempts reached.'},
                status=status.HTTP_403_FORBIDDEN
            )

        attempt = ExamAttempt.objects.create(
            user=request.user,
            exam=exam,
            ends_at=timezone.now() + timedelta(minutes=exam.duration)
        )

        return Response({
            'attempt_id': attempt.id,
            'ends_at': attempt.ends_at,
            'saved_answers': {},
            'message': 'Exam started.'
        }, status=status.HTTP_201_CREATED)


class SaveAnswerView(APIView):
    @swagger_auto_schema(request_body=SaveAnswerSerializer)
    def post(self, request):
        serializer = SaveAnswerSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        attempt = get_object_or_404(
            ExamAttempt,
            id=serializer.validated_data['attempt_id'],
            user=request.user,
            is_submitted=False
        )

        if timezone.now() > attempt.ends_at:
            auto_submit_if_expired(attempt)
            return Response(
                {'error': 'Time expired. Your exam has been auto-submitted.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        question = get_object_or_404(Question, id=serializer.validated_data['question_id'])
        choice = get_object_or_404(Choice, id=serializer.validated_data['choice_id'])

        Answer.objects.update_or_create(
            attempt=attempt,
            question=question,
            defaults={'choice': choice}
        )

        return Response({'status': 'ok'})


class SubmitExamView(APIView):
    @swagger_auto_schema(operation_description="Submit the exam. No request body needed.")
    def post(self, request, exam_id):
        exam = get_object_or_404(Exam, id=exam_id)
        attempt = get_object_or_404(
            ExamAttempt,
            user=request.user,
            exam=exam,
            is_submitted=False
        )

        auto_submit_if_expired(attempt)
        attempt.refresh_from_db()

        if not attempt.is_submitted:
            score = sum(
                1 for answer in attempt.answers.select_related('choice')
                if answer.choice.is_correct
            )
            attempt.score = score
            attempt.is_submitted = True
            attempt.save()

        serializer = AttemptResultSerializer(attempt)
        return Response(serializer.data)


class ExamResultView(APIView):
    def get(self, request, attempt_id):
        attempt = get_object_or_404(ExamAttempt, id=attempt_id, user=request.user)
        serializer = AttemptResultSerializer(attempt)
        return Response(serializer.data)
