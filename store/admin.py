import json

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.db import models
from django.db.models import Sum, F
from django.db.models.functions import ExtractQuarter, TruncMonth, TruncQuarter, TruncYear
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.timezone import now, timedelta, localtime
from multi_captcha_admin.admin import MultiCaptchaAdminAuthenticationForm
from unfold.admin import ModelAdmin
from unfold.contrib.forms.widgets import WysiwygWidget
from unfold.forms import AdminPasswordChangeForm, UserCreationForm, UserChangeForm
from unfold.sites import UnfoldAdminSite

from store import dao
from .models import User, Restaurant, Food, Category, Menu, OrderDetails, Order, Payment

admin.site.unregister(Group)


class CustomAdminSite(UnfoldAdminSite):
	index_title = "Quản lý hệ thống Yumspot"
	site_title = "Quản lý hệ thống"
	login_form = MultiCaptchaAdminAuthenticationForm
	login_template = 'admin/login.html'

	def get_urls(self):
		return [
			path('stats/', self.admin_view(self.stats_view), name='stats'),
		] + super().get_urls()

	def stats_view(self, request):
		stats = dao.count_restaurants_per_owner()
		return TemplateResponse(request, 'admin/stats.html', {
			"stats_data": {
				"headers": ['Người dùng', 'Số nhà hàng'],
				"rows": [[stat['username'], stat['count']] for stat in stats],
			},

			"cohorts": {
				"headers": [
					{
						"title": "Số nhà hàng",
						"subtitle": "Mỗi người dùng sở hữu",
					},
				],
				"rows": [
					{
						"header": {
							"title": stat["username"],
							"subtitle": f"ID: {stat['user_id']}" if "user_id" in stat else "",
						},
						"cols": [
							{
								"value": str(stat["count"]),
								"subtitle": "nhà hàng",
							}
						]
					}
					for stat in stats
				]
			},

			"trackers": [
				{
					"color": "bg-primary-400 dark:bg-primary-700",
					"tooltip": "Custom value 1",
				},
				{
					"color": "bg-primary-400 dark:bg-primary-700",
					"tooltip": "Custom value 2",
				}
			]
		})


custom_admin_site = CustomAdminSite(name="custom_admin_site")


@admin.register(User, site=custom_admin_site)
class UserAdmin(BaseUserAdmin, ModelAdmin):
	list_display = ("username", "email", "role", "is_active")
	list_filter = BaseUserAdmin.list_filter + ("username", "role", "is_active")
	list_editable = getattr(BaseUserAdmin, "list_editable", ()) + ("role", "is_active")
	form = UserChangeForm
	add_form = UserCreationForm
	change_password_form = AdminPasswordChangeForm
	compressed_fields = True
	warn_unsaved_form = True
	change_form_show_cancel_button = True
	list_filter_sheet = True
	ordering = ['id']

	add_fieldsets = (
		(None, {
			"classes": ("wide",),
			"fields": ("username", "email", "role", "password1", "password2"),
		}),
	)

	fieldsets = BaseUserAdmin.fieldsets + (
		('Role Information', {
			'fields': ('role',),  # Thêm trường 'role' vào một fieldset riêng
		}),
	)

	def has_add_permission(self, request):
		return request.user.is_superuser

	def has_change_permission(self, request, obj=None):
		return request.user.is_superuser

	def has_delete_permission(self, request, obj=None):
		return request.user.is_superuser


@admin.register(Group, site=custom_admin_site)
class GroupAdmin(ModelAdmin):
	pass


@admin.register(Restaurant, site=custom_admin_site)
class RestaurantAdmin(ModelAdmin):
	list_display = ("name", "location", "user", "description")
	list_editable = ("location", "user")
	list_filter = ("name", "location", "user")
	search_fields = ("name", "location")
	compressed_fields = True
	warn_unsaved_form = True
	change_form_show_cancel_button = True
	list_filter_sheet = True
	ordering = ['id']

	formfield_overrides = {
		models.TextField: {
			"widget": WysiwygWidget,
		}
	}


@admin.register(Food, site=custom_admin_site)
class FoodAdmin(ModelAdmin):
	list_display = ("id", "name", "price", "category",)
	list_editable = ("name", "price", "category")
	list_filter = ("name", "price", "category")
	search_fields = ("name", "price")
	compressed_fields = True
	warn_unsaved_form = True
	change_form_show_cancel_button = True
	list_filter_sheet = True
	ordering = ['id']


@admin.register(Category, site=custom_admin_site)
class CategoryAdmin(ModelAdmin):
	list_display = ("id", "name", "icon")
	list_editable = ("name", "icon")
	list_filter = ("name",)
	search_fields = ("name",)
	compressed_fields = True
	warn_unsaved_form = True
	change_form_show_cancel_button = True
	list_filter_sheet = True
	ordering = ['id']


@admin.register(Menu, site=custom_admin_site)
class MenuAdmin(ModelAdmin):
	list_display = ("id", "restaurant", "category")
	list_editable = ("restaurant", "category")
	list_filter = ("restaurant", "category")
	compressed_fields = True
	warn_unsaved_form = True
	change_form_show_cancel_button = True
	list_filter_sheet = True
	ordering = ['id']


def dashboard_callback(request, context):
	"""
    Callback to prepare custom variables for index template which is used as dashboard
    template. It can be overridden in application by creating custom admin/index.html.
    """

	def build_filter_item(req, label, value):
		query_dict = req.GET.copy()
		query_dict['filter'] = value
		return {
			'label': label,
			'url': f"{reverse('admin:index')}?{query_dict.urlencode()}",
			'active': req.GET.get('filter', 'month') == value,
		}

	filter_options = [
		build_filter_item(request, "Theo tháng", "month"),
		build_filter_item(request, "Theo quý", "quarter"),
		build_filter_item(request, "Theo năm", "year"),
	]

	filter_type = request.GET.get('filter', 'month')
	today = now()

	labels = []
	revenues = []
	product_counts = []

	# Lấy orders phù hợp (filter theo năm nếu cần)
	orders_qs = Order.objects.all()
	if filter_type in ['month', 'quarter']:
		orders_qs = orders_qs.filter(created_at__year=today.year)

	# Truy vấn tổng doanh thu theo khoảng thời gian
	if filter_type == 'month':
		payments_qs = Payment.objects.filter(
			order__in=orders_qs,
			status='success'
		).annotate(period=TruncMonth('order__created_at')).values('period').annotate(
			total_revenue=Sum('amount')
		).order_by('period')

		orderdetails_qs = OrderDetails.objects.filter(
			order__in=orders_qs
		).annotate(period=TruncMonth('order__created_at')).values('period').annotate(
			total_products=Sum('quantity')
		).order_by('period')

		for pay_entry in payments_qs:
			labels.append(pay_entry['period'].strftime('%B'))
			revenues.append(pay_entry['total_revenue'])

		for od_entry in orderdetails_qs:
			product_counts.append(od_entry['total_products'])

	elif filter_type == 'quarter':
		payments_qs = Payment.objects.filter(
			order__in=orders_qs,
			status='success'
		).annotate(period=TruncQuarter('order__created_at')).values('period').annotate(
			total_revenue=Sum('amount')
		).order_by('period')

		orderdetails_qs = OrderDetails.objects.filter(
			order__in=orders_qs
		).annotate(period=TruncQuarter('order__created_at')).values('period').annotate(
			total_products=Sum('quantity')
		).order_by('period')

		for pay_entry in payments_qs:
			quarter = (pay_entry['period'].month - 1) // 3 + 1
			labels.append(f"Q{quarter} {pay_entry['period'].year}")
			revenues.append(pay_entry['total_revenue'])

		for od_entry in orderdetails_qs:
			product_counts.append(od_entry['total_products'])

	elif filter_type == 'year':
		payments_qs = Payment.objects.filter(
			order__in=orders_qs,
			status='success'
		).annotate(period=TruncYear('order__created_at')).values('period').annotate(
			total_revenue=Sum('amount')
		).order_by('period')

		orderdetails_qs = OrderDetails.objects.filter(
			order__in=orders_qs
		).annotate(period=TruncYear('order__created_at')).values('period').annotate(
			total_products=Sum('quantity')
		).order_by('period')

		for pay_entry in payments_qs:
			labels.append(str(pay_entry['period'].year))
			revenues.append(pay_entry['total_revenue'])

		for od_entry in orderdetails_qs:
			product_counts.append(od_entry['total_products'])

	# Nếu số lượng sản phẩm nhỏ hơn labels thì pad bằng 0 (tránh lỗi)
	while len(product_counts) < len(labels):
		product_counts.append(0)

	# Chuẩn bị dữ liệu biểu đồ như trước
	revenue_chart_data = {
		'labels': labels,
		'datasets': [{
			'label': 'Doanh thu',
			'data': revenues,
			'borderColor': 'rgb(34,197,94)',
			'backgroundColor': 'rgba(34,197,94,0.2)',
			'fill': True,
		}]
	}

	products_chart_data = {
		'labels': labels,
		'datasets': [{
			'label': 'Tổng số sản phẩm bán',
			'data': product_counts,
			'borderColor': 'rgb(59,130,246)',
			'backgroundColor': 'rgba(59,130,246,0.2)',
			'fill': True,
		}]
	}

	days_range = 15
	labels = []
	user_counts = []
	restaurant_counts = []

	for i in range(days_range):
		# Lấy ngày hiện tại với múi giờ chính xác
		day = localtime(now()) - timedelta(days=days_range - i - 1)
		labels.append(day.strftime("%d-%m-%Y"))

		# Tính tổng số lượng người dùng đã đăng ký đến ngày hôm đó
		user_per_day = User.objects.filter(date_joined__lte=day).count()

		# Tính tổng số lượng nhà hàng đã tạo đến ngày hôm đó
		restaurant_per_day = Restaurant.objects.filter(created_at__lte=day).count()

		# Thêm vào danh sách
		user_counts.append(user_per_day)
		restaurant_counts.append(restaurant_per_day)

	# Dữ liệu biểu đồ
	user_chart_data = {
		'labels': labels,
		'datasets': [
			{
				"label": "Users",
				"data": user_counts,
				"borderColor": "#3B82F6",
				"backgroundColor": "rgba(59, 130, 246, 0.2)",
				"fill": True,
			}
		],
	}

	restaurant_chart_data = {
		'labels': labels,
		'datasets': [
			{
				"label": "Restaurants",
				"data": restaurant_counts,
				"borderColor": "#F97316",
				"backgroundColor": "rgba(249, 115, 22, 0.2)",
				"fill": True,
			}
		]
	}

	stats = dao.count_restaurants_per_owner()

	# test thử
	current_year = now().year

	# Dữ liệu doanh thu theo quý
	quarterly_revenue = (
		OrderDetails.objects
		.filter(order__created_at__year=current_year)
		.annotate(quarter=ExtractQuarter('order__created_at'))
		.values('quarter')
		.annotate(revenue=Sum(F('quantity') * F('food__price')))
		.order_by('quarter')
	)

	# Chuẩn hoá dữ liệu ra dạng list để đưa vào Chart.js
	labels = [f"Q{q}" for q in range(1, 5)]
	revenue_data = [0, 0, 0, 0]

	for item in quarterly_revenue:
		q = item['quarter']
		revenue = item['revenue'] or 0
		revenue_data[q - 1] = float(revenue)

	quarterly_revenue_chart = {
		"labels": labels,
		"datasets": [
			{
				"label": f"Doanh thu năm {current_year}",
				"data": revenue_data,
				"borderColor": "rgba(75, 192, 192, 1)",
				"backgroundColor": "rgba(75, 192, 192, 0.2)",
				"fill": True,
				"tension": 0.4,
			}
		]
	}

	options = [
		{'value': 'month', 'label': 'Theo tháng'},
		{'value': 'quarter', 'label': 'Theo quý'},
		{'value': 'year', 'label': 'Theo năm'},
	]

	# Send data to dashboard
	context.update(
		{
			'revenueChartData': json.dumps(revenue_chart_data, default=str),

			'productsChartData': json.dumps(products_chart_data),

			"filters": filter_options,

			"kpis": [
				{
					"title": "Total Active Users (Last 7 days)",
					"metric": 10,
				},
				{
					"title": "Number of Polls (Last 7 days)",
					"metric": 7,
				},
				{
					"title": "Total Active Organisations",
					"metric": 18,
				},
			],

			"stats_data": {
				"headers": ['Người dùng', 'Số nhà hàng'],
				"rows": [[stat['username'], stat['count']] for stat in stats],
			},

			"dauChartData": json.dumps({
				'datasets': [
					{'data': [0, 1, 3, 2, 5, 8, 7],
					 'borderColor': 'rgb(147 51 234)'
					 }
				],
				'labels': [
					'2024-11-18',
					'2024-11-19',
					'2024-11-20',
					'2024-11-21',
					'2024-11-22',
					'2024-11-23',
					'2024-11-24'
				]
			}),

			"dpsChartData": json.dumps({
				'datasets': [
					{'data': [7, 15, 12, 23, 5, 10, 18],
					 'borderColor': 'rgb(147 51 234)'
					 }
				],
				'labels': [
					'2024-11-18',
					'2024-11-19',
					'2024-11-20',
					'2024-11-21',
					'2024-11-22',
					'2024-11-23',
					'2024-11-24'
				]
			}),

			"userChartData": json.dumps(user_chart_data),
			"restaurantChartData": json.dumps(restaurant_chart_data),

			"table": {
				"headers": ["Awesome column", "This one too!"],
				"rows": [
					["a", "b"],
					["c", "d"],
					["e", "f"],
				]
			},

			"quarterlyRevenueChartData": json.dumps(quarterly_revenue_chart),
		}
	)
	return context
