from django.urls import path
from . import views

urlpatterns = [
    path('exam/<int:exam_id>/start/', views.start_exam, name='start_exam'),
    path('exam/<int:exam_id>/take/', views.take_exam, name='take_exam'),
    path('exam/<int:exam_id>/submit/', views.submit_exam, name='submit_exam'),
    path('exam/submitted/', views.exam_submitted, name='exam_submitted'),
]
