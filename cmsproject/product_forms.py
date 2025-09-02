from django import forms
from .models import Product
import os

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = "__all__"
    
    def clean_sub_category(self):
        sub_category = self.cleaned_data.get("sub_category")
        if not sub_category:
            raise forms.ValidationError("Sub Category is required.")
        return sub_category

    def clean_category(self):
        category = self.cleaned_data.get("category")
        if not category:
            raise forms.ValidationError("Category is required.")
        return category

    def clean_price(self):
        price = self.cleaned_data.get("product_price")
        if not price:
            raise forms.ValidationError("Price is required.")
        return price

    def clean_quantity(self):
        quantity = self.cleaned_data.get("product_quantity")
        if not quantity:
            raise forms.ValidationError("Quantity is required.")
        return quantity

    def clean_image(self):
        image = self.cleaned_data.get("product_image")
        if not image:
            return image
        ext = os.path.splitext(image.name)[1].lower()
        valid_extensions = [".jpg", ".jpeg", ".png"]
        if ext not in valid_extensions:
            raise forms.ValidationError("Only .jpg, .jpeg and .png formats are allowed.")
        return image