from django.contrib import admin
from django.utils.html import format_html
from .models import Category
from .category_forms import CategoryForm

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    form = CategoryForm
    list_display = ('category_name', 'image_preview')
    search_fields = ('category_name',)
    list_filter = ('category_name',)
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 50px; object-fit: cover; border-radius: 4px;" />',
                obj.image.url
            )
        return "No image"
    
    
    readonly_fields = ('image_preview',)
    fields = ('category_name', 'image', 'image_preview')
