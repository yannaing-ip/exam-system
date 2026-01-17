from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta

from .models import Exam, ExamAttempt, Question, Answer, Choice

@login_required
def start_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id, is_active=True)

    # count previous attempts
    attempts = ExamAttempt.objects.filter(
        user=request.user,
        exam=exam
    ).count()

    if attempts >= exam.max_attempts:
        return redirect('exam_not_allowed')

    # create attempt
    start_time = timezone.now()
    end_time = start_time + timedelta(minutes=exam.duration)

    ExamAttempt.objects.create(
        user=request.user,
        exam=exam,
        start_time=start_time,
        end_time=end_time
    )

    return redirect('take_exam', exam_id=exam.id)

@login_required
def take_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id, is_active=True)

    attempt = ExamAttempt.objects.filter(
        user=request.user,
        exam=exam,
        is_submitted=False
    ).order_by('-start_time').first()

    if not attempt:
        return redirect('start_exam', exam_id=exam.id)

    # auto-submit if time expired
    if timezone.now() > attempt.end_time:
        attempt.is_submitted = True
        attempt.save()
        return redirect('exam_time_over')

    questions = Question.objects.filter(exam=exam).prefetch_related('choices')

    if request.method == 'POST':
        for question in questions:
            choice_id = request.POST.get(f'question_{question.id}')
            if choice_id:
                choice = Choice.objects.get(id=choice_id)
                Answer.objects.update_or_create(
                    attempt=attempt,
                    question=question,
                    defaults={'choice': choice}
                )

        return redirect('submit_exam', exam_id=exam.id)

    return render(request, 'core/take_exam.html', {
        'exam': exam,
        'attempt': attempt,
        'questions': questions,
    })

@login_required
def submit_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    attempt = ExamAttempt.objects.filter(
        user=request.user,
        exam=exam,
        is_submitted=False
    ).first()

    if attempt:
        attempt.is_submitted = True
        attempt.save()

    return redirect('exam_submitted')

@login_required
def exam_submitted(request):
    return render(request, 'core/exam_submitted.html')


