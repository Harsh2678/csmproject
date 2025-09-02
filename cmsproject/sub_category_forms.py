from django import forms
from .models import SubCategory
import os

class SubCategoryForm(forms.ModelForm):
    class Meta:
        model = SubCategory
        fields = "__all__"
    
    def clean_category(self):
        category = self.cleaned_data.get("category")
        if not category:
            raise forms.ValidationError("Category is required.")  # ✅ Only this will show
        return category

    def clean_image(self):
        image = self.cleaned_data.get("sub_category_image")

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
