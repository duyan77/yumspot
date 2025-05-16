from django.db.models import Count

from .models import Food, Restaurant, User


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
