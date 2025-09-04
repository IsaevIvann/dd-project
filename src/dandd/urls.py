from django.conf import settings
from django.contrib import admin
from django.urls import path, re_path
from django.views.static import serve
from core.views import index, order_create, offer, contacts, privacy, telegram_webhook, LinkChatView, yandex_verify

urlpatterns = [
    path('', index, name='index'),
    path('order/', order_create, name='order_create'),
    path('offer/', offer, name='offer'),
    path('contacts/', contacts, name='contacts'),
    path('admin/', admin.site.urls),
    path("privacy/", privacy, name="privacy"),
    path("telegram/webhook/<str:secret>/", telegram_webhook, name="telegram_webhook"),
    path("api/link_chat/", LinkChatView.as_view(), name="link_chat"),
    path("yandex_d9211e0eacffb670.html", yandex_verify),
    re_path(r'^sitemap\.xml$', serve, {'document_root': settings.BASE_DIR / 'staticfiles', 'path': 'sitemap.xml'}),

]
