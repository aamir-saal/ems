from enum import Enum

from django.db import models

from django.contrib.auth.models import Permission, AbstractUser
from django.db.models.signals import post_migrate
from django.contrib.contenttypes.models import ContentType

from django.core.validators import MinValueValidator
from django.db.models import Sum
from django.utils.safestring import mark_safe

from django.conf import settings
from simple_history.models import HistoricalRecords


class User(AbstractUser):
    profile_pic = models.FileField()

    class Meta:
        verbose_name = 'Employee'
        verbose_name_plural = 'Employees'
        permissions = (
            ('CAN_VIEW_UserProfile', 'Can View UserProfile'),
        )

    def __str__(self):
        return self.get_full_name()

    def profile_pic_tag(self):
        return mark_safe(f'<img src="{settings.MEDIA_URL}/{self.profile_pic}" width="50" height="50" />')

    profile_pic_tag.short_description = 'Picture'

    def _total_earning(self):
        return "{:.2f}".format(Ledger.user_total_expenses_or_earning(
            self, ExpenseTypes.SALARY.name))

    _total_earning.short_description = "Total Earning"

    def _total_expenses(self):
        return "{:.2f}".format(Ledger.user_total_expenses_or_earning(self, ExpenseTypes.EXPENSE_ADVANCE.name))

    _total_expenses.short_description = "Total Expenses"

    def _current_balance(self):
        total_earning = Ledger.user_total_expenses_or_earning(
            self, ExpenseTypes.SALARY.name)
        total_expenses = Ledger.user_total_expenses_or_earning(
            self, ExpenseTypes.EXPENSE_ADVANCE.name)
        current_balance = total_earning - total_expenses
        color = 'style="color: red;"' if current_balance < 0 else ''
        current_balance = "{:.2f}".format(current_balance)
        return mark_safe(f'<span {color}>{current_balance}</span>')

    _current_balance.short_description = "Current Balance"


class TimeStampedModel(models.Model):
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class WorkSite(TimeStampedModel):
    name = models.CharField(max_length=550)
    location = models.CharField(max_length=550)

    class Meta:
        permissions = (
            ('CAN_VIEW_WorkSite', 'Can View WorkSite'),
        )

    def __str__(self):
        return f"{self.name}"


class DocumentType(Enum):
    PASSPORT = "Passport"
    VISA = "Visa"
    LABOUR_CARD = "Labour card"
    EMIRATES_ID = "Emirates ID"
    HOME_COUNTRY_ID = "Home country ID"

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]


class UserDocument(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    document_type = models.CharField(choices=DocumentType.choices(), max_length=550)
    name = models.CharField(max_length=256, null=False, blank=True)
    description = models.CharField(max_length=512, null=False, blank=True)
    issued_by = models.CharField(max_length=256, null=False, blank=True)
    issued_date = models.DateField(null=True)
    expiry_date = models.DateField(null=True)
    image = models.FileField()

    class Meta:
        permissions = (
            ('CAN_VIEW_UserDocument', 'Can View UserDocument'),
        )

    def __str__(self):
        return "{}'s {}".format(self.user, self.document_type)

    def image_tag(self):
        return mark_safe(f'<img src="{settings.MEDIA_URL}/{self.image}" width="50" height="50" />')

    image.short_description = 'Image'


class TimeSheetMonthlyRecord(TimeStampedModel):
    work_month = models.DateField(null=False)
    time_sheet_file = models.FileField()
    work_site = models.ForeignKey(WorkSite, on_delete=models.PROTECT, null=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        permissions = (
            ('CAN_VIEW_TimeSheetMonthlyRecord', 'Can View TimeSheetMonthlyRecord'),
        )
    
    def __str__(self):
        return f"{self.work_month.strftime('%B, %Y')}({self.work_site})"


class ExpenseTypes(Enum):
    EXPENSE_ADVANCE = 'Expense_or_advance'
    SALARY = 'Salary'

    @classmethod
    def choices(cls):
        return tuple((choice.name, choice.value) for choice in cls)


class Ledger(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='ledgers')
    type = models.CharField(
        choices=ExpenseTypes.choices(),
        max_length=50
    )
    expense_date = models.DateField(null=False)
    amount = models.FloatField(null=False, blank=False)
    notes = models.TextField(null=True)

    time_sheet_record = models.ForeignKey(TimeSheetMonthlyRecord, null=True, on_delete=models.SET_NULL, blank=True)
    hours = models.FloatField(validators=[MinValueValidator(0.0)], null=True, blank=True)
    hourly_rate = models.FloatField(validators=[MinValueValidator(0.0)], null=True, blank=True)
    trade = models.CharField(max_length=255, null=True, blank=True)

    history = HistoricalRecords()

    class Meta:
        ordering = ('-expense_date', 'user', 'type')
        permissions = (
            ('CAN_VIEW_Ledger', 'Can View Ledger'),
        )

    @classmethod
    def user_total_expenses_or_earning(cls, user, expense_type):
        total_expense_or_earning = cls.objects.filter(
                    user=user, type=expense_type
                ).values('user').annotate(total=Sum('amount')).order_by('user').first()

        return total_expense_or_earning.get('total') if total_expense_or_earning else 0


def add_view_only_permission(sender, **kwargs):
    '''This creates a view only permission for sender'''
    for content_type in ContentType.objects.all():
        codename = 'can_view_%s' % content_type.model
        name = 'Can View %s' % content_type.name
        if not Permission.objects.filter(
            content_type=content_type,
            codename=codename):
            Permission.objects.create(
            content_type=content_type,
            codename=codename,
            name=name)

post_migrate.connect(add_view_only_permission)
