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
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.core.paginator import Paginator
from django.utils.http import urlencode

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

def list_categories(request):
    categories = Category.objects.all().order_by('category_name')
    return render(request, "list_categories.html", {"categories": categories})

def subcategories(request, category_id):
    category = get_object_or_404(Category, pk=category_id)
    sub_categories = SubCategory.objects.filter(category=category).order_by('sub_category_name')
    context = {
        'category': category,
        'sub_categories': sub_categories,
    }
    return render(request, "subcategories.html", context)

def products(request):
    products_qs = Product.objects.all()
    q = (request.GET.get('q') or '').strip()
    min_price = (request.GET.get('min_price') or '').strip()
    max_price = (request.GET.get('max_price') or '').strip()
    sort = (request.GET.get('sort') or '').strip()

    if q:
        products_qs = products_qs.filter(product_name__icontains=q)
    if min_price:
        try:
            products_qs = products_qs.filter(product_price__gte=min_price)
        except Exception:
            pass
    if max_price:
        try:
            products_qs = products_qs.filter(product_price__lte=max_price)
        except Exception:
            pass

    if sort == 'name_asc':
        products_qs = products_qs.order_by('product_name')
    elif sort == 'name_desc':
        products_qs = products_qs.order_by('-product_name')
    else:
        products_qs = products_qs.order_by('-id')

    paginator = Paginator(products_qs, 12)
    page_number = request.GET.get("page")
    products_page = paginator.get_page(page_number)

    # Preserve filters in pagination links
    querydict = request.GET.copy()
    if 'page' in querydict:
        del querydict['page']
    querystring = querydict.urlencode()

    context = {
        'products': products_page,
        'page_obj': products_page,
        'paginator': paginator,
        'q': q,
        'min_price': min_price,
        'max_price': max_price,
        'sort': sort,
        'querystring': querystring,
    }
    return render(request, "products.html", context)

def products_by_subcategory(request, subcategory_id):
    subcategory = get_object_or_404(SubCategory, pk=subcategory_id)
    products_qs = Product.objects.filter(sub_category=subcategory)

    q = (request.GET.get('q') or '').strip()
    min_price = (request.GET.get('min_price') or '').strip()
    max_price = (request.GET.get('max_price') or '').strip()
    sort = (request.GET.get('sort') or '').strip()

    if q:
        products_qs = products_qs.filter(product_name__icontains=q)
    if min_price:
        try:
            products_qs = products_qs.filter(product_price__gte=min_price)
        except Exception:
            pass
    if max_price:
        try:
            products_qs = products_qs.filter(product_price__lte=max_price)
        except Exception:
            pass

    if sort == 'name_asc':
        products_qs = products_qs.order_by('product_name')
    elif sort == 'name_desc':
        products_qs = products_qs.order_by('-product_name')
    else:
        products_qs = products_qs.order_by('-id')

    paginator = Paginator(products_qs, 12)
    page_number = request.GET.get("page")
    products_page = paginator.get_page(page_number)

    querydict = request.GET.copy()
    if 'page' in querydict:
        del querydict['page']
    querystring = querydict.urlencode()

    return render(request, "products.html", {
        "products": products_page,
        "subcategory": subcategory,
        "page_obj": products_page,
        "paginator": paginator,
        'q': q,
        'min_price': min_price,
        'max_price': max_price,
        'sort': sort,
        'querystring': querystring,
    })

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
    orders_qs = Order.objects.filter(user=request.user).order_by("-created_at")
    paginator = Paginator(orders_qs, 12)
    page_number = request.GET.get("page")
    orders_page = paginator.get_page(page_number)
    return render(request, "order.html", {
        'orders': orders_page,
        'page_obj': orders_page,
        'paginator': paginator,
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
                "shipping_first_name": form.cleaned_data.get('shipping_first_name') or '',
                "shipping_last_name": form.cleaned_data.get('shipping_last_name') or '',
                "shipping_email": form.cleaned_data.get('shipping_email') or '',
                "shipping_phone_number": form.cleaned_data.get('shipping_phone_number') or '',
                "shipping_address": form.cleaned_data.get('shipping_address') or '',
                "shipping_city": form.cleaned_data.get('shipping_city') or '',
                "shipping_state": form.cleaned_data.get('shipping_state') or '',
                "shipping_zipcode": form.cleaned_data.get('shipping_zipcode') or '',
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
    cart_items = cart.items.select_related("product")
    if not cart_items.exists():
        return respond_error("Cart empty", status=400)

    subtotal = sum(item.product.product_price * item.quantity for item in cart_items)
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

    for item in cart_items:
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
        # Send order confirmation email (HTML template)
        try:
            to_email = shipping_data.get('shipping_email')
            if to_email:
                subject = f"Order #{order_obj.id} confirmed"
                # Build absolute base URL for images in email
                base_url = request.build_absolute_uri("/").rstrip("/")
                items = list(order_obj.items.select_related('product'))
                context = {"order": order_obj, "shipping": ShippingInfo.objects.filter(order=order_obj).first(), "base_url": base_url}
                html_body = render_to_string("emails/order_confirmation.html", context)
                text_body = f"Your order #{order_obj.id} has been placed. Total: ₹{order_obj.total_price}"
                msg = EmailMultiAlternatives(subject, text_body, settings.DEFAULT_FROM_EMAIL, [to_email])
                msg.attach_alternative(html_body, "text/html")
                # Try embedding images as inline attachments (some clients block external http URLs)
                try:
                    from email.mime.image import MIMEImage
                    for item in items:
                        prod = item.product
                        if getattr(prod, 'product_image', None) and getattr(prod.product_image, 'path', None):
                            with open(prod.product_image.path, 'rb') as f:
                                img = MIMEImage(f.read())
                                img.add_header('Content-ID', f'<prod_{item.id}>')
                                img.add_header('Content-Disposition', 'inline', filename=f'prod_{item.id}.jpg')
                                msg.attach(img)
                    # Provide a simple cid map flag to the template
                    context.update({"cid_map": {"item_ids": [i.id for i in items]}})
                    html_body = render_to_string("emails/order_confirmation.html", context)
                    msg.attach_alternative(html_body, "text/html")
                except Exception:
                    pass
                msg.send(fail_silently=False)
        except Exception as e:
            import logging
            logging.getLogger('django.core.mail').exception("Error sending order confirmation email: %s", e)

    # Fallback: for redirect flows where session may be missing, rebuild from Razorpay order notes
    if not shipping_data:
        try:
            rp_order = client.order.fetch(data.get('razorpay_order_id'))
            notes = rp_order.get('notes') or {}
            to_email = notes.get('shipping_email')
            if to_email:
                ShippingInfo.objects.create(
                    order=order_obj,
                    user=user,
                    shipping_first_name=notes.get('shipping_first_name') or '',
                    shipping_last_name=notes.get('shipping_last_name') or '',
                    shipping_email=to_email,
                    shipping_phone_number=notes.get('shipping_phone_number') or '',
                    shipping_address=notes.get('shipping_address') or '',
                    shipping_city=notes.get('shipping_city') or '',
                    shipping_zipcode=notes.get('shipping_zipcode') or '',
                    shipping_state=notes.get('shipping_state') or '',
                )
                try:
                    subject = f"Order #{order_obj.id} confirmed"
                    base_url = request.build_absolute_uri("/").rstrip("/")
                    items = list(order_obj.items.select_related('product'))
                    context = {"order": order_obj, "shipping": ShippingInfo.objects.filter(order=order_obj).first(), "base_url": base_url}
                    html_body = render_to_string("emails/order_confirmation.html", context)
                    text_body = f"Your order #{order_obj.id} has been placed. Total: ₹{order_obj.total_price}"
                    msg = EmailMultiAlternatives(subject, text_body, settings.DEFAULT_FROM_EMAIL, [to_email])
                    msg.attach_alternative(html_body, "text/html")
                    try:
                        from email.mime.image import MIMEImage
                        for item in items:
                            prod = item.product
                            if getattr(prod, 'product_image', None) and getattr(prod.product_image, 'path', None):
                                with open(prod.product_image.path, 'rb') as f:
                                    img = MIMEImage(f.read())
                                    img.add_header('Content-ID', f'<prod_{item.id}>')
                                    img.add_header('Content-Disposition', 'inline', filename=f'prod_{item.id}.jpg')
                                    msg.attach(img)
                        context.update({"cid_map": {"item_ids": [i.id for i in items]}})
                        html_body = render_to_string("emails/order_confirmation.html", context)
                        msg.attach_alternative(html_body, "text/html")
                    except Exception:
                        pass
                    msg.send(fail_silently=False)
                except Exception as e:
                    import logging
                    logging.getLogger('django.core.mail').exception("Fallback email send failed: %s", e)
        except Exception:
            pass

    # Clear cart
    cart.items.all().delete()
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

    # For redirect-based flows (typically GET callbacks), send an HTTP redirect to success page
    if request.method == "GET":
        return redirect("order_success")
    # For AJAX (popup) flows, return JSON so client JS can redirect
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
    if is_ajax:
        return JsonResponse({"status": "success", "redirect_url": redirect("order_success").url})
    return redirect("order_success")

