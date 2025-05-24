import json
import os

import requests
import stripe
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from dotenv import load_dotenv

from yumspot import settings

load_dotenv()

# Sử dụng biến từ .env
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
api_key = os.getenv("SENDINBLUE_API_KEY_1")
key = os.getenv("SENDINBLUE_API_KEY_2")
endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")


def send_payment_confirmation_email(api_key, to_email, to_name, transaction_id, amount, currency,
									receipt_url):
	url = "https://api.brevo.com/v3/smtp/email"
	headers = {
		"accept": "application/json",
		"api-key": api_key,
		"content-type": "application/json"
	}
	data = {
		"sender": {
			"name": "Công Ty An Toàn Thông Tin Của Tấn",
			"email": "nguyentan14kute@gmail.com"
		},
		"to": [{"email": to_email, "name": to_name}],
		"subject": "Xác nhận thanh toán thành công",
		"htmlContent": f"""
            <html>
                <body>
                    <p>Chào {to_name},</p>
                    <p>Cảm ơn bạn đã thanh toán thành công!</p>
                    <p><strong>Số tiền:</strong> {amount} {currency.upper()}</p>
                    <p><strong>Mã giao dịch:</strong> {transaction_id}</p>
                    <p><a href="{receipt_url}">Xem hóa đơn</a></p>
                    <p>Trân trọng,</p>
                    <p>Đội ngũ An Toàn Thông Tin</p>
                </body>
            </html>
        """
	}
	response = requests.post(url, headers=headers, json=data)
	if response.status_code == 201:
		print("✅ Email đã gửi thành công.")
	else:
		print(f"❌ Gửi email thất bại: {response.status_code} - {response.text}")


@csrf_exempt
def stripe_webhook(request):
	if request.method == 'POST':
		payload = request.body
		sig_header = request.META['HTTP_STRIPE_SIGNATURE']
		event = None

		# Kiểm tra chữ ký webhook để đảm bảo tính hợp lệ của yêu cầu
		try:
			event = stripe.Webhook.construct_event(
				payload, sig_header, endpoint_secret  # Thay bằng secret thật của bạn
			)
		except ValueError as e:
			return JsonResponse({'error': f"Invalid payload: {str(e)}"}, status=400)
		except stripe.error.SignatureVerificationError as e:
			return JsonResponse({'error': f"Invalid signature: {str(e)}"}, status=400)

		if event['type'] == 'charge.succeeded':
			charge = event['data']['object']

			receipt_url = charge.get('receipt_url', '')
			email = charge['metadata'].get('email', '')
			name = charge['metadata'].get('name', '')
			transaction_id = charge.get('payment_intent', charge.get('id'))
			amount = charge.get('amount', 0) / 100
			currency = charge.get('currency', 'vnd')

			# Nếu có email mới gửi mail
			if email:
				send_payment_confirmation_email(
					api_key=key,
					to_email=email,
					to_name=name,
					transaction_id=transaction_id,
					amount=amount,
					currency=currency,
					receipt_url=receipt_url
				)
	return JsonResponse({'status': 'success'}, status=200)


@csrf_exempt
def create_checkout_session(request):
	if request.method == 'POST':
		try:
			data = json.loads(request.body)
			print("Dữ liệu nhận được từ React Native:", data)

			# Tạo checkout session
			checkout_session = stripe.checkout.Session.create(
				payment_method_types=['card'],

				line_items=[
					{
						'price_data': {
							'currency': 'vnd',
							'unit_amount': 228000,
							'product_data': {
								'name': 'Đơn hàng từ LOOP',
							},
						},
						'quantity': 1,
					},
				],
				mode='payment',
				success_url='https://db09-14-169-73-56.ngrok-free.app/success?session_id={CHECKOUT_SESSION_ID}',
				cancel_url='https://db09-14-169-73-56.ngrok-free.app/cancel',
			)

			return JsonResponse({'id': checkout_session.id, 'url': checkout_session.url})

		except Exception as e:
			return JsonResponse({'error': str(e)}, status=400)

	return JsonResponse({'error': 'Invalid request method'}, status=405)


@csrf_exempt
def payment_sheet(request):
	# Parse JSON từ body
	data = json.loads(request.body)
	cart_items = data.get('cart', [])

	print("📦 Dữ liệu nhận được:\n", json.dumps(data, indent=4, ensure_ascii=False))

	if not cart_items:
		return JsonResponse({'error': 'Giỏ hàng trống.'}, status=400)

	# Tổng tiền của tất cả đơn hàng
	total_amount = 0
	order_ids = []
	shipping_methods = []

	for order in cart_items:
		order_total = int(order.get('orderTotal', 0))
		shipping_price = int(order.get('shipping', {}).get('price', 0))
		total_amount += order_total + shipping_price
		order_ids.append(order.get('orderID'))
		shipping_methods.append(order.get('shipping', {}).get('method'))

	# Lấy thông tin khách hàng từ đơn đầu tiên (nếu tất cả đơn đều chung khách)
	customer_info = cart_items[0].get('customer', {})

	# Tạo Stripe customer
	customer = stripe.Customer.create(
		name=customer_info.get('name'),
		email=customer_info.get('email_phone'),
		metadata={'address': customer_info.get('address')}
	)

	# Tạo Ephemeral key
	ephemeral_key = stripe.EphemeralKey.create(
		customer=customer.id,
		stripe_version='2025-04-30.basil',
	)

	# Tạo PaymentIntent với tổng số tiền
	payment_intent = stripe.PaymentIntent.create(
		amount=total_amount,
		currency='vnd',
		customer=customer.id,
		payment_method_types=["card"],
		metadata={
			"order_ids": ",".join(order_ids),
			"shipping_methods": ",".join(shipping_methods),
			"email": customer_info.get('email_phone'),
			"name": customer_info.get('name'),
		}
	)

	# Trả về thông tin cho frontend
	return JsonResponse({
		'paymentIntent': payment_intent.client_secret,
		'ephemeralKey': ephemeral_key.secret,
		'customer': customer.id,
		'publishableKey': settings.STRIPE_PUBLISHABLE_KEY,
	})
