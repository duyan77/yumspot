from tkinter.font import names

from django.db.models import Count, Sum, F
from django.db.models.functions import TruncQuarter, TruncYear

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


def get_quarterly_stats_by_category(restaurant_id=None, quarter_number=None, year=None):
	qs = OrderDetails.objects.filter(
		order__payment__isnull=False
	).annotate(
		quarter=TruncQuarter('order__payment__created_at'),
		category=F('food__category__name'),
		restaurant=F('order__restaurant__name')
	)

	if restaurant_id:
		qs = qs.filter(order__restaurant__id=restaurant_id)

	if year:
		qs = qs.filter(order__payment__created_at__year=year)

	if quarter_number:
		# Xác định các tháng tương ứng với quý
		if quarter_number == 1:
			qs = qs.filter(order__payment__created_at__month__in=[1, 2, 3])
		elif quarter_number == 2:
			qs = qs.filter(order__payment__created_at__month__in=[4, 5, 6])
		elif quarter_number == 3:
			qs = qs.filter(order__payment__created_at__month__in=[7, 8, 9])
		elif quarter_number == 4:
			qs = qs.filter(order__payment__created_at__month__in=[10, 11, 12])
		else:
			raise ValueError("quarter_number phải nằm trong khoảng 1 đến 4.")

	return qs.values('quarter', 'restaurant', 'category').annotate(
		total_revenue=Sum(F('quantity') * F('food__price')),
		total_quantity=Sum('quantity')
	).order_by('quarter')


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


def get_food_stats(restaurant_id=None, year=None, quarter=None):
	qs = OrderDetails.objects.filter(order__payment__isnull=False)

	if restaurant_id:
		qs = qs.filter(order__restaurant_id=restaurant_id)

	if year:
		qs = qs.filter(order__payment__created_at__year=year)

	if quarter:
		quarter = int(quarter)
		start_month = (quarter - 1) * 3 + 1
		end_month = start_month + 2
		qs = qs.filter(order__payment__created_at__month__range=(start_month, end_month))

	qs = qs.annotate(
		name=F('food__name')
	).values('name').annotate(
		total_revenue=Sum(F('quantity') * F('food__price')),
		total_quantity=Sum('quantity')
	).order_by('-total_revenue')

	return qs
