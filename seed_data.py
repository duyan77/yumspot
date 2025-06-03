from datetime import timedelta
from django.utils.timezone import now
import random
from store.models import User, Restaurant, Order, OrderDetails, Food, Payment

# Giả định đã có ít nhất 1 user, 1 restaurant và vài món ăn
user = User.objects.first()
restaurant = Restaurant.objects.first()
foods = list(Food.objects.all()[:3])  # lấy 3 món ăn đầu tiên

for i in range(12):  # tạo 12 đơn hàng, mỗi cái cách nhau 1 tháng
    created_at = now() - timedelta(days=30 * (11 - i))
    order = Order.objects.create(user=user, restaurant=restaurant, created_at=created_at)

    # Thêm 1–3 món ăn cho mỗi đơn
    for _ in range(random.randint(1, 3)):
        food = random.choice(foods)
        quantity = random.randint(1, 5)
        OrderDetails.objects.create(order=order, food=food, quantity=quantity)

    # Tổng tiền thanh toán (giả định): đơn giá * số lượng * hệ số
    total_quantity = sum(od.quantity for od in order.orderdetails_set.all())
    amount = total_quantity * random.randint(10, 30)  # mỗi món 10–30k

    Payment.objects.create(order=order, amount=amount, status='success', created_at=created_at)
