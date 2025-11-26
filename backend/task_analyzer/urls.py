"""
URL configuration for task_analyzer project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/tasks/', include('tasks.urls')),
]

