from django.contrib import admin
from django.utils.html import format_html
from .models import Category, SubCategory
from .category_forms import CategoryForm
from .sub_category_forms import SubCategoryForm

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

@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    form = SubCategoryForm
    list_display = ('category', 'sub_category_name', 'image_preview')
    search_fields = ('sub_category_name', 'category__category_name')
    list_filter = ('sub_category_name', 'category__category_name')
    
    def image_preview(self, obj):
        if obj.sub_category_image:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 50px; object-fit: cover; border-radius: 4px;" />',
                obj.sub_category_image.url
            )
        return "No image"
    
    
    readonly_fields = ('image_preview',)
    fields = ('category', 'sub_category_name', 'sub_category_image', 'image_preview')
