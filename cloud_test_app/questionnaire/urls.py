from django.urls import path
from questionnaire import views

urlpatterns = [
    path('', views.index, name="index"),
    path('questionnaire', views.questionnaire, name="questionnaire"),
    path('vote', views.vote, name="vote"),
    path('results', views.results, name="results"),
]