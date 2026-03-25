from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Exam System API",
        default_version='v1',
        description="REST API for the Exam System",
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

def handler429(request, exception=None):
    return JsonResponse({'error': 'Too many attempts. Please wait a minute.'}, status=429)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path('api/exams/', include('exams.urls')),
    path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='swagger-ui'),
]
