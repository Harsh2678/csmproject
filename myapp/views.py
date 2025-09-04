from django.shortcuts import render, get_object_or_404
from cmsproject.models import Category, SubCategory

def home(request):
    categories = Category.objects.all()
    context = {
        'categories': categories
    }
    return render(request, "home.html", context)

def about(request):
    return render(request, "about.html")


def subcategories(request, category_id):
    category = get_object_or_404(Category, pk=category_id)
    sub_categories = SubCategory.objects.filter(category=category).order_by('sub_category_name')
    context = {
        'category': category,
        'sub_categories': sub_categories,
    }
    return render(request, "subcategories.html", context)
