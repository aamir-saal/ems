import datetime

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models import Sum, F
from django.utils.safestring import mark_safe

# from ems.settings import MEDIA_DIRECTORY
from django.conf import settings


class DocumentType(models.Model):
    name = models.CharField(max_length=512, blank=False, null=False)
    description = models.TextField(null=False, blank=True)

    def __str__(self):
        return self.name


class UserDocument(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    document_type = models.ForeignKey(DocumentType, on_delete=models.CASCADE, null=False)
    name = models.CharField(max_length=256, null=False, blank=True)
    description = models.CharField(max_length=512, null=False, blank=True)
    issued_by = models.CharField(max_length=256, null=False, blank=True)
    issued_date = models.DateField(null=True)
    expiry_date = models.DateField(null=True)
    image = models.FileField()

    def __str__(self):
        return "{}'s {}".format(self.user, self.document_type)

    def image_tag(self):
        return mark_safe(f'<img src="{settings.MEDIA_URL}/{self.image}" width="50" height="50" />')

    image.short_description = 'Image'


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    profile_pic = models.FileField()

    def __str__(self):
        return self.user.get_full_name()

    def profile_pic_tag(self):
        return mark_safe(f'<img src="{settings.MEDIA_URL}/{self.profile_pic}" width="50" height="50" />')

    profile_pic_tag.short_description = 'Picture'

    def get_current_month_earning(self):
        return EmployeeTimeSheet.get_user_current_month_earning(self.user)

    get_current_month_earning.short_description = "Current month earning"

    def get_current_month_expenses(self):
        return EmployeeExpense.get_user_current_month_expenses(self.user)

    get_current_month_expenses.short_description = "Current month expenses"

    def get_current_month_net_salary(self):
        return self.get_current_month_earning() - self.get_current_month_expenses()

    get_current_month_net_salary.short_description = "Current month net salary"


class EmployeeTimeSheet(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    work_date = models.DateField(null=False)
    hours = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(24)])
    hourly_rate = models.FloatField(validators=[MinValueValidator(0.0)], null=True)

    @classmethod
    def get_user_current_month_earning(cls, user):
        total_current_month_earning = cls.objects.filter(
            work_date__month=datetime.datetime.now().month,
            user=user
        ).values('user').annotate(total_earning=Sum(F('hours') * F('hourly_rate'))).order_by('user').first()

        return total_current_month_earning.get('total_earning', 0)

    get_user_current_month_earning.short_description = 'Current month Earning'

    def __str__(self):
        return f"{self.user}->{self.work_date}:{self.hours}@{self.hourly_rate}"

    class Meta:
        ordering = ('user', '-work_date')


class EmployeeExpense(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    expense_date = models.DateField(null=False)
    amount = models.FloatField(null=False, blank=False)
    notes = models.TextField(null=True)

    @classmethod
    def get_user_current_month_expenses(cls, user):
        total_current_month_earning = cls.objects.filter(
            expense_date__month=datetime.datetime.now().month,
            user=user
        ).values('user').annotate(total_expenses=Sum('amount')).order_by('user').first()

        return total_current_month_earning.get('total_expenses', 0)

    get_user_current_month_expenses.short_description = 'Current month Expenses'

    def __str__(self):
        return f"{self.user}-{self.expense_date}-{self.amount}"

    class Meta:
        ordering = ('user', '-expense_date')


class Invoice(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    amount = models.FloatField()
