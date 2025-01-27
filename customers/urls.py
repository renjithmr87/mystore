from django.urls import path
from django.conf.urls.static import static
from django.conf import settings

from . import views

urlpatterns = [
    path('account', views.show_account, name='account'),
    path('logout', views.signout, name='logout'),
    path('edit_account/<pk>', views.edit_profile, name='edit_account')
]

