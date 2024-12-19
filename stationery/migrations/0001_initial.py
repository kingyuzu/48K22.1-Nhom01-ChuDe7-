from pathlib import Path
import pandas as pd
import random
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models
from django.contrib.auth.hashers import make_password

# Intialized data paths
USER_CSV_PATH = Path(__file__).parent / "data" / "users.csv"
CATEGORY_CSV_PATH = Path(__file__).parent / "data" / "categories.csv"
SUPPLIER_CSV_PATH = Path(__file__).parent / "data" / "suppliers.csv"
AISLE_CSV_PATH = Path(__file__).parent / "data" / "aisles.csv"
PRODUCT_CSV_PATH = Path(__file__).parent / "data" / "products.csv"


def load_user_models_from_csv(apps, _):
    '''
    Load User models from CSV file
    '''
    User = apps.get_model("stationery", "User")
    user_data = pd.read_csv(USER_CSV_PATH, encoding="utf-8")
    for _, row in user_data.iterrows():
        username = row["username"]
        email = row["email"]
        password = make_password(row["password"])
        role = row["role"]
        first_name = row["firstname"]
        last_name = row["lastname"]

        User.objects.create(
            username=username,
            email=email,
            password=password,
            role=role,
            is_staff=True,
            is_superuser=True,
            is_active=True,
            first_name=first_name,
            last_name=last_name
        )


def load_category_models_from_csv(apps, _):
    '''
    Load Category models from CSV file
    '''
    Category = apps.get_model("stationery", "Category")
    category_data = pd.read_csv(CATEGORY_CSV_PATH, encoding="utf-8")
    for _, row in category_data.iterrows():
        name = row["name"]
        Category.objects.create(name=name)


def load_supplier_models_from_csv(apps, _):
    '''
    Load Supplier models from CSV file
    '''
    Supplier = apps.get_model("stationery", "Supplier")
    supplier_data = pd.read_csv(SUPPLIER_CSV_PATH, encoding="utf-8")
    for _, row in supplier_data.iterrows():
        name = row["name"]
        email = row["email"]
        address = row["address"]
        phone = row["phone"]
        Supplier.objects.create(
            name=name,
            email=email,
            address=address,
            phone=phone
        )


def load_aisle_models_from_csv(apps, _):
    '''
    Load Aisle models from CSV file
    '''
    Aisle = apps.get_model("stationery", "Aisle")
    Category = apps.get_model("stationery", "Category")
    aisle_data = pd.read_csv(AISLE_CSV_PATH, encoding="utf-8")
    for _, row in aisle_data.iterrows():
        code = row["code"]
        description = row["description"]
        capacity = row["capacity"]
        category_id = row["category_id"]
        Aisle.objects.create(
            code=code,
            description=description,
            capacity=capacity,
            category_id=Category.objects.get(category_id=category_id)
        )


def load_products_from_csv(apps, _):
    '''
    Load Products from CSV file
    '''
    Product = apps.get_model("stationery", "Product")
    Category = apps.get_model("stationery", "Category")
    Aisle = apps.get_model("stationery", "Aisle")
    Item = apps.get_model("stationery", "Item")
    product_data = pd.read_csv(PRODUCT_CSV_PATH, encoding="utf-8")
    for _, row in product_data.iterrows():
        sku = row["sku"]
        name = row["name"]
        unit = row["unit"]
        min_stock = row["min_stock"]
        category_id = row["category_id"]
        amount = row["amount"]
        price = random.randint(1, 100) * 1000

        aisles = Aisle.objects.filter(category_id=category_id)
        aisle_map = {aisle: aisle.capacity for aisle in aisles}

        product = Product.objects.create(
            sku=sku,
            name=name,
            unit=unit,
            min_stock=min_stock,
            price=price,
            category_id=Category.objects.get(category_id=category_id),
        )

        for _ in range(amount):
            aisle = max(aisle_map, key=aisle_map.get)
            Item.objects.create(
                product_id=product,
                aisle_id=aisle
            )
            aisle_map[aisle] -= 1


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="Category",
            fields=[
                (
                    "category_id",
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False
                    ),
                ),
                ("name", models.CharField(max_length=256)),
            ],
        ),
        migrations.CreateModel(
            name="Supplier",
            fields=[
                (
                    "supplier_id",
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False
                    ),
                ),
                ("name", models.CharField(max_length=256)),
                ("email", models.EmailField(max_length=256)),
                ("address", models.CharField(max_length=256)),
                ("phone", models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name="User",
            fields=[
                (
                    "user_id",
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False
                    ),
                ),
                ("password", models.CharField(
                    max_length=128, verbose_name="password")),
                (
                    "last_login",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="last login"
                    ),
                ),
                (
                    "first_name",
                    models.CharField(
                        blank=True, max_length=150, verbose_name="first name"
                    ),
                ),
                (
                    "last_name",
                    models.CharField(
                        blank=True, max_length=150, verbose_name="last name"
                    ),
                ),
                (
                    "date_joined",
                    models.DateTimeField(
                        default=django.utils.timezone.now, verbose_name="date joined"
                    ),
                ),
                ("username", models.CharField(max_length=150, unique=True)),
                ("email", models.EmailField(max_length=256, unique=True)),
                (
                    "role",
                    models.CharField(
                        choices=[
                            ("superuser", "Superuser"),
                            ("manager", "Manager"),
                            ("user", "User"),
                        ],
                        default="user",
                        max_length=50,
                    ),
                ),
                ("is_staff", models.BooleanField(default=True)),
                ("is_superuser", models.BooleanField(default=True)),
                ("is_active", models.BooleanField(default=True)),
                (
                    "groups",
                    models.ManyToManyField(
                        blank=True,
                        help_text="The groups this user belongs to. A user will get all permissions granted to each of their groups.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.group",
                        verbose_name="groups",
                    ),
                ),
                (
                    "user_permissions",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Specific permissions for this user.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.permission",
                        verbose_name="user permissions",
                    ),
                ),
            ],
            options={
                "verbose_name": "user",
                "verbose_name_plural": "users",
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Aisle",
            fields=[
                (
                    "aisle_id",
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False
                    ),
                ),
                ("code", models.CharField(max_length=50)),
                ("description", models.CharField(blank=True, max_length=256)),
                ("capacity", models.IntegerField(default=0)),
                (
                    "category_id",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="stationery.category",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Product",
            fields=[
                (
                    "product_id",
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False
                    ),
                ),
                ("sku", models.CharField(max_length=50)),
                ("name", models.CharField(blank=True, max_length=256)),
                ("description", models.TextField(blank=True)),
                ("photo", models.ImageField(blank=True, upload_to="products")),
                ("unit", models.CharField(blank=True, max_length=50)),
                ("min_stock", models.IntegerField(default=0)),
                ("price", models.DecimalField(decimal_places=2, max_digits=10)),
                (
                    "category_id",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="stationery.category",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Item",
            fields=[
                (
                    "item_id",
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False
                    ),
                ),
                (
                    "aisle_id",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="stationery.aisle",
                    ),
                ),
                (
                    "product_id",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="stationery.product",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ExportReceipt",
            fields=[
                (
                    "receipt_id",
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False
                    ),
                ),
                ("date", models.DateField(auto_now=True)),
                ("recipient_name", models.CharField(max_length=256)),
                ("recipient_contact", models.CharField(max_length=256)),
                ("note", models.TextField(blank=True)),
                (
                    "payment",
                    models.CharField(
                        choices=[
                            ("cash", "Cash"),
                            ("credit_card", "Credit Card"),
                            ("debit_card", "Debit Card"),
                            ("paypal", "Paypal"),
                        ],
                        default="cash",
                        max_length=50,
                    ),
                ),
                ("quantity", models.IntegerField()),
                ("export_price", models.DecimalField(
                    decimal_places=2, max_digits=10)),
                (
                    "user_id",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "product_id",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="stationery.product",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ImportReceipt",
            fields=[
                (
                    "receipt_id",
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False
                    ),
                ),
                ("date", models.DateField(auto_now=True)),
                ("note", models.TextField(blank=True)),
                (
                    "payment",
                    models.CharField(
                        choices=[
                            ("cash", "Cash"),
                            ("credit_card", "Credit Card"),
                            ("debit_card", "Debit Card"),
                            ("paypal", "Paypal"),
                        ],
                        default="cash",
                        max_length=50,
                    ),
                ),
                ("quantity", models.IntegerField()),
                ("import_price", models.DecimalField(
                    decimal_places=2, max_digits=10)),
                (
                    "user_id",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "product_id",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="stationery.product",
                    ),
                ),
                (
                    "supplier_id",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="stationery.supplier",
                    ),
                ),
            ],
        ),
        migrations.RunPython(load_user_models_from_csv),
        migrations.RunPython(load_category_models_from_csv),
        migrations.RunPython(load_supplier_models_from_csv),
        migrations.RunPython(load_aisle_models_from_csv),
        migrations.RunPython(load_products_from_csv),
    ]
