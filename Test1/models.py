from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    money = models.DecimalField(max_digits=15, decimal_places=2)


class StocksRecord(models.Model):
    symbol = models.CharField(max_length=5)
    user = models.ForeignKey(User, related_name="holding", on_delete=models.CASCADE)
    amount = models.IntegerField()
    bought_at = models.DecimalField(max_digits=10, decimal_places=2)
    sold_at = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
