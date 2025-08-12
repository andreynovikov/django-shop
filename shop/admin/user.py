from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.utils.translation import gettext_lazy as _

# from tagging.models import Tag, TaggedItem
from import_export import resources
from import_export.admin import ExportMixin
from django_admin_listfilter_dropdown.filters import SimpleDropdownFilter, DropdownFilter

from shop.models import ShopUser

from .widgets import TagAutoComplete


class UserCreationForm(forms.ModelForm):
    error_messages = {
        'password_mismatch': _("The two password fields didn't match."),
    }
    password1 = forms.CharField(label=_("Password"),
                                widget=forms.PasswordInput)
    password2 = forms.CharField(label=_("Password confirmation"),
                                widget=forms.PasswordInput,
                                help_text=_("Enter the same password as above, for verification."))

    class Meta:
        model = ShopUser
        fields = '__all__'

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(
                self.error_messages['password_mismatch'],
                code='password_mismatch',
            )
        return password2

    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField(help_text=_("Raw passwords are not stored, so there is no way to see "
                                                     "this user's password, but you can change the password "
                                                     "using <a href=\"../password/\">this form</a>."))

    class Meta:
        model = ShopUser
        fields = '__all__'
        widgets = {
            'tags': TagAutoComplete(model=ShopUser),
        }

    def clean_password(self):
        # Regardless of what the user provides, return the initial value.
        # This is done here, rather than on the field, because the
        # field does not have access to the initial value
        return self.initial["password"]


class TagListFilter(SimpleDropdownFilter):
    """
    Filter records by tags for the current model only. Tags are sorted alphabetically by name.
    """
    title = _('tags')
    parameter_name = 'tag'

    def lookups(self, request, model_admin):
        model_tags = []  # tag.name for tag in Tag.objects.usage_for_model(model_admin.model)]
        model_tags.sort()
        return tuple([(tag, tag) for tag in model_tags])

    def queryset(self, request, queryset):
        if self.value() is not None:
            # return ShopUser.tagged.with_all(self.value(), queryset)
            # return TaggedItem.objects.get_by_model(queryset, self.value())
            return None


class ShopUserResource(resources.ModelResource):
    class Meta:
        model = ShopUser
        import_id_fields = ['phone']
        exclude = ('id', 'password', 'groups', 'is_active', 'is_staff', 'is_superuser', 'tags')


class ShopUserAdmin(ExportMixin, UserAdmin):
    # The forms to add and change user instances
    form = UserChangeForm
    add_form = UserCreationForm

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = ('phone', 'name', 'email', 'discount', 'bonuses', 'tags', 'is_staff', 'is_superuser')
    list_filter = (('discount', DropdownFilter), TagListFilter, 'groups', 'is_staff', 'is_superuser')
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        (None, {
            'fields': ('phone', 'name', 'password1', 'password2')
        }),
    )
    search_fields = ('phone', 'name', 'email', 'tags')
    ordering = ('phone', 'name')
    filter_horizontal = ()
    # change_list_template = 'admin/change_list_filter_sidebar.html'
    # change_list_filter_template = 'admin/filter_listing.html'
    resource_class = ShopUserResource
    change_form_template = 'loginas/change_form.html'

    def get_fieldsets(self, request, obj=None):
        if not obj:
            return super().get_fieldsets(request, obj)
        fieldsets = [
            (None, {'fields': ('phone', 'password', 'permanent_password')}),
            ('Personal info', {'fields': ('name', 'username', 'email', 'postcode', 'city', 'address')}),
            ('Marketing', {'fields': ('discount', 'bonuses', 'tags')}),
            ('Important dates', {'fields': ('last_login',)}),
        ]
        # if obj is None or obj.is_firm:
        #     fieldsets[2][1]['fields'].extend(('firm_address', 'firm_details'))
        if request.user.is_superuser:
            fieldsets.append(('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}))
        return fieldsets


# Now register the new UserAdmin...
admin.site.register(ShopUser, ShopUserAdmin)
