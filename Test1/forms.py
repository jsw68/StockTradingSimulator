from . import models
from django.forms import ModelForm


class StockForm(ModelForm):
    class Meta:
        model = models.StocksRecord
        fields = ["symbol", "amount", "bought_at"]
