from django.urls import path, include
from rest_framework import routers

from store import views

router = routers.DefaultRouter()
router.register(r'restaurants', views.RestaurantViewSet, basename='restaurants')
router.register(r'users', views.UserViewSet, basename='users')
router.register(r'categories', views.CategoryViewSet, basename='categories')
router.register(r'foods', views.FoodViewSet, basename='foods')
router.register(r'reviews', views.ReviewViewSet, basename='reviews')
router.register(r'payments', views.PaymentViewSet, basename='payments')

router.register(r'stats', views.StatsViewSet, basename='stats')
urlpatterns = [
	path("", include(router.urls)),
]
