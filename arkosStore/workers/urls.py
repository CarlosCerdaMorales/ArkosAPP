from django.urls import path
from . import views

urlpatterns = [
    path("list/", views.worker_list_view, name="worker_list"),
    path("admin/create/", views.admin_create_worker, name="admin_create_worker"),
    path('<int:worker_id>/reviews/', views.worker_reviews_view, name='worker_reviews'),
]
