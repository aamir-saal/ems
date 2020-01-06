from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.db.models import Sum
from simple_history.admin import SimpleHistoryAdmin

from apps.users.forms import LedgerModelForm
from apps.users.models import UserDocument, UserProfile, WorkSite, TimeSheetMonthlyRecord, Ledger


class UserDocumentAdmin(admin.ModelAdmin):
    list_display = ('user', 'document_type', 'name', 'description', 'issued_by', 'issued_date', 'expiry_date',
                    'image_tag')

    list_filter = ('user', 'document_type')

    class Meta:
        model = UserDocument


class UserAdmin(admin.ModelAdmin):

    class Meta:
        model = User


class UserProfileAdmin(admin.ModelAdmin):

    list_display = ('user', 'profile_pic_tag', '_total_expenses', '_total_earning', '_current_balance')

    def get_queryset(self, request):
        queryset = super(UserProfileAdmin, self).get_queryset(request)
        # queryset2 = queryset.annotate(total_expenses=Sum('user__ledgers__amount'))
        return queryset

    class Meta:
        model = UserProfile


class WorkSiteAdmin(SimpleHistoryAdmin):
    list_display = ('id', 'name', 'location')

    class Meta:
        model = WorkSite


class LedgerAdmin(admin.ModelAdmin):
    list_display = ['user', 'type', 'expense_date', 'amount', 'notes', 'time_sheet_record', 'hours', 'hourly_rate',
                    'trade']

    list_filter = ['type', 'user', 'expense_date']

    form = LedgerModelForm

    class Meta:
        model = Ledger


class MonthlySheetAdmin(admin.ModelAdmin):

    list_display = ['work_month', 'time_sheet_file', 'work_site', 'notes']

    class Meta:
        model = TimeSheetMonthlyRecord


admin.site.unregister(User)
admin.site.unregister(Group)

admin.site.register(User, UserAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(UserDocument, UserDocumentAdmin)
admin.site.register(WorkSite, WorkSiteAdmin)
admin.site.register(TimeSheetMonthlyRecord, MonthlySheetAdmin)
admin.site.register(Ledger, LedgerAdmin)
