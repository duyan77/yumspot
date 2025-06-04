import os

import requests


def send_food_notification_email(api_key, to_email, to_name, food_name, restaurant_name,
								 restaurant_id):
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
                   <p>Trân trọng,</p>
                   <p>Đội ngũ An Toàn Thông Tin</p>
               </body>
           </html>
       """
	}
	response = requests.post(url, headers=headers, json=data)
	if response.status_code == 201:
		print("✅ Gửi email thành công.")
	else:
		print(f"❌ Gửi email thất bại: {response.status_code} - {response.text}")


if __name__ == "__main__":
	send_food_notification_email(
		api_key=os.getenv("SENDINBLUE_API_KEY_1"),
		to_email="anbui5948@gmail.com",  # Thay bằng email thực để test
		to_name="Người Dùng Test",
		food_name="Phở Bò Đặc Biệt",
		restaurant_name="Nhà Hàng Việt",
		restaurant_id=1
	)
