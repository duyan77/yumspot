from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
	username = models.CharField(verbose_name="Tên Đăng Nhập", max_length=150, unique=True)
	email = models.EmailField(unique=True)
	created_at = models.DateTimeField(auto_now_add=True)
	is_staff = models.BooleanField(verbose_name="Nhân Viên")
	is_superuser = models.BooleanField(verbose_name="Quản Trị Viên")

	def __str__(self):
		return self.username

	class Meta:
		verbose_name = 'User'
		verbose_name_plural = 'Users'


class Restaurant(models.Model):
	name = models.CharField(max_length=255, verbose_name="Tên Nhà Hàng")
	description = models.TextField(verbose_name="Mô Tả")
	location = models.CharField(max_length=255, verbose_name="Địa Chỉ")
	user = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'is_staff': True},
							 verbose_name="Người quản lí")
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return self.name


class Follow(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
	created_at = models.DateTimeField(auto_now_add=True)


class Review(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
	rating = models.IntegerField()
	comment = models.TextField()
	created_at = models.DateTimeField(auto_now_add=True)


class Like(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	review = models.ForeignKey(Review, on_delete=models.CASCADE)
	created_at = models.DateTimeField(auto_now_add=True)


class Category(models.Model):
	name = models.CharField(max_length=255)
	created_at = models.DateTimeField(auto_now_add=True)


class Menu(models.Model):
	restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
	category = models.ForeignKey(Category, on_delete=models.CASCADE)
	created_at = models.DateTimeField(auto_now_add=True)


class Food(models.Model):
	name = models.CharField(max_length=255)
	price = models.DecimalField(max_digits=10, decimal_places=2)
	menu = models.ForeignKey(Menu, on_delete=models.CASCADE)
	created_at = models.DateTimeField(auto_now_add=True)


class Order(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
	created_at = models.DateTimeField(auto_now_add=True)


class OrderDetails(models.Model):
	order = models.ForeignKey(Order, on_delete=models.CASCADE)
	food = models.ForeignKey(Food, on_delete=models.CASCADE)
	quantity = models.IntegerField()
	created_at = models.DateTimeField(auto_now_add=True)


class Payment(models.Model):
	order = models.ForeignKey(Order, on_delete=models.CASCADE)
	amount = models.DecimalField(max_digits=10, decimal_places=2)
	status = models.CharField(max_length=50)
	created_at = models.DateTimeField(auto_now_add=True)


class Delivery(models.Model):
	order = models.ForeignKey(Order, on_delete=models.CASCADE)
	status = models.CharField(max_length=50)
	delivery_date = models.DateTimeField()
	created_at = models.DateTimeField(auto_now_add=True)
