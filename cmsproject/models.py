import pprint
from django.db import models
from django.db.models import UniqueConstraint
from django.db.models.functions import Lower
from django.core.exceptions import ValidationError
import os

class Category(models.Model):
    category_name = models.CharField(max_length=255)
    image = models.ImageField(upload_to="categories/")

    class Meta:
        constraints = [
            UniqueConstraint(
                Lower("category_name"),
                name="unique_category_name_ci"  # case-insensitive uniqueness
            )
        ]

    def clean(self):
        """Custom validation for case-insensitive uniqueness and image rules."""

        # 🔹 Case-insensitive uniqueness
        if Category.objects.exclude(pk=self.pk).filter(category_name__iexact=self.category_name).exists():
            raise ValidationError({"category_name": "Category already exists."})

        # 🔹 Image validation
        if self.image:
            ext = os.path.splitext(self.image.name)[1].lower()  # file extension
            valid_extensions = ['.jpg', '.jpeg', '.png']
            if ext not in valid_extensions:
                raise ValidationError({"image": "Only .jpg, .jpeg and .png formats are allowed."})

            max_size = 10 * 1024  # 10 KB in bytes
            if self.image.size > max_size:
                raise ValidationError({"image": "Image size must not exceed 10 KB."})

    def save(self, *args, **kwargs):
        """Ensure validation runs before saving."""
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.category_name
