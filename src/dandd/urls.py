from django.contrib import admin
from django.urls import path
from core.views import index, order_create, offer, contacts

urlpatterns = [
    path('', index, name='index'),
    path('order/', order_create, name='order_create'),
    path('offer/', offer, name='offer'),
    path('contacts/', contacts, name='contacts'),
    path('admin/', admin.site.urls),
]
