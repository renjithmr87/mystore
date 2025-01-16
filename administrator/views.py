from django.shortcuts import render
from products.models import Product
from django.core.paginator import Paginator
# Create your views here.
def show_admin_account(request):
    featured_products=Product.objects.order_by('priority')[:4]
    latest_products=Product.objects.order_by('-id')[:4]
    context={
        'featured_products':featured_products,
        'latest_products':latest_products
    }
    return render(request,'index.html',context)