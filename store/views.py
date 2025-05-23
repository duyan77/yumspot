import json

from django.db.models import ExpressionWrapper, F, DecimalField
from django.http import JsonResponse
from oauth2_provider.models import AccessToken
from oauth2_provider.views import TokenView
from rest_framework import status
from rest_framework import viewsets, generics, parsers, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from store import serializers, paginators, perms
from .models import Restaurant, User, Category, Food, Review, UserLikeRestaurant, Follow
from .paginators import ReviewPaginator
from .serializers import RestaurantSerializer


class RestaurantViewSet(viewsets.ViewSet, generics.ListAPIView, generics.CreateAPIView,
						generics.RetrieveAPIView):
	queryset = Restaurant.objects.filter(
		active=True).all()
	serializer_class = serializers.RestaurantSerializer
	pagination_class = paginators.RestaurantPaginator

	def get_queryset(self):
		# Lấy tất cả các nhà hàng đang hoạt động
		queryset = self.queryset

		# Lọc theo tên nhà hàng nếu có
		name = self.request.query_params.get("q")
		if name:
			queryset = queryset.filter(name__icontains=name)

		return queryset

	def get_permissions(self):
		if self.action in ["add_review", "like_restaurant"]:
			return [permissions.IsAuthenticated()]
		elif self.action == "create":
			return [perms.IsRestaurantOwner(), perms.OwnerAuthenticated()]
		return [permissions.AllowAny()]

	@action(methods=['get'], url_path="foods", detail=True)
	def get_foods(self, request, pk):
		# Lấy nhà hàng theo pk
		restaurant = self.get_object()

		# Lấy tất cả các món ăn của nhà hàng
		foods = Food.objects.filter(menu__restaurant=restaurant, active=True)

		# Phân trang kết quả
		page = self.paginate_queryset(foods)
		if page is not None:
			serializer = serializers.FoodSerializer(page, many=True)
			return self.get_paginated_response(serializer.data)

		# Nếu không có phân trang, trả về tất cả kết quả
		serializer = serializers.FoodSerializer(foods, many=True)
		return Response(serializer.data)

	@action(methods=['post'], url_path="add-review", detail=True)
	def add_review(self, request, pk):
		cmt = request.data.get("comment")
		if cmt:
			review = Review.objects.create(comment=cmt, user=request.user,
										   restaurant=self.get_object())
			return Response(serializers.ReviewSerializer(review).data,
							status=status.HTTP_201_CREATED)
		return Response(status=status.HTTP_400_BAD_REQUEST)

	@action(methods=['get'], url_path="comments", detail=True)
	def get_comments(self, request, pk):
		# Lấy nhà hàng theo pk
		restaurant = self.get_object()

		# Lấy tất cả các bình luận của nhà hàng
		reviews = restaurant.review_set.all()

		# Phân trang kết quả
		page = self.paginate_queryset(reviews)
		if page is not None:
			serializer = serializers.ReviewSerializer(page, many=True)
			return self.get_paginated_response(serializer.data)

		# Nếu không có phân trang, trả về tất cả kết quả
		serializer = serializers.ReviewSerializer(reviews, many=True)
		return Response(serializer.data)

	def toggle_relationship(self, model_class, user, restaurant):
		obj, created = model_class.objects.get_or_create(user=user, restaurant=restaurant)
		if not created:
			obj.active = not obj.active
			obj.save()
		return obj

	@action(methods=['post'], url_path="like", detail=True)
	def like_restaurant(self, request, pk):
		restaurant = self.get_object()
		self.toggle_relationship(UserLikeRestaurant, request.user, restaurant)
		return Response(
			serializers.RestaurantDetailSerializer(restaurant, context={'request': request}).data)

	@action(methods=['post'], url_path="follow", detail=True)
	def follow_restaurant(self, request, pk):
		restaurant = self.get_object()
		self.toggle_relationship(Follow, request.user, restaurant)
		return Response(
			serializers.RestaurantDetailSerializer(restaurant, context={'request': request}).data)

	@action(methods=['get'], url_path="follwed-user", detail=True)
	def get_liked_user(self, request, pk):
		# Lấy nhà hàng theo pk
		restaurant = self.get_object()

		# Lấy tất cả các người dùng đã thích nhà hàng này
		users = User.objects.filter(follow__restaurant=restaurant).values_list(
			'id', flat=True
		)

		return Response(users)


class UserViewSet(viewsets.ViewSet, generics.CreateAPIView, generics.ListAPIView):
	queryset = User.objects.filter(is_active=True).all()
	serializer_class = serializers.UserSerializer
	parser_classes = [parsers.MultiPartParser]

	def get_permissions(self):
		if self.action in ["current_user", "liked_restaurant"]:
			return [permissions.IsAuthenticated()]
		return [permissions.AllowAny()]

	@action(methods=['get'], url_path="current-user", detail=False)
	def current_user(self, request):
		return Response(serializers.UserSerializer(request.user).data, status=status.HTTP_200_OK)

	@action(methods=['get'], url_path="current-user/liked-restaurant", detail=False)
	def liked_restaurant(self, request):
		user = request.user
		liked_restaurants = Restaurant.objects.filter(userlikerestaurant__user=user)
		serializer = RestaurantSerializer(liked_restaurants, many=True)
		return Response(serializer.data)

	@action(methods=['put', 'patch'], url_path='current-user/update', detail=False,
			permission_classes=[permissions.IsAuthenticated])
	def update_current_user(self, request):
		user = request.user
		serializer = self.get_serializer(user, data=request.data, partial=True)
		if serializer.is_valid():
			if 'password' in request.data:
				user.set_password(request.data['password'])
			serializer.save()
			return Response(serializers.UserSerializer(user).data, status=status.HTTP_200_OK)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomTokenView(TokenView):
	def post(self, request, *args, **kwargs):
		response = super().post(request, *args, **kwargs)

		if response.status_code == 200:
			# Parse JSON từ response content
			data = json.loads(response.content)

			access_token = data.get("access_token")
			token = AccessToken.objects.get(token=access_token)

			user = token.user
			data["username"] = user.username
			data["email"] = user.email

			return JsonResponse(data)

		return response


class CategoryViewSet(viewsets.ViewSet, generics.ListAPIView):
	queryset = Category.objects.filter(active=True)
	serializer_class = serializers.CategorySerializer


class FoodViewSet(viewsets.ViewSet, generics.ListAPIView):
	queryset = Food.objects.filter(active=True).select_related(
		'category',
		'menu__restaurant'
	).prefetch_related(
		'review_set'
	)
	serializer_class = serializers.FoodSerializer
	pagination_class = paginators.FoodPaginator

	def get_queryset(self):
		queryset = self.queryset

		# Tính discounted_price = price * (1 - discount / 100)
		discounted_price_expr = ExpressionWrapper(
			F('price') * (1 - F('discount') / 100),
			output_field=DecimalField(max_digits=10, decimal_places=2)
		)

		queryset = queryset.annotate(discounted_price=discounted_price_expr)

		name = self.request.query_params.get("q")
		if name:
			queryset = queryset.filter(name__icontains=name)

		min_price = self.request.query_params.get("min_price")
		max_price = self.request.query_params.get("max_price")
		if min_price:
			queryset = queryset.filter(discounted_price__gte=min_price)
		if max_price:
			queryset = queryset.filter(discounted_price__lte=max_price)

		category_id = self.request.query_params.get("category_id")
		category_name = self.request.query_params.get("category")
		if category_id:
			queryset = queryset.filter(category__id=category_id)
		elif category_name:
			queryset = queryset.filter(category__name__icontains=category_name)

		restaurant_id = self.request.query_params.get("restaurant_id")
		restaurant_name = self.request.query_params.get("restaurant")
		if restaurant_id:
			queryset = queryset.filter(menu__restaurant__id=restaurant_id)
		elif restaurant_name:
			queryset = queryset.filter(menu__restaurant__name__icontains=restaurant_name)

		return queryset

	@action(methods=['get'], url_path="discounted", detail=False)
	def get_discounted_food(self, request):
		# Lấy queryset đã lọc từ get_queryset
		queryset = self.get_queryset()

		# Lọc các món có discount > 0
		discounted_foods = queryset.filter(discount__gt=0)  # gt: greater than

		# Phân trang kết quả
		page = self.paginate_queryset(discounted_foods)
		if page is not None:
			serializer = self.get_serializer(page, many=True)
			return self.get_paginated_response(serializer.data)

		# Nếu không có phân trang, trả về tất cả kết quả
		serializer = self.get_serializer(discounted_foods, many=True)
		return Response(serializer.data)

	@action(methods=['get'], url_path="comments", detail=True)
	def get_comments(self, request, pk):
		# Lấy món ăn theo pk
		food = self.get_object()

		# Lấy tất cả các bình luận của món ăn
		reviews = food.review_set.all()

		paginator = ReviewPaginator()
		page = paginator.paginate_queryset(reviews, request)

		if page is not None:
			serializer = serializers.ReviewSerializer(page, many=True)
			return paginator.get_paginated_response(serializer.data)

		# Nếu không có phân trang, trả về tất cả kết quả
		serializer = serializers.ReviewSerializer(reviews, many=True)
		return Response(serializer.data)

	@action(methods=['post'], url_path="add-review", detail=True,
			permission_classes=[permissions.IsAuthenticated])
	def add_review(self, request, pk):
		cmt = request.data.get("comment")
		rating = request.data.get("rating")
		if cmt:
			if rating:
				review = Review.objects.create(comment=cmt, rating=rating, user=request.user,
											   food=self.get_object())
			else:
				review = Review.objects.create(comment=cmt, user=request.user,
											   food=self.get_object())
			return Response(serializers.ReviewSerializer(review).data,
							status=status.HTTP_201_CREATED)
		return Response(status=status.HTTP_400_BAD_REQUEST)


class ReviewViewSet(viewsets.ModelViewSet):
	queryset = Review.objects.select_related('user').filter(active=True).order_by('-created_at')
	serializer_class = serializers.ReviewSerializer
	pagination_class = ReviewPaginator

	def get_permissions(self):
		if self.action in ["destroy", "update", "create"]:
			return [perms.OwnerAuthenticated()]
		return [permissions.AllowAny()]
