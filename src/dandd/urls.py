
from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView
from core.views import index, order_create, offer, contacts, privacy, telegram_webhook, LinkChatView, yandex_verify

urlpatterns = [
    path("", index, name="index"),
    path("order/", order_create, name="order_create"),
    path("offer/", offer, name="offer"),
    path("contacts/", contacts, name="contacts"),
    path("admin/", admin.site.urls),
    path("privacy/", privacy, name="privacy"),
    path("telegram/webhook/<str:secret>/", telegram_webhook, name="telegram_webhook"),
    path("api/link_chat/", LinkChatView.as_view(), name="link_chat"),
    path("yandex_d9211e0eacffb670.html", yandex_verify),
    path("googleedb31e5f1d3d89c2.html",TemplateView.as_view(template_name="core/googleedb31e5f1d3d89c2.html", content_type="text/plain"),),
    path("robots.txt", TemplateView.as_view(template_name="core/robots.txt", content_type="text/plain"), name="robots"),
    path("sitemap.xml", TemplateView.as_view(template_name="core/sitemap.xml", content_type="application/xml"), name="sitemap"),
]

