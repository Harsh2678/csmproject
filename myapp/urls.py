from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("category/<int:category_id>/", views.subcategories, name="category_subcategories"),
    path("products/", views.products, name="products"),
]
