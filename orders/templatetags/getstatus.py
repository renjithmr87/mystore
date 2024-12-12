from django import template
register= template.Library()

# Custom Template Tag
@register.simple_tag(name='getstatus')
def getstatus(status):
    status = status-1
    status_array = ['confirmed','processed','deliverd','rejected']
    return status_array[status]
