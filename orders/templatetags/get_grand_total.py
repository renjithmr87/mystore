from django import template
register= template.Library()

# Custom Template Tag
@register.simple_tag(name = 'getgrandtotal')
def getgrandtotal(cart):
    total = 0
    tax = 0
    grand_total = 0
    for item in cart.added_items.all():
        total += item.product.price * item.quantity
        tax = total * 12/100
        grand_total = total + tax
    return grand_total