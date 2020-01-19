import datetime

from django.contrib.auth import forms
from django.forms import ModelForm, DateField, Form, FileField
from django.contrib.auth.forms import UserChangeForm as BaseUserChangeForm
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm

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


class UserChangeForm(BaseUserChangeForm):
    def __init__(self, *args, **kwargs):
        super(UserChangeForm, self).__init__(*args, **kwargs)
        self.fields['profile_pic'] = FileField(label="Profile Picture")
