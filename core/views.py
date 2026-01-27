from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Exam, ExamAttempt, Question, Answer, Choice


def landing(request):
	"""Landing page view - redirects authenticated users to home"""
	if request.user.is_authenticated:
		return redirect("home")

	return render(
		request,
		"core/landing.html",
		{
			"year": timezone.now().year,
		},
	)


@login_required
def home(request):
	"""Home page showing all active exams with attempt information"""
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

		exams_info.append(
			{
				"exam": exam,
				"attempts_done": attempts_done,
				"attempts_remaining": attempts_remaining,
				"can_start": can_start,
			}
		)

	return render(request, "core/home.html", {"exams_info": exams_info})


@login_required
def start_exam(request, exam_id):
	"""Create a new exam attempt"""
	exam = get_object_or_404(Exam, id=exam_id, is_active=True)

	# Count previous attempts
	attempts = ExamAttempt.objects.filter(user=request.user, exam=exam).count()

	if exam.max_attempts > 0 and attempts >= exam.max_attempts:
		return redirect("exam_not_allowed")

	# Create new attempt
	start_time = timezone.now()
	end_time = start_time + timedelta(minutes=exam.duration)

	ExamAttempt.objects.create(
		user=request.user,
		exam=exam,
		start_time=start_time,
		end_time=end_time,
	)

	return redirect("take_exam", exam_id=exam.id)


@login_required
def take_exam(request, exam_id):
	"""Main exam taking view"""
	exam = get_object_or_404(Exam, id=exam_id, is_active=True)

	# Get the latest unsubmitted attempt
	attempt = (
		ExamAttempt.objects.filter(user=request.user, exam=exam, is_submitted=False)
		.order_by("-start_time")
		.prefetch_related("answers__choice", "answers__question")
		.first()
	)

	if not attempt:
		return redirect("start_exam", exam_id=exam.id)

	# Calculate remaining time
	now = timezone.now()
	time_remaining = (attempt.end_time - now).total_seconds()

	# Auto-submit if time expired (with 5 second buffer to prevent immediate submission)
	if time_remaining < -5:
		attempt.score = calculate_score(attempt)
		attempt.is_submitted = True
		attempt.save()
		return redirect("exam_result", attempt_id=attempt.id)

	questions = Question.objects.filter(exam=exam).prefetch_related("choices")

	return render(
		request,
		"core/take_exam.html",
		{
			"exam": exam,
			"attempt": attempt,
			"questions": questions,
			"time_remaining": max(0, int(time_remaining)),  # Pass remaining seconds
		},
	)


@login_required
@require_POST
def save_answer(request):
	"""AJAX endpoint to save individual answers"""
	attempt_id = request.POST.get("attempt_id")
	question_id = request.POST.get("question_id")
	choice_id = request.POST.get("choice_id")

	try:
		attempt = get_object_or_404(
			ExamAttempt, id=attempt_id, user=request.user, is_submitted=False
		)
		question = get_object_or_404(Question, id=question_id)
		choice = get_object_or_404(Choice, id=choice_id)

		# Update or create ensures one answer per question per attempt
		Answer.objects.update_or_create(
			attempt=attempt,
			question=question,
			defaults={"choice": choice},
		)

		return JsonResponse({"status": "ok"})
	except Exception as e:
		return JsonResponse({"status": "fail", "error": str(e)}, status=400)


@login_required
def submit_exam(request, exam_id):
	"""Submit the exam and calculate score"""
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

	return redirect("home")


@login_required
def exam_submitted(request):
	"""Confirmation page after exam submission"""
	return render(request, "core/exam_submitted.html")

@login_required
def exam_confirm(request, exam_id):
	"""Review page before final submission"""
	exam = get_object_or_404(Exam, id=exam_id)
	attempt = ExamAttempt.objects.filter(
		user=request.user, exam=exam, is_submitted=False
	).last()

	if not attempt:
		return redirect("start_exam", exam_id=exam.id)

	# Calculate remaining time
	now = timezone.now()
	time_remaining = (attempt.end_time - now).total_seconds()

	# Get all answers for this attempt as a list
	answers = list(attempt.answers.select_related("choice", "question").all())
	questions = exam.questions.prefetch_related("choices")

	return render(
		request,
		"core/exam_confirm.html",
		{
			"exam": exam,
			"attempt": attempt,
			"questions": questions,
			"answers": answers,
			"time_remaining": max(0, int(time_remaining)),  # Pass remaining seconds
		},
	)


def calculate_score(attempt):
	"""Calculate the number of correct answers for an attempt"""
	correct_answers = 0
	for answer in attempt.answers.select_related("choice"):
		if answer.choice.is_correct:
			correct_answers += 1
	return correct_answers


def calculate_percentage(attempt):
	"""Calculate the percentage score for an attempt"""
	total_questions = attempt.exam.questions.count()
	if total_questions == 0:
		return 0
	return (attempt.score / total_questions) * 100


@login_required
def exam_result(request, attempt_id):
	"""Display exam results with correct/incorrect answers"""
	attempt = get_object_or_404(ExamAttempt, id=attempt_id, user=request.user)
	questions = attempt.exam.questions.prefetch_related("choices")

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
