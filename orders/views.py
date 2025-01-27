from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from . models import Order, OrderedItem
from django.contrib import messages
from products.models import Product
from customers.models import Customer
from orders.models import Order

# Add to Cart
@login_required(login_url='account')
def add_to_cart(request):
    if request.POST and request.user.is_authenticated:
        user = request.user
        customer = user.customer_profile
        quantity = int(request.POST.get('quantity', 1))
        size = request.POST.get('size')
        product_id = request.POST.get('product_id')
        cart_obj, created = Order.objects.get_or_create(
             owner = customer,
             order_status = Order.CART_STAGE
        )
        product = Product.objects.get(pk = product_id)
        ordered_item,created = OrderedItem.objects.get_or_create(
            product = product,
            owner = cart_obj,
            quantity = quantity,
            size = size,
        )
        if created:
            ordered_item.quantity = quantity
            ordered_item.save()
        else:
            ordered_item.quantity = ordered_item.quantity + quantity
            ordered_item.save()
            
        return redirect('cart')
    else:
        return redirect('login')

# Show the added Cart
def show_cart(request):
    user = request.user
    customer = user.customer_profile
    cart_obj, created = Order.objects.get_or_create(
             owner = customer,
             order_status = Order.CART_STAGE
        )
    context = {
        'cart': cart_obj
    }
    
    return render(request, 'cart.html', context)

# Remove an item from the cart
def remove_item_from_cart(request, pk):
    item = OrderedItem.objects.get(pk=pk)
    if item:
        item.delete()
    return redirect('cart')

# Checkout Cart
def checkout_cart(request):
    if request.POST:
        try:
            user = request.user
            customer = user.customer_profile
            total = float(request.POST.get('total'))
            order_obj = Order.objects.filter(
                owner = customer,
                order_status = Order.CART_STAGE
            )
            if order_obj:
                order_obj.order_status = Order.ORDER_CONFIRMED
                order_obj.total_price = total
                order_obj.save()
                status_message = "Your order has been  processed and delivered with in 2 working days"
                messages.success(request, status_message)
            else:
                status_message = "Unable to Process. Your cart is empty"
                messages.error(request, status_message)
        except Exception as e:
            status_message = "An unexpected error occurred. Please try again."
            messages.error(request, status_message)
    return redirect('cart')

# Order Status Check
@login_required(login_url='account')
def show_orders(request):
        user = request.user
        customer = user.customer_profile
        # Customer related Filter
        all_orders = Order.objects.filter(owner=customer).exclude(order_status=0)
        context = {'orders': all_orders}
        return render(request, 'orders.html', context)
