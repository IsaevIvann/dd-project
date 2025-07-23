from django.shortcuts import render, redirect
from .forms import OrderForm
from .utils import notify_telegram_new_order

def order_create(request):
    if request.method == "POST":
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save()                        # Сохраняем в переменную!
            notify_telegram_new_order(order)           # Уведомление в TG
            return render(request, "core/order_success.html")
    else:
        form = OrderForm()
    return render(request, "core/order_form.html", {"form": form})

def index(request):
    return render(request, "core/index.html")

def offer(request):
    return render(request, "core/offer.html")

def contacts(request):
    return render(request, "core/contacts.html")