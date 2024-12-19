from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _

# ----------------- USER ----------------- #


class UserRole(models.TextChoices):
    '''
    Enum define User roles
    '''
    SUPERUSER = 'superuser', _('Superuser')
    MANAGER = 'manager', _('Manager')
    USER = 'user', _('User')


class UserManager(BaseUserManager):
    '''
    Manager for User model
    '''

    def create_user(self, username, email, password=None, **extra_fields):
        '''
        Create user
        '''
        if not username:
            raise ValueError(_('The Username must be set'))
        if not email:
            raise ValueError(_('The Email must be set'))

        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        '''
        Create superuser
        '''
        extra_fields.setdefault('role', UserRole.SUPERUSER)
        return self.create_user(username, email, password, **extra_fields)


class User(AbstractUser):
    '''
    User model
    '''
    user_id = models.AutoField(primary_key=True, auto_created=True)
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(max_length=256, unique=True)
    role = models.CharField(
        max_length=50, choices=UserRole.choices, default=UserRole.USER)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)

    objects = UserManager()

    # By default, all account can be logged in to dashboard
    is_staff = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.username


# ----------------- PRODUCT ----------------- #

class Category(models.Model):
    '''
    Category of product
    '''
    category_id = models.AutoField(primary_key=True, auto_created=True)
    name = models.CharField(max_length=256)

    def __str__(self):
        return self.name


class Aisle(models.Model):
    '''
    Aisle in the store
    '''
    aisle_id = models.AutoField(primary_key=True, auto_created=True)
    code = models.CharField(max_length=50)
    description = models.CharField(max_length=256, blank=True)
    capacity = models.IntegerField(default=0)
    category_id = models.ForeignKey(Category, on_delete=models.CASCADE)

    def __str__(self):
        return self.code


class Product(models.Model):
    '''
    Represent for a type of product
    '''
    product_id = models.AutoField(primary_key=True, auto_created=True)
    sku = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=256, blank=True)
    description = models.TextField(blank=True)
    photo = models.ImageField(upload_to='products', blank=True)
    unit = models.CharField(max_length=50, blank=True)
    min_stock = models.IntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category_id = models.ForeignKey(Category, on_delete=models.CASCADE)

    def __str__(self):
        return f"[{self.sku}] {self.name}"


class Item(models.Model):
    '''
    Represent for an item of product
    '''
    item_id = models.AutoField(primary_key=True, auto_created=True)
    product_id = models.ForeignKey(Product, on_delete=models.CASCADE)
    aisle_id = models.ForeignKey(Aisle, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.product_id)


# ----------------- RECEIPT ----------------- #

class PaymentMethod(models.TextChoices):
    '''
    Enum define Payment methods
    '''
    CASH = 'cash', _('Cash')
    CREDIT_CARD = 'credit_card', _('Credit Card')
    DEBIT_CARD = 'debit_card', _('Debit Card')
    PAYPAL = 'paypal', _('Paypal')


class Supplier(models.Model):
    '''
    Supplier of product
    '''
    supplier_id = models.AutoField(primary_key=True, auto_created=True)
    name = models.CharField(max_length=256)
    email = models.EmailField(max_length=256)
    address = models.CharField(max_length=256)
    phone = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class ImportReceipt(models.Model):
    '''
    A receipt of importing product
    '''
    receipt_id = models.AutoField(primary_key=True, auto_created=True)
    date = models.DateField(auto_now=True)
    supplier_id = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    product_id = models.ForeignKey(Product, on_delete=models.CASCADE)
    note = models.TextField(blank=True)
    payment = models.CharField(
        max_length=50, choices=PaymentMethod.choices, default=PaymentMethod.CASH)
    quantity = models.IntegerField()
    import_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.supplier_id.name} -> {self.user_id.username}"


class ExportReceipt(models.Model):
    '''
    A receipt of exporting product
    '''
    receipt_id = models.AutoField(primary_key=True, auto_created=True)
    date = models.DateField(auto_now=True)
    recipient_name = models.CharField(max_length=256)
    recipient_contact = models.CharField(max_length=256)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    product_id = models.ForeignKey(Product, on_delete=models.CASCADE)
    note = models.TextField(blank=True)
    payment = models.CharField(
        max_length=50, choices=PaymentMethod.choices, default=PaymentMethod.CASH)
    quantity = models.IntegerField()
    export_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.user_id.username} -> {self.recipient_name}"
