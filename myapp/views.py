from django.shortcuts import redirect, render, get_object_or_404
try:
    import razorpay  # type: ignore
except Exception:
    razorpay = None
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from cmsproject.models import Category, SubCategory, Product, Cart, CartItem, Order, OrderItem, ShippingInfo
from .forms import ShippingInfoForm
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.contrib.auth import get_user_model

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
    # persist on cart
    cart.cart_subtotal = subtotal
    cart.tax_amount = tax
    cart.cart_total = total
    cart.save(update_fields=["cart_subtotal", "tax_amount", "cart_total"])
    return render(request, "cart.html", {
        "cart": cart,
        "subtotal": subtotal,
        "tax": tax,
        "total": total,
    })


@login_required
def checkout(request):
    cart = get_object_or_404(Cart, user=request.user)
    items = cart.items.select_related("product")
    if not items.exists():
        return redirect("products")
    # compute current totals for display
    subtotal = sum(item.product.product_price * item.quantity for item in items)
    tax = (subtotal * Decimal('0.08')).quantize(Decimal('0.01'))
    total = (subtotal + tax).quantize(Decimal('0.01'))
    # Only render; order is created after successful payment
    return render(request, "checkout.html", {"cart": cart, "items": items, "subtotal": subtotal, "tax": tax, "total": total, "form": ShippingInfoForm()})


@login_required
def order_success(request):
    return render(request, "order_success.html")

@login_required
def order_error(request):
    message = request.GET.get('message') or "Payment failed. Please try another method."
    return render(request, "order_error.html", {"message": message})

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

# duplicate checkout removed
@login_required
def order(request):
    orders = Order.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "order.html", {
        'orders': orders,
    })

@require_POST
def start_payment(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication required"}, status=401)
    """Validate shipping, create a Razorpay order for the cart total, store shipping in session."""
    cart = get_object_or_404(Cart, user=request.user)
    items = cart.items.select_related("product")
    if not items.exists():
        return JsonResponse({"error": "Cart is empty"}, status=400)

    form = ShippingInfoForm(request.POST)
    if not form.is_valid():
        return JsonResponse({"errors": form.errors}, status=400)

    subtotal = sum(item.product.product_price * item.quantity for item in items)
    tax = (subtotal * Decimal('0.08')).quantize(Decimal('0.01'))
    total = (subtotal + tax).quantize(Decimal('0.01'))

    amount_paise = int(total * 100)
    # Razorpay requires minimum amount of 100 paise (₹1)
    if amount_paise < 100:
        amount_paise = 100
    if razorpay is None:
        return JsonResponse({"error": "Razorpay SDK not installed"}, status=500)
    try:
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        order = client.order.create({
            "amount": amount_paise,
            "currency": "INR",
            "payment_capture": 1,
            "notes": {
                "user_id": str(request.user.id),
            },
            "receipt": f"rcpt_{request.user.id}_{cart.id}",
        })
    except Exception as exc:
        return JsonResponse({"error": f"Failed to create Razorpay order: {exc}"}, status=500)

    # Save shipping temporarily in session to use after verification
    request.session['pending_shipping'] = form.cleaned_data
    request.session['pending_razorpay_order_id'] = order.get('id')

    callback_url = request.build_absolute_uri(reverse("verify_payment"))
    return JsonResponse({
        "razorpay_key": settings.RAZORPAY_KEY_ID,
        "order": order,
        "amount": amount_paise,
        "currency": "INR",
        "name": "ShopEase",
        "description": "Order Payment",
        "callback_url": callback_url,
        "prefill": {
            "name": f"{form.cleaned_data.get('shipping_first_name')} {form.cleaned_data.get('shipping_last_name')}",
            "email": form.cleaned_data.get('shipping_email'),
            "contact": form.cleaned_data.get('shipping_phone_number'),
        }
    })

@csrf_exempt
def verify_payment(request):
    if razorpay is None:
        return JsonResponse({"status": "failed", "message": "Razorpay SDK not installed"}, status=500)
    data = request.POST if request.method == "POST" else request.GET
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    # Helper to return error depending on AJAX vs redirect callback
    def respond_error(message, status=400):
        is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
        if is_ajax:
            return JsonResponse({"status": "failed", "message": message}, status=status)
        return redirect(f"{reverse('order_error')}?message={message}")

    try:
        client.utility.verify_payment_signature({
            "razorpay_order_id": data["razorpay_order_id"],
            "razorpay_payment_id": data["razorpay_payment_id"],
            "razorpay_signature": data["razorpay_signature"],
        })
    except Exception:
        return respond_error("Signature verification failed", status=400)

    # Determine user: prefer session user, else fall back to order notes
    user = request.user if request.user.is_authenticated else None
    if user is None:
        try:
            rp_order = client.order.fetch(data.get("razorpay_order_id"))
            user_id_str = (rp_order.get("notes") or {}).get("user_id")
            if user_id_str:
                UserModel = get_user_model()
                user = UserModel.objects.get(pk=int(user_id_str))
        except Exception:
            user = None
    if user is None:
        return respond_error("User not found for payment", status=400)

    # Recompute totals and create Order
    cart = get_object_or_404(Cart, user=user)
    items = cart.items.select_related("product")
    if not items.exists():
        return respond_error("Cart empty", status=400)

    subtotal = sum(item.product.product_price * item.quantity for item in items)
    tax = (subtotal * Decimal('0.08')).quantize(Decimal('0.01'))
    total = (subtotal + tax).quantize(Decimal('0.01'))

    order_obj = Order.objects.create(
        user=user,
        subtotal=subtotal,
        tax_amount=tax,
        total_price=total,
        razorpay_order_id=data.get("razorpay_order_id"),
        razorpay_payment_id=data.get("razorpay_payment_id"),
        razorpay_signature=data.get("razorpay_signature"),
        payment_method="razorpay",
        payment_status="paid",
    )

    for item in items:
        OrderItem.objects.create(
            order=order_obj,
            product=item.product,
            quantity=item.quantity,
            unit_price=item.product.product_price,
            line_total=item.product.product_price * item.quantity,
        )

    shipping_data = request.session.pop('pending_shipping', None)
    if shipping_data:
        ShippingInfo.objects.create(
            order=order_obj,
            user=user,
            shipping_first_name=shipping_data.get('shipping_first_name'),
            shipping_last_name=shipping_data.get('shipping_last_name'),
            shipping_email=shipping_data.get('shipping_email'),
            shipping_phone_number=shipping_data.get('shipping_phone_number'),
            shipping_address=shipping_data.get('shipping_address'),
            shipping_city=shipping_data.get('shipping_city'),
            shipping_zipcode=shipping_data.get('shipping_zipcode'),
            shipping_state=shipping_data.get('shipping_state'),
        )

    # Clear cart
    items.delete()
    cart.cart_subtotal = Decimal('0.00')
    cart.tax_amount = Decimal('0.00')
    cart.cart_total = Decimal('0.00')
    cart.save(update_fields=["cart_subtotal", "tax_amount", "cart_total"])

    # Attempt to fetch and store more payment details (best-effort)
    try:
        payment_info = client.payment.fetch(data.get("razorpay_payment_id"))
        if payment_info:
            order_obj.payment_details = payment_info
            method = payment_info.get('method')
            if method:
                order_obj.payment_method = method
            # Extract method-specific fields
            if method == 'upi':
                order_obj.upi_vpa = payment_info.get('vpa')
            elif method == 'card':
                order_obj.card_last4 = payment_info.get('card', {}).get('last4') if isinstance(payment_info.get('card'), dict) else payment_info.get('last4')
                order_obj.card_network = payment_info.get('card', {}).get('network') if isinstance(payment_info.get('card'), dict) else payment_info.get('network')
                order_obj.card_type = payment_info.get('card', {}).get('type') if isinstance(payment_info.get('card'), dict) else payment_info.get('type')
            elif method == 'netbanking':
                order_obj.bank_name = payment_info.get('bank') or payment_info.get('bank_name')
            elif method == 'wallet':
                order_obj.wallet_provider = payment_info.get('wallet') or payment_info.get('provider')
            order_obj.save(update_fields=[
                "payment_details", "payment_method", "upi_vpa", "card_last4", "card_network", "card_type", "bank_name", "wallet_provider"
            ])
    except Exception:
        pass

    # Cleanup session
    request.session.pop('pending_razorpay_order_id', None)

    # If called via Razorpay redirect (netbanking), send an HTTP redirect to success page
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
    if not is_ajax:
        return redirect("order_success")
    return JsonResponse({"status": "success", "redirect_url": redirect("order_success").url})

