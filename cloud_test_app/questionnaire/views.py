from django.shortcuts import render


def index(request):
    #TODO: make this a real number:
    num_answers = 0
    context = {
        'title': "Basic Questions!",
        'num_answers': num_answers,
    }
    return render(request, 'questionnaire/index.html', context)

def questionnaire(request):
    return render(request, 'questionnaire/questionnaire.html')