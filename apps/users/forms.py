import datetime

from django.forms import ModelForm, DateField

from apps.users.models import Ledger
from apps.users.widgets import MonthYearWidget


def get_years_range():
    current_year = datetime.datetime.now().year + 1
    return range(current_year - 5, current_year)


class LedgerModelForm(ModelForm):
    expense_date = DateField(widget=MonthYearWidget())

    class Meta:
        fields = '__all__'
        model = Ledger
