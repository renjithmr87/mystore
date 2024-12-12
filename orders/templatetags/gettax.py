from django import template
register= template.Library()

# Custom Template Tag
@register.simple_tag(name = 'gettax')
def gettax(cart):
    total = 0
    tax = 0
    for item in cart.added_items.all():
        total += item.product.price * item.quantity
        tax = total * 12/100
    return tax