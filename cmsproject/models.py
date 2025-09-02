from django.db import models
from django.db.models import UniqueConstraint
from django.db.models.functions import Lower
from django.core.exceptions import ValidationError

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
