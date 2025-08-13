from django.contrib import admin
from django.urls import path

from core import views
from core.views import index, order_create, offer, contacts, privacy, telegram_webhook, LinkChatView

urlpatterns = [
    path('', index, name='index'),
    path('order/', order_create, name='order_create'),
    path('offer/', offer, name='offer'),
    path('contacts/', contacts, name='contacts'),
    path('admin/', admin.site.urls),
    path("privacy/", privacy, name="privacy"),
    path("telegram/webhook/<str:secret>/", telegram_webhook, name="telegram_webhook"),
    path("api/link_chat/", LinkChatView.as_view(), name="link_chat"),

]
