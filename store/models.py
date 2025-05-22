from cloudinary.models import CloudinaryField
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
	ROLE_CHOICES = [
		('admin', 'Admin'),
		('customer', 'Customer'),
		('restaurant', 'Restaurant Owner'),
	]
	username = models.CharField(verbose_name="Tên Đăng Nhập", max_length=150, unique=True)
	role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer',
							verbose_name='Vai trò')
	email = models.EmailField(unique=True)
	created_at = models.DateTimeField(auto_now_add=True)
	avatar = CloudinaryField('avatar', null=True, blank=True)

	def __str__(self):
		return self.username

	def save(self, *args, **kwargs):
		"""Nếu role là restaurant và user đang được tạo, thì đặt chưa kích hoạt."""
		is_new = self.pk is None  # pk sẽ là None nếu user chưa được lưu lần nào
		if is_new and self.role == 'restaurant':
			self.is_active = False
		super().save(*args, **kwargs)

	def __str__(self):
		return f"{self.username} ({self.role})" if self.role and self.username else "No Name"

	class Meta:
		verbose_name = 'User'
		verbose_name_plural = 'Users'


class BaseModel(models.Model):
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	active = models.BooleanField(default=True)

	class Meta:
		abstract = True


class Restaurant(BaseModel):
	name = models.CharField(max_length=255, verbose_name="Tên Nhà Hàng", null=False, blank=False,
							default='No Name')
	description = models.TextField(verbose_name="Mô Tả")
	location = models.CharField(max_length=255, verbose_name="Địa Chỉ")
	user = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={
		'is_active': True,
		'role': 'restaurant'
	}, verbose_name="Chủ Nhà Hàng")
	image = CloudinaryField('image', null=True, blank=True)
	price_per_km = models.DecimalField(
		max_digits=10,
		decimal_places=2,
		default=5000.0,
		verbose_name="Giá mỗi km"
	)

	def __str__(self):
		return str(self.name) if self.name else "No Name"


class Category(BaseModel):
	name = models.CharField(max_length=255, null=False, blank=False, default='No Name')
	icon = CloudinaryField('icon', null=True, blank=True)

	def __str__(self):
		return str(self.name) if self.name else "No Name"


class Menu(BaseModel):
	restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
	category = models.ForeignKey(Category, on_delete=models.CASCADE)

	def __str__(self):
		return f"{self.restaurant.name} - {self.category.name}"


class Food(BaseModel):
	name = models.CharField(max_length=255)
	price = models.DecimalField(max_digits=10, decimal_places=0)
	menu = models.ForeignKey(Menu, on_delete=models.CASCADE)
	category = models.ForeignKey(Category, on_delete=models.CASCADE, default=None)
	discount = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
	image = CloudinaryField('image', null=True, blank=True)
	description = models.TextField(null=True, blank=True)

	def __str__(self):
		return self.name


class Follow(BaseModel):
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)

	class Meta:
		unique_together = ('user', 'restaurant')


class UserLikeRestaurant(BaseModel):
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)

	class Meta:
		unique_together = ('user', 'restaurant')


class Review(BaseModel):
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, null=True, blank=True)
	food = models.ForeignKey(Food, on_delete=models.CASCADE, null=True, blank=True)
	rating = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)], default=5)
	comment = models.TextField()
	image = CloudinaryField('image', null=True, blank=True)


class UserLikeComment(BaseModel):
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	review = models.ForeignKey(Review, on_delete=models.CASCADE)


class Order(BaseModel):
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)


class OrderDetails(BaseModel):
	order = models.ForeignKey(Order, on_delete=models.CASCADE)
	food = models.ForeignKey(Food, on_delete=models.CASCADE)
	quantity = models.IntegerField()


class Payment(BaseModel):
	order = models.ForeignKey(Order, on_delete=models.CASCADE)
	amount = models.DecimalField(max_digits=10, decimal_places=2)
	status = models.CharField(max_length=50)


class Delivery(BaseModel):
	order = models.ForeignKey(Order, on_delete=models.CASCADE)
	status = models.CharField(max_length=50)
	delivery_date = models.DateTimeField()

# đánh giá res, food
