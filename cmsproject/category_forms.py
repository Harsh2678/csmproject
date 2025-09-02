from django import forms
from .models import Category
import os

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = "__all__"

    def clean_image(self):
        image = self.cleaned_data.get("image")

        if not image:
            return image

        # Extension check
        ext = os.path.splitext(image.name)[1].lower()
        valid_extensions = [".jpg", ".jpeg", ".png"]
        if ext not in valid_extensions:
            raise forms.ValidationError("Only .jpg, .jpeg and .png formats are allowed.")

        # Size check (10 KB)
        max_size = 10 * 1024
        if image.size > max_size:
            raise forms.ValidationError("Image size must not exceed 10 KB.")

        return image
