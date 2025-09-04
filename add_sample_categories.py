#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cmsproject.settings')
django.setup()

from cmsproject.models import Category

# Create sample categories
categories_data = [
    {'category_name': 'Electronics'},
    {'category_name': 'Fashion'},
    {'category_name': 'Home & Living'},
    {'category_name': 'Sports'},
    {'category_name': 'Books'},
    {'category_name': 'Toys'},
]

# Add categories to database
for cat_data in categories_data:
    category, created = Category.objects.get_or_create(
        category_name=cat_data['category_name']
    )
    if created:
        print(f"Created category: {category.category_name}")
    else:
        print(f"Category already exists: {category.category_name}")

print(f"\nTotal categories in database: {Category.objects.count()}")
