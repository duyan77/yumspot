from rest_framework.pagination import PageNumberPagination


class RestaurantPaginator(PageNumberPagination):
	page_size = 5


class FoodPaginator(PageNumberPagination):
	page_size = 5


class ReviewPaginator(PageNumberPagination):
	page_size = 10
