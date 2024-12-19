from django import forms
from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.http import HttpRequest
from .models import (
    User,
    UserRole,
    Category,
    Aisle,
    Product,
    Item,
    Supplier,
    ImportReceipt,
    ExportReceipt,
)

admin.site.site_header = 'Stationery Management System'
admin.site.site_title = 'Stationery Management System'


# ----------------- USER ----------------- #


admin.site.unregister(Group)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    '''
    Define display and filter for User model
    '''
    list_display = ('username', 'email', 'role')
    list_filter = ('role',)
    fieldsets = [
        (
            "User Information",
            {
                'fields': ('username', 'password', 'email', 'first_name', 'last_name')
            }
        ),
        (
            "Permission",
            {
                'fields': ('role',)
            }
        )
    ]
    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': ('username', 'email', 'password1', 'password2', 'role', 'first_name', 'last_name')
            }
        ),
    )

    def has_module_permission(self, request: HttpRequest) -> bool:
        allow_list = [UserRole.SUPERUSER]
        if isinstance(request.user, User) and request.user.role in allow_list:
            return True
        return False


# ----------------- PRODUCT ----------------- #


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)

    def has_module_permission(self, request: HttpRequest) -> bool:
        allow_list = [UserRole.MANAGER, UserRole.SUPERUSER]
        if isinstance(request.user, User) and request.user.role in allow_list:
            return True
        return False


@admin.register(Aisle)
class AisleAdmin(admin.ModelAdmin):
    list_display = ('code', 'capacity', 'category_id')
    list_filter = ('category_id',)

    def has_module_permission(self, request: HttpRequest) -> bool:
        allow_list = [UserRole.MANAGER, UserRole.SUPERUSER]
        if isinstance(request.user, User) and request.user.role in allow_list:
            return True
        return False


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('sku', 'name', 'unit', 'min_stock',
                    'price', 'category_id')
    list_filter = ('price', 'category_id')

    def has_module_permission(self, request: HttpRequest) -> bool:
        allow_list = [UserRole.MANAGER, UserRole.SUPERUSER]
        if isinstance(request.user, User) and request.user.role in allow_list:
            return True
        return False


class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get('product_id')
        aisle = cleaned_data.get('aisle_id')

        if product.category_id != aisle.category_id:
            raise forms.ValidationError(
                "Product and aisle must have the same category")

        if Item.objects.filter(aisle_id=aisle).count() >= aisle.capacity:
            raise forms.ValidationError("Aisle is full")

        return cleaned_data


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    form = ItemForm
    list_display = ('product_id', 'aisle_id')
    list_filter = ('product_id', 'aisle_id')

    def has_module_permission(self, request: HttpRequest) -> bool:
        allow_list = [UserRole.MANAGER, UserRole.SUPERUSER]
        if isinstance(request.user, User) and request.user.role in allow_list:
            return True
        return False


# ----------------- RECEIPT ----------------- #


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'address')
    list_filter = ('name',)

    def has_module_permission(self, request: HttpRequest) -> bool:
        allow_list = [UserRole.MANAGER, UserRole.SUPERUSER]
        if isinstance(request.user, User) and request.user.role in allow_list:
            return True
        return False


@admin.register(ImportReceipt)
class ImportReceiptAdmin(admin.ModelAdmin):
    list_display = ('date', 'supplier_id', 'user_id',
                    'product_id', 'payment', 'quantity', 'import_price')
    list_filter = ('supplier_id', 'user_id', 'product_id', 'payment')

    def has_add_permission(self, request: HttpRequest) -> bool:
        # Unregistered user can't add new import receipt in admin page
        return False

    def has_module_permission(self, request: HttpRequest) -> bool:
        allow_list = [UserRole.MANAGER, UserRole.SUPERUSER]
        if isinstance(request.user, User) and request.user.role in allow_list:
            return True
        return False


@admin.register(ExportReceipt)
class ExportReceiptAdmin(admin.ModelAdmin):
    list_display = ('date', 'recipient_name', 'user_id',
                    'product_id', 'payment', 'quantity', 'export_price')
    list_filter = ('user_id', 'product_id', 'payment')

    def has_add_permission(self, request: HttpRequest) -> bool:
        # Unregistered user can't add new export receipt in admin page
        return False

    def has_module_permission(self, request: HttpRequest) -> bool:
        allow_list = [UserRole.MANAGER, UserRole.SUPERUSER]
        if isinstance(request.user, User) and request.user.role in allow_list:
            return True
        return False
