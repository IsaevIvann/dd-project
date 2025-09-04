import json
from uuid import UUID

import requests
from django.conf import settings
from django.db.models import Q
from django.http import HttpResponseForbidden, HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .forms import OrderForm
from .models import Order
from .notify import send_welcome
from .serializers import LinkChatSerializer
from .utils import build_telegram_deeplink


def _client_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def index(request):
    return render(request, "core/index.html")


def offer(request):
    return render(request, "core/offer.html")


def contacts(request):
    return render(request, "core/contacts.html")


def privacy(request):
    return render(request, "core/privacy.html")


def order_create(request):
    if request.method == "POST":
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)

            if order.consent_pdn:
                if not order.consent_ts:
                    order.consent_ts = timezone.now()
                order.consent_ip = _client_ip(request)
                order.consent_ua = request.META.get("HTTP_USER_AGENT", "")[:256]

            order.save()  # TG и письмо клиенту уйдут из сигналов post_save
            tg_link = build_telegram_deeplink(order)
            return render(request, "core/order_success.html", {"tg_link": tg_link})
        else:
            print("OrderForm errors:", form.errors.as_json())
    else:
        form = OrderForm()

    return render(request, "core/order_form.html", {"form": form})


@csrf_exempt
def telegram_webhook(request, secret: str):
    if secret != getattr(settings, "TELEGRAM_WEBHOOK_SECRET", ""):
        return HttpResponseForbidden("forbidden")

    if request.method != "POST":
        return HttpResponse("ok")

    try:
        payload = json.loads(request.body.decode("utf-8"))
        print("[TG webhook] payload:", json.dumps(payload, ensure_ascii=False))
    except Exception:
        return HttpResponse("bad json")

    msg = payload.get("message") or payload.get("edited_message")
    if not msg:
        return HttpResponse("no message")

    chat_id = msg.get("chat", {}).get("id")
    text = msg.get("text", "") or ""
    reply = "Этот бот отправляет уведомления по заявкам. Используйте ссылку со страницы «Спасибо»."

    if text.startswith("/start"):
        parts = text.split(maxsplit=1)
        if len(parts) == 2:
            raw_token = parts[1].strip()
            try:
                token = UUID(raw_token)
            except Exception:
                reply = "Похоже, ссылка некорректна. Пожалуйста, вернитесь на сайт и нажмите кнопку заново."
                return _tg_reply_and_ok(chat_id, reply)

            order = Order.objects.filter(public_token=token).first()
            if order:
                order.telegram_chat_id = str(chat_id)
                order.save(update_fields=["telegram_chat_id", "updated_at"])
                reply = (
                    "Готово! Мы привязали этот чат к вашей заявке.\n"
                    "Будем присылать обновления статуса."
                )
            else:
                reply = "Не нашли заявку по ссылке. Проверьте ссылку со страницы «Спасибо»."
        else:
            reply = "Чтобы привязать уведомления, откройте бота по ссылке со страницы «Спасибо»."

    return _tg_reply_and_ok(chat_id, reply)


def _tg_reply_and_ok(chat_id, text):
    token_bot = getattr(settings, "TELEGRAM_BOT_TOKEN", "")
    if token_bot and chat_id:
        url = f"https://api.telegram.org/bot{token_bot}/sendMessage"
        data = {"chat_id": str(chat_id), "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
        try:
            requests.post(url, data=data, timeout=10)
        except Exception as e:
            print("[TG webhook] reply failed:", e)
    return HttpResponse("ok")


@csrf_exempt
def save_chat_id(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    try:
        data = json.loads(request.body)
        order_id = data.get("order_id")
        chat_id = data.get("chat_id")
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    if not order_id or not chat_id:
        return JsonResponse({"error": "Missing order_id or chat_id"}, status=400)

    try:
        order = Order.objects.get(id=order_id)
        order.telegram_chat_id = str(chat_id)
        order.save(update_fields=["telegram_chat_id"])
        return JsonResponse({"success": True})
    except Order.DoesNotExist:
        return JsonResponse({"error": "Order not found"}, status=404)


class LinkChatView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        if request.headers.get("X-TG-TOKEN") != getattr(settings, "TELEGRAM_SHARED_TOKEN", ""):
            return Response({"error": "forbidden"}, status=status.HTTP_403_FORBIDDEN)

        s = LinkChatSerializer(data=request.data)
        if not s.is_valid():
            return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)

        order_id = s.validated_data.get("order_id")
        phone = s.validated_data.get("phone")
        email = s.validated_data.get("email")
        chat_id = s.validated_data["chat_id"]

        if order_id:
            q = Order.objects.filter(id=order_id)
        else:
            filters = []
            if phone:
                filters.append(Q(phone__iexact=phone) | Q(phone__icontains=phone))
            if email:
                filters.append(Q(email__iexact=email))
            if not filters:
                return Response({"error": "order_id or phone/email required"}, status=status.HTTP_400_BAD_REQUEST)
            q = Order.objects.filter(filters.pop())
            for f in filters:
                q = q | Order.objects.filter(f)

        order = q.order_by("-created_at").first()
        if not order:
            return Response({"error": "order not found"}, status=status.HTTP_404_NOT_FOUND)

        order.telegram_chat_id = str(chat_id)
        order.save(update_fields=["telegram_chat_id"])
        send_welcome(order)
        return Response({"success": True, "order_id": order.id})

def yandex_verify(request):
    return render(request, "core/yandex_d9211e0eacffb670.html")