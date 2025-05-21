from django.db import models
from rest_framework import serializers

from .models import Restaurant, User, Review, Category, Food


class RestaurantSerializer(serializers.ModelSerializer):
	rating = serializers.SerializerMethodField()
	reviews = serializers.SerializerMethodField()
	image = serializers.SerializerMethodField()

	class Meta:
		model = Restaurant
		fields = ['id', 'name', 'location', 'rating', 'reviews', 'image', 'price_per_km',
				  'description']

	def get_rating(self, res):
		food_reviews = res.review_set.all()
		if food_reviews.exists():
			avg = food_reviews.aggregate(models.Avg('rating'))['rating__avg']
			return f"{avg:.1f}"
		return "0.0"

	def get_reviews(self, res):
		count = res.review_set.count()
		if count >= 1000:
			return f"{count / 1000:.1f}k"
		return str(count)

	def get_image(self, res):
		if res.image:
			return res.image.url
		return None

	def create(self, validated_data):
		request = self.context.get('request')
		user = request.user if request else None
		if not user:
			raise serializers.ValidationError("User is required.")

		restaurant = Restaurant.objects.create(user=user, **validated_data)
		return restaurant


class UserSerializer(serializers.ModelSerializer):
	avatar = serializers.SerializerMethodField()

	class Meta:
		model = User
		fields = ['id', 'username', 'email', 'role', 'is_active', 'avatar', 'password']
		read_only_fields = ['is_active']
		extra_kwargs = {
			'password': {'write_only': True},
		}

	def get_avatar(self, obj):
		if obj.avatar:
			return obj.avatar.url  # Trả về URL đầy đủ từ CloudinaryField
		return None

	def create(self, validated_data):
		request = self.context.get('request')
		avatar = request.FILES.get('avatar') if request else None

		password = validated_data.pop('password', None)

		user = User(**validated_data)
		if password:
			user.set_password(password)
		if avatar:
			user.avatar = avatar
		user.save()
		return user


class ReviewSerializer(serializers.ModelSerializer):
	user = serializers.SerializerMethodField()

	def get_user(self, obj):
		return {
			'username': obj.user.username,
		}

	class Meta:
		model = Review
		fields = '__all__'
		read_only_fields = ['user', 'restaurant']


class CategorySerializer(serializers.ModelSerializer):
	icon = serializers.SerializerMethodField()

	class Meta:
		model = Category
		fields = ['id', 'name', 'icon']

	def get_icon(self, obj):
		if obj.icon:
			return obj.icon.url
		return None


class FoodSerializer(serializers.ModelSerializer):
	rating = serializers.SerializerMethodField()
	reviews = serializers.SerializerMethodField()
	oldPrice = serializers.SerializerMethodField()
	newPrice = serializers.SerializerMethodField()
	restaurant = serializers.SerializerMethodField()
	category = serializers.SerializerMethodField()
	image = serializers.SerializerMethodField()

	class Meta:
		model = Food
		fields = [
			'id', 'name', 'rating', 'reviews', 'oldPrice', 'newPrice',
			'discount', 'image', 'restaurant', 'category', 'description'
		]

	def get_rating(self, food):
		reviews = food.review_set.all()
		if reviews.exists():
			avg = reviews.aggregate(models.Avg('rating'))['rating__avg']
			return f"{avg:.1f}"
		return "0.0"

	def get_reviews(self, food):
		count = food.review_set.count()
		if count >= 1000:
			return f"{count / 1000:.1f}k"
		return str(count)

	def get_oldPrice(self, food):
		return f"{food.price:,.0f}".replace(',', '.')

	def get_newPrice(self, food):
		discounted = food.price * (1 - food.discount / 100)
		return f"{discounted:,.0f}".replace(',', '.')

	def get_restaurant(self, food):
		return RestaurantSerializer(food.menu.restaurant).data

	def get_category(self, food):
		return food.category.name if food.category else None

	def get_image(self, food):
		if food.image:
			return food.image.url
		return None


class ReviewSerializer(serializers.ModelSerializer):
	class Meta:
		model = Review
		fields = ['id', 'comment', 'created_at', 'updated_at']
