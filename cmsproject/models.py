from django.db import models
from django.db.models import UniqueConstraint
from django.db.models.functions import Lower
from django.core.exceptions import ValidationError


class Category(models.Model):
    category_name = models.CharField(max_length=255, unique=True)
    image = models.ImageField(upload_to="categories/")

    class Meta:
        constraints = [
            UniqueConstraint(
                Lower("category_name"), 
                name="unique_category_name_ci"  # case-insensitive uniqueness
            )
        ]
    
    def clean(self):
        """Custom validation for case-insensitive uniqueness."""
        if Category.objects.exclude(pk=self.pk).filter(category_name__iexact=self.category_name).exists():
            raise ValidationError({"category_name": "Category already exists (case-insensitive)."})

    def __str__(self):
        return self.category_name
