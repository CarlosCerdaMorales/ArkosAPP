from django.urls import path

from . import views

urlpatterns = [
    path('history/', views.appointment_history_view, name='appointment_history'),
    path('upcoming/', views.upcoming_appointments_view, name='upcoming_appointments'),
    path('create/', views.create_appointment_view, name='create_appointment'),
    path('api/get-available-slots/', views.get_available_slots, name='get_available_slots'),
    path('success/<int:pk>/', views.appointment_success_view, name='appointment_success'),
    path('cancel/<int:pk>/', views.cancel_appointment_view, name='cancel_appointment'),
    path("services/", views.services_list_view, name="services_list"),
    path('modify/<int:pk>/', views.modify_appointment_view, name='modify_appointment'),
    path('admin/cancel/<int:pk>/', views.admin_cancel_appointment, name='admin_cancel_appointment'),
]
