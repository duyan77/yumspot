import json

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.urls import path
from django.utils.timezone import now, timedelta
from django.views.generic import TemplateView
from unfold.admin import ModelAdmin
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm
from unfold.views import UnfoldModelAdminViewMixin

from .models import User, Restaurant

admin.site.unregister(Group)


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
	list_display = ("username", "email", "is_staff", "is_superuser")
	list_filter = BaseUserAdmin.list_filter + ("username",)
	list_editable = BaseUserAdmin.list_editable + ("is_staff", "is_superuser", "email")
	form = UserChangeForm
	add_form = UserCreationForm
	change_password_form = AdminPasswordChangeForm
	compressed_fields = True
	warn_unsaved_form = True

	def has_add_permission(self, request):
		return request.user.is_superuser

	def has_change_permission(self, request, obj=None):
		return request.user.is_superuser

	def has_delete_permission(self, request, obj=None):
		return request.user.is_superuser


@admin.register(Group)
class GroupAdmin(ModelAdmin):
	pass


@admin.register(Restaurant)
class RestaurantAdmin(ModelAdmin):
	list_display = ("name", "location", "user")
	list_editable = ("location", "user")
	list_filter = ("name", "location", "user")
	search_fields = ("name", "location")
	compressed_fields = True
	warn_unsaved_form = True


# Custom dasboard view
admin.site.index_title = 'Dashboard'


class DashboardView(UnfoldModelAdminViewMixin, TemplateView):
	title = "Dashboard"
	permission_required = ()
	template_name = "admin/index.html"


class DashboardAdmin(ModelAdmin):
	def get_urls(self):
		return super().get_urls() + [
			path(
				"index",
				DashboardView.as_view(model_admin=self),
				name="index"
			),
		]


def dashboard_callback(request, context):
	# Lấy 7 ngày gần nhất (theo thứ tự từ cũ đến mới)
	num_days = 7
	today = now().date()
	date_labels = [(today - timedelta(days=i)).strftime("%d/%m/%Y") for i in
				   reversed(range(num_days))]

	# Đếm tổng số lượng User tính đến mỗi ngày
	user_counts = [
		User.objects.filter(date_joined__date__lte=(today - timedelta(days=i))).count()
		for i in reversed(range(num_days))
	]

	# Đếm tổng số lượng Restaurants tính đến mỗi ngày
	restaurant_counts = [
		Restaurant.objects.filter(created_at__date__lte=(today - timedelta(days=i))).count()
		for i in reversed(range(num_days))
	]

	# Dữ liệu biểu đồ tổng User
	user_chart_data = {
		"labels": date_labels,
		"datasets": [
			{
				"label": "Total Users",
				"data": user_counts,
				"borderColor": "#3B82F6",
				"backgroundColor": "rgba(59, 130, 246, 0.2)",
				"fill": True,
			}
		],
	}

	# Dữ liệu biểu đồ tổng Restaurants
	restaurant_chart_data = {
		"labels": date_labels,
		"datasets": [
			{
				"label": "Total Restaurants",
				"data": restaurant_counts,
				"borderColor": "#F97316",
				"backgroundColor": "rgba(249, 115, 22, 0.2)",
				"fill": True,
			}
		],
	}

	# Send data to dashboard
	context.update(
		{
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

			"dauChartData": json.dumps({
				'datasets': [
					{'data': [0, 1, 3, 2, 5, 8, 7],
					 'borderColor': 'rgb(147 51 234)'
					 }
				],
				'labels': [
					'18/11/2024',
					'19/11/2024',
					'20/11/2024',
					'21/11/2024',
					'22/11/2024',
					'23/11/2024',
					'24/11/2024'
				]
			}),

			"dpsChartData": json.dumps({
				'datasets': [
					{'data': [7, 15, 12, 23, 5, 10, 18],
					 'borderColor': 'rgb(147 51 234)'
					 }
				],
				'labels': [
					'18/11/2024',
					'19/11/2024',
					'20/11/2024',
					'21/11/2024',
					'22/11/2024',
					'23/11/2024',
					'24/11/2024',
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

		}
	)
	return context
