from django.urls import path
from .views import (
    ExamListView, ExamDetailView,
    StartExamView, SaveAnswerView,
    SubmitExamView, ExamResultView
)

urlpatterns = [
    path('', ExamListView.as_view(), name='exam_list'),
    path('<int:exam_id>/', ExamDetailView.as_view(), name='exam_detail'),
    path('<int:exam_id>/start/', StartExamView.as_view(), name='start_exam'),
    path('<int:exam_id>/submit/', SubmitExamView.as_view(), name='submit_exam'),
    path('save-answer/', SaveAnswerView.as_view(), name='save_answer'),
    path('result/<int:attempt_id>/', ExamResultView.as_view(), name='exam_result'),
]
