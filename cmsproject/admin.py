from django.contrib import admin
from django.utils.html import format_html
from .models import Category, SubCategory, Product, Order, OrderItem
from .category_forms import CategoryForm
from .sub_category_forms import SubCategoryForm
from .product_forms import ProductForm
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import CustomUser


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

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductForm
    list_display = ('get_category', 'sub_category','product_name', 'product_price', 'product_quantity', 'product_description', 'image_preview')
    search_fields = ('sub_category__sub_category_name', 'sub_category__category__category_name', 'product_name', 'product_price', 'product_quantity', 'product_description')
    list_filter = ('sub_category', 'sub_category__category', 'product_name', 'product_price', 'product_quantity')
    
    def image_preview(self, obj):
        if obj.product_image:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 50px; object-fit: cover; border-radius: 4px;" />',
                obj.product_image.url
            )
        return "No image"
    
    
    readonly_fields = ('image_preview',)
    fields = ('sub_category', 'product_name', 'product_image', 'product_price', 'product_quantity', 'product_description', 'image_preview')

    def get_category(self, obj):
        return obj.sub_category.category
    get_category.short_description = 'category'
    get_category.admin_order_field = 'sub_category__category__category_name'

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'quantity', 'unit_price', 'line_total', 'product_image_preview')
    fields = ('product', 'product_image_preview', 'quantity', 'unit_price', 'line_total')

    def has_add_permission(self, request, obj=None):
        return False  # remove "Add another" button inline

    def has_change_permission(self, request, obj=None):
        return False  # disable editing inline records

    def has_delete_permission(self, request, obj=None):
        return False  # disable deleting inline records

    def has_view_history_permission(self, request, obj=None):
        return False  # remove History button inline

    def product_image_preview(self, obj):
        if obj.product.product_image:
            return format_html(
                '<img src="{}" style="max-height:40px;max-width:40px;object-fit:cover;border-radius:4px;" />',
                obj.product.product_image.url)
        return "No image"
    product_image_preview.short_description = "Product Image"


class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at', 'subtotal', 'tax_amount', 'total_price', 'payment_status')
    search_fields = ('id', 'user__username', 'user__email')
    list_filter = ('payment_status', 'created_at')
    inlines = [OrderItemInline]
    readonly_fields = ('subtotal', 'tax_amount', 'total_price', 'created_at')

    def has_add_permission(self, request):
        return False  # remove Add button for Orders

    def has_change_permission(self, request, obj=None):
        return False  # disable editing order

    def has_delete_permission(self, request, obj=None):
        return False  # disable deleting order

    def has_view_history_permission(self, request, obj=None):
        return False  # remove History button on order

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        extra_context = extra_context or {}
        # Hide all save and delete buttons
        extra_context['show_save'] = False
        extra_context['show_save_and_continue'] = False
        extra_context['show_save_and_add_another'] = False
        extra_context['show_delete'] = False
        return super().changeform_view(request, object_id, form_url, extra_context)


admin.site.register(Order, OrderAdmin)

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser

    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'profile_photo_preview')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email', 'phone_number', 'profile_photo')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    readonly_fields = ('profile_photo_preview', 'last_login', 'date_joined')

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )

    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)

    def profile_photo_preview(self, obj):
        if obj.profile_photo:
            return format_html('<img src="{}" style="height:50px; width:50px; border-radius:50%;" />', obj.profile_photo.url)
        return "-"
    profile_photo_preview.short_description = "Profile Photo"