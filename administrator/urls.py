from django.urls import path
from django.conf.urls.static import static
from django.conf import settings

from . import views

urlpatterns = [
    path('administrator/', views.show_admin_account, name='administrator'),
]

