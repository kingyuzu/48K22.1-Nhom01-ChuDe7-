from typing import TypedDict
from django.core.paginator import Paginator
from .models import *


class ProductAdditionalInfo(TypedDict):
    stock: int
    aisles: list[str]


def get_product_with_stock_status_business_logic(
    status: int,  # 0: All, 1: In stock, 2: Out of stock
    page: int = 1,
    page_size: int = 10,
    category_filter: list[int] = None
) -> tuple[list[Product], list[str], list[ProductAdditionalInfo], Paginator]:
    # Find all products
    if category_filter is None:
        products = Product.objects.all()
    else:
        products = Product.objects.filter(
            category_id__in=category_filter
        )

    # Get pagination data
    paginator = Paginator(products, page_size)
    page_object = paginator.page(page)

    # Out of stock messages
    out_of_stock_messages = []

    # Find products that are out of stock
    additional_info: list[ProductAdditionalInfo] = []
    all_products = []

    out_of_stock_additional_info = []
    out_of_stock_products = []

    in_stock_additional_info = []
    in_stock_products = []
    for product in page_object.object_list:
        all_products.append(product)

        # Count the number of items of the product
        product_items = Item.objects.filter(product_id=product)

        # Get additional info
        product_additional_info: ProductAdditionalInfo = {
            'stock': product_items.count(),
            'aisles': set(product_items.values_list('aisle_id__code', flat=True))
        }
        additional_info.append(product_additional_info)

        product_count = product_additional_info['stock']

        if product_count == 0:
            out_of_stock_products.append(product)
            out_of_stock_messages.append(
                f"Product {product.sku} is out of stock"
            )
            out_of_stock_additional_info.append(product_additional_info)
        elif product_count <= product.min_stock:
            out_of_stock_products.append(product)
            out_of_stock_messages.append(
                f"Product {product.sku} is running out of stock ({product_count}/{product.min_stock})"
            )
            out_of_stock_additional_info.append(product_additional_info)
        else:
            in_stock_products.append(product)
            in_stock_additional_info.append(product_additional_info)

    if status == 0:
        return all_products, out_of_stock_messages, additional_info, paginator
    elif status == 1:
        return in_stock_products, out_of_stock_messages, in_stock_additional_info, paginator
    elif status == 2:
        return out_of_stock_products, out_of_stock_messages, out_of_stock_additional_info, paginator


def update_product_business_logic(
    product_id: int,
    updated_stock_value: int
):
    product = Product.objects.get(product_id=product_id)
    product_stock = Item.objects.filter(product_id=product).count()

    if updated_stock_value < product_stock:
        items = Item.objects.filter(
            product_id=product
        )
        items_to_delete = items[:product_stock - updated_stock_value]
        for item in items_to_delete:
            item.delete()

        return None

    elif updated_stock_value > product_stock:
        aisles = Aisle.objects.filter(category_id=product.category_id)

        total_available_capacity = 0
        aisle_map = {}
        for aisle in aisles:
            remaining_capacity = aisle.capacity - \
                Item.objects.filter(aisle_id=aisle).count()
            if remaining_capacity > 0:
                aisle_map[aisle] = remaining_capacity
                total_available_capacity += remaining_capacity

        if total_available_capacity < updated_stock_value - product_stock:
            return f"Unable to update the stock of product {product.sku}. The total available capacity is {total_available_capacity}"

        for _ in range(updated_stock_value - product_stock):
            aisle = max(aisle_map, key=aisle_map.get)
            Item.objects.create(
                product_id=product,
                aisle_id=aisle
            )
            aisle_map[aisle] -= 1

        return None

    return None


def import_product_business_logic(
    user: User,
    supplier: Supplier,
    product: Product,
    note: str,
    payment: str,
    quantity: int,
    import_price: float
):
    # Find the aisle of the product by category
    aisles = Aisle.objects.filter(category_id=product.category_id)

    # Count the remaining capacity of each aisle
    total_available_capacity = 0
    aisle_map = {}
    for aisle in aisles:
        remaining_capacity = aisle.capacity - \
            Item.objects.filter(aisle_id=aisle).count()
        if remaining_capacity > 0:
            aisle_map[aisle] = remaining_capacity
            total_available_capacity += remaining_capacity

    # Check if there is enough capacity to add the items
    if total_available_capacity < quantity:
        return f"Unable to import {quantity} items of product {product.sku}. The total available capacity is {total_available_capacity}"

    # Create import receipt
    ImportReceipt.objects.create(
        supplier_id=supplier,
        user_id=user,
        product_id=product,
        note=note,
        payment=payment,
        quantity=quantity,
        import_price=import_price
    )

    # Add items
    for _ in range(quantity):
        # Find the aisle with the most remaining capacity
        aisle = max(aisle_map, key=aisle_map.get)

        # Add item to the aisle
        Item.objects.create(
            product_id=product,
            aisle_id=aisle
        )

        # Update the remaining capacity of the aisle
        aisle_map[aisle] -= 1

    return None


def export_product_business_logic(
    user: User,
    recipient_name: str,
    recipient_contact: str,
    product: Product,
    note: str,
    payment: str,
    quantity: int,
    export_price: float
):
    # Find the items to be exported
    items = Item.objects.filter(
        product_id=product,
    )[:quantity]

    # Check if there are enough items to export
    total_items = items.count()
    if total_items < quantity:
        return f"Unable to export {quantity} items of product {product.sku}. There are only {total_items} items available"

    # Create export receipt
    ExportReceipt.objects.create(
        recipient_name=recipient_name,
        recipient_contact=recipient_contact,
        user_id=user,
        product_id=product,
        note=note,
        payment=payment,
        quantity=quantity,
        export_price=export_price
    )

    # Remove items
    for item in items:
        item.delete()

    return None


def get_report_business_logic(
    category: Category,
    start_date: str,
    end_date: str
) -> tuple[
    int,  # Stock before period
    int,  # Stock after period
    int,  # Total stock value
    dict[str, int],  # Product numbers
    dict[str, int],  # Supplier numbers
    dict[str, int]  # Stock values
]:
    # Get all the receipts before the period
    import_receipts_before = ImportReceipt.objects.filter(
        date__lt=start_date
    )
    export_receipts_before = ExportReceipt.objects.filter(
        date__lt=start_date
    )

    # Calculate the stock before the period
    stock_before_period = 0
    for import_receipt in import_receipts_before:
        stock_before_period += import_receipt.quantity
    for export_receipt in export_receipts_before:
        stock_before_period -= export_receipt.quantity

    # Get all the receipts end at the period
    import_receipts_end = ImportReceipt.objects.filter(
        date__lte=end_date
    )
    export_receipts_end = ExportReceipt.objects.filter(
        date__lte=end_date
    )

    # Calculate the stock after the period
    stock_after_period = 0
    for import_receipt in import_receipts_end:
        stock_after_period += import_receipt.quantity
    for export_receipt in export_receipts_end:
        stock_after_period -= export_receipt.quantity

    # Get all products in the category
    products = Product.objects.filter(category_id=category)

    # Calculate the total stock value
    total_stock_value = 0
    product_numbers = {}
    stock_values = {}

    for product in products:
        # Number of items of the product
        product_items = Item.objects.filter(product_id=product).count()

        # Calculate the stock value of the product
        stock_value = product.price * product_items
        total_stock_value += stock_value
        stock_values[product.sku] = float(stock_value)

        # Count the number of products
        product_numbers[product.sku] = product_items

    # Get all import receipts in the period
    import_receipts = ImportReceipt.objects.filter(
        date__range=[start_date, end_date]
    )

    # Count the number of suppliers
    supplier_numbers = {}
    for import_receipt in import_receipts:
        if import_receipt.supplier_id.name in supplier_numbers:
            supplier_numbers[import_receipt.supplier_id.name] += 1
        else:
            supplier_numbers[import_receipt.supplier_id.name] = 1

    return stock_before_period, stock_after_period, total_stock_value, product_numbers, supplier_numbers, stock_values
