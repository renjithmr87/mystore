from django.db import models
from django.contrib.auth.models import User

# Admin Model.
class Administrator(models.Model):
    name = models.CharField(max_length=255)
    username = models.CharField(max_length=50)
    password = models.CharField(max_length=20)
    admin_user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='admin_profile')
    email = models.EmailField(null=True)



    def __str__(self) -> str:
        return self.name