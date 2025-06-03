from django.db import models
from rest_framework import serializers

from .models import Restaurant, User, Review, Category, Food, Payment, Menu, Order, OrderDetails


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


class RestaurantSerializer(serializers.ModelSerializer):
	rating = serializers.SerializerMethodField()
	reviews = serializers.SerializerMethodField()
	image = serializers.SerializerMethodField()
	categories = serializers.SerializerMethodField()
	username = serializers.CharField(write_only=True)
	password = serializers.CharField(write_only=True)
	email = serializers.EmailField(write_only=True)
	role = serializers.CharField(write_only=True)
	avatar = serializers.ImageField(write_only=True, required=False)

	class Meta:
		model = Restaurant
		fields = ['id', 'name', 'location', 'rating', 'reviews', 'image', 'price_per_km',
				  'description', 'categories', 'username', 'password', 'email', 'role', 'avatar']

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

	def get_categories(self, res):
		menus = Menu.objects.filter(restaurant=res)
		categories = Category.objects.filter(
			id__in=menus.values_list('category_id', flat=True).distinct())
		return CategorySerializer(categories, many=True).data

	def create(self, validated_data):
		username = validated_data.pop('username')
		password = validated_data.pop('password')
		email = validated_data.pop('email')
		role = validated_data.pop('role')
		avatar = validated_data.pop('avatar', None)

		user = User.objects.create_user(
			username=username,
			password=password,
			email=email,
			role=role,
		)

		if avatar:
			user.avatar = avatar
			user.save()

		restaurant = Restaurant.objects.create(user=user, **validated_data)
		return restaurant


class RestaurantDetailSerializer(RestaurantSerializer):
	liked = serializers.SerializerMethodField()
	followed = serializers.SerializerMethodField()

	def get_liked(self, restaurant):
		request = self.context.get('request')
		if request and request.user.is_authenticated:
			return restaurant.userlikerestaurant_set.filter(active=True).exists()
		return False

	def get_followed(self, restaurant):
		request = self.context.get('request')
		if request and request.user.is_authenticated:
			return restaurant.follow_set.filter(active=True).exists()
		return False

	class Meta:
		model = RestaurantSerializer.Meta.model
		fields = RestaurantSerializer.Meta.fields + ['liked', 'followed']


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
			'discount', 'image', 'restaurant', 'category', 'description',
			'created_at'
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


class FoodCreateSerializer(serializers.ModelSerializer):
	class Meta:
		model = Food
		fields = ['name', 'price', 'discount', 'image', 'description', 'menu', 'category']


class ReviewSerializer(serializers.ModelSerializer):
	username = serializers.SerializerMethodField()
	image = serializers.SerializerMethodField()

	def get_username(self, review):
		if review.user:
			return review.user.username
		return ''

	def get_image(self, review):
		if review.image:
			return review.image.url
		return None

	class Meta:
		model = Review
		fields = ['id', 'comment', 'created_at', 'updated_at', 'username', 'image']


class PaymentSerializer(serializers.ModelSerializer):
	class Meta:
		model = Payment
		fields = '__all__'


class FoodInOrderSerializer(serializers.ModelSerializer):
	food_name = serializers.CharField(source='food.name', read_only=True)
	food_image = serializers.SerializerMethodField()
	price = serializers.SerializerMethodField()  # Giá lấy từ food.price

	class Meta:
		model = OrderDetails
		fields = ['food_name', 'food_image', 'quantity', 'price']

	def get_food_image(self, obj):
		if obj.food.image:
			return obj.food.image.url
		return None

	def get_price(self, obj):
		return obj.food.price  # Lấy giá từ món ăn


class OrderSerializer(serializers.ModelSerializer):
	user = serializers.SerializerMethodField()
	foods = serializers.SerializerMethodField()

	def get_user(self, order):
		if order.user:
			return order.user.id
		return None

	def get_foods(self, order):
		order_details = order.orderdetails_set.all()
		return FoodInOrderSerializer(order_details, many=True).data

	class Meta:
		model = Order
		fields = ['id', 'user', 'restaurant', 'created_at', 'updated_at', 'foods']
