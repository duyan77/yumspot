from django.urls import path

from .views import payment_sheet, stripe_webhook

urlpatterns = [
	path('webhook/', stripe_webhook, name='stripe-webhook'),
	path('payment-sheet', payment_sheet, name='payment-sheet'),
]
