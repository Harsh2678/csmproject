from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("list_categories/", views.list_categories, name="list_categories"),
    path("about/", views.about, name="about"),
    path("category/<int:category_id>/", views.subcategories, name="category_subcategories"),
    path("products/", views.products, name="products"),
    path("products/sub/<int:subcategory_id>/", views.products_by_subcategory, name="products_by_subcategory"),
    path("cart/add/<int:product_id>/", views.add_to_cart, name="add_to_cart"),
    path("cart/", views.cart_view, name="cart"),
    path("cart/update/<int:item_id>/", views.update_cart, name="update_cart"),
    path("cart/remove/<int:item_id>/", views.remove_from_cart, name="remove_from_cart"),
    path("checkout/", views.checkout, name="checkout"),
    path("order/success/", views.order_success, name="order_success"),
    path("order/error/", views.order_error, name="order_error"),
    path("order/", views.order, name="order"),
    path("payment/start/", views.start_payment, name="start_payment"),
    path("payment/verify/", views.verify_payment, name="verify_payment"),
    path("profile/", views.profile, name="profile")
]
