from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Plan(models.Model):
    name = models.CharField(max_length=50)   # Basic / Pro
    price = models.IntegerField()
    duration_days = models.IntegerField()

    def __str__(self):
        return self.name


class Subscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    plan = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True)

    active = models.BooleanField(default=True)
    start_date = models.DateTimeField(default=timezone.now)
    expiry = models.DateTimeField()

    def is_active(self):
        return self.active and self.expiry > timezone.now()