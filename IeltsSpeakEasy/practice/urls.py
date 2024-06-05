from django.urls import path
from . import views

urlpatterns = [
    path('practice/', views.practice, name='practice'),
]
