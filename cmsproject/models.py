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
