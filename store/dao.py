from django.db.models import Count, Sum, F
from django.db.models.functions import TruncQuarter, TruncYear, TruncMonth

from .models import Food, Restaurant, User, OrderDetails


def load_foods(params={}):
	q = Food.objects.filter(active=True)

	kw = params.get("kw")
	if kw:
		q = q.filter(name__icontains=kw)

	cate_id = params.get("category_id")
	if cate_id:
		q = q.filter(category_id=cate_id)

	return q


def load_restaurants(params={}):
	q = Restaurant.objects.filter(active=True)

	kw = params.get("kw")
	if kw:
		q = q.filter(name__icontains=kw)

	return q


def count_restaurants_per_owner():
	return User.objects.filter(role='restaurant').annotate(count=Count('restaurant__id')) \
		.values('id', 'username', 'count').order_by('-count')


def get_stats_by_category(restaurant_id=None, quarter_number=None, month=None, year=None):
	from django.db.models.functions import TruncMonth, TruncQuarter, TruncYear

	qs = OrderDetails.objects.filter(order__payment__isnull=False).annotate(
		category=F('food__category__name'),
		restaurant=F('order__restaurant__name')
	)

	if restaurant_id:
		qs = qs.filter(order__restaurant__id=restaurant_id)

	if year:
		qs = qs.filter(order__payment__created_at__year=year)

	# Thống kê theo quý
	if quarter_number:
		if quarter_number not in [1, 2, 3, 4]:
			raise ValueError("quarter_number phải từ 1 đến 4.")
		qs = qs.filter(order__payment__created_at__quarter=quarter_number)
		qs = qs.annotate(time=TruncQuarter('order__payment__created_at'))

	# Thống kê theo tháng
	elif month:
		if not (1 <= month <= 12):
			raise ValueError("month phải từ 1 đến 12.")
		qs = qs.filter(order__payment__created_at__month=month)
		qs = qs.annotate(time=TruncMonth('order__payment__created_at'))

	# Thống kê theo năm (mặc định)
	else:
		qs = qs.annotate(time=TruncYear('order__payment__created_at'))

	# Gộp nhóm theo thời gian - nhà hàng - danh mục
	return qs.values('time', 'restaurant', 'category').annotate(
		total_revenue=Sum(F('quantity') * F('food__price')),
		total_quantity=Sum('quantity')
	).order_by('time')


def get_yearly_stats_by_food(restaurant_id=None, year=None):
	qs = OrderDetails.objects.filter(
		order__payment__isnull=False
	).annotate(
		year=TruncYear('order__payment__created_at'),
		food_name=F('food__name'),
		restaurant=F('order__restaurant__name')
	)

	if restaurant_id:
		qs = qs.filter(order__restaurant__id=restaurant_id)

	if year:
		qs = qs.filter(order__payment__created_at__year=year)

	return qs.values('year', 'restaurant', 'food_name').annotate(
		total_revenue=Sum(F('quantity') * F('food__price')),
		total_quantity=Sum('quantity')
	).order_by('year')


def get_yearly_stats_by_restaurant(year=None):
	qs = OrderDetails.objects.filter(
		order__payment__isnull=False
	).annotate(
		year=TruncYear('order__payment__created_at'),
		restaurant=F('order__restaurant__name')
	)

	if year:
		qs = qs.filter(order__payment__created_at__year=year)

	return qs.values('year', 'restaurant').annotate(
		total_revenue=Sum(F('quantity') * F('food__price')),
		total_quantity=Sum('quantity')
	).order_by('year')


def get_food_stats(restaurant_id=None, year=None, quarter=None, month=None):
	qs = OrderDetails.objects.filter(order__payment__isnull=False)

	if restaurant_id:
		qs = qs.filter(order__restaurant_id=restaurant_id)

	if year:
		qs = qs.filter(order__payment__created_at__year=year)

	# Thống kê theo quý
	if quarter:
		quarter = int(quarter)
		if quarter not in [1, 2, 3, 4]:
			raise ValueError("quarter phải từ 1 đến 4.")
		qs = qs.filter(order__payment__created_at__quarter=quarter)
		qs = qs.annotate(time=TruncQuarter('order__payment__created_at'))

	# Thống kê theo tháng
	elif month:
		if not (1 <= month <= 12):
			raise ValueError("month phải từ 1 đến 12.")
		qs = qs.filter(order__payment__created_at__month=month)
		qs = qs.annotate(time=TruncMonth('order__payment__created_at'))

	# Thống kê theo năm (hoặc toàn bộ)
	else:
		qs = qs.annotate(time=TruncYear('order__payment__created_at'))

	# Thống kê theo món ăn
	qs = qs.annotate(
		name=F('food__name')
	).values('time', 'name').annotate(
		total_revenue=Sum(F('quantity') * F('food__price')),
		total_quantity=Sum('quantity')
	).order_by('-total_revenue')

	return qs
