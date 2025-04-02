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
	list_display = ("name", "location", "user", "description")
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
	"""
    Callback to prepare custom variables for index template which is used as dashboard
    template. It can be overridden in application by creating custom admin/index.html.
    """
	days_range = 15
	labels = []
	user_counts = []
	restaurant_counts = []

	for i in range(days_range):
		day = now() - timedelta(days=days_range - i - 1)
		labels.append(day.strftime("%Y-%m-%d"))

		# Tính tổng số lượng users và restaurants tính đến ngày hôm đó
		user_per_day = User.objects.filter(date_joined__lte=day.date()).count()
		restaurant_per_day = Restaurant.objects.filter(created_at__lte=day.date()).count()

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

		}
	)
	return context
