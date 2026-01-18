from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import Exam, ExamAttempt, Question, Answer, Choice

@login_required
def home(request):
    exams = Exam.objects.filter(is_active=True)

    exams_info = []
    for exam in exams:
        attempts_done = ExamAttempt.objects.filter(user=request.user, exam=exam).count()
        if exam.max_attempts == 0:
            attempts_remaining = "Unlimited"
            can_start = True
        else:
            attempts_remaining = max(exam.max_attempts - attempts_done, 0)
            can_start = attempts_remaining > 0

        exams_info.append({
            "exam": exam,
            "attempts_done": attempts_done,
            "attempts_remaining": attempts_remaining,
            "can_start": can_start,
        })

    return render(request, "core/home.html", {"exams_info": exams_info})

@login_required
def start_exam(request, exam_id):
	exam = get_object_or_404(Exam, id=exam_id, is_active=True)

	# count previous attempts
	attempts = ExamAttempt.objects.filter(user=request.user, exam=exam).count()

	if attempts >= exam.max_attempts:
		return redirect("exam_not_allowed")

	# create attempt
	start_time = timezone.now()
	end_time = start_time + timedelta(minutes=exam.duration)

	ExamAttempt.objects.create(
		user=request.user, exam=exam, start_time=start_time, end_time=end_time
	)

	return redirect("take_exam", exam_id=exam.id)


@login_required
def take_exam(request, exam_id):
	exam = get_object_or_404(Exam, id=exam_id, is_active=True)

	attempt = (
		ExamAttempt.objects.filter(user=request.user, exam=exam, is_submitted=False)
		.order_by("-start_time")
		.first()
	)

	if not attempt:
		return redirect("start_exam", exam_id=exam.id)

	# auto-submit if time expired
	if timezone.now() > attempt.end_time:
		# calculate score automatically
		attempt.score = calculate_score(attempt)
		attempt.is_submitted = True
		attempt.save()
		return redirect("exam_result", attempt_id=attempt.id)

	questions = Question.objects.filter(exam=exam).prefetch_related("choices")

	if request.method == "POST":
		for question in questions:
			choice_id = request.POST.get(f"question_{question.id}")
			if choice_id:
				choice = Choice.objects.get(id=choice_id)
				Answer.objects.update_or_create(
					attempt=attempt, question=question, defaults={"choice": choice}
				)

		return redirect("submit_exam", exam_id=exam.id)

	return render(
		request,
		"core/take_exam.html",
		{
			"exam": exam,
			"attempt": attempt,
			"questions": questions,
		},
	)


@login_required
@csrf_exempt
def save_answer(request):
	if request.method == "POST":
		attempt_id = request.POST.get("attempt_id")
		question_id = request.POST.get("question_id")
		choice_id = request.POST.get("choice_id")

		attempt = get_object_or_404(ExamAttempt, id=attempt_id, user=request.user)
		question = get_object_or_404(Question, id=question_id)
		choice = get_object_or_404(Choice, id=choice_id)

		# update_or_create ensures one answer per question per attempt
		Answer.objects.update_or_create(
			attempt=attempt, question=question, defaults={"choice": choice}
		)

		return JsonResponse({"status": "ok"})

	return JsonResponse({"status": "fail"}, status=400)


@login_required
def submit_exam(request, exam_id):
	exam = get_object_or_404(Exam, id=exam_id)
	attempt = ExamAttempt.objects.filter(
		user=request.user, exam=exam, is_submitted=False
	).first()

	if attempt:
		# Calculate score
		attempt.score = calculate_score(attempt)
		attempt.is_submitted = True
		attempt.save()

	return redirect("exam_result", attempt_id=attempt.id)


@login_required
def exam_submitted(request):
	return render(request, "core/exam_submitted.html")

@login_required
def exam_confirm(request, exam_id):
	exam = get_object_or_404(Exam, id=exam_id)
	attempt = ExamAttempt.objects.filter(
		user=request.user, exam=exam, is_submitted=False
	).last()

	# Pass all answers as a queryset
	answers = attempt.answers.select_related("choice", "question").all()
	questions = exam.questions.prefetch_related("choices")

	return render(
		request,
		"core/exam_confirm.html",
		{
			"exam": exam,
			"attempt": attempt,
			"questions": questions,
			"answers": answers,  # now queryset
		},
	)


def calculate_score(attempt):
	"""
	Calculate the number of correct answers for an attempt.
	"""
	correct_answers = 0
	for answer in attempt.answers.select_related("choice"):
		if answer.choice.is_correct:
			correct_answers += 1
	return correct_answers


def calculate_percentage(attempt):
	total_questions = attempt.exam.questions.count()
	if total_questions == 0:
		return 0
	return (attempt.score / total_questions) * 100


@login_required
def exam_result(request, attempt_id):
	attempt = get_object_or_404(ExamAttempt, id=attempt_id, user=request.user)
	questions = attempt.exam.questions.prefetch_related(
		"choices"
	)  # <-- removed 'answers'

	results = []
	for question in questions:
		answer = attempt.answers.filter(question=question).first()
		results.append(
			{
				"question": question,
				"selected": answer.choice if answer else None,
				"correct": question.choices.filter(is_correct=True).first(),
			}
		)

	return render(
		request,
		"core/exam_result.html",
		{
			"attempt": attempt,
			"results": results,
		},
	)
