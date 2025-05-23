from django.urls import path, include
from rest_framework import routers

from store import views

router = routers.DefaultRouter()
router.register('restaurants', views.RestaurantViewSet, basename='restaurants')
router.register('users', views.UserViewSet, basename='users')
router.register('categories', views.CategoryViewSet, basename='categories')
router.register('foods', views.FoodViewSet, basename='foods')
router.register('reviews', views.ReviewViewSet, basename='reviews')
urlpatterns = [

	path("", include(router.urls)),
]
