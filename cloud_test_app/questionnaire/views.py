from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import render
from .models import FilledQuestionnaire

def index(request):
    #TODO: make this a real number:
    num_answers = 0
    context = {
        'title': "Basic Questions!",
        'num_answers': num_answers,
    }
    return render(request, 'questionnaire/index.html', context)

def questionnaire(request):
    context = {
        "day_choices":  FilledQuestionnaire.DAY_CHOICES,
        "month_choices": FilledQuestionnaire.MONTH_CHOICES
    }
    return render(request, 'questionnaire/questionnaire.html', context)

def vote(request):
    # TODO: Validate form
    filled_questionnaire = FilledQuestionnaire(
        favourite_day = int(request.POST["day_choice"]),
        favourite_month = int(request.POST["month_choice"])
    )
    filled_questionnaire.save()
    return HttpResponseRedirect(reverse('index'))