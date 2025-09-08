from django.shortcuts import redirect, render, get_object_or_404
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from cmsproject.models import Category, SubCategory, Product, Cart, CartItem

def home(request):
    categories = Category.objects.all()
    products = Product.objects.order_by('-id')[:4]
    context = {
        'categories': categories,
        'products': products,
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

def products(request):
    products = Product.objects.order_by('-id')
    context = {
        'products': products
    }
    return render(request, "products.html", context)

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    cart, created = Cart.objects.get_or_create(user=request.user)

    # check if product already in cart
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        cart_item.quantity += 1
        cart_item.save()

    return redirect("cart")  # create a cart page view/template

@login_required
def cart_view(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    items = cart.items.all()
    subtotal = sum(item.product.product_price * item.quantity for item in items)
    tax = (subtotal * Decimal('0.08')).quantize(Decimal('0.01'))
    total = (subtotal + tax).quantize(Decimal('0.01'))
    return render(request, "cart.html", {
        "cart": cart,
        "subtotal": subtotal,
        "tax": tax,
        "total": total,
    })

@login_required
def update_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "increase":
            item.quantity += 1
            item.save()
        elif action == "decrease" and item.quantity > 1:
            item.quantity -= 1
            item.save()
    return redirect("cart")

@login_required
def remove_from_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    item.delete()
    return redirect("cart")

@login_required
def checkout(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    items = cart.items.all()
    subtotal = sum(item.product.product_price * item.quantity for item in items)
    tax = (subtotal * Decimal('0.08')).quantize(Decimal('0.01'))
    total = (subtotal + tax).quantize(Decimal('0.01'))
    return render(request, "checkout.html", {
        "cart": cart,
        "subtotal": subtotal,
        "tax": tax,
        "total": total,
    })
