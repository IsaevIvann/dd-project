
from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView

from core import views
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
    path("faq/", TemplateView.as_view(template_name="core/faq.html"), name="faq"),
    path("hranenie-bagazha-moskva/", views.storage_moscow, name="storage_moscow"),
    path("luggage-storage-moscow/", views.luggage_storage_moscow, name="luggage_storage_moscow"),
    path("benefits/", TemplateView.as_view(template_name="core/benefits.html"), name="benefits"),
    path("aero/<slug:code>/", views.aero, name="aero"),
    path("concept/", views.concept, name="concept"),
    path("dostavka-bagazha-moskva/", TemplateView.as_view(template_name="core/dostavka_bagazha_moskva.html"),name="delivery_moscow",),
    path("gde-ostavit-bagazh-v-moskve/",TemplateView.as_view(template_name="core/where_to_leave_luggage.html"),name="where_to_leave_luggage",),
    path("station/<slug:code>/", views.station, name="station"),
    path("kamera-hraneniya-bagazha-moskva/",views.kamera_hraneniya_bagazha_moskva,name="kamera_hraneniya_bagazha_moskva"),

]

