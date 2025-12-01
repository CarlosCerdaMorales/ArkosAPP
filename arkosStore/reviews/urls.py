from django.urls import path
from . import views

urlpatterns = [
    path('create/<int:appointment_id>/', views.create_review_view, name='create_review'),
    path('my-reviews/', views.my_reviews_view, name='my_reviews')
]
