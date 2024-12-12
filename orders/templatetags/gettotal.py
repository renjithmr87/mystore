from django import template
register= template.Library()

# Custom Template Tag
@register.simple_tag(name='gettotal')
def gettotal(cart):
    total = 0
    for item in cart.added_items.all():
        total += item.product.price * item.quantity
    return total
