from django.db import models
from django.db.models import UniqueConstraint
from django.db.models.functions import Lower
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User  # or your custom user

class Category(models.Model):
    category_name = models.CharField(max_length=255)
    image = models.ImageField(upload_to="categories/", null=True, blank=True)

    class Meta:
        constraints = [
            UniqueConstraint(
                Lower("category_name"),
                name="unique_category_name_ci"
            )
        ]

    def clean(self):
        """Model-level validation (works outside Admin too)."""

        # Case-insensitive uniqueness
        if Category.objects.exclude(pk=self.pk).filter(category_name__iexact=self.category_name).exists():
            raise ValidationError({"category_name": "Category already exists."})

    def save(self, *args, **kwargs):
        self.full_clean()  # ensures validation always runs
        super().save(*args, **kwargs)

    def __str__(self):
        return self.category_name

class SubCategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    sub_category_name = models.CharField(max_length=255)
    sub_category_image = models.ImageField(upload_to="sub_categories/", null=True, blank=True)

    class Meta:
        constraints = [
            UniqueConstraint(
                Lower("sub_category_name"),
                "category",
                name="unique_sub_category_per_category_ci"
            )
        ]

    def clean(self):
        if not self.category_id:
            raise ValidationError({"category": "Category is required."})

        if SubCategory.objects.exclude(pk=self.pk).filter(sub_category_name__iexact=self.sub_category_name, category=self.category).exists():
            raise ValidationError({"sub_category_name": "Sub Category already exists."})
        
        if self.sub_category_name and len(self.sub_category_name) < 3:
            raise ValidationError({"sub_category_name": "Sub Category name must be at least 3 characters long."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.sub_category_name

class Product(models.Model):
    sub_category = models.ForeignKey(SubCategory, on_delete=models.CASCADE)
    product_name = models.CharField(max_length=255)
    product_image = models.ImageField(upload_to="products/", null=True, blank=True)
    product_price = models.DecimalField(max_digits=10, decimal_places=2)
    product_description = models.TextField(null=True, blank=True)
    product_quantity = models.IntegerField()
    product_created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            UniqueConstraint(
                Lower("product_name"),
                "sub_category",
                name="unique_product_per_sub_category_ci"
            )
        ]
    
    def clean(self):
        if not self.sub_category_id:
            raise ValidationError({"sub_category": "Sub Category is required."})
        
        if Product.objects.exclude(pk=self.pk).filter(product_name__iexact=self.product_name, sub_category=self.sub_category).exists():
            raise ValidationError({"product_name": "Product already exists."})
        
        if self.product_name and len(self.product_name) < 3:
            raise ValidationError({"product_name": "Product name must be at least 3 characters long."})
        
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.product_name

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="carts")
    created_at = models.DateTimeField(auto_now_add=True)
    cart_subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cart_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f"Cart {self.id} for {self.user.username}"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey("Product", on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} × {self.product.product_name}"

    @property
    def total_price(self):
        return self.product.product_price * self.quantity


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    created_at = models.DateTimeField(auto_now_add=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    # Razorpay identifiers for reconciliation
    razorpay_order_id = models.CharField(max_length=255, null=True, blank=True)
    razorpay_payment_id = models.CharField(max_length=255, null=True, blank=True)
    razorpay_signature = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"Order {self.id} by {self.user.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    line_total = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} × {self.product.product_name}"

class ShippingInfo(models.Model):
    from django.core.validators import RegexValidator

    STATE_CHOICES = [
        ("CA", "California"),
        ("NY", "New York"),
        ("TX", "Texas"),
        ("FL", "Florida"),
        ("IL", "Illinois"),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="shipping_info")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="shipping_infos")
    shipping_first_name = models.CharField(
        max_length=255,
        validators=[RegexValidator(r'^[A-Za-z\s-]+$', "This field may only contain letters, spaces, and hyphens.")]
    )
    shipping_last_name = models.CharField(
        max_length=255,
        validators=[RegexValidator(r'^[A-Za-z\s-]+$', "This field may only contain letters, spaces, and hyphens.")]
    )
    shipping_email = models.EmailField(max_length=255)
    shipping_phone_number = models.CharField(
        max_length=10,
        validators=[RegexValidator(r"^\+?\d{10}$", "Enter a valid phone number.")]
    )
    shipping_address = models.CharField(max_length=255)
    shipping_city = models.CharField(max_length=255)
    shipping_zipcode = models.CharField(
        max_length=7,
        validators=[RegexValidator(r"^\+?\d{6}$", "Enter a valid ZIP/Postal code.")]
    )
    shipping_state = models.CharField(max_length=2, choices=STATE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Rely on ModelForm field validators/messages for per-field errors