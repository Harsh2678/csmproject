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