from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="home"),
    path("contact/", views.contact, name="contact"),
    path("resources/", views.resources_view, name="resources"),
]
