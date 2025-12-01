from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="home"),
    path("contact/", views.contact, name="contact"),
    path("admin/", views.custom_admin, name='custom_admin'),
    path("resources/", views.resources_view, name="resources"),
    path('terms/', views.terms_conditions_view, name='terms_conditions'),
]
