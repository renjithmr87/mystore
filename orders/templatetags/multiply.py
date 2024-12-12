from django import template
register= template.Library()

# Custom Template Tag
@register.simple_tag(name='multiply')
def multiply(a, b):
    return a*b