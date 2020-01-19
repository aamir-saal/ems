from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Permission, Group
from django.utils.translation import gettext_lazy as _

from apps.users.forms import LedgerModelForm, UserChangeForm
from apps.users.models import UserDocument, WorkSite, TimeSheetMonthlyRecord, Ledger, User

from django.contrib.admin.options import flatten_fieldsets
from django.contrib.admin.templatetags.admin_modify import register
from django.contrib.admin.templatetags.admin_modify import submit_row as original_submit_row


class ReadOnlyModelAdmin(admin.ModelAdmin):
    """
    ModelAdmin class that prevents modifications through the admin.
    The changelist and the detail view work, but a 403 is returned
    if one actually tries to edit an object.
    Source: https://gist.github.com/aaugustin/1388243
    """
    actions = None

    # We cannot call super().get_fields(request, obj) because that method calls
    # get_readonly_fields(request, obj), causing infinite recursion. Ditto for
    # super().get_form(request, obj). So we  assume the default ModelForm.
    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return []
        return self.fields or [f.name for f in self.model._meta.fields]

    def has_change_permission(self, request, obj=None):
        return True if request.user.is_superuser else (request.method in ['GET', 'HEAD'] and
                                                       request.user.is_staff)

    def has_module_permission(self, request):
        return request.user.is_superuser or request.user.is_staff

    def get_readonly_fields(self, request, obj=None):
        user = request.user
        if user.is_staff and not user.is_superuser:
            if self.fieldsets:
                return flatten_fieldsets(self.fieldsets or [])
            else:
                return list(set(
                    [field.name for field in self.opts.local_fields] +
                    [field.name for field in self.opts.local_many_to_many]))

        return super().get_readonly_fields(request, obj)

    @register.inclusion_tag('admin/submit_line.html', takes_context=True)
    def submit_row(context):
        ctx = original_submit_row(context)

        user = context['request'].user
        if user.is_staff and not user.is_superuser:
            ctx.update({
                'show_save_and_add_another': False,
                'show_save_and_continue': False,
                'show_save': False,
                'show_save_as_new': False,
            })
        return ctx

    def has_view_permission(self, request, obj=None):
        return request.user.is_staff


class UserDocumentAdmin(ReadOnlyModelAdmin):
    list_display = ('user', 'document_type', 'name', 'description', 'issued_by', 'issued_date', 'expiry_date',
                    'image_tag')

    list_filter = ('user', 'document_type')

    class Meta:
        model = UserDocument

    def get_queryset(self, request):
        queryset = super(UserDocumentAdmin, self).get_queryset(request)
        if not request.user.is_superuser:
            queryset = queryset.filter(user=request.user)
        return queryset

    def get_list_filter(self, request):
        if not request.user.is_superuser:
            return []
        return self.list_filter


class EmployeeAdmin(ReadOnlyModelAdmin, UserAdmin):
    form = UserChangeForm

    list_display = ('id', '_name', 'profile_pic_tag', '_total_expenses', '_total_earning', '_current_balance')

    def get_queryset(self, request):
        queryset = super(EmployeeAdmin, self).get_queryset(request)
        if not request.user.is_superuser:
            queryset = queryset.filter(pk=request.user.pk)
        # queryset2 = queryset.annotate(total_expenses=Sum('user__ledgers__amount'))
        return queryset

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2')
        }),
    )

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'profile_pic')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    class Meta:
        model = User

    @staticmethod
    def _name(obj):
        return obj.get_full_name() or obj.username
    _name.short_description = "Name"

    def get_list_filter(self, request):
        if not request.user.is_superuser:
            return []
        return self.list_filter

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if not request.user.is_superuser:
            readonly_fields.extend(
                ['is_superuser', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions',
                 ])
            readonly_fields = tuple(readonly_fields)
        return readonly_fields

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        is_superuser = request.user.is_superuser
        disabled_fields = set()  # type: Set[str]

        if not is_superuser:
            disabled_fields |= {
                'username',
                'is_superuser',
                'date_joined',
            }

        for f in disabled_fields:
            if f in form.base_fields:
                form.base_fields[f].disabled = True

        return form


class WorkSiteAdmin(ReadOnlyModelAdmin):
    list_display = ('id', 'name', 'location')

    class Meta:
        model = WorkSite

    def has_module_permission(self, request):
        return True if request.user.is_superuser else False


class LedgerAdmin(ReadOnlyModelAdmin):
    list_display = ['user', 'type', 'expense_date', 'amount', 'notes', 'time_sheet_record', 'hours', 'hourly_rate',
                    'trade']

    list_filter = ['type', 'expense_date']

    form = LedgerModelForm

    class Meta:
        model = Ledger

    def get_queryset(self, request):
        queryset = super(LedgerAdmin, self).get_queryset(request)
        if not request.user.is_superuser:
            queryset = queryset.filter(user=request.user)
        return queryset

    def get_list_filter(self, request):
        list_filter = self.list_filter
        if request.user.is_superuser:
            self.list_filter.append('user')
        return list_filter


class MonthlySheetAdmin(ReadOnlyModelAdmin):

    list_display = ['work_month', 'time_sheet_file', 'work_site', 'notes']

    class Meta:
        model = TimeSheetMonthlyRecord


admin.site.unregister(Group)

admin.site.register(User, EmployeeAdmin)
admin.site.register(UserDocument, UserDocumentAdmin)
admin.site.register(WorkSite, WorkSiteAdmin)
admin.site.register(TimeSheetMonthlyRecord, MonthlySheetAdmin)
admin.site.register(Ledger, LedgerAdmin)
