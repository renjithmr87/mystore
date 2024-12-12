from django.db import models
from django.contrib.auth.models import User

# Customer Model.
class Customer(models.Model):
    LIVE = 1
    DELETE = 0
    DELETE_CHOICES = ((LIVE,'live'),(DELETE,'DELETE'))
    first_name = models.CharField(max_length=100, null=True)
    last_name = models.CharField(max_length=100, null=True)
    username = models.CharField(max_length=20,)
    password = models.CharField(max_length=16, null=True)
    address = models.CharField(max_length=50,)
    user = models.OneToOneField(User,on_delete=models.CASCADE,related_name='customer_profile')
    phone = models.CharField(max_length=10,)
    delete_status = models.IntegerField(choices=DELETE_CHOICES, default=LIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

# Combine first_name and last_name as a property
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


    def __str__(self) -> str:
        return self.full_name

