import re
from django import forms
from .models import *


class AddProductForm(forms.Form):
    sku = forms.CharField(
        label="SKU",
        widget=forms.TextInput(),
        required=True
    )
    name = forms.CharField(
        label="Name",
        widget=forms.TextInput(),
        required=True
    )
    categories = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        label="Category",
        widget=forms.Select(),
        required=True
    )
    description = forms.CharField(
        label="Description",
        widget=forms.Textarea(),
        required=False
    )
    unit = forms.CharField(
        label="Unit",
        widget=forms.TextInput(),
        required=True
    )
    min_stock = forms.IntegerField(
        label="Minimum stock",
        widget=forms.NumberInput(),
        required=True
    )
    price = forms.DecimalField(
        label="Price",
        widget=forms.NumberInput(),
        required=True
    )
    photo = forms.ImageField(
        label="Photo",
        widget=forms.FileInput(),
        required=False
    )


class ImportForm(forms.Form):
    suppliers = forms.ModelChoiceField(
        queryset=Supplier.objects.all(),
        label="Supplier",
        widget=forms.Select(),
        required=True
    )
    products = forms.ModelChoiceField(
        queryset=Product.objects.all(),
        label="Product",
        widget=forms.Select(),
        empty_label="Select a product",
        required=True
    )
    note = forms.CharField(
        label="Note",
        widget=forms.Textarea(),
        required=False
    )
    payments = forms.ChoiceField(
        choices=PaymentMethod.choices,
        label="Payment",
        widget=forms.Select(),
        required=True
    )
    quantity = forms.IntegerField(
        label="Quantity",
        widget=forms.NumberInput(),
        required=True
    )
    import_price = forms.DecimalField(
        label="Import price",
        widget=forms.NumberInput(),
        required=True
    )


class ExportForm(forms.Form):
    recipient_name = forms.CharField(
        label="Recipient name",
        widget=forms.TextInput(),
        required=True
    )
    recipient_contact = forms.CharField(
        label="Recipient contact",
        widget=forms.TextInput(),
        required=True
    )
    products = forms.ModelChoiceField(
        queryset=Product.objects.all(),
        label="Product",
        widget=forms.Select(),
        required=True
    )
    note = forms.CharField(
        label="Note",
        widget=forms.Textarea(),
        required=False,
    )
    payments = forms.ChoiceField(
        choices=PaymentMethod.choices,
        label="Payment",
        widget=forms.Select(),
        required=True
    )
    quantity = forms.IntegerField(
        label="Quantity",
        widget=forms.NumberInput(),
        required=True
    )
    export_price = forms.DecimalField(
        label="Export price",
        widget=forms.NumberInput(),
        required=True
    )

    # Form validator
    def clean_recipient_contact(self):
        contact = self.cleaned_data.get('recipient_contact')
        # Define a regex for phone number validation
        phone_regex = r'^\+?[1-9]\d{9,14}$'  # E.164 format

        if not re.match(phone_regex, contact):
            raise forms.ValidationError(
                "Enter a valid phone number, including the country code (e.g., +123456789).")

        return contact


class ReportForm(forms.Form):
    start_date = forms.DateField(
        label="Start date",
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'id': 'report-form-start-date'
        })
    )
    end_date = forms.DateField(
        label="End date",
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'id': 'report-form-end-date'
        })
    )
    categories = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        label="Category",
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'report-form-category'
        }),
        empty_label="All categories"
    )
