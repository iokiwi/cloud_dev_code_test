from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import render
from .models import FilledQuestionnaire
from django.db.models import Count
import calendar

def index(request):
    #TODO: make this a real number:

    num_answers = FilledQuestionnaire.objects.all().count()
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
    return HttpResponseRedirect(reverse('results'))


def results(request):
    # TODO: Validate form
    
    results = FilledQuestionnaire.objects.all()
    total = results.count()

    day_frequencies = {}
    month_frequencies = {}
    day_frequencies_by_month = {}

    # Populate Day Frequencies
    for result in list(results):
        # Build a dictionary of the frequency of response for each day   
        day_frequencies[result.favourite_day] = day_frequencies.get(result.favourite_day, 0) + 1
        # Build a dictionary of the frequency of response for each month
        month_frequencies[result.favourite_month] = month_frequencies.get(result.favourite_month, 0) + 1
        # Build a dictionary of the frequency of response for each day by month
        if not result.favourite_month in day_frequencies_by_month.keys():
            day_frequencies_by_month[result.favourite_month] = {}
        if result.favourite_day in day_frequencies_by_month[result.favourite_month].keys():
            day_frequencies_by_month[result.favourite_month][result.favourite_day] += 1
        else:
            day_frequencies_by_month[result.favourite_month][result.favourite_day] = 1
    
    # results = FilledQuestionnaire.objects.values("favourite_day") \
    #     .annotate(Count('favourite_day')) \
    #     .order_by('favourite_day') 
    
    # day_results = []
    # for result in results:
    #     day_results.append({
    #         "name": calendar.day_name[result["favourite_day"]],
    #         "count": result["favourite_day__count"],
    #         "percent": result["favourite_day__count"] / total * 100,
    #     })

    # Calculate percentages and format data for response
    day_results = []
    for k, v in day_frequencies.items():
        percent = v / total * 100
        day_results.append({
            "day_number": k,
            "name": calendar.day_name[k],
            "count": v, "percent": "{:.1f}".format(percent)})
    day_results = sorted(day_results, key=lambda k: k['day_number'])


    # results = FilledQuestionnaire.objects.values("favourite_month") \
    #     .annotate(Count('favourite_month')) \
    #     .order_by('favourite_month') 
    
    # month_results = []
    # for result in results:
    #     month_results.append({
    #         "name": calendar.month_name[result["favourite_month"]],
    #         "count": result["favourite_month__count"],
    #         "percent": result["favourite_month__count"] / total * 100,
    #     })

    # Calculate percentages and format data for HttpResponse
    month_results = []
    for k, v in month_frequencies.items():
        percent = v / total * 100
        month_results.append({
            "month_number": k,
            "name": calendar.month_name[k],
            "count": v,
            "percent": "{:.1f}".format(percent)})
    month_results = sorted(month_results, key=lambda k: k['month_number'])


    # Calulate the most popular day of the week for each month
    most_popular_days_by_month = []
    for month, day_frequencies in day_frequencies_by_month.items():
        most_popular_day = max(day_frequencies.keys(), key=(lambda k: day_frequencies[k]))
        most_popular_days_by_month.append({
            "month_number": month,
            "month_name": calendar.month_name[month],
            "most_popular_day": calendar.day_name[most_popular_day]
        })
    most_popular_days_by_month = sorted(most_popular_days_by_month, key=lambda k: k['month_number'])

    context = {
        "month_results": month_results,
        "day_results": day_results,
        "days_by_month": most_popular_days_by_month,
    }
    return render(request, 'questionnaire/results.html', context)