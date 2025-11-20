from django.urls import path
from . import views

urlpatterns = [
    path('list/', views.worker_list_view, name='worker_list'),
]