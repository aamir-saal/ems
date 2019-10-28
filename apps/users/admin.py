from django.contrib import admin
from django.contrib.auth.models import User, Group

from apps.users.models import DocumentType, UserDocument, UserProfile, EmployeeExpense, EmployeeTimeSheet


class DocumentTypeAdmin(admin.ModelAdmin):

    class Meta:
        model = DocumentType


class UserDocumentAdmin(admin.ModelAdmin):
    list_display = ('user', 'document_type', 'name', 'description', 'issued_by', 'issued_date', 'expiry_date',
                    'image_tag')

    class Meta:
        model = UserDocument


class UserAdmin(admin.ModelAdmin):

    class Meta:
        model = User


class UserProfileAdmin(admin.ModelAdmin):

    list_display = ('user', 'profile_pic_tag', 'get_current_month_earning', 'get_current_month_expenses',
                    'get_current_month_net_salary')

    class Meta:
        model = UserProfile


class EmployeeTimeSheetAdmin(admin.ModelAdmin):
    list_display = ('user', 'work_date', 'hours', 'hourly_rate')

    class Meta:
        model = EmployeeTimeSheet


class EmployeeExpenseAdmin(admin.ModelAdmin):
    list_display = ('user', 'expense_date', 'amount', 'notes')

    class Meta:

        model = EmployeeExpense


admin.site.unregister(User)
admin.site.unregister(Group)

admin.site.register(User, UserAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(DocumentType, DocumentTypeAdmin)
admin.site.register(UserDocument, UserDocumentAdmin)
admin.site.register(EmployeeTimeSheet, EmployeeTimeSheetAdmin)
admin.site.register(EmployeeExpense, EmployeeExpenseAdmin)
