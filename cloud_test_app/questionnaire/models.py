from django.db import models
import calendar

class FilledQuestionnaire(models.Model):
    DAY_CHOICES = tuple([(i, calendar.day_name[i]) for i in range(7)])
    MONTH_CHOICES = tuple([(i, calendar.month_name[i]) for i in range(1,13)])
    favourite_day = models.IntegerField(choices=DAY_CHOICES)
    favourite_month = models.IntegerField(choices=MONTH_CHOICES)