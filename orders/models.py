from django.db import models
from customers.models import Customer
from products.models import Product
# Orders Model.

class Order(models.Model):
    LIVE = 1
    DELETE = 0
    DELETE_CHOICES = ((LIVE,'live'),(DELETE,'DELETE'))

    CART_STAGE=0
    ORDER_CONFIRMED=1
    ORDER_PROCSSED=2
    ORDER_DELIVERD=3
    ORDER_REJECTED=4
    STATUS_CHOICE=((ORDER_CONFIRMED,"ORDER_CONFIRMED"),
                   (ORDER_PROCSSED,"ORDER_PROCSSED"),
                   (ORDER_DELIVERD,"ORDER_DELIVERD"),
                   (ORDER_REJECTED,"ORDER_REJECTED")
                   )
    order_status = models.IntegerField(choices=STATUS_CHOICE, default=CART_STAGE)
    total_price = models.FloatField(default=0)
    owner = models.ForeignKey(Customer, on_delete=models.SET_NULL,related_name='orders',null=True) 
    delete_status = models.IntegerField(choices=DELETE_CHOICES, default=LIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    # Get Customer Name
    def __str__(self) -> str:
        return "order-{}-{}".format(self.id, self.owner.first_name)

# Order Item
class OrderedItem(models.Model):
    product = models.ForeignKey(Product,related_name='added_carts', on_delete=models.SET_NULL,null=True,)
    quantity = models.IntegerField(default=1)
    owner = models.ForeignKey(Order, on_delete=models.CASCADE,related_name="added_items")
    size = models.CharField(null=True)
