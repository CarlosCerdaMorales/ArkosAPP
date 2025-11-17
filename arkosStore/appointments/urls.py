from django.urls import path
from . import views

urlpatterns = [
    path('history/', views.appointment_history_view, name='appointment_history'),
    path('upcoming/', views.upcoming_appointments_view, name='upcoming_appointments'),
]