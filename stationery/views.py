from typing import TypedDict
import json
from django.forms import formset_factory
from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from .models import (
    Category,
    Product,
    Item,
    ImportReceipt,
    ExportReceipt,
    PaymentMethod
)
from .forms import ImportForm, ExportForm, ReportForm, AddProductForm
from .controller import (
    get_product_with_stock_status_business_logic,
    update_product_business_logic,
    import_product_business_logic,
    export_product_business_logic,
    get_report_business_logic
)

# ------------------- Utils ------------------- #


def __format_price(price: float) -> str:
    return f'{price:,.0f}'


# ------------------- Authentication View ------------------- #


class AdminLoginView(LoginView):
    template_name = 'admin/login.html'  # Use the admin login template
    redirect_authenticated_user = True

    def get_success_url(self):
        # Redirect to your desired app after successful login
        # Replace with your app's home view name
        return reverse_lazy('view_products')


# ------------------- Product view ------------------- #


class DisplayProduct(TypedDict):
    id: int
    sku: str
    name: str
    unit: str
    stock: int
    min_stock: int
    price: float
    category: str
    aisle: str


@login_required
def view_products(request):
    # Get query params
    stock_status = int(request.GET.get('stock', 0))
    page = int(request.GET.get('page', 1))
    category_filter = request.GET.get('category', None)
    category_filter = [int(cat) for cat in category_filter.split(
        ',')] if category_filter else None

    # Categories
    categories = Category.objects.all()

    # Product list
    product_list: list[DisplayProduct] = []
    products, messages, additional_info, paginator = get_product_with_stock_status_business_logic(
        status=stock_status,
        page=page,
        category_filter=category_filter
    )
    for product, info in zip(products, additional_info):
        product_list.append({
            'id': product.product_id,
            'sku': product.sku,
            'name': product.name,
            'unit': product.unit,
            'stock': info['stock'],
            'min_stock': product.min_stock,
            'price': __format_price(product.price),
            'category': product.category_id.name,
            'aisle': ', '.join(info['aisles'])
        })

    context = {
        'categories': categories,
        'products': product_list,
        'out_of_stock_messages': messages if len(messages) > 0 else None,
        'stock_status': stock_status,
        'category_filter': category_filter,
        'page': page,
        'paginator': paginator
    }
    return render(request, 'products/products.html', context)


@login_required
def view_product_by_id(request, id):
    # If method is POST, then it is an delete request
    if request.method == 'POST':
        Product.objects.get(product_id=id).delete()
        return redirect('view_products')

    # Get product
    product = Product.objects.get(product_id=id)
    product.price = __format_price(product.price)

    product_count = Item.objects.filter(product_id=product).count()
    aisles = Item.objects.filter(product_id=product).values_list(
        'aisle_id__code', flat=True)

    context = {
        'user': request.user,
        'product': product,
        'stock': product_count,
        'aisles': ', '.join(set(aisles)),
        'is_out_of_stock': product_count == 0,
        'is_running_out_of_stock': product_count <= product.min_stock,
    }
    return render(request, 'products/view_product.html', context)


@login_required
def add_product(request):
    form = None
    if request.method == 'POST':
        form = AddProductForm(request.POST, request.FILES)
        if form.is_valid():
            sku = form.cleaned_data['sku']
            name = form.cleaned_data['name']
            category = form.cleaned_data['categories']
            description = form.cleaned_data['description']
            unit = form.cleaned_data['unit']
            min_stock = form.cleaned_data['min_stock']
            price = form.cleaned_data['price']
            photo = form.cleaned_data['photo']

            # Save to database
            product = Product(
                sku=sku,
                name=name,
                category_id=category,
                description=description,
                unit=unit,
                min_stock=min_stock,
                price=price,
                photo=photo
            )
            product.save()

            return redirect('view_products')

    context = {
        'user': request.user,
        'product': None,
        'form': form or AddProductForm()
    }
    return render(request, 'products/modify_product.html', context)


@login_required
def edit_product(request, id):
    form = None
    product = Product.objects.get(product_id=id)
    if request.method == 'POST':
        form = AddProductForm(request.POST, request.FILES)
        if form.is_valid():
            sku = form.cleaned_data['sku']
            name = form.cleaned_data['name']
            category = form.cleaned_data['categories']
            description = form.cleaned_data['description']
            unit = form.cleaned_data['unit']
            min_stock = form.cleaned_data['min_stock']
            price = form.cleaned_data['price']
            photo = form.cleaned_data['photo']

            # Save to database
            product.sku = sku if sku else product.sku
            product.name = name if name else product.name
            product.category_id = category if category else product.category_id
            product.description = description if description else product.description
            product.unit = unit if unit else product.unit
            product.min_stock = min_stock if min_stock else product.min_stock
            product.price = price if price else product.price
            product.photo = photo if photo else product.photo
            product.save()

            return redirect('view_products')

    context = {
        'user': request.user,
        'product': product,
        'form': form or AddProductForm()
    }
    return render(request, 'products/modify_product.html', context)


@login_required
def view_stock(request):
    # Query params
    status = int(request.GET.get('status', 0))

    err_message = None

    # If method is POST, then it is an update request
    if request.method == 'POST':
        inputs = {key.replace('product-stock-', ''): value for key, value in request.POST.items()
                  if key.startswith('product-stock-')}
        for product_id, stock_value in inputs.items():
            if stock_value == '':
                continue
            err_message = update_product_business_logic(
                int(product_id), int(stock_value))

    out_of_stock_product_count = 0
    running_out_of_stock_product_count = 0
    in_stock_product_count = 0
    display_products = []
    for product in Product.objects.all():
        product_count = Item.objects.filter(product_id=product).count()

        # Count product stock status
        if product_count == 0:
            out_of_stock_product_count += 1
        elif product_count <= product.min_stock:
            running_out_of_stock_product_count += 1
        else:
            in_stock_product_count += 1

        # If status is 0, then display all products
        if status == 0:
            display_products.append({
                'id': product.product_id,
                'sku': product.sku,
                'name': product.name,
                'min_stock': product.min_stock,
                'stock': product_count
            })

        # If status is 1, then display out of stock products
        elif status == 1 and product_count == 0:
            display_products.append({
                'id': product.product_id,
                'sku': product.sku,
                'name': product.name,
                'min_stock': product.min_stock,
                'stock': product_count
            })

        # If status is 2, then display running out of stock products
        elif status == 2 and product_count <= product.min_stock and product_count > 0:
            display_products.append({
                'id': product.product_id,
                'sku': product.sku,
                'name': product.name,
                'min_stock': product.min_stock,
                'stock': product_count
            })

        # If status is 3, then display in stock products
        elif status == 3 and product_count > product.min_stock:
            display_products.append({
                'id': product.product_id,
                'sku': product.sku,
                'name': product.name,
                'min_stock': product.min_stock,
                'stock': product_count
            })

        else:
            continue

    context = {
        'status': status,
        'products': display_products,
        'out_of_stock_count': out_of_stock_product_count,
        'running_out_of_stock_count': running_out_of_stock_product_count,
        'in_stock_count': in_stock_product_count,
        'err_message': err_message
    }
    return render(request, 'products/stocks.html', context)


# ------------------- Import and Export view ------------------- #


class DisplayImport(TypedDict):
    date: str
    supplier: str
    importer: str
    username: str
    product: str
    payment: str
    quantity: int
    import_price: float
    total_price: float


@login_required
def view_imports(request):
    # Render the form
    import_list: list[DisplayImport] = []
    imports = ImportReceipt.objects.all()
    for import_receipt in imports:
        import_list.append({
            'date': import_receipt.date.strftime('%Y-%m-%d'),
            'supplier': import_receipt.supplier_id.name,
            'importer': f"{import_receipt.user_id.first_name} {import_receipt.user_id.last_name}",
            'username': import_receipt.user_id.username,
            'product': import_receipt.product_id.name,
            'payment': import_receipt.payment,
            'quantity': import_receipt.quantity,
            'import_price': __format_price(import_receipt.import_price),
            'total_price': __format_price(import_receipt.quantity * import_receipt.import_price)
        })

    context = {
        'imports': import_list[::-1]
    }
    return render(request, 'imports/view_imports.html', context)


@login_required
def add_import(request):
    # Query params
    count = int(request.GET.get('count', 1))
    ImportFormSet = formset_factory(ImportForm, extra=count)

    formset = None
    errors = None
    if request.method == 'POST':
        formset = ImportFormSet(request.POST or None)
        if formset.is_valid():
            is_success = True
            for form in formset:
                # Create data
                supplier = form.cleaned_data['suppliers']
                product = form.cleaned_data['products']
                note = form.cleaned_data['note']
                payment = form.cleaned_data['payments']
                quantity = form.cleaned_data['quantity']
                import_price = form.cleaned_data['import_price']

                # Save to database
                err = import_product_business_logic(
                    request.user, supplier, product, note, payment, quantity, import_price)
                if not err:
                    continue
                else:
                    errors = err
                    is_success = False
                    break

            # Redirect
            if is_success:
                return redirect('view_imports')

    # Payment methods
    payment_methods = PaymentMethod.choices
    context = {
        'forms': formset or ImportFormSet(),
        'payments': payment_methods,
        'errors': errors
    }
    return render(request, 'imports/add_import.html', context)


class DisplayExport(TypedDict):
    date: str
    recipient_name: str
    recipient_contact: str
    exporter: str
    username: str
    product: str
    payment: str
    quantity: int
    export_price: float
    total_price: float


@login_required
def view_exports(request):
    # Export list
    export_list: list[DisplayExport] = []
    exports = ExportReceipt.objects.all()
    for export_receipt in exports:
        export_list.append({
            'date': export_receipt.date.strftime('%Y-%m-%d'),
            'recipient_name': export_receipt.recipient_name,
            'recipient_contact': export_receipt.recipient_contact,
            'exporter': f"{export_receipt.user_id.first_name} {export_receipt.user_id.last_name}",
            'username': export_receipt.user_id.username,
            'product': export_receipt.product_id.name,
            'payment': export_receipt.payment,
            'quantity': export_receipt.quantity,
            'export_price': __format_price(export_receipt.export_price),
            'total_price': __format_price(export_receipt.quantity * export_receipt.export_price)
        })

    context = {
        'exports': export_list[::-1]
    }
    return render(request, 'exports/view_exports.html', context)


@login_required
def add_export(request):
    # Query params
    count = int(request.GET.get('count', 1))
    ExportFormSet = formset_factory(ExportForm, extra=count)

    formset = None
    errors = None
    if request.method == 'POST':
        formset = ExportFormSet(request.POST or None)
        if formset.is_valid():
            is_success = True
            for form in formset:
                # Create data
                product = form.cleaned_data['products']
                recipient_name = form.cleaned_data['recipient_name']
                recipient_contact = form.cleaned_data['recipient_contact']
                note = form.cleaned_data['note']
                payment = form.cleaned_data['payments']
                quantity = form.cleaned_data['quantity']
                export_price = form.cleaned_data['export_price']

                # Save to database
                err = export_product_business_logic(
                    request.user, recipient_name, recipient_contact, product, note, payment, quantity, export_price)
                if not err:
                    continue
                else:
                    errors = err
                    is_success = False
                    break

            # Redirect if success
            if is_success:
                return redirect('view_exports')

    # Payment methods
    payment_methods = PaymentMethod.choices

    context = {
        'forms': formset or ExportFormSet(),
        'payments': payment_methods,
        'errors': errors
    }
    return render(request, 'exports/add_export.html', context)


# ------------------- Report view ------------------- #


@login_required
def report_view(request):
    # Variables
    form = None
    stock_before_period = None
    stock_after_period = None
    total_stock_value = None
    product_numbers = None
    supplier_numbers = None
    stock_values = None

    # Post request
    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            category = form.cleaned_data['categories']
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']

            # Get report
            stock_before_period, stock_after_period, total_stock_value, product_numbers, supplier_numbers, stock_values = get_report_business_logic(
                category, start_date, end_date
            )

    context = {
        'form': form or ReportForm(),
        'stock_before_period': stock_before_period,
        'stock_after_period': stock_after_period,
        'total_stock_value': __format_price(total_stock_value) if total_stock_value else None,
        'product_numbers': json.dumps(product_numbers) if product_numbers else None,
        'supplier_numbers': json.dumps(supplier_numbers) if supplier_numbers else None,
        'stock_values': json.dumps(stock_values) if stock_values else None
    }
    return render(request, 'reports/report.html', context)
