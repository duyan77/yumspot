import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "yumspot.settings")  # Đổi nếu tên project khác
django.setup()

import random
from datetime import datetime
from django.utils import timezone
from store.models import User, Restaurant, Food, Order, OrderDetails, Payment


def create_random_orders():
    users = list(User.objects.all())
    restaurants = list(Restaurant.objects.all())

    if not users or not restaurants:
        print("Thiếu dữ liệu User hoặc Restaurant.")
        return

    years = [2023, 2024, 2025]
    months = list(range(1, 13))  # Tháng 1–12

    for restaurant in restaurants:
        # Lọc món ăn thông qua menu liên kết với restaurant
        foods = list(Food.objects.filter(menu__restaurant=restaurant))
        if not foods:
            continue

        for year in years:
            for month in random.sample(months, k=4):  # 4 tháng ngẫu nhiên mỗi năm
                for _ in range(random.randint(3, 6)):  # 3–6 đơn mỗi tháng
                    user = random.choice(users)
                    order = Order.objects.create(user=user, restaurant=restaurant)

                    total = 0
                    for _ in range(random.randint(1, 4)):  # 1–4 món mỗi đơn
                        food = random.choice(foods)
                        quantity = random.randint(1, 5)
                        OrderDetails.objects.create(order=order, food=food, quantity=quantity)
                        total += float(food.price) * quantity

                    created_at = timezone.make_aware(datetime(
                        year, month, random.randint(1, 28),
                        random.randint(8, 20), random.randint(0, 59)
                    ))

                    payment = Payment.objects.create(
                        order=order,
                        amount=total,
                        status='PAID',
                    )

                    Payment.objects.filter(pk=payment.pk).update(
                        created_at=created_at,
                        updated_at=created_at
                    )

    print("Tạo dữ liệu mẫu đơn hàng thành công cho nhiều nhà hàng.")


if __name__ == "__main__":
    create_random_orders()
