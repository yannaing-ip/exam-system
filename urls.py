from django.urls import path
from . import views

urlpatterns = [
	path("", views.home, name="home"),
	path("exam/<int:exam_id>/start/", views.start_exam, name="start_exam"),
	path("exam/<int:exam_id>/take/", views.take_exam, name="take_exam"),
	path("exam/<int:exam_id>/submit/", views.submit_exam, name="submit_exam"),
	path("exam/submitted/", views.exam_submitted, name="exam_submitted"),
	path("exam/result/<int:attempt_id>/", views.exam_result, name="exam_result"),
	path("exam/save-answer/", views.save_answer, name="save_answer"),
	path("exam/<int:exam_id>/confirm/", views.exam_confirm, name="exam_confirm"),
]
